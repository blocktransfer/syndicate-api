# ----------------------------------------------------- #
# EXTERNAL: PUBLIC FUNCTION WITH NO USER AUTHENTICATION #
# ----------------------------------------------------- #

import json, requests

BT_ISSUER = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7"
HORIZON_INST = "https://horizon.stellar.org"

def lambda_handler(event, context):
  code = event["pathParameters"]["code"]
  ledgerBalances = getUnrestrictedShares(code)
  ledgerBalancesWithRestricted = addRestrictedShares(ledgerBalances, code)
  return ledgerBalancesWithRestricted
  
  # pending Soroban implementation of employment comp and other types of custom shares
  ledgerBalancesWithRestrictedAndContract = addSorobanShares(ledgerBalancesWithRestricted, code)
  return ledgerBalancesWithRestrictedAndContract

def getUnrestrictedShares(code):
  ledgerBalances = {}
  chiefLedger = requests.get(
    f"{HORIZON_INST}/accounts",
    params = {
      "asset": f"{code}:{BT_ISSUER}",
      "limit": 200
    }
  ).json()
  links = chiefLedger["_links"]
  records = chiefLedger["_embedded"]["records"]
  while(records):
    for accounts in records:
      for balances in accounts["balances"]:
        # Use .get() to filter out XLM
        if balances.get("asset_issuer") != BT_ISSUER: continue
        if balances["asset_code"] != code: continue
        ledgerBalances[
          accounts["account_id"]
        ] = {"unrestricted": balances["balance"]}
        break
    links, records = getNextPage(links)
  return ledgerBalances

def addRestrictedShares(ledgerBalances, code):
  chiefLedger = requests.get(
    f"{HORIZON_INST}/claimable_balances",
    params = {
      "asset": f"{code}:{BT_ISSUER}",
      "limit": 200
    }
  ).json()
  links = chiefLedger["_links"]
  records = chiefLedger["_embedded"]["records"]
  while(records):
    for CBs in records:
      ledgerBalances.setdefault(
        # Assume user is chief claimant
        CBs["claimants"][0]["destination"], {}
      )["restricted"] = CBs["amount"]
    links, records = getNextPage(links)
  return ledgerBalances

def getNextPage(predecessorLinks):
  nextPage = requests.get(
    predecessorLinks["next"]["href"].replace("\u0026", "&").replace("%3A", ":")
  ).json() # Manual JSON symbol replacement faster than using urllib at scale
  print(predecessorLinks["next"]["href"])
  return nextPage["_links"], nextPage["_embedded"]["records"]
