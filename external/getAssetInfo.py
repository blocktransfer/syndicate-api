import boto3, json, requests, toml
from decimal import Decimal

def lambda_handler(event, context):
  code = event["pathParameters"].get("code").upper()
  if code.isdigit():
    return displayAssetCodesForIssuer(code)
  try: # todo: this try/except doesn't catch cases when asset doesn't exist
       #      need a quick way to check that asset exists, and then get all the key info lol
       #      and then potentially add totalAuted vs totalAuthorized vs totalOnLedger (outstanding full vs adjusted can be merged to interlinked steps)
    return {
      "statusCode": 200,
      "body": json.dumps({
        "outstanding": getNumOutstanding(code)
      })
    }
  except Exception:
    return {
      "statusCode": 404,
      "body": json.dumps({
        "error": "Asset Not Found",
        "help": "Use a CIK from Issuers.Info",
        "usage": "https://api.blocktransfer.com/assets/{CIK}"
      })
    }

def getNumOutstanding(code):
  try:
    XLMassetInfo = requests.get(
      "https://horizon.stellar.org/assets",
      params = {
        "asset_code": code,
        "asset_issuer": "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7",
        "limit": 200
      }
    ).json()["_embedded"]["records"][0]
  except (KeyError, IndexError):
    return 0
  adjLedgerBals = sum(Decimal(bals) for bals in XLMassetInfo["balances"].values())
  sumBalWithRestricted = adjLedgerBals + Decimal(XLMassetInfo["claimable_balances_amount"])
  sumBalWithRestrictedAndLiqPools = sumBalWithRestricted + Decimal(XLMassetInfo["liquidity_pools_amount"])
  return str(sumBalWithRestrictedAndLiqPools) if bool(sumBalWithRestrictedAndLiqPools) else ""

def displayAssetCodesForIssuer(digitQuery):
  assumedCIK = int(digitQuery)
  stellarToml = toml.loads(
    requests.get(
      "https://blocktransfer.com/.well-known/stellar.toml"
    ).content.decode()
  )
  issuerAssets = []
  for assets in stellarToml.get("CURRENCIES"):
    if assets["issuer_cik"] == assumedCIK:
      issuerAssets.append(assets["code"])
  if issuerAssets:
    return {
      "statusCode": 200,
      "body": json.dumps({
        "issuer_cik": assumedCIK,
        "issuer_assets": issuerAssets,
        "blame": "https://blocktransfer.com/.well-known/stellar.toml"
      })
    }
  else:
    return {
      "statusCode": 404,
      "body": json.dumps({
        "error": "Issuer Not Found",
        "help": "Use a CIK from Issuers.Info",
        "usage": "https://api.blocktransfer.com/assets/{CIK}"
      })
    }
