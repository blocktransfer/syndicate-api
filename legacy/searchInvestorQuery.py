import boto3

LEGACY_DB = boto3.resource("dynamodb").Table("legacy")

def lambda_handler(event, context):
  try:
    first = event["pathParameters"]["first"]
    response = LEGACY_DB.query(
      KeyConditionExpression="#pk = :val",
      ExpressionAttributeNames={"#pk": "first"},
      ExpressionAttributeValues={":val": first}
    )
    if "Items" in response:
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
