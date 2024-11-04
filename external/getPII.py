# Requests authorized via API Gateway `AWS_IAM` tokens

import boto3

PII_DB = boto3.resource("dynamodb").Table("PII")

def lambda_handler(event, context):
  try:
    response = PII_DB.get_item(
      Key = {
        "PK": event["pathParameters"]["PK"]
      }
    )
    if "Item" in response:
      return response["Item"]
    else:
      return {
        "statusCode": 404,
        "body": "Item not found"
      }
  except Exception:
    return "Internal Service Error"
