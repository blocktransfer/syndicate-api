import base64, boto3, hashlib, json, time, uuid

def lambda_handler(event, context):
  requestorIP = event["requestContext"]["http"]["sourceIp"]
  sessionID = b""
  for _ in range(0,15):
    sessionID += hashlib.sha3_256(
      str(
        uuid.uuid4()
      ).encode()
    ).digest()
  sessionID = base64.b64encode(sessionID).decode()
  tableData =  {
    "PK": sessionID,
    "IP": event["requestContext"]["http"]["sourceIp"],
    "TTL": int(time.time()) + 7200,
    "verified": False
  }
  try:
    table = boto3.resource("dynamodb").Table("issuerSessions")
    table.put_item(Item = tableData)
  except Exception as e:
    return {
      "statusCode": 500,
      "body": str(e)
    }
  return json.dumps(f"bt.issuer://link?s={sessionID}&ip={requestorIP}")
