# TODO: This should probably get migrated to a WalletConnect channel

import boto3

def lambda_handler(event, context):
  userIP = event["requestContext"]["http"]["sourceIp"]
  try:
    session = json.loads(event["headers"]["authorization"])
    table = boto3.resource("dynamodb").Table("issuerSessions")
    response = table.get_item(Key = {"PK": session})
    if "Item" in response:
      sessionData = response["Item"]
      IPmatch = userIP == sessionData["IP"]
      if sessionData["valid"] and IPmatch:
        response = {
          "isAuthorized": True,
          "context": {
            "user": sessionData["user"],
            "issuers": sessionData["issuers"]
          }
        }
    else:
      raise PermissionError()
  except Exception:
    print("DeniedIP: {userIP}")
    return {"isAuthorized": False}
