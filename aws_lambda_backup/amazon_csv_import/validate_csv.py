import boto3
import pandas as pd

def lambda_handler(event, context):
    """
    Validate the structure and data of the uploaded CSV file in S3.

    Args:
        event (dict): Event containing S3 bucket and key information.
        context (LambdaContext): Lambda context object (not used).

    Returns:
        dict: Validation status and file details if successful.

    Raises:
        ValueError: If required columns are missing in the CSV.
    """
    # Initialize S3 client
    s3 = boto3.client('s3')

    # Get bucket and key from the event
    bucket = event['bucket']
    key = event['key']

    # Retrieve the file from S3
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj['Body'])

    # Define required columns
    required_columns = ['column1', 'column2']

    # Validate the presence of required columns
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {', '.join(required_columns)}")

    # Return validation success
    return {
        "status": "Validated",
        "bucket": bucket,
        "key": key
    }