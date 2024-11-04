import boto3

def lambda_handler(event, context):
  table = boto3.resource("dynamodb").Table("legacyAccs")
  try:
    CIK = int(event["pathParameters"]["CIK"])
    response = table.query(
      IndexName = "forCIK",
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
  except Exception as e:
    return {
      "statusCode": 500,
      "body": str(e)
    }
