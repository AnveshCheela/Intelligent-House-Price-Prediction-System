import json
import boto3
import random
from datetime import datetime

# Initialize SQS client
sqs = boto3.client('sqs')

# Configuration - REPLACE WITH YOUR QUEUE URL
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/485824811208/property-stream-queue'

def lambda_handler(event, context):
    print("Starting UPDATED property data generation...")
    
    # Number of properties to generate
    num_properties = event.get('count', 50)
    
    generated_count = 0
    
    for i in range(num_properties):
        property_data = generate_updated_property_data(1000 + i)
        
        # Send to SQS
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(property_data)
        )
        
        generated_count += 1
        print(f"Generated property {i+1}: {property_data['house_id']}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successfully generated {generated_count} property records',
            'properties_generated': generated_count,
            'queue_url': QUEUE_URL
        })
    }

def generate_updated_property_data(house_id):
    """Generate property data matching Kaggle dataset scale"""
    
    # Base area calculation - match Kaggle dataset (7000-16000 range)
    bedrooms = random.randint(2, 5)
    base_area = random.randint(6000, 12000)
    
    # Generate ALL features from your dataset
    property_data = {
        'house_id': house_id,
        'timestamp': datetime.utcnow().isoformat(),
        
        # Core features - MATCH KAGGLE DATASET SCALE
        'area': base_area,
        'bedrooms': bedrooms,
        'bathrooms': random.randint(1, 4),
        'price': random.randint(5000000, 15000000),  # 5-15 million to match Kaggle
        
        # Additional dataset features
        'stories': random.randint(1, 4),
        'mainroad': random.choice(['yes', 'no']),
        'guestroom': random.choice(['yes', 'no']),
        'basement': random.choice(['yes', 'no']),
        'hotwaterheating': random.choice(['yes', 'no']),
        'airconditioning': random.choice(['yes', 'no']),
        'parking': random.randint(0, 3),
        'prefarea': random.choice(['yes', 'no']),
        'furnishingstatus': random.choice(['furnished', 'semi-furnished', 'unfurnished'])
    }
    
    return property_data