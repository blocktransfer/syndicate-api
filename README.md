# Block Transfer API Server

These functions read off the Stellar blockchain and manipulate internal Syndicate databases. In due time, the structure of these relationships will get documented in the TAD3 docs, to the extent they are not already public.

## Short-Term Goal

Specify open API docs at `blocktransfer.dev` using trail routing logic in API Gateway.

## AWS Config

Presently, these are all instantiated as independent Lambdas in the same `dir` with minimal IAM permissions.
I'll need to think further through how we publicly detail the security policies after doing IssuerLink cold auth.
