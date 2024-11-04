from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
import base64, boto3, json, time, requests

PII_DB = boto3.resource("dynamodb").Table("PII")
HORIZON_INST = "https://horizon.stellar.org"

def lambda_handler(event, context):
  ''' 
  Authorization header:
    {
      "token": {
        "session": sessionNonce,
        "linkIP": desktopIP
      }
      "sig": tokenSignature,
      "PK": claimedPubKey
    }
  '''
  try:
    userIP, token, signature, pubKey = getFuncInputs(event)
    verifySignature(token, signature, pubKey)
    userInfo = verifyValidAcc(pubKey)
    verifyLinkSessionAndAddUserInfo(token, userInfo)
    infoAboutAuthCIKs = verifyIsIssuerSigner(pubKey)
    return {
      "isAuthorized": True,
      "context": {
        "self": userInfo,
        "issuers": infoAboutAuthCIKs
      }
    }
  except PermissionError as e:
    print(f"DeniedIP: {userIP} Reason: {str(e)}")
    return {"isAuthorized": False}
  except SystemError as e:
    return json.dumps(f"Error: {str(e)}")
  return {"Authentication successful"}


def encodeSessionIDforLocalStorage(something):
  return schemaTBD
# this generates a cookie expiring in 7500 seconds 
# doesn't implement CSRF protection
def createCookieHeader(sessionNonce):
    cookieHeader = f"secureJwtCookie={sessionNonce}; HttpOnly; Secure; Path=/; Max-Age=7500"
    return cookieHeader




def getFuncInputs(event):
  userIP = event["requestContext"]["http"]["sourceIp"]
  try:
    auth = json.loads(event["headers"]["authorization"])
    token = auth["token"]
    signature = auth["sig"]
    pubKey = auth["PK"]
  except KeyError:
    raise PermissionError("bad header")
  return userIP, token, signature, pubKey


def verifySignature(token, signature, PK):
  try:
    bytesToken = token.encode()
    bytesSig = base64.b64decode(signature)
    bytesPK = base64.b32decode(PK.encode())[1:-2]
    Ed25519PublicKey.from_public_bytes(bytesPK).verify(bytesSig, bytesToken)
  except (ValueError, InvalidSignature):
    raise PermissionError("bad signature")

def verifyValidAcc(pubKey):
  try:
    response = PII_DB.get_item(Key = {"PK": pubKey})
    if "Item" in response:
      account = response["Item"]
    else:
      raise PermissionError("no account")
    if "restrictions" in account:
      if account["restrictions"]["status"] != 200:
        raise PermissionError("bad account")
  except Exception as e:
    raise SystemError(f"PII DB resolution failed: {str(e)}")
  return account

def verifyLinkSessionAndAddUserInfo(token, userInfo):
  sessionID, sessionIP = getSessionDataFromToken(token)
  try:
    table = boto3.resource("dynamodb").Table("issuerSessions")
    response = table.get_item(Key = {"PK": sessionID})
    if "Item" in response:
      sessionData = response["Item"] #
      if sessionData["IP"] != sessionIP:
        raise PermissionError("bad linkIP")
      boto3.resource("dynamodb").update_item(
        TableName = "issuerSessions",
        Key = bearerClaim,
        UpdateExpression = "set user = :val",
        ExpressionAttributeValues = {":val": userInfo},
        ReturnValues = "ALL_NEW"
      )
    else:
      raise PermissionError("bad session")
  except Exception as e:
    raise SystemError(f"Session resolution failed: {str(e)}")

def getSessionDataFromToken(token):
  try:
    token = json.loads(token)
    sessionID = token["session"]
    sessionIP = token["linkIP"]
  except KeyError:
    raise PermissionError("bad token")
  return sessionID, sessionIP

def verifyIsIssuerSigner(PK):
  authCIKs = {}
  for clients in getAccsPKsignsFor(PK):
    PKuserSignsFor = clients["account_id"]
    if(PKuserSignsFor == PK):
      continue
    try:
      response = PII_DB.get_item(Key = {"PK": PKuserSignsFor})
      if "Item" in response:
        issuerClient = "CIK" in response["Item"]
        if not issuerClient:
          continue
      else:
        print(f"Anomaly: {PK} signs {PKuserSignsFor}?")
        continue
      CIK = int(response["Item"]["CIK"])
    except Exception as e:
      raise SystemError(f"PII DB resolution failed: {str(e)}")
    signers, thresholds, sequence = getIssuerAuthInfo(clients, PK)
    authCIKs[CIK] = {
      "signers": signers,
      "thresholds": thresholds,
      "currSequence": sequence
    }
  if not authCIKs:
    raise PermissionError("no affiliations")
  return authCIKs

def getAccsPKsignsFor(PK):
  try:
    response = requests.get(
      f"{HORIZON_INST}/accounts?signer={PK}"
    ).json()
    if "status" in response:
      raise PermissionError("invalid pubKey")
  except Exception as e:
    raise SystemError(f"Horizon signer lookup failed: {str(e)}")
  return response["_embedded"]["records"]

def getIssuerAuthInfo(issuerAcc, PK):
  thresholds = getAccThresh(issuerAcc)
  issuerSigners = {}
  for ledgerSigners in issuerAcc["signers"]:
    weight = ledgerSigners["weight"]
    if ledgerSigners["type"] != "ed25519_public_key":
      continue
    issuerSigners[
      ledgerSigners["key"]
    ] = {
      "weight": weight,
      "authority": getAuthority(weight, thresholds)
    }
  return issuerSigners, thresholds, int(issuerAcc["sequence"])

def getAccThresh(account):
  thresholds = account["thresholds"]
  return {
    "high": thresholds["high_threshold"],
    "med": thresholds["med_threshold"],
    "low": thresholds["low_threshold"]
  }

def getAuthority(weight, thresholds):
  if weight >= thresholds["high"]:
    return "high"
  elif weight >= thresholds["med"]:
    return "med"
  elif weight >= thresholds["low"]:
    return "low"
  else:
    return "self"
