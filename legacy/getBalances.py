# Shares not on blockchain / in TAD3 etc

import boto3, json, re

LEGACY_DB = boto3.resource("dynamodb").Table("legacy")

def lambda_handler(event, context):
  try:
    code = event["pathParameters"]["code"]
    match = re.search(r"\d+", code)
    CIK = int(match.group()) if match else 0
    response = LEGACY_DB.query(
      IndexName = "clients",
      KeyConditionExpression = "CIK = :val",
      ExpressionAttributeValues = { ":val": CIK }
    )
    if response["Items"]:
      balances = []
      for items in response["Items"]:
        for assets in items.get("holdings"):
          if assets["code"] == code:
            balance = assets["amount"]
        balances.append({
          "amount": balance,
          "registration": f"{items['first']} {items.get('regRest')}",
          "addr": items.get("addr")
        })
      return balances
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
