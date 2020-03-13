#!/bin/env python3
import awsudo.main
import os
import pathlib
import json
import datetime
import dateutil.parser
import pytz
import boto3



cache_dir = "~/.aws/awsudo/cache/"
cache_file = "session.json"
session_creds = {}

#awsudo.main.main()

# mkdir ~/.aws/awsudo
# if ~/.aws/awsudo/session.json or expired then
#   Get session token
# if PROFILE defined then
#   Get ASSUME role
#   with cache
# else
#   No idea...

# class session_creds:
#   def __init__(self, data):
#       self.data = data

def fetch_session_token():
    import getpass
    import configparser

    config = configparser.ConfigParser()
    config.read([os.path.expanduser("~/.aws/config")])
    durationSeconds = config.get("default", 'duration_seconds')
    mfaSerial = config.get("default", 'mfa_serial')

    sts_client = boto3.client('sts')

    mfaToken = getpass.getpass(prompt="Enter MFa token: ")

    sessionCreds = sts_client.get_session_token(durationSeconds, mfaSerial, mfaToken)

def main():
    cache_dir_path = os.path.expanduser(cache_dir)
    pathlib.Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

    # Load session creds
    if os.path.isfile(cache_dir_path + cache_file):
        with open(cache_dir_path + cache_file) as json_file:
            session_creds = json.load(json_file)

    # Should we refresh session creds?
    if data.has_key('Expiration')
        expiration_utc = dateutil.parser.isoparse(data['Expiration'])
        now_utc = pytz.utc.localize(datetime.datetime.utcnow())
        max_accepted_timedelta = datetime.timedelta(hours=1)
        
        if (expiration_utc - now_utc) <= max_accepted_timedelta:
            #renew
    else:
        #renew        

    # here session creds are fine.


# If outdated - 1h:
#   Query AWS



# import json
# print(json.dumps({'4': 5, '6': 7}, sort_keys=True, indent=4))

if __name__ == '__main__':
    main()