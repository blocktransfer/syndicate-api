import stellar_sdk as xlm
import boto3

PII_DB = boto3.resource("dynamodb").Table("PII")
AWS_SECRETS = boto3.client("secretsmanager")
BETA = "Thank you for being a beta user!"
NEW = "http://www.blocktransfer.com/beta"

def lambda_handler(event, context):
  try:
    sender, receiver, transferOp = getInputsFromXDR(
      event["queryStringParameters"]["tx"]
    )
    verifyBothAccs(sender, receiver)
    BTsignerAcc = getServerKeypair()
    serverKeypair = 
    transactionBuilder = xlm.TransactionBuilder(
      source_account = serverKeypair,
      network_passphrase = xlm.Network.PUBLIC_NETWORK_PASSPHRASE,
      base_fee = BASE_FEE>..._
    )
    transactionBuilder.append_transaction_op(transferOp)
    transactionBuilder.sign()
    transactionResponse = transactionBuilder.submit()
    return {"statusCode": 200, "body": "Transaction successfully signed and submitted."}
  except LookupError:
    return formatActionReq(f"{BETA} To complete this transaction, you must link your account at {NEW}")
  except UserWarning:
    return formatActionReq(f"{BETA} The person you are trying to transfer to does not have an account with Block Transfer :( They can open an account at {NEW} :)")
  except PermissionError:
    return formatRejection("Account restricted. Contact support@blocktransfer.com")
  except ReferenceError:
    return formatRejection(f"{BETA} The transfer destination account is restricted :(")
  except SyntaxError:
    return formatRejection(f"{BETA} Block Transfer presently supports only stock transfers. If you believe you've encountered this error mistakenly, please contact support@blocktransfer.com for assistance :)")
  except Exception as e: ## prod -- no e
    return {
      "statusCode": 200,
      "body": {
        "status": "pending",
        "timeout": 0,
        "error": str(e) ## "Internal Service Error"
      }
    }

def getInputsFromXDR(txnXDR):
  txn = xlm.xdr.TransactionEnvelope.from_xdr(txnXDR)
  if(txn.type != 2):
    raise SyntaxError()
  txn = txn.v1.tx
  ops = txn.operations
  if len(ops) != 1:
    raise SyntaxError()
  op = ops[0]
  transfer = op.body.payment_op
  if not transfer:
    raise SyntaxError()
  # Does not support muxed accounts... #
  sender = (op.source_account or txn.source_account).ed25519
  receiver = transfer.destination.ed25519
  # ...which is fine for basic beta! #
  if not sender or not receiver:
    raise SyntaxError()
  return ed25519toPK(sender), ed25519toPK(receiver), transfer

def ed25519toPK(Ed25519):
  return xlm.StrKey.encode_ed25519_public_key(Ed25519.uint256)

def verifyBothAccs(senderPK, receiverPK):
  try:
    senderPII = PII_DB.get_item(Key = {"PK": senderPK})
    if "Item" in senderPII:
      if isAccRestricted(senderPII):
        raise PermissionError()
    else:
      raise LookupError()
    receiverPII = PII_DB.get_item(Key = {"PK": receiverPK})
    if "Item" in receiverPII:
      if isAccRestricted(senderPII["Item"]):
        raise ReferenceError()
    else:
      raise UserWarning()
  except Exception as e:
    raise SystemError()

def getPII(pubKey):
  return 

def isAccRestricted(rawAccount):
  user = rawAccount["Item"]
  return "restrictions" in user and user["restrictions"]["status"] != 200

def getAuthServerKeypair():
  response = AWS_SECRETS.get_secret_value(SecretId = "hotSigners/trustlines")
  return xlm.Keypair.from_secret(response["SecretString"])

def formatActionReq(error):
  return {
    "statusCode": 200,
    "body": {
      json.dumps(
        {
          "status": "action_required",
          "timeout": 0,
          "message": error
        }
      )
    }
  }

def formatRejection(reason):
  return {
    "statusCode": 400,
    "body": {
      json.dumps(
        {
          "status": "rejected",
          "message": reason
        }
      )
    }
  }
