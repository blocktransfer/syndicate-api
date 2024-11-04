# ----------------------------------------------------- #
# EXTERNAL: PUBLIC FUNCTION WITH NO USER AUTHENTICATION #
# ----------------------------------------------------- #

import requests, json
from decimal import Decimal

BT_ISSUER = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7"
HORIZON_INST = "https://horizon.stellar.org"

def lambda_handler(event, context):
  code = event["pathParameters"]["code"]
  outstanding = getLedgarTotal(code)
  return str(outstanding)

def getLedgarTotal(queryAsset):
  try:
    XLMassetInfo = requests.get(
      f"{HORIZON_INST}/assets",
      params = {
        "asset_code": queryAsset,
        "asset_issuer": BT_ISSUER,
        "limit": 200
      }
    ).json()["_embedded"]["records"][0]
  except IndexError:
    return 0
  adjLedgerBals = sum(Decimal(bals) for bals in XLMassetInfo["balances"].values())
  sumBalWithRestricted = adjLedgerBals + Decimal(XLMassetInfo["claimable_balances_amount"])
  sumBalWithRestrictedAndLiqPools = sumBalWithRestricted + Decimal(XLMassetInfo["liquidity_pools_amount"])
  # sumBalWithRestrictedLiqPoolsAndSorobon = 
  return sumBalWithRestrictedAndLiqPools

def dsjaio():
  # -> https://horizon.stellar.org/assets?asset_code=DEMO&asset_issuer=GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7
  assetData = requests.get(assetAddr).json()["_embedded"]["records"][0]
  shares = Decimal(assetData["liquidity_pools_amount"])
  for balances in assetData["balances"].values():  
    shares += Decimal(balances)
  shares += Decimal(assetData["claimable_balances_amount"])
  return shares - treasuryShares - reservedShares
