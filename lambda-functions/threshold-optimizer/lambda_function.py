"""
ThresholdOptimizer Lambda Function — The Brain of the System
=============================================================
Dynamically calculates optimal T1/T2/T3 thresholds based on:
  - Current traffic patterns (SQS queue depth)
  - Model performance scores (DynamoDB prediction accuracy)
  - Cost efficiency metrics (CloudWatch invocation reduction)

Then pushes the optimized thresholds to the PropertyCollector Lambda
environment, persists results to DynamoDB, publishes CloudWatch metrics,
and fires SNS alerts on significant accuracy degradation.
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

# ---------------------------------------------------------------------------
# Module-level configuration
# ---------------------------------------------------------------------------
RESULTS_TABLE = os.environ.get('RESULTS_TABLE', 'ProcessedResults')
OPTIMIZATION_TABLE = os.environ.get('OPTIMIZATION_TABLE', 'OptimizationHistory')
SNS_TOPIC_ARN = os.environ.get(
    'SNS_TOPIC_ARN',
    'arn:aws:sns:us-east-1:485824811208:production-ml-alerts',
)
COLLECTOR_FUNCTION_NAME = os.environ.get(
    'COLLECTOR_FUNCTION_NAME',
    'production-property-collector',
)
QUEUE_URL = os.environ.get(
    'QUEUE_URL',
    'https://sqs.us-east-1.amazonaws.com/485824811208/property-stream-queue',
)

# AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')
sqs = boto3.client('sqs')
lambda_client = boto3.client('lambda')


# ---------------------------------------------------------------------------
# Traffic helpers
# ---------------------------------------------------------------------------

def classify_traffic_level(queue_depth):
    """Classify current traffic into low / medium / high buckets."""
    if queue_depth < 20:
        return 'low'
    elif queue_depth < 100:
        return 'medium'
    else:
        return 'high'


def get_base_thresholds(traffic_level):
    """Return the baseline T1/T2/T3 values for a given traffic level."""
    levels = {
        'low':    {'T1': 5,  'T2': 25,  'T3': 50},
        'medium': {'T1': 11, 'T2': 50,  'T3': 100},
        'high':   {'T1': 20, 'T2': 100, 'T3': 226},
    }
    return levels.get(traffic_level, levels['medium'])


# ---------------------------------------------------------------------------
# Metric collection
# ---------------------------------------------------------------------------

def get_current_queue_depth():
    """Poll SQS for the approximate number of messages in the queue."""
    try:
        response = sqs.get_queue_attributes(
            QueueUrl=QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages'],
        )
        return int(response['Attributes']['ApproximateNumberOfMessages'])
    except Exception as exc:
        print(f'⚠️  Could not read queue depth: {exc}')
        return 0


def analyze_traffic_pattern(metrics):
    """Determine the current traffic level from the live queue depth."""
    queue_depth = get_current_queue_depth()
    return classify_traffic_level(queue_depth)


def calculate_performance_score(metrics):
    """
    Scan recent predictions from the ProcessedResults table and compute
    the mean prediction accuracy normalised to 0-1.
    """
    try:
        table = dynamodb.Table(RESULTS_TABLE)
        response = table.scan(Limit=200)
        items = response.get('Items', [])

        if not items:
            print('ℹ️  No items in ProcessedResults — using default performance score.')
            return 0.7

        accuracies = []
        for item in items:
            acc = item.get('prediction_accuracy')
            if acc is not None:
                try:
                    accuracies.append(float(acc))
                except (ValueError, TypeError):
                    continue

        if not accuracies:
            print('ℹ️  No valid accuracy values found — using default.')
            return 0.7

        mean_accuracy = sum(accuracies) / len(accuracies)
        print(f'📊 Mean accuracy from {len(accuracies)} predictions: {mean_accuracy:.2f}%')
        return mean_accuracy / 100.0
    except Exception as exc:
        print(f'⚠️  Error calculating performance score: {exc}')
        return 0.7


def compute_cost_metrics(metrics):
    """
    Fetch the Invocation_Reduction_Percentage metric from CloudWatch
    for the last 10 minutes and return a normalised 0-1 efficiency score.
    """
    try:
        now = datetime.utcnow()
        response = cloudwatch.get_metric_statistics(
            Namespace='Custom/HousePriceML',
            MetricName='Invocation_Reduction_Percentage',
            StartTime=now - timedelta(minutes=10),
            EndTime=now,
            Period=600,
            Statistics=['Average'],
        )

        datapoints = response.get('Datapoints', [])
        if not datapoints:
            print('ℹ️  No cost metric datapoints — using default efficiency.')
            return 0.9

        # Use the most recent datapoint
        latest = max(datapoints, key=lambda dp: dp['Timestamp'])
        value = latest['Average']
        print(f'💰 Invocation reduction: {value:.2f}%')
        return value / 100.0
    except Exception as exc:
        print(f'⚠️  Error computing cost metrics: {exc}')
        return 0.9


# ---------------------------------------------------------------------------
# Threshold calculation
# ---------------------------------------------------------------------------

def calculate_optimal_thresholds(metrics):
    """
    Core optimisation logic.  Combines traffic, performance, and cost
    signals into a set of clamped T1/T2/T3 thresholds.
    """
    traffic_level = analyze_traffic_pattern(metrics)
    system_performance = calculate_performance_score(metrics)
    cost_efficiency = compute_cost_metrics(metrics)
    base_values = get_base_thresholds(traffic_level)

    performance_factor = max(0.5, min(1.5, system_performance * 1.2))

    new_T1 = int(base_values['T1'] * performance_factor)
    new_T2 = int(base_values['T2'] * (1 + cost_efficiency) / 2)
    new_T3 = int(base_values['T3'] * system_performance)

    # Clamp into safe operating ranges
    T1 = max(2, min(new_T1, 50))
    T2 = max(T1 + 1, min(new_T2, 200))
    T3 = max(T2 + 1, min(new_T3, 500))

    print(f'🧠 Traffic={traffic_level}  perf={system_performance:.3f}  '
          f'cost_eff={cost_efficiency:.3f}  perf_factor={performance_factor:.3f}')
    print(f'🔧 Calculated thresholds → T1={T1}  T2={T2}  T3={T3}')

    return {
        'T1': T1,
        'T2': T2,
        'T3': T3,
        'traffic_level': traffic_level,
        'performance_factor': performance_factor,
        'cost_efficiency': cost_efficiency,
        'system_performance': system_performance,
    }


# ---------------------------------------------------------------------------
# Actuators — push thresholds into the system
# ---------------------------------------------------------------------------

def update_collector_environment(thresholds):
    """
    Hot-patch the PropertyCollector Lambda's environment variables with
    the newly optimised T1/T2/T3 values.
    """
    try:
        config = lambda_client.get_function_configuration(
            FunctionName=COLLECTOR_FUNCTION_NAME,
        )
        env_vars = config.get('Environment', {}).get('Variables', {})

        env_vars['OPTIMIZED_T1'] = str(thresholds['T1'])
        env_vars['OPTIMIZED_T2'] = str(thresholds['T2'])
        env_vars['OPTIMIZED_T3'] = str(thresholds['T3'])

        lambda_client.update_function_configuration(
            FunctionName=COLLECTOR_FUNCTION_NAME,
            Environment={'Variables': env_vars},
        )
        print(f'✅ Updated {COLLECTOR_FUNCTION_NAME} env → '
              f"T1={thresholds['T1']}, T2={thresholds['T2']}, T3={thresholds['T3']}")
    except Exception as exc:
        print(f'⚠️  Failed to update collector environment: {exc}')
        print('↪  Falling back to DynamoDB threshold store.')
        save_thresholds_to_dynamodb(thresholds)


def save_thresholds_to_dynamodb(thresholds):
    """Persist the optimisation result to the OptimizationHistory table."""
    try:
        table = dynamodb.Table(OPTIMIZATION_TABLE)
        optimization_id = f"opt-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.utcnow().isoformat()

        table.put_item(Item={
            'optimization_id': optimization_id,
            'timestamp': timestamp,
            'thresholds': {
                'T1': Decimal(str(thresholds['T1'])),
                'T2': Decimal(str(thresholds['T2'])),
                'T3': Decimal(str(thresholds['T3'])),
            },
            'performance_metrics': {
                'system_performance': Decimal(str(round(thresholds.get('system_performance', 0), 4))),
                'cost_efficiency': Decimal(str(round(thresholds.get('cost_efficiency', 0), 4))),
                'performance_factor': Decimal(str(round(thresholds.get('performance_factor', 0), 4))),
            },
            'traffic_level': thresholds.get('traffic_level', 'unknown'),
        })
        print(f'💾 Saved optimisation {optimization_id} to {OPTIMIZATION_TABLE}')
    except Exception as exc:
        print(f'⚠️  Error saving thresholds to DynamoDB: {exc}')


def publish_optimization_metrics(thresholds):
    """Push the latest threshold and confidence metrics to CloudWatch."""
    try:
        now = datetime.utcnow()
        system_performance = thresholds.get('system_performance', 0.7)

        metric_data = [
            {
                'MetricName': 'Threshold_T1',
                'Timestamp': now,
                'Value': float(thresholds['T1']),
                'Unit': 'Count',
            },
            {
                'MetricName': 'Threshold_T2',
                'Timestamp': now,
                'Value': float(thresholds['T2']),
                'Unit': 'Count',
            },
            {
                'MetricName': 'Threshold_T3',
                'Timestamp': now,
                'Value': float(thresholds['T3']),
                'Unit': 'Count',
            },
            {
                'MetricName': 'Optimization_Confidence_Score',
                'Timestamp': now,
                'Value': float(system_performance),
                'Unit': 'None',
            },
            {
                'MetricName': 'Current_Model_Accuracy',
                'Timestamp': now,
                'Value': float(system_performance * 100),
                'Unit': 'Percent',
            },
        ]

        cloudwatch.put_metric_data(
            Namespace='Custom/HousePriceML',
            MetricData=metric_data,
        )
        print(f'📈 Published {len(metric_data)} optimisation metrics to CloudWatch')
    except Exception as exc:
        print(f'⚠️  Error publishing CloudWatch metrics: {exc}')


# ---------------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------------

def send_alert(optimization_id, metrics):
    """
    Fire an SNS alert when model accuracy has degraded by more than 10 %
    from the 85 % baseline.
    """
    try:
        current_accuracy = metrics.get('system_performance', 0.7) * 100
        baseline_accuracy = 85.0
        degradation = baseline_accuracy - current_accuracy

        if degradation <= 10:
            return  # No alert needed

        subject = f'🚨 ML Accuracy Degradation Alert — {degradation:.1f}% drop'
        message = (
            f'Accuracy Degradation Detected\n'
            f'{"=" * 40}\n\n'
            f'Optimization ID : {optimization_id}\n'
            f'Current Accuracy: {current_accuracy:.2f}%\n'
            f'Baseline        : {baseline_accuracy:.2f}%\n'
            f'Degradation     : {degradation:.2f}%\n\n'
            f'Action Items:\n'
            f'  1. Review recent training data quality\n'
            f'  2. Check feature pipeline for anomalies\n'
            f'  3. Consider triggering a model retrain\n'
            f'  4. Inspect DynamoDB ProcessedResults for outliers\n\n'
            f'Timestamp: {datetime.utcnow().isoformat()}Z\n'
        )

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100],  # SNS subject max 100 chars
            Message=message,
        )
        print(f'🚨 Alert sent — accuracy degradation of {degradation:.1f}%')
    except Exception as exc:
        print(f'⚠️  Error sending SNS alert: {exc}')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    """AWS Lambda entry point for the ThresholdOptimizer."""
    print('🎯 Starting threshold optimizer...')

    try:
        # Metrics dict is a placeholder; each helper fetches its own data
        metrics = {}

        # 1. Calculate optimal thresholds
        thresholds = calculate_optimal_thresholds(metrics)

        # 2. Push to collector Lambda environment
        update_collector_environment(thresholds)

        # 3. Persist to DynamoDB
        save_thresholds_to_dynamodb(thresholds)

        # 4. Publish CloudWatch metrics
        publish_optimization_metrics(thresholds)

        # 5. Check for accuracy degradation and alert if needed
        current_accuracy = thresholds.get('system_performance', 0.7) * 100
        baseline_accuracy = 85.0
        degradation = baseline_accuracy - current_accuracy
        if degradation > 10:
            optimization_id = f"opt-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            send_alert(optimization_id, thresholds)

        print(f"✅ Optimisation complete — T1={thresholds['T1']}  "
              f"T2={thresholds['T2']}  T3={thresholds['T3']}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Threshold optimization completed successfully',
                'thresholds': {
                    'T1': thresholds['T1'],
                    'T2': thresholds['T2'],
                    'T3': thresholds['T3'],
                },
                'traffic_level': thresholds['traffic_level'],
                'system_performance': round(thresholds['system_performance'], 4),
                'cost_efficiency': round(thresholds['cost_efficiency'], 4),
                'performance_factor': round(thresholds['performance_factor'], 4),
                'timestamp': datetime.utcnow().isoformat(),
            }),
        }

    except Exception as exc:
        print(f'❌ Threshold optimisation failed: {exc}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Threshold optimization failed',
                'error': str(exc),
                'timestamp': datetime.utcnow().isoformat(),
            }),
        }