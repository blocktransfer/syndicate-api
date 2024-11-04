import base64, boto3, json, random

LEGACY_DB = boto3.resource("dynamodb").Table("legacy")

def lambda_handler(event, context):
  data = json.loads(base64.b64decode(event["body"]))
  n = 0
  with LEGACY_DB.batch_writer() as batch:
    for accounts in data:
      n += addAcc(accounts, batch)
  return json.dumps({
    "statusCode": 200,
    "body": f"Added {n} legacy accounts"
  })
  except Exception:
    return json.dumps({
      "statusCode": 500,
      "body": "Internal Service Error"
    })

def addAcc(data, batchItem):
  while True:
    data["claim"] = getClaimCode()
    try:
      batchItem.put_item(
        Item = data,
        ConditionExpression = "attribute_not_exists(claim)"
      )
      return 1
    except ConditionalCheckFailedException:
      pass

def getClaimCode():
  firstNum = str(random.randint(1, 9))
  baseCode = firstNum + "".join(
    random.choices("0123456789", k=14)
  )
  return int(baseCode + getLuhnChecksum(baseCode))

def getLuhnChecksum(baseCode):
  digits = [int(d) for d in str(baseCode)][::-1]
  for i in range(1, len(digits), 2):
    digits[i] *= 2
    if digits[i] > 9:
      digits[i] -= 9
  total = sum(digits)
  checksum = (10 - (total % 10)) % 10
  return checksum
