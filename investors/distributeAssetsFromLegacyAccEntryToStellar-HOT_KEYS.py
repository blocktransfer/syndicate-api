# ---------------------------------------- #
# CAUTION: SENDS LIVE ASSETS WITH HOT KEYS # ...
# ---------------------------------------- #

# todo - replace pandas here for 144 date math
import boto3
import json
import pandas
import requests
import stellar_sdk as xlm

BT_ISSUER = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7"
BT_DISTRIBUTOR = "GAQKSRI4E5643UUUMJT4RWCZVLY25TBNZXDME4WLRIF5IPOLTLV7N4N6"
ISSUERS_INFO_API = "https://api.issuers.info"
HORIZON_INST = "https://horizon.stellar.org"
R144_PRIVATE_NUM_MO = 12
R144_PUBLIC_NUM_MO = 6
DEF_TIMEOUT = 3200
BASE_FEE = 2000

LEGACY_DB = boto3.resource("dynamodb").Table("legacy")
LAMBDA = boto3.client("lambda")

# Just build the distribution transaction :)
# Return an onject including the actual legacy acc assets and first/addNS

def lambda_handler(event, context):
  investorAccID = "WUPVU2TRH"
  legacyAccFirst = "OBBeatzz"
  legacyAccAddNS = 1697749627280649763
  
  legacyAcc = getLegacyAcc(legacyAccFirst, legacyAccAddNS)
  investorPK = getPKfromAccIDwExpCountry(investorAccID, legacyAcc["expCtry"]) # now this country check could be rolled up into the review process
  
  distributeTxn = xlm.TransactionBuilder(
    source_account=xlm.Server(HORIZON_INST).load_account(account_id=BT_DISTRIBUTOR),
    network_passphrase=xlm.Network.PUBLIC_NETWORK_PASSPHRASE,
    base_fee=BASE_FEE,
  )
  
  
  issuerInfo = requests.get(f"{ISSUERS_INFO_API}/{legacyAcc['CIK']}").json()
  isPublic = issuerInfo.get("current_SEC_public_reports_for_past_90_days")
  
  # let's build them one at a time so each has proper ledger memo basis vals
  basisVals = set()
  for assets in legacyAcc["holdings"]:
    basisVals.add(assets["basis"])
    distributeTxn.append_create_claimable_balance_op(
      asset=xlm.Asset(assets["code"], issuer=BT_ISSUER),
      amount=assets["amount"],
      claimants=[
        xlm.Claimant(
          destination=investorPK,
          predicate=xlm.ClaimPredicate.predicate_not(
            xlm.ClaimPredicate.predicate_before_absolute_time(
              get144avaliableUnix(isPublic, assets["aqAt"])
            )
          )
        )
      ]
    )
  memoBasis = basisVals.pop() if len(basisVals) == 1 else "various"
  distributeTxn = distributeTxn.add_text_memo(f"Basis: ${memoBasis}").set_timeout(DEF_TIMEOUT).build()
  return distributeTxn.to_xdr()

# Submit txn
# success = delete legacyAccRecord

def get144avaliableUnix(isPublic, baseUnix):
  baseDate = pandas.to_datetime(int(baseUnix), unit="s", origin="unix")
  numMonths144 = R144_PUBLIC_NUM_MO if isPublic else R144_PRIVATE_NUM_MO
  avaliableDate = baseDate + pandas.DateOffset(months=numMonths144)
  return int(avaliableDate.timestamp())

def getLegacyAcc(first, addNS):
  try:
    response = LEGACY_DB.get_item(
      Key = {
        "first": first,
        "addNS": addNS
      }
    )
    if "Item" in response:
      return response["Item"]
    else:
      raise LookupError("Legacy Account Not Found")
  except Exception:
    raise SystemError("Legacy DB Failed") # Need to handle 404s better

def getPKfromAccIDwExpCountry(investorAccID, expectedCtry):
  
  # You actually can't use this, since you will be onboarding legacy minors, retirement accs, etc. 
  # TODO - Direct user query 👍
  
  response = LAMBDA.invoke(
    FunctionName = "external-Federation",
    InvocationType = "RequestResponse",
    Payload = json.dumps({
      "queryStringParameters": {
        "q": investorAccID,
        "type": "plus"
      }
    })
  )
  response = json.loads(response["Payload"].read().decode())
  if response["statusCode"] == 200:
    federationInfo = json.loads(response["body"])
    assert(federationInfo["country"] == expectedCtry,
      f"Account ID citizen ({federationInfo['country']}) does not match legacy account expected jurisdiction ({expectedCtry})")
    return federationInfo["PK"]
  else:
    raise LookupError("Account ID not found")
