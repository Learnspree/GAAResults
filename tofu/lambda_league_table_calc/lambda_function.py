import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Scan the leagues table and log league_code and league_name for each item."""
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE', 'gaa-results-leagues-production')
    table = dynamodb.Table(table_name)

    try:
        count = 0
        response = table.scan(ProjectionExpression="league_code, league_name")
        items = response.get('Items', [])
        for it in items:
            logger.info(f"league_code={it.get('league_code')} league_name={it.get('league_name')}")
            count += 1

        while 'LastEvaluatedKey' in response:
            response = table.scan(ProjectionExpression="league_code, league_name", ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
            for it in items:
                logger.info(f"league_code={it.get('league_code')} league_name={it.get('league_name')}")
                count += 1

        return {'status': 'completed', 'items_logged': count}
    except Exception as e:
        logger.exception(f"Error scanning table {table_name}: {e}")
        return {'status': 'failed', 'error': str(e)}

