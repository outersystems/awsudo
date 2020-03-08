#!/bin/env python3
import awsudo.main

awsudo.main.main()

# mkdir ~/.aws/awsudo
# if ~/.aws/awsudo/session.json or expired then
#   Get session token
# if PROFILE defined then
#   Get ASSUME role
#   with cache
# else
#   No idea...

