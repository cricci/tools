#!/usr/bin/env python3
import os
import sys
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

def upload_directory_to_s3(source_directory, bucket_name, aws_access_key_id=None, aws_secret_access_key=None):
    """
    Should probably break this up from the blob it has become
    Todo: add support for prefix in s3 bucket/path.
    """

    # Load environment variables from .env file
    load_dotenv()

    # Use environment variables if not provided
    if aws_access_key_id is None:
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    if aws_secret_access_key is None:
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    # Check for missing parameters
    if not aws_access_key_id:
        print("Error: Missing AWS Access Key ID")
        return
    if not aws_secret_access_key:
        print("Error: Missing AWS Secret Access Key")
        return
    if not source_directory:
        print("Error: Missing source directory")
        return
    if not bucket_name:
        print("Error: Missing S3 bucket name")
        return

    # Initialize the S3 client
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
    except NoCredentialsError:
        print("Error: AWS credentials not provided or incorrect")
        return

    # Upload all files in the source directory to the S3 bucket
    for root, dirs, files in os.walk(source_directory):
        for file in files:
            file_path = os.path.join(root, file)
            s3_key = os.path.relpath(file_path, source_directory)  # S3 object name
            try:
                s3_client.upload_file(file_path, bucket_name, s3_key)
                print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 3:
        print("Usage: [python] upload_to_s3.py <source_directory> <bucket_name> [aws_access_key_id] [aws_secret_access_key]")
        sys.exit(1)

    # Parse command-line arguments
    source_directory = sys.argv[1]
    bucket_name = sys.argv[2]
    aws_access_key_id = sys.argv[3] if len(sys.argv) > 3 else None
    aws_secret_access_key = sys.argv[4] if len(sys.argv) > 4 else None

    upload_directory_to_s3(source_directory, bucket_name, aws_access_key_id, aws_secret_access_key)
