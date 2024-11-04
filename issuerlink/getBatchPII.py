import boto3, json
from datetime import datetime

def lambda_handler(event, context):
  try:
    inputPKs = (event["queryStringParameters"]["PKs"]).split(",")
  except KeyError:
    return formatError(400, "Missing PKs array in body.")
  keys = [{"PK": {"S": pubKeys}} for pubKeys in inputPKs]
  try:
    response = getBatchPII(keys)
    if response["UnprocessedKeys"]:
      # get the next batch
      raise NotImplementedError("Failed attempt at pagignation")
    accounts = response["Responses"]["PII"]
    if len(accounts) == len(inputPKs):
      return extractNecessaryIssuerInfoOnly(accounts)
    else:
      responsePKs = [data["PK"]["S"] for data in accounts]
      notFound = [PKs for PKs in inputPKs if PKs not in responsePKs]
      return formatError(404, f"Items not found: {notFound}")
  except Exception as e:
    return formatError(500, str(e))

def getBatchPII(keys):
  dynamoDB = boto3.client("dynamodb")
  try:
    return dynamoDB.batch_get_item(RequestItems = {"PII": {"Keys": keys}})
  except Exception as e:
    raise SystemError(e) # Limit batch to 100 PKs.

def extractNecessaryIssuerInfoOnly(accountsRaw):
  output = {}
  for accounts in accountsRaw:
    output[
      accounts["PK"]["S"]
    ] = {
      "address": getAccAddr(accounts),
      "citizen": getS(accounts, "citizen"),
      "registration": getS(accounts, "legalName"),
      "more": {
        "accredited": getAccAccr(accounts)
        "ageRange": getAccAgeSpan(accounts),
        "email": bool(accounts.get("email")),
        "ID": getS(accounts, "ID"),
        "phone": bool(accounts.get("phone")),
        "typeCode": getS(accounts, "type")
      }
    }
  return output

def getS(item, attr):
  return item.get(attr, {}).get("S", "")

def getAccAccr(account)
  accred = account.get("accred", {}).get("M")
  if not accred: return False
  hardTilUnix = accred.get("hardTil", {}).get("N")
  if hardTil > time.time():
    return "hard"
  soft = accred.get("hardTil", {}).get("B")
  return "soft" if soft else "not"

def getAccAddr(account):
  rawAddr = account.get("addr", {}).get("M")
  output = [getS(rawAddr, keys) for keys in ["L1", "L2", "L3", "L4", "city"]]
  subdAndCode = [(keys, getS(rawAddr, keys)) for keys in ["subd", "code"]]
  output.append(" ".join([value for key, value in subdAndCode if value]))
  country = getS(rawAddr, "ctry")
  if country != "US": output.append(country)
  return ", ".join(list(filter(None, output)))

def getAccAgeSpan(account):
  DOB = getS(account, "DOB")
  if not DOB: return False
  DOB = datetime.strptime(DOB, "%Y-%m-%d").date()
  delta = datetime.today().date() - DOB
  age = delta.days // 365
  if age < 18: return "minor"
  if age < 25: return "18-24"
  if age < 35: return "25-34"
  if age < 45: return "35-44"
  if age < 55: return "45-54"
  if age < 65: return "55-64"
  if age < 100: return "65+"
  return "100+"

def formatError(status, error):
  return {
    "statusCode": status,
    "body": json.dumps({"error": error})
  }
