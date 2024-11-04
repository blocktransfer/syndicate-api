import stellar_sdk
from stellar_sdk import Server, Keypair, TransactionBuilder, Network

def lambda_handler(event, context):
  server = Server("https://horizon.stellar.org")
  network = Network.PUBLIC_NETWORK_PASSPHRASE
  test_account_id = "GDRM3MK6KMHSYIT4E2AG2S2LWTDBJNYXE4H72C7YTTRWOWX5ZBECFWO7"

  account = server.accounts().account_id(test_account_id).call()
  xlm_balance = None
  for balance in account["balances"]:
    if balance["asset_type"] == "native":
      xlm_balance = float(balance["balance"])
      break
  assert(xlm_balance >= 0)

  account = server.accounts().account_id(test_account_id).call()
  num_signers = len(account["signers"])
  assert(num_signers >= 5)

  account = server.accounts().account_id(test_account_id).call()
  home_domain = account["home_domain"]
  expected_home_domain = "blocktransfer.com"
  assert(home_domain == expected_home_domain)
  
  return "Success"
