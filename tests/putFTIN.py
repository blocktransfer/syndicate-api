# Implicates seperate root account for secure isolation, which is documented internally and must be moved to TAD3 docs

import boto3, json

def lambda_handler(event, context):
  stsClient = boto3.client("sts")
  assumedRole = stsClient.assume_role(
    RoleArn="arn:aws:lambda:us-east-2:389400851932:function:tryLast4",
    RoleSessionName="AssumeRoleSession"
  )
  lambdaClient = boto3.client("lambda",
    awsAccessKeyId = assumedRole["Credentials"]["AccessKeyId"],
    awsSecretAccessKey = assumedRole["Credentials"]["SecretAccessKey"],
    awsSessionToken = assumedRole["Credentials"]["SessionToken"],
    regionName="us-east-2"
  )
  payload = json.dumps({
    "last4": "1234",
    "token": "your_token_here"
  })

  payloadJson = json.dumps(payload)

  response = lambdaClient.invoke(
    FunctionName="arn:aws:lambda:us-east-2:088831146342:function:test_putFTIN",
    InvocationType="RequestResponse",
    Payload=payloadJson
  )

  responsePayload = response["Payload"].read()
  return responsePayload
