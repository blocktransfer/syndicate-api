import boto3, json

CANNOT_SEND_TO_ACC_TYPES_NOT_RESOLVED = ["MINOR", "RETIRE"]
BT_TLD = "BLOCKTRANSFER.COM"

PII_DB = boto3.resource("dynamodb").Table("PII")

def lambda_handler(event, context):
  try:
    query = event["queryStringParameters"]["q"].upper()
    qType = event["queryStringParameters"]["type"].upper()
    if not (query and qType): raise ValueError("Input Missing")
    match qType:
      case "NAME":
        federationQueryPart, domain = query.split("*")
        if not federationQueryPart or domain != BT_TLD: raise ValueError("Bad Fed")
        PK, country = resolveFedAccQueryToPKandCtryOptPlusMode(federationQueryPart)
        return {
          "statusCode": 200,
          "body": json.dumps({
            "stellar_address": query,
            "account_id": PK
          })
        }
      case "PLUS":
        PK, country = resolveFedAccQueryToPKandCtryOptPlusMode(query, True)
        return {
          "statusCode": 200,
          "body": json.dumps({
            "user": query,
            "PK": PK,
            "country": country
          })
        }
      case "ID":
        # TODO - easy implimentation, but could create privacy concerns
        return formatError(501, f"Reverse federation not presently supported. Reach out if needed - hello@blocktransfer.dev")
      case _:
        return formatError(501, f"{qType} not supported")
  except KeyError:
    return formatError(400, "Missing 'q' and 'type' params")
  except ValueError as e:
    print(str(e))
    return formatError(400, f"Invalid federation")
  except LookupError:
    return formatError(404, "Not Found")
  except Exception:
    return formatError(500, "Internal Service Error")

def resolveFedAccQueryToPKandCtryOptPlusMode(federationQueryPart, plusMode=False):
  rootAccID, childType = getRootIDandAnyChildType(federationQueryPart)
  if childType:
    PK = getChildPK(rootAccID, childType)
    if plusMode:
      _, country = getAccPKandCountry(rootAccID)
      return PK, country
    return PK, "N/A"
  else:
    return getAccPKandCountry(rootAccID)

def getRootIDandAnyChildType(fedQuery):
  fedItems = fedQuery.split(".")
  rootAccID = fedItems[0]
  childType = None
  if len(fedItems) != 1:
    if not rootAccID.isdigit():
      investorChildAccClass = fedItems[1]
      if any(t in investorChildAccClass for t in CANNOT_SEND_TO_ACC_TYPES_NOT_RESOLVED):
        raise LookupError()
    childType = ".".join([i for i in fedItems[1:]])
  return rootAccID, childType

  rawChildStr = None if len(fedItems) == 1 else ".".join(item.lower() for item in fedItems[1:])
  fedQuery = fedItems[0].upper()
  return fedQuery, rawChildStr

def getAccPKandCountry(accID):
  response = PII_DB.query(
    IndexName = "users",
    KeyConditionExpression = "ID = :val AND begins_with(#SK, :root)",
    ExpressionAttributeNames = {"#SK": "type"},
    ExpressionAttributeValues = {
      ":val": accID,
      ":root": "_"
    }
  )
  if response["Count"] == 1:
    account = response["Items"][0]
    pubKey = account["PK"]
    citizen = account["citizen"]
    country = citizen.split("/")[0] if citizen != "many" else "various"
  else:
    raise LookupError()
  return pubKey, country

def getChildPK(rootAccID, childTypeFormatted):
  response = PII_DB.query(
    IndexName = "users",
    KeyConditionExpression = "ID = :parentID AND #SK = :childType",
    ExpressionAttributeNames = {"#SK": "type"},
    ExpressionAttributeValues = {
      ":parentID": rootAccID,
      ":childType": childTypeFormatted
    }
  )
  if response["Count"] == 1:
    return response["Items"][0]["PK"]
  else:
    raise LookupError()

def formatError(status, error):
  return {
    "statusCode": status,
    "body": json.dumps({
      "error": error
    })
  }
