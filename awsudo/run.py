#!/bin/env python3
import awsudo.main
import os
import pathlib
import json
import datetime
import dateutil.parser
import pytz
import boto3
import botocore
import pdb


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
    durationSeconds = int(config.get("default", 'duration_seconds'))
    mfaSerial = config.get("default", 'mfa_serial')

    sts_client = boto3.client('sts')

    try:
        mfaToken = getpass.getpass(prompt="Enter MFa token: ")
    except KeyboardInterrupt as e:
        print(e)
        exit(1)

    try:
        return sts_client.get_session_token(DurationSeconds=durationSeconds, SerialNumber=mfaSerial, TokenCode=mfaToken)
    except botocore.exceptions.ClientError as e:
        print ("Error to get session token. MFA Errorneous?")
        exit(1)


def main():
    cache_dir_path = os.path.expanduser(cache_dir)
    pathlib.Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

    # Load session creds
    if os.path.isfile(cache_dir_path + cache_file):
        with open(cache_dir_path + cache_file) as json_file:
            try:
                session_creds = json.load(json_file)
            except json.decoder.JSONDecodeError as e:
                print(e)
                exit(1)
    else:
        session_creds = {}
        with open(cache_dir_path + cache_file, "w+") as json_file:
            json.dump(session_creds, json_file)

    # Should we refresh session creds?
    if 'Credentials' in session_creds.keys():
        expiration_utc = dateutil.parser.isoparse(session_creds['Credentials']['Expiration'])
        now_utc = pytz.utc.localize(datetime.datetime.utcnow())
        max_accepted_timedelta = datetime.timedelta(hours=1)
        
        if (expiration_utc - now_utc) <= max_accepted_timedelta:
            print("renew")
            session_creds = fetch_session_token()
            with open(cache_dir_path + cache_file) as json_file:
                json.dump(session_creds, json_file)
        else:
            print("Cache valid")
    else:
        print("renew")
        session_creds = fetch_session_token()

        with open(cache_dir_path + cache_file, "w") as json_file:
            json.dump(session_creds, json_file, indent=4, sort_keys=True, default=str)


    # here session creds are fine.


# If outdated - 1h:
#   Query AWS


# import json
# print(json.dumps({'4': 5, '6': 7}, sort_keys=True, indent=4))

if __name__ == '__main__':
    main()