import boto3, csv, json, re, requests, time

LIVE_MODE = 'no, testing...'

FTIN_SERVER = "https://ftinmanager.blocktransfer.com"
mTLS_auth_FTINs = 1 #?
HORIZON_INST = "https://horizon.stellar.org"
BT_ISSUER = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7"
clientDB = boto3.client("dynamodb")

def lambda_handler(event, context):
  
  legacyImportTxnHash = "37be2f6976bf0fc8ca9c716e49e970a2271dd6574feda80df8377530eb88b80a"
  
  importCodes, CIK = getCodesAndCIKfromHash(legacyImportTxnHash)
  importUnix = getLegacyImportUnix(legacyImportTxnHash, CIK)
  
  accounts = []
  legacyImport = [{}] # get as param input, make this the only endpoiunt 
  
  for investors in legacyImport:
    holdings = []
    for codes in importCodes:
      if investors.get(f"{codes}-quantity"):
        holdings.append({
          "M": {
            "code": {"S": codes},
            "amount": {"S": investors.get(f"{codes}_quantity")},
            "basis": {"N": investors.get(f"{codes}_basis", "unknown")},
            "fiat": {"S": investors.get(f"{codes}_basis_fiat", "USD")},
            "aqAt": {"N": investors.get(f"{codes}_aquired_at", importUnix)},
            "notes": {"S": investors.get(f"{codes}_notes")}
          }
        })
    FTIN = investors.get("FTIN")
    token = "" if not FTIN else putFTIN({
      "FTIN": FTIN,
      "type": investors.get("FTIN_type")
    })
    legalName = investors["legal_name"]
    importAcc = scrubNullVals({
      "CIK": {"N": CIK},
      "FTIN": {"S": token},
      "holdings": {"L": holdings},
      "legalName": {"S": legalName},
      "from": {"S": legacyImportTxnHash},
      "addNS": {"N": str(time.time_ns())},
      "DOB": {"S": investors.get("DOB", "")},
      "first": {"S": legalName.split(" ")[0]},
      "email": {"S": investors.get("email", "")},
      "phone": {"S": investors.get("phone", "")},
      "notes": {"S": investors.get("notes", "")},
      "addr": {"S": investors.get("address", "")},
      "minor": {"BOOL": investors.get("minor", False)},
      "expCtry": {"S": investors["expected_citizenship"]},
      "mailAddr": {"S": investors.get("mail_address", "")},
      "orgChiefExec": {"S": investors.get("org_chief_executive", "")},
      "orgOtherUsers": {"S": investors.get("org_other_contacts", "")}
    })
    accounts.append({"PutRequest": {"Item": importAcc}})
    if len(accounts) == 25:
      createLegacyAccs(accounts)
      accounts = []
  createLegacyAccs(accounts)
  return accounts
  return f"Successfully imported {len(legacyImport)} accounts"

def getCodesAndCIKfromHash(legacyImportTxnHash):
  ledgerOps = requests.get(
    f"{HORIZON_INST}/transactions/{legacyImportTxnHash}/operations"
  ).json()
  codesImported = []
  CIKs = set()
  for issueOps in ledgerOps["_embedded"]["records"]:
    assert(issueOps["asset_issuer"] == BT_ISSUER)
    code = issueOps["asset_code"]
    codesImported.append(code)
    CIKs.add(getCIKfromCode(code))
  sameCIKs = len(CIKs) == 1
  if not sameCIKs: raise ImportError
  return codesImported, CIKs.pop()

def getLegacyImportUnix(legacyImportTxnHash, ledgerCIK):
  table = boto3.resource("dynamodb").Table("legacyImports")
  try:
    response = table.get_item(
      Key = {"hash": legacyImportTxnHash},
      ProjectionExpression = "received, CIK"
    )
    item = response["Item"]
    importUnix = str(item["received"])
    tableCIK = str(item["CIK"])
  except Exception:
    raise LookupError
  assert(tableCIK == ledgerCIK)
  return importUnix

def createLegacyAccs(accounts):
  return LIVE_MODE
  items = {"legacyAccs": accounts}
  response = clientDB.batch_write_item(RequestItems=items)
  if response["UnprocessedItems"]: raise NotImplementedError

def getCIKfromCode(code):
  nums = re.search(r"\d+", code)
  return nums.group() if nums else ""

def scrubNullVals(data):
  if not data: return None
  if isinstance(data, list):
    return [v for v in (scrubNullVals(items) for items in data) if v]
  if isinstance(data, dict):
    newDict = {}
    for key, value in data.items():
      scrubbedValue = scrubNullVals(value)
      if scrubbedValue is not None:
        newDict[key] = scrubbedValue
    return newDict if newDict else None
  return data

def putFTIN(data):
  return requests.post(FTIN_SERVER, params=data, auth="self_").json()
