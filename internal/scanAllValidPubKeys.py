# ----------------- Todo: Scaling ------------------ #
# You can do this much better by having an arbitrary #
# storage location maintain a list of valid account  #
# public keys, which gets updated by Dynamo Streams. #
# -------------------------------------------------- #

import boto3

PII_DB = boto3.resource("dynamodb").Table("PII")

def lambda_handler(event, context):
  try:
    response = PII_DB.scan()
    validPubKeys = []
    for accounts in response["Items"]: # TODO - need to implement pagignation
      if not accounts.get("hold"):
        validPubKeys.append(accounts["PK"])
    return validPubKeys
  except Exception as e:
    return "Internal Service Error"
