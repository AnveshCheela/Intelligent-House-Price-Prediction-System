#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting House Price Prediction Deployment${NC}"

# Configuration
STACK_NAME="house-price-pipeline"
REGION="us-east-1"
ENVIRONMENT="production"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install it first.${NC}"
    exit 1
fi

# Create Lambda deployment packages
echo -e "${YELLOW}📦 Creating Lambda deployment packages...${NC}"

# Data Generator
cd lambda-functions/data-generator
pip install -r requirements.txt -t . --quiet
zip -r ../../data-generator.zip . > /dev/null
cd ../..

# Property Collector
cd lambda-functions/property-collector
pip install -r requirements.txt -t . --quiet
zip -r ../../property-collector.zip . > /dev/null
cd ../..

# Property Processor
cd lambda-functions/property-processor
pip install -r requirements.txt -t . --quiet
zip -r ../../property-processor.zip . > /dev/null
cd ../..

# Threshold Optimizer
cd lambda-functions/threshold-optimizer
pip install -r requirements.txt -t . --quiet
zip -r ../../threshold-optimizer.zip . > /dev/null
cd ../..

echo -e "${GREEN}✅ Lambda packages created${NC}"

# Deploy CloudFormation stack
echo -e "${YELLOW}☁️ Deploying CloudFormation stack...${NC}"

aws cloudformation deploy \
    --template-file cloudformation/template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides EnvironmentName=$ENVIRONMENT \
    --capabilities CAPABILITY_IAM \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CloudFormation stack deployed successfully${NC}"
else
    echo -e "${RED}❌ CloudFormation deployment failed${NC}"
    exit 1
fi

# Get stack outputs
echo -e "${YELLOW}📋 Getting stack outputs...${NC}"
QUEUE_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='PropertyQueueURL'].OutputValue" \
    --output text \
    --region $REGION)

# Update Lambda function code
echo -e "${YELLOW}⚙️ Updating Lambda function code...${NC}"

# Get function names
DATA_GENERATOR_FN="$ENVIRONMENT-data-generator"
PROPERTY_COLLECTOR_FN="$ENVIRONMENT-property-collector"
PROPERTY_PROCESSOR_FN="$ENVIRONMENT-property-processor"
THRESHOLD_OPTIMIZER_FN="$ENVIRONMENT-threshold-optimizer"

# Update each function
aws lambda update-function-code \
    --function-name $DATA_GENERATOR_FN \
    --zip-file fileb://data-generator.zip \
    --region $REGION > /dev/null

aws lambda update-function-code \
    --function-name $PROPERTY_COLLECTOR_FN \
    --zip-file fileb://property-collector.zip \
    --region $REGION > /dev/null

aws lambda update-function-code \
    --function-name $PROPERTY_PROCESSOR_FN \
    --zip-file fileb://property-processor.zip \
    --region $REGION > /dev/null

aws lambda update-function-code \
    --function-name $THRESHOLD_OPTIMIZER_FN \
    --zip-file fileb://threshold-optimizer.zip \
    --region $REGION > /dev/null

echo -e "${GREEN}✅ Lambda functions updated${NC}"

# Clean up zip files
rm -f data-generator.zip property-collector.zip property-processor.zip threshold-optimizer.zip

# Test the setup
echo -e "${YELLOW}🧪 Testing the setup...${NC}"

# Invoke data generator
aws lambda invoke \
    --function-name $DATA_GENERATOR_FN \
    --payload '{"count": 10, "batch_mode": true}' \
    --region $REGION \
    response.json > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test successful! Check response.json for details${NC}"
else
    echo -e "${RED}❌ Test failed${NC}"
fi

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo -e "Next steps:"
echo -e "1. Check CloudWatch dashboards for metrics"
echo -e "2. Monitor DynamoDB tables for processed data"
echo -e "3. Set up SNS email subscription for alerts"
echo -e "4. Review CloudWatch Logs for any errors"