# ----------------- TODO: Scaling ------------------ #
# Not sure how much we'll use this. DB scans = bad.  #
# You can do this much better by keeping a live      #
# list of valid user PKs, updated by Dynamo Streams. #
# -------------------------------------------------- #

import boto3

PII_DB = boto3.resource("dynamodb").Table("PII")

def lambda_handler(event, context):
  try:
    pubKeys = []
    response = table.scan(
      IndexName = "users"
    ) # TODO - need to implement pagignation here
    for accounts in response["Items"]:
      pubKeys.append(accounts["PK"])
    return pubKeys
  except Exception as e:
    return "PII DB failed"
