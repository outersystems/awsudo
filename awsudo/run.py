#!/bin/env python3
import awsudo.main
import os
import pathlib
import json

cache_dir = "~/.aws/awsudo/cache/"
cache_file = "session.json"

#awsudo.main.main()

# mkdir ~/.aws/awsudo
# if ~/.aws/awsudo/session.json or expired then
#   Get session token
# if PROFILE defined then
#   Get ASSUME role
#   with cache
# else
#   No idea...


cache_dir_path = os.path.expanduser(cache_dir)
pathlib.Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

session_creds = {}

if os.path.isfile(cache_dir_path + cache_file):
    print("Yes")
    with open(cache_dir_path + cache_file) as json_file:
        data = json.load(json_file)
        session_creds['field1'] = data['field1']
        
else:
    print("No")

# If outdated - 1h:
#   Query AWS



# import json
# print(json.dumps({'4': 5, '6': 7}, sort_keys=True, indent=4))