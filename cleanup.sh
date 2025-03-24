#!/bin/bash
# AWS RAG Workshop Cleanup Script Wrapper

# Display help message
show_help() {
    echo "AWS RAG Workshop Cleanup Script"
    echo ""
    echo "Usage: ./cleanup.sh [OPTIONS]"
    echo ""
    echo "This script helps you clean up all AWS resources created during the AWS RAG Workshop."
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -b, --bucket NAME          S3 bucket name (required)"
    echo "  -r, --region REGION        AWS region (default: from AWS config)"
    echo "  -a, --agent NAME           Bedrock Agent name"
    echo "  -k, --kb-names NAMES       Knowledge Base names (space-separated, in quotes)"
    echo "  -d, --domain NAME          SageMaker domain name"
    echo "  -s, --space NAME           SageMaker space name (default: advanced-rag-workshop)"
    echo "  --dry-run                  Perform a dry run without deleting resources"
    echo ""
    echo "Example:"
    echo "  ./cleanup.sh --bucket bedrock-kb-workshop-123456789012 --region us-west-2"
    echo ""
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if boto3 is installed
if ! python3 -c "import boto3" &> /dev/null; then
    echo "Warning: boto3 is not installed. Attempting to install it..."
    pip install boto3
    
    # Check if installation was successful
    if ! python3 -c "import boto3" &> /dev/null; then
        echo "Error: Failed to install boto3. Please install it manually with 'pip install boto3'."
        exit 1
    fi
    
    echo "boto3 installed successfully."
fi

# Default values
BUCKET_NAME=""
REGION=""
AGENT_NAME=""
KB_NAMES=""
DOMAIN_NAME=""
SPACE_NAME=""
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--bucket)
            BUCKET_NAME="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -a|--agent)
            AGENT_NAME="$2"
            shift 2
            ;;
        -k|--kb-names)
            KB_NAMES="$2"
            shift 2
            ;;
        -d|--domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        -s|--space)
            SPACE_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if bucket name is provided
if [ -z "$BUCKET_NAME" ]; then
    echo "Error: S3 bucket name is required."
    echo "Use --bucket to specify the S3 bucket name."
    echo ""
    show_help
    exit 1
fi

# Build the command
CMD="python3 cleanup.py --bucket-name $BUCKET_NAME"

if [ ! -z "$REGION" ]; then
    CMD="$CMD --region $REGION"
fi

if [ ! -z "$AGENT_NAME" ]; then
    CMD="$CMD --agent-name \"$AGENT_NAME\""
fi

if [ ! -z "$KB_NAMES" ]; then
    CMD="$CMD --kb-names $KB_NAMES"
fi

if [ ! -z "$DOMAIN_NAME" ]; then
    CMD="$CMD --sagemaker-domain-name \"$DOMAIN_NAME\""
fi

if [ ! -z "$SPACE_NAME" ]; then
    CMD="$CMD --sagemaker-space-name \"$SPACE_NAME\""
fi

if [ "$DRY_RUN" = true ]; then
    CMD="$CMD --dry-run"
fi

# Print the command
echo "Executing: $CMD"
echo ""

# Execute the command
eval $CMD
