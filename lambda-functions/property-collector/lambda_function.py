import json
import boto3
import time
import uuid
import os
from datetime import datetime
from decimal import Decimal

# Configuration (env vars with fallbacks)
QUEUE_URL = os.environ.get('QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/485824811208/property-stream-queue')
S3_BUCKET = os.environ.get('PROCESSING_BUCKET', 'house-price-data-485824811208')
BATCH_METADATA_TABLE = os.environ.get('COLLECTION_TABLE', 'BatchMetadata')

# AWS Clients (module-level for Lambda container reuse)
sqs = boto3.client('sqs')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')


class AdaptiveBatchProcessor:
    def __init__(self):
        self.previous_rate = 0
        self.alpha = 0.7
        self.T1 = int(os.environ.get('OPTIMIZED_T1', 5))
        self.T2 = int(os.environ.get('OPTIMIZED_T2', 16))
        self.T3 = int(os.environ.get('OPTIMIZED_T3', 40))

        thresholds = {
            'T1': self.T1,
            'T2': self.T2,
            'T3': self.T3
        }
        print(f'🎯✅ USING ENVIRONMENT THRESHOLDS: {thresholds}')

    def predict_load(self, current_rate):
        if self.previous_rate == 0:
            self.previous_rate = current_rate
            return current_rate
        predicted = self.alpha * current_rate + (1 - self.alpha) * self.previous_rate
        self.previous_rate = predicted
        return predicted

    def determine_load_mode(self, predicted_rate):
        if predicted_rate <= self.T1:
            return 'low'
        elif predicted_rate <= self.T2:
            return 'medium'
        else:
            return 'high'

    def calculate_optimal_batch_size(self, predicted_rate, load_mode, queue_depth):
        # Factor 1: Base size from predicted rate (8 seconds worth of messages)
        base_size = predicted_rate * 8

        # Factor 2: Mode-adjusted size
        mode_multipliers = {'low': 0.6, 'medium': 0.9, 'high': 1.3}
        size_from_mode = base_size * mode_multipliers[load_mode]

        # Factor 3: Queue-depth-adjusted size
        if queue_depth < 100:
            size_from_queue = queue_depth * 0.8
        else:
            size_from_queue = min(queue_depth * 0.4, 800)

        # Factor 4: Max by payload (Lambda 6MB limit)
        max_by_payload = 1000

        # Factor 5: Max by timeout (processing time safety)
        max_by_timeout = 2000

        # Determine optimal from candidates
        candidates = [size_from_mode, size_from_queue, max_by_payload, max_by_timeout]
        optimal = min(candidates)
        optimal = max(50, min(optimal, 1000))

        return int(optimal)


def lambda_handler(event, context):
    # Initialize processor
    processor = AdaptiveBatchProcessor()

    # Get queue attributes
    queue_attrs = sqs.get_queue_attributes(
        QueueUrl=QUEUE_URL,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    queue_depth = int(queue_attrs['Attributes'].get('ApproximateNumberOfMessages', 0))

    # Calculate current rate
    current_rate = min(queue_depth / 60, 100)

    # Get predicted rate, load mode, and batch size
    predicted_rate = processor.predict_load(current_rate)
    load_mode = processor.determine_load_mode(predicted_rate)
    batch_size = processor.calculate_optimal_batch_size(predicted_rate, load_mode, queue_depth)

    # Map load_mode to max_wait_time
    wait_time_map = {'low': 8, 'medium': 5, 'high': 2}
    max_wait_time = wait_time_map[load_mode]

    # Map load_mode to Load_Mode_Number
    load_mode_number_map = {'low': 1, 'medium': 2, 'high': 3}
    load_mode_number = load_mode_number_map[load_mode]

    # Collect messages in a loop
    messages = []
    start_time = time.time()

    while len(messages) < batch_size and (time.time() - start_time) < max_wait_time:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=2
        )

        if 'Messages' in response:
            for msg in response['Messages']:
                body = json.loads(msg['Body'])
                messages.append({
                    'data': body,
                    'ReceiptHandle': msg['ReceiptHandle'],
                    'MessageId': msg['MessageId']
                })
                if len(messages) >= batch_size:
                    break

    # If no messages, return early
    if not messages:
        return {
            'statusCode': 200,
            'body': json.dumps('No messages')
        }

    # Target batch size for efficiency calculation
    target_batch_size = 50

    # Calculate metrics
    message_count = len(messages)
    invocation_reduction = (1 - 1 / message_count) * 100
    batch_efficiency = (message_count / target_batch_size) * 100

    # Log messages
    print(f'📊 Invocation Comparison: We used 1 vs Traditional {message_count}')
    print(f'Efficiency: {message_count} records/invocation ({invocation_reduction:.1f}% reduction)')
    print(f'📊 Batch Efficiency: {batch_efficiency:.1f}% ({message_count}/{target_batch_size} records)')

    # Publish CloudWatch metrics
    cloudwatch.put_metric_data(
        Namespace='Custom/HousePriceML',
        MetricData=[
            {
                'MetricName': 'Our_System_Invocations',
                'Value': 1,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Traditional_System_Invocations',
                'Value': message_count,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Records_Per_Invocation',
                'Value': message_count,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Invocation_Reduction_Percentage',
                'Value': invocation_reduction,
                'Unit': 'Percent'
            },
            {
                'MetricName': 'Batch_Efficiency_Percentage',
                'Value': batch_efficiency,
                'Unit': 'Percent'
            },
            {
                'MetricName': 'Actual_Batch_Size',
                'Value': message_count,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Target_Batch_Size',
                'Value': target_batch_size,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Load_Mode_Number',
                'Value': load_mode_number,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Cost_Savings_Scaled',
                'Value': message_count - 1,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Our_Cost_Estimate',
                'Value': 0.0000002 * 1,
                'Unit': 'None'
            },
            {
                'MetricName': 'Traditional_Cost_Estimate',
                'Value': 0.0000002 * message_count,
                'Unit': 'None'
            }
        ]
    )

    # Store batch in S3
    batch_id = str(uuid.uuid4())
    batch_data = {
        'batch_id': batch_id,
        'timestamp': datetime.utcnow().isoformat(),
        'record_count': message_count,
        'load_mode': load_mode,
        'records': [msg['data'] for msg in messages]
    }

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=f'batches/{batch_id}.json',
        Body=json.dumps(batch_data),
        ContentType='application/json'
    )

    # Store metadata in DynamoDB
    table = dynamodb.Table(BATCH_METADATA_TABLE)
    table.put_item(
        Item={
            'batch_id': batch_id,
            'record_count': message_count,
            'load_mode': load_mode,
            'predicted_rate': Decimal(str(round(predicted_rate, 4))),
            'batch_size': batch_size,
            'queue_depth': queue_depth,
            'timestamp': datetime.utcnow().isoformat()
        }
    )

    # Delete processed messages from SQS (batch delete, max 10 per call)
    receipt_handles = [{'Id': str(i), 'ReceiptHandle': msg['ReceiptHandle']} for i, msg in enumerate(messages)]

    for i in range(0, len(receipt_handles), 10):
        batch = receipt_handles[i:i + 10]
        sqs.delete_message_batch(
            QueueUrl=QUEUE_URL,
            Entries=batch
        )

    # Return response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': message_count,
            'efficiency': f'{batch_efficiency:.1f}%',
            'load_mode': load_mode,
            'batch_size': batch_size
        })
    }