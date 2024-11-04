import boto3

LEGACY_DB = boto3.resource("dynamodb").Table("legacy")

def lambda_handler(event, context):
  try:
    CIK = int(event["pathParameters"]["CIK"])
    response = LEGACY_DB.query(
      IndexName = "clients",
      KeyConditionExpression = "CIK = :val",
      ExpressionAttributeValues = { ":val": CIK }
    )
    if response["Items"]:
      return response["Items"]
    else:
      return {
        "statusCode": 404,
        "body": "Item not found"
      }
  except Exception:
    return {
      "statusCode": 500,
      "body": "Internal Service Error"
    }
