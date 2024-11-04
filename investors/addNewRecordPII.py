import boto3, hashlib, json, random, time

PII_DB = boto3.resource("dynamodb").Table("PII")

def lambda_handler(event, context):
  ID =  "" # use hardened putItem conditional on ID --- generateAccID()
  investor = {
    "ID": ID,
    "PK": "",
    "regFirst": "",
    "regRest": "",
    "addr": {
     "city": "",
     "code": "",
     "L1": "",
     "subd": ""
    },
    #"affiliated": [],
    "citizen": "",
    "DOB": ,
    "email": "",
    "PSNA": "",
    "onbd": int(time.time()),
    "phone": ,
    "type": "_person"
  }
  try:
    response = PII_DB.put_item(
      Item = investor,
      ConditionExpression = "attribute_not_exists(ID)"
    )
  except ConditionalCheckFailedException:
    lambda_handler(event, context)
  except Exception as e:
    return json.dumps({
      "statusCode": 500,
      "body": str(e)
    })
  return ID

def generateAccID():
  b32alph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
  base = "".join(random.choices(b32alph, k = 8))
  checksum = b32alph[int(hashlib.sha3_256(base.encode()).hexdigest(), 16) % 32]
  ID = base + checksum
  return ID
