# AWS RAG Workshop Cleanup Script

This script helps you clean up all AWS resources created during the AWS RAG Workshop. It will delete:

1. Amazon Bedrock Agents
2. Amazon Bedrock Knowledge Bases (both OpenSearch and Neptune Analytics/GraphRAG)
3. S3 bucket and all its contents
4. SageMaker resources (spaces and optionally domains)

## Prerequisites

- Python 3.6 or later
- AWS CLI configured with appropriate credentials
- Boto3 library installed (`pip install boto3`)

## Usage

```bash
python cleanup.py --bucket-name YOUR_BUCKET_NAME [OPTIONS]
```

### Required Arguments

- `--bucket-name`: The name of the S3 bucket created for the workshop (e.g., `bedrock-kb-workshop-123456789012`)

### Optional Arguments

- `--region`: AWS region (default: uses the default region from your AWS config)
- `--agent-name`: Bedrock Agent name (if you remember it)
- `--kb-names`: Knowledge Base names (default: `aosrag-workshop graphrag-workshop`)
- `--sagemaker-domain-name`: SageMaker domain name
- `--sagemaker-space-name`: SageMaker space name (default: `advanced-rag-workshop`)
- `--dry-run`: Perform a dry run without actually deleting resources

## Examples

### Basic Usage

```bash
python cleanup.py --bucket-name bedrock-kb-workshop-123456789012
```

### Specify Region

```bash
python cleanup.py --bucket-name bedrock-kb-workshop-123456789012 --region us-west-2
```

### Dry Run (No Actual Deletion)

```bash
python cleanup.py --bucket-name bedrock-kb-workshop-123456789012 --dry-run
```

### Specify Agent and Knowledge Base Names

```bash
python cleanup.py --bucket-name bedrock-kb-workshop-123456789012 --agent-name my-agent --kb-names aosrag-workshop graphrag-workshop
```

## Interactive Mode

If you don't provide specific resource names, the script will run in interactive mode:

1. It will list all available resources of each type
2. You can select which specific resources to delete
3. You can choose to delete all resources of a type or skip deletion entirely

## Safety Features

- The script includes a `--dry-run` option to preview what would be deleted without actually deleting anything
- Interactive prompts ask for confirmation before deleting critical resources
- Detailed logging shows exactly what's happening at each step

## Troubleshooting

If you encounter any errors:

1. Check that your AWS credentials have the necessary permissions
2. Verify that the resource names and IDs are correct
3. Some resources may have dependencies that need to be deleted first
4. Check the error messages for specific issues

## Note

Some AWS resources may take time to delete completely. The script initiates the deletion process, but you may need to check the AWS Console to confirm that all resources have been fully removed.
