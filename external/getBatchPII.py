import boto3, json

def lambda_handler(event, context):
  try:
    inputPKs = (event["queryStringParameters"]["PKs"]).split(",")
  except KeyError:
    return formatError(400, "Missing PKs array in body.")
  keys = [
    {
      "PK": {
        "S": pubKeys
      }
    } for pubKeys in inputPKs
  ]
  try:
    response = getBatchPII(keys)
    if response["UnprocessedKeys"]:
      # get the next batch
      raise NotImplementedError("Failed attempt at pagignation")
    accounts = response["Responses"]["PII"]
    if len(accounts) == len(inputPKs):
      return accounts
    else:
      responsePKs = [data["PK"]["S"] for data in accounts]
      notFound = [PKs for PKs in inputPKs if PKs not in responsePKs]
      return formatError(404, f"Items not found: {notFound}")
  except Exception as e:
    return formatError(500, str(e))

def getBatchPII(keys):
  dynamoDB = boto3.client("dynamodb")
  try:
    return dynamoDB.batch_get_item(
      RequestItems = {
        "PII": {
          "Keys": keys
        }
      }
    )
  except Exception as e:
    if "ValidationException" in str(e):
      raise ValueError("Limit batch to 100 PKs.")
    raise SystemError(e)

def formatError(status, error):
  return {
    "statusCode": status,
    "body": json.dumps(
      {
        "error": error
      }
    )
  }
