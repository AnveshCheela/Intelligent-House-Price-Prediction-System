import json
import boto3
import csv
import pickle
import base64
import random
import os
from datetime import datetime
from decimal import Decimal
from io import StringIO

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROCESSED_RESULTS_TABLE = os.environ.get('PROCESSED_RESULTS_TABLE', 'ProcessedResults')
BATCH_METADATA_TABLE = os.environ.get('BATCH_METADATA_TABLE', 'BatchMetadata')
DATASET_BUCKET = os.environ.get('DATASET_BUCKET', 'house-price-datasets-485824811208')

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')


# ---------------------------------------------------------------------------
# ScikitLearnPredictor
# ---------------------------------------------------------------------------
class ScikitLearnPredictor:
    """ML predictor that trains on Housing.csv and persists the best model to
    DynamoDB so that subsequent Lambda cold-starts can skip training."""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.load_or_train_model()

    # ---- persistence -------------------------------------------------------
    def load_or_train_model(self):
        """Attempt to load a previously-persisted model from DynamoDB.
        Fall back to training from the dataset if anything goes wrong."""
        try:
            table = dynamodb.Table(BATCH_METADATA_TABLE)
            response = table.get_item(Key={'batch_id': 'scikit_ml_model'})
            item = response['Item']
            model_bytes = base64.b64decode(item['model_bytes'])
            payload = pickle.loads(model_bytes)
            self.model = payload['model']
            self.scaler = payload['scaler']
            self.is_trained = True
            print("Model loaded successfully from DynamoDB")
        except Exception as e:
            print(f"Could not load model from DynamoDB ({e}). Training from dataset...")
            self.train_with_dataset()

    # ---- training ----------------------------------------------------------
    def train_with_dataset(self):
        """Download Housing.csv from S3, train three candidate models, pick the
        best one by R² score, and persist it to DynamoDB."""
        try:
            # ------ load CSV from S3 ----------------------------------------
            obj = s3_client.get_object(Bucket=DATASET_BUCKET, Key='Housing.csv')
            csv_text = obj['Body'].read().decode('utf-8')
            reader = csv.DictReader(StringIO(csv_text))

            X = []
            y = []

            for row in reader:
                features = [
                    float(row['area']),
                    float(row['bedrooms']),
                    float(row['bathrooms']),
                    float(row['stories']),
                    float(row['parking']),
                    1.0 if row['mainroad'].strip().lower() == 'yes' else 0.0,
                    1.0 if row['guestroom'].strip().lower() == 'yes' else 0.0,
                    1.0 if row['basement'].strip().lower() == 'yes' else 0.0,
                    1.0 if row['hotwaterheating'].strip().lower() == 'yes' else 0.0,
                    1.0 if row['airconditioning'].strip().lower() == 'yes' else 0.0,
                    1.0 if row['prefarea'].strip().lower() == 'yes' else 0.0,
                    2.0 if row['furnishingstatus'].strip().lower() == 'furnished'
                    else (1.0 if row['furnishingstatus'].strip().lower() == 'semi-furnished' else 0.0),
                ]
                X.append(features)
                y.append(float(row['price']))

            # ------ train / test split (first 80 % train) -------------------
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]

            # ------ candidate models ----------------------------------------
            candidates = {
                'LinearRegression': LinearRegression(),
                'Ridge': Ridge(alpha=1.0),
                'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
            }

            scores = {}
            for name, mdl in candidates.items():
                mdl.fit(X_train, y_train)
                pred = mdl.predict(X_test)
                scores[name] = r2_score(y_test, pred)

            best_name = max(scores, key=scores.get)
            best_model = candidates[best_name]

            # ------ scale & re-train best model -----------------------------
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            best_model.fit(X_train_scaled, y_train)
            self.model = best_model
            self.is_trained = True

            # ------ persist to DynamoDB -------------------------------------
            payload = pickle.dumps({'model': self.model, 'scaler': self.scaler})
            encoded = base64.b64encode(payload).decode('utf-8')

            table = dynamodb.Table(BATCH_METADATA_TABLE)
            table.put_item(Item={
                'batch_id': 'scikit_ml_model',
                'model_bytes': encoded,
            })

            # ------ report --------------------------------------------------
            print(f"Best model: {best_name}")
            for name, score in scores.items():
                print(f"  {name} R² = {score:.4f}")

        except Exception as e:
            print(f"WARNING: training failed ({e}). Falling back to heuristic mode.")
            self.is_trained = False

    # ---- prediction --------------------------------------------------------
    def predict(self, property_data):
        """Return an integer predicted price for *property_data* (dict)."""
        area = float(property_data.get('area', 0))
        bedrooms = float(property_data.get('bedrooms', 0))
        bathrooms = float(property_data.get('bathrooms', 0))
        stories = float(property_data.get('stories', 0))
        parking = float(property_data.get('parking', 0))

        mainroad = 1.0 if str(property_data.get('mainroad', 'no')).strip().lower() == 'yes' else 0.0
        guestroom = 1.0 if str(property_data.get('guestroom', 'no')).strip().lower() == 'yes' else 0.0
        basement = 1.0 if str(property_data.get('basement', 'no')).strip().lower() == 'yes' else 0.0
        hotwaterheating = 1.0 if str(property_data.get('hotwaterheating', 'no')).strip().lower() == 'yes' else 0.0
        airconditioning = 1.0 if str(property_data.get('airconditioning', 'no')).strip().lower() == 'yes' else 0.0
        prefarea = 1.0 if str(property_data.get('prefarea', 'no')).strip().lower() == 'yes' else 0.0

        furnishing_raw = str(property_data.get('furnishingstatus', 'unfurnished')).strip().lower()
        if furnishing_raw == 'furnished':
            furnishing = 2.0
        elif furnishing_raw == 'semi-furnished':
            furnishing = 1.0
        else:
            furnishing = 0.0

        features = [[
            area, bedrooms, bathrooms, stories, parking,
            mainroad, guestroom, basement, hotwaterheating,
            airconditioning, prefarea, furnishing,
        ]]

        if self.is_trained and self.model is not None:
            scaled = self.scaler.transform(features)
            predicted_price = self.model.predict(scaled)[0]
        else:
            predicted_price = (
                (area * 800)
                + (bedrooms * 500000)
                + (bathrooms * 300000)
                + (stories * 200000)
                + (parking * 150000)
            )
            predicted_price = max(1750000, min(13300000, predicted_price))

        return int(predicted_price)


# ---------------------------------------------------------------------------
# CloudWatch metrics
# ---------------------------------------------------------------------------
def publish_ml_metrics(processed_results):
    """Publish model-accuracy and prediction-distribution metrics to
    CloudWatch under the Custom/HousePriceML namespace."""
    if not processed_results:
        return

    avg_accuracy = sum(r['accuracy'] for r in processed_results) / len(processed_results)

    under_5m = 0
    between_5m_10m = 0
    over_10m = 0

    for r in processed_results:
        pred = r['predicted_price']
        if pred < 5_000_000:
            under_5m += 1
        elif pred <= 10_000_000:
            between_5m_10m += 1
        else:
            over_10m += 1

    cloudwatch.put_metric_data(
        Namespace='Custom/HousePriceML',
        MetricData=[
            {'MetricName': 'Model_Accuracy', 'Value': avg_accuracy, 'Unit': 'Percent'},
            {'MetricName': 'Records_Processed', 'Value': len(processed_results), 'Unit': 'Count'},
            {'MetricName': 'Predictions_Under_5M', 'Value': under_5m, 'Unit': 'Count'},
            {'MetricName': 'Predictions_5M_10M', 'Value': between_5m_10m, 'Unit': 'Count'},
            {'MetricName': 'Predictions_Over_10M', 'Value': over_10m, 'Unit': 'Count'},
        ],
    )


# ---------------------------------------------------------------------------
# Module-level predictor (reused across Lambda warm starts)
# ---------------------------------------------------------------------------
predictor = ScikitLearnPredictor()


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------
def lambda_handler(event, context):
    """Process a batch of property records dropped into S3 by the ingestion
    pipeline, run ML predictions, store results, and publish metrics."""

    # ------ locate the batch file in S3 -------------------------------------
    s3_record = event['Records'][0]['s3']
    s3_bucket = s3_record['bucket']['name']
    s3_key = s3_record['object']['key']

    print(f"Processing batch: s3://{s3_bucket}/{s3_key}")

    # ------ download & parse ------------------------------------------------
    obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
    batch_data = json.loads(obj['Body'].read().decode('utf-8'))

    results_table = dynamodb.Table(PROCESSED_RESULTS_TABLE)
    processed_results = []

    for record in batch_data:
        actual_price = float(record['price'])
        predicted_price = predictor.predict(record)

        accuracy = max(0.0, 100.0 - abs(actual_price - predicted_price) / actual_price * 100.0)

        processed_record = {
            'house_id': str(record.get('house_id', str(random.randint(100000, 999999)))),
            'timestamp': datetime.utcnow().isoformat(),
            'area': Decimal(str(record.get('area', 0))),
            'bedrooms': Decimal(str(record.get('bedrooms', 0))),
            'bathrooms': Decimal(str(record.get('bathrooms', 0))),
            'price': Decimal(str(actual_price)),
            'predicted_price': Decimal(str(predicted_price)),
            'prediction_accuracy': Decimal(str(round(accuracy, 2))),
            'price_difference': Decimal(str(actual_price - predicted_price)),
        }

        results_table.put_item(Item=processed_record)

        processed_results.append({
            'accuracy': accuracy,
            'predicted_price': predicted_price,
        })

    # ------ metrics ---------------------------------------------------------
    publish_ml_metrics(processed_results)

    avg_accuracy = (
        sum(r['accuracy'] for r in processed_results) / len(processed_results)
        if processed_results
        else 0.0
    )

    print(f"Processed {len(processed_results)} records — avg accuracy: {avg_accuracy:.2f}%")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'records_processed': len(processed_results),
            'average_accuracy': round(avg_accuracy, 2),
        }),
    }