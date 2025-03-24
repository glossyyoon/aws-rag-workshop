#!/usr/bin/env python3
"""
Cleanup script for AWS RAG Workshop resources.
This script will delete all resources created during the workshop.
"""

import boto3
import time
import sys
import argparse
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Cleanup AWS RAG Workshop resources')
    parser.add_argument('--region', type=str, default=None, 
                        help='AWS region (default: use default region from AWS config)')
    parser.add_argument('--bucket-name', type=str, required=True,
                        help='S3 bucket name created for the workshop (e.g., bedrock-kb-workshop-123456789012)')
    parser.add_argument('--agent-name', type=str, default='',
                        help='Bedrock Agent name (if you remember it)')
    parser.add_argument('--kb-names', type=str, nargs='+', default=['aosrag-workshop', 'graphrag-workshop'],
                        help='Knowledge Base names (default: aosrag-workshop graphrag-workshop)')
    parser.add_argument('--sagemaker-domain-name', type=str, default='default-1234567890',
                        help='SageMaker domain name (if you want to delete it)')
    parser.add_argument('--sagemaker-space-name', type=str, default='advanced-rag-workshop',
                        help='SageMaker space name (default: advanced-rag-workshop)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Perform a dry run without actually deleting resources')
    
    return parser.parse_args()

def get_session(region=None):
    """Create and return a boto3 session"""
    return boto3.session.Session(region_name=region)

def delete_bedrock_agent(agent_name, bedrock_agent_client, dry_run=False):
    """Delete Bedrock Agent"""
    try:
        # List all agents to find the one with the matching name
        logger.info(f"Looking for Bedrock Agent: {agent_name}")
        
        if not agent_name:
            logger.info("No agent name provided, listing all agents...")
            response = bedrock_agent_client.list_agents()
            agents = response.get('agentSummaries', [])
            
            if not agents:
                logger.info("No Bedrock Agents found")
                return
            
            logger.info(f"Found {len(agents)} Bedrock Agents:")
            for i, agent in enumerate(agents):
                logger.info(f"  {i+1}. {agent['agentName']} (ID: {agent['agentId']})")
            
            try:
                choice = input("Enter the number of the agent to delete (or 'all' to delete all, or 'skip' to skip): ")
                if choice.lower() == 'skip':
                    logger.info("Skipping Bedrock Agent deletion")
                    return
                elif choice.lower() == 'all':
                    agent_ids = [agent['agentId'] for agent in agents]
                else:
                    idx = int(choice) - 1
                    if idx < 0 or idx >= len(agents):
                        logger.error("Invalid choice")
                        return
                    agent_ids = [agents[idx]['agentId']]
            except ValueError:
                logger.error("Invalid input")
                return
        else:
            # Find agent by name
            response = bedrock_agent_client.list_agents()
            agents = response.get('agentSummaries', [])
            agent_ids = [agent['agentId'] for agent in agents if agent['agentName'] == agent_name]
            
            if not agent_ids:
                logger.warning(f"No Bedrock Agent found with name: {agent_name}")
                return
        
        # Delete each selected agent
        for agent_id in agent_ids:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete Bedrock Agent with ID: {agent_id}")
            else:
                logger.info(f"Deleting Bedrock Agent with ID: {agent_id}")
                bedrock_agent_client.delete_agent(agentId=agent_id)
                logger.info(f"Bedrock Agent deletion initiated for ID: {agent_id}")
    
    except ClientError as e:
        logger.error(f"Error deleting Bedrock Agent: {e}")

def delete_knowledge_bases(kb_names, bedrock_agent_client, dry_run=False):
    """Delete Bedrock Knowledge Bases"""
    try:
        # List all knowledge bases
        logger.info("Listing all Knowledge Bases...")
        response = bedrock_agent_client.list_knowledge_bases()
        kbs = response.get('knowledgeBaseSummaries', [])
        
        if not kbs:
            logger.info("No Knowledge Bases found")
            return
        
        logger.info(f"Found {len(kbs)} Knowledge Bases:")
        for i, kb in enumerate(kbs):
            logger.info(f"  {i+1}. {kb['name']} (ID: {kb['knowledgeBaseId']})")
        
        # Find knowledge bases by name or let user select
        if kb_names:
            kb_ids = [kb['knowledgeBaseId'] for kb in kbs if kb['name'] in kb_names]
            if not kb_ids:
                logger.warning(f"No Knowledge Bases found with names: {kb_names}")
                
                try:
                    choice = input("Do you want to select Knowledge Bases to delete? (y/n): ")
                    if choice.lower() != 'y':
                        return
                    
                    choice = input("Enter the numbers of the Knowledge Bases to delete (comma-separated, or 'all'): ")
                    if choice.lower() == 'all':
                        kb_ids = [kb['knowledgeBaseId'] for kb in kbs]
                    else:
                        indices = [int(idx.strip()) - 1 for idx in choice.split(',')]
                        kb_ids = [kbs[idx]['knowledgeBaseId'] for idx in indices if 0 <= idx < len(kbs)]
                except ValueError:
                    logger.error("Invalid input")
                    return
        else:
            try:
                choice = input("Enter the numbers of the Knowledge Bases to delete (comma-separated, or 'all', or 'skip'): ")
                if choice.lower() == 'skip':
                    logger.info("Skipping Knowledge Base deletion")
                    return
                elif choice.lower() == 'all':
                    kb_ids = [kb['knowledgeBaseId'] for kb in kbs]
                else:
                    indices = [int(idx.strip()) - 1 for idx in choice.split(',')]
                    kb_ids = [kbs[idx]['knowledgeBaseId'] for idx in indices if 0 <= idx < len(kbs)]
            except ValueError:
                logger.error("Invalid input")
                return
        
        # Delete each selected knowledge base
        for kb_id in kb_ids:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete Knowledge Base with ID: {kb_id}")
            else:
                logger.info(f"Deleting Knowledge Base with ID: {kb_id}")
                bedrock_agent_client.delete_knowledge_base(knowledgeBaseId=kb_id)
                logger.info(f"Knowledge Base deletion initiated for ID: {kb_id}")
    
    except ClientError as e:
        logger.error(f"Error deleting Knowledge Bases: {e}")

def delete_s3_bucket(bucket_name, s3_client, dry_run=False):
    """Delete S3 bucket and all its contents"""
    try:
        logger.info(f"Checking S3 bucket: {bucket_name}")
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"S3 bucket does not exist: {bucket_name}")
                return
            else:
                raise
        
        if dry_run:
            logger.info(f"[DRY RUN] Would delete all objects in S3 bucket: {bucket_name}")
            logger.info(f"[DRY RUN] Would delete S3 bucket: {bucket_name}")
            return
        
        # Delete all objects
        logger.info(f"Deleting all objects in S3 bucket: {bucket_name}")
        
        # Delete objects
        paginator = s3_client.get_paginator('list_objects_v2')
        object_count = 0
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                if objects:
                    s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
                    object_count += len(objects)
        
        logger.info(f"Deleted {object_count} objects from S3 bucket")
        
        # Delete versioned objects if bucket has versioning
        try:
            paginator = s3_client.get_paginator('list_object_versions')
            version_count = 0
            
            for page in paginator.paginate(Bucket=bucket_name):
                delete_list = []
                
                # Delete versions
                if 'Versions' in page:
                    delete_list.extend([{'Key': obj['Key'], 'VersionId': obj['VersionId']} 
                                        for obj in page['Versions']])
                
                # Delete delete markers
                if 'DeleteMarkers' in page:
                    delete_list.extend([{'Key': obj['Key'], 'VersionId': obj['VersionId']} 
                                        for obj in page['DeleteMarkers']])
                
                if delete_list:
                    s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': delete_list})
                    version_count += len(delete_list)
            
            if version_count > 0:
                logger.info(f"Deleted {version_count} versioned objects/delete markers")
        except Exception as e:
            logger.warning(f"Error deleting versioned objects (can be ignored if bucket doesn't use versioning): {e}")
        
        # Wait for objects to be deleted
        time.sleep(3)
        
        # Delete bucket
        logger.info(f"Deleting S3 bucket: {bucket_name}")
        s3_client.delete_bucket(Bucket=bucket_name)
        logger.info(f"S3 bucket deleted: {bucket_name}")
    
    except ClientError as e:
        logger.error(f"Error deleting S3 bucket: {e}")

def delete_sagemaker_resources(domain_name, space_name, sagemaker_client, dry_run=False):
    """Delete SageMaker resources"""
    try:
        # List domains to find the one with the matching name
        logger.info("Listing SageMaker domains...")
        
        domains = []
        paginator = sagemaker_client.get_paginator('list_domains')
        for page in paginator.paginate():
            domains.extend(page['Domains'])
        
        if not domains:
            logger.info("No SageMaker domains found")
            return
        
        logger.info(f"Found {len(domains)} SageMaker domains:")
        for i, domain in enumerate(domains):
            logger.info(f"  {i+1}. {domain['DomainName']} (ID: {domain['DomainId']})")
        
        # Find domain by name or let user select
        domain_id = None
        if domain_name:
            matching_domains = [d for d in domains if d['DomainName'] == domain_name]
            if matching_domains:
                domain_id = matching_domains[0]['DomainId']
            else:
                logger.warning(f"No SageMaker domain found with name: {domain_name}")
        
        if domain_id is None:
            try:
                choice = input("Do you want to select a SageMaker domain? (y/n): ")
                if choice.lower() != 'y':
                    logger.info("Skipping SageMaker resource deletion")
                    return
                
                choice = input("Enter the number of the domain: ")
                idx = int(choice) - 1
                if 0 <= idx < len(domains):
                    domain_id = domains[idx]['DomainId']
                else:
                    logger.error("Invalid choice")
                    return
            except ValueError:
                logger.error("Invalid input")
                return
        
        # List spaces in the domain
        logger.info(f"Listing spaces in domain ID: {domain_id}")
        
        spaces = []
        paginator = sagemaker_client.get_paginator('list_spaces')
        for page in paginator.paginate(DomainId=domain_id):
            spaces.extend(page['Spaces'])
        
        if not spaces:
            logger.info(f"No spaces found in domain ID: {domain_id}")
        else:
            logger.info(f"Found {len(spaces)} spaces:")
            for i, space in enumerate(spaces):
                logger.info(f"  {i+1}. {space['SpaceName']} (Status: {space['Status']})")
            
            # Find space by name or let user select
            space_names_to_delete = []
            if space_name:
                matching_spaces = [s for s in spaces if s['SpaceName'] == space_name]
                if matching_spaces:
                    space_names_to_delete = [space_name]
                else:
                    logger.warning(f"No space found with name: {space_name}")
            
            if not space_names_to_delete:
                try:
                    choice = input("Enter the numbers of the spaces to delete (comma-separated, or 'all', or 'skip'): ")
                    if choice.lower() == 'skip':
                        logger.info("Skipping space deletion")
                    elif choice.lower() == 'all':
                        space_names_to_delete = [s['SpaceName'] for s in spaces]
                    else:
                        indices = [int(idx.strip()) - 1 for idx in choice.split(',')]
                        space_names_to_delete = [spaces[idx]['SpaceName'] for idx in indices if 0 <= idx < len(spaces)]
                except ValueError:
                    logger.error("Invalid input")
            
            # Delete selected spaces
            for space_name in space_names_to_delete:
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete space: {space_name} in domain ID: {domain_id}")
                else:
                    logger.info(f"Deleting space: {space_name} in domain ID: {domain_id}")
                    try:
                        sagemaker_client.delete_space(DomainId=domain_id, SpaceName=space_name)
                        logger.info(f"Space deletion initiated for: {space_name}")
                    except ClientError as e:
                        logger.error(f"Error deleting space {space_name}: {e}")
        
        # Ask if user wants to delete the domain
        choice = input(f"Do you want to delete the SageMaker domain '{domains[idx]['DomainName']}'? (y/n): ")
        if choice.lower() == 'y':
            if dry_run:
                logger.info(f"[DRY RUN] Would delete SageMaker domain ID: {domain_id}")
            else:
                logger.info(f"Deleting SageMaker domain ID: {domain_id}")
                try:
                    # List all user profiles in the domain
                    user_profiles = []
                    paginator = sagemaker_client.get_paginator('list_user_profiles')
                    for page in paginator.paginate(DomainId=domain_id):
                        user_profiles.extend(page['UserProfiles'])
                    
                    # Delete each user profile
                    for profile in user_profiles:
                        logger.info(f"Deleting user profile: {profile['UserProfileName']}")
                        sagemaker_client.delete_user_profile(
                            DomainId=domain_id,
                            UserProfileName=profile['UserProfileName']
                        )
                    
                    # Delete the domain
                    sagemaker_client.delete_domain(DomainId=domain_id)
                    logger.info(f"SageMaker domain deletion initiated for ID: {domain_id}")
                except ClientError as e:
                    logger.error(f"Error deleting SageMaker domain: {e}")
        else:
            logger.info("Skipping SageMaker domain deletion")
    
    except ClientError as e:
        logger.error(f"Error managing SageMaker resources: {e}")

def main():
    """Main function to clean up AWS RAG Workshop resources"""
    args = parse_arguments()
    
    # Create session and clients
    session = get_session(args.region)
    region = session.region_name
    logger.info(f"Using AWS region: {region}")
    
    s3_client = session.client('s3')
    bedrock_agent_client = session.client('bedrock-agent')
    sagemaker_client = session.client('sagemaker')
    
    if args.dry_run:
        logger.info("Running in DRY RUN mode - no resources will be deleted")
    
    # Delete Bedrock Agent
    delete_bedrock_agent(args.agent_name, bedrock_agent_client, args.dry_run)
    
    # Delete Knowledge Bases
    delete_knowledge_bases(args.kb_names, bedrock_agent_client, args.dry_run)
    
    # Delete S3 bucket
    delete_s3_bucket(args.bucket_name, s3_client, args.dry_run)
    
    # Delete SageMaker resources
    delete_sagemaker_resources(args.sagemaker_domain_name, args.sagemaker_space_name, 
                              sagemaker_client, args.dry_run)
    
    logger.info("Cleanup completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nCleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
