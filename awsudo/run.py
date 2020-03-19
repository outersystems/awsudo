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


cache_dir = "~/.aws/awsudo/cache/"
user_cache_file = "user.session.json"

#awsudo.main.main()

def fetch_user_token():
    """Query AWS to get temporary credentials of a user with an MFA."""
    import getpass
    import configparser

    config = configparser.ConfigParser()
    config.read([os.path.expanduser("~/.aws/config")])
    
    durationSeconds = int(config.get("default", 'duration_seconds'))

    # Using the mfa_serial from the profile named default
    mfaSerial = config.get("default", 'mfa_serial')

    sts_client = boto3.client('sts')

    try:
        mfaToken = getpass.getpass(prompt="Enter MFA token: ")
    except KeyboardInterrupt as e:
        print(e)
        exit(1)

    try:
        return sts_client.get_session_token(DurationSeconds=durationSeconds, SerialNumber=mfaSerial, TokenCode=mfaToken)
    except botocore.exceptions.ClientError as e:
        print ("Error to get session token. MFA Errorneous?")
        exit(1)

def fetch_role_session_token():
    """Query AWS to get temporary credentials for a role, derived from user session token."""
    print ("stuff")

def get_last_session(cache_dir, cache_file):
    """Return the current session from cache_dir/cache_file.
    Could be {} if no file found"""
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
    
    return session_creds

def is_session_valid(session_creds):
    """Check if a session is still valid, based on its expiration date"""
    if 'Credentials' in session_creds.keys():
        expiration_utc = dateutil.parser.isoparse(session_creds['Credentials']['Expiration'])
        now_utc = pytz.utc.localize(datetime.datetime.utcnow())
        max_accepted_timedelta = datetime.timedelta(hours=1)
        
        if (expiration_utc - now_utc) > max_accepted_timedelta:
            return True

    return False


def refresh_session(filename):
    """Refresh credentials and cache them."""
    session_creds = fetch_user_token()

    with open(os.path.expanduser(filename), "w+") as json_file:
        json.dump(session_creds, json_file, indent=2, sort_keys=True, default=str)

    return session_creds

def fetch_assume_role_creds(user_session_token):
    print("assume role!")

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html
    # assume_role_session = boto3.session.Session(
    #     aws_access_key_id=None,
    #     aws_secret_access_key=None,
    #     aws_session_token=None,
    #     region_name=None,
    #     botocore_session=None,
    #     profile_name=None)

    # user_session = boto3.session.Session(
    #     aws_access_key_id=user_session_token['Credentials']['AccessKeyId'],
    #     aws_secret_access_key=user_session_token['Credentials']['SecretAccessKey'],
    #     aws_session_token=user_session_token['Credentials']['SessionToken'],
    #     region_name=None,
    #     botocore_session=None,
    #     profile_name=None)

    # https://stackoverflow.com/questions/42809096/difference-in-boto3-between-resource-client-and-session
    # https://stackoverflow.com/questions/45981950/how-to-specify-credentials-when-connecting-to-boto3-s3
    c = boto3.client('sts',
        aws_access_key_id=,
        aws_secret_access_key=
        region_name=)

    # Then         assume_role_object = sts_connection.assume_role(RoleArn=arn, RoleSessionName=ARN_ROLE_SESSION_NAME,DurationSeconds=3600
    # https://stackoverflow.com/questions/44171849/aws-boto3-assumerole-example-which-includes-role-usage

    role_arn = 'arn:aws:iam::313341868584:role/ec2'
    # fetcher = botocore.credentials.AssumeRoleCredentialFetcher(
    #     client_creator = user_session._session.create_client,
    #     source_credentials = user_session.get_credentials(),
    #     role_arn = role_arn,
    #     extra_args = {
    #     #    'RoleSessionName': None # set this if you want something non-default
    #     }
    # )
    # creds = botocore.credentials.DeferredRefreshableCredentials(
    #     method = 'assume-role',
    #     refresh_using = fetcher.fetch_credentials,
    #     time_fetcher = lambda: datetime.datetime.now(tzlocal())
    # )
    # botocore_session = botocore.session.Session()
    # botocore_session._credentials = creds
    # # return boto3.Session(botocore_session = botocore_session)

    # # ses

    boto.Credentials.get_credentials()
    
# Current hypothesis: https://stackoverflow.com/questions/44171849/aws-boto3-assumerole-example-which-includes-role-usage
# usage:
# session = assumed_role_session('arn:aws:iam::ACCOUNTID:role/ROLE_NAME')







    #print(assume_role_session)
    # creds = assume_role_session.get_credentials()
    # print(assume_role_session.get_credentials())
    
    # client = boto3.client('sts', 'us-west-2')



    response = user_session.assume_role(
        RoleArn='arn:aws:iam::313341868584:role/ec2',
        DurationSeconds=900)

    # tmp_credentials = {
    #         'sessionId': response['Credentials']['AccessKeyId'],
    #         'sessionKey': response['Credentials']['SecretAccessKey'],
    #         'sessionToken':response['Credentials']['SessionToken']
    #         }

    print("So?")

def main():

    session_creds = get_last_session(cache_dir, user_cache_file)
    
    if not is_session_valid(session_creds):
        session_creds = refresh_session(cache_dir + user_cache_file)

    fetch_assume_role_creds(session_creds)

if __name__ == '__main__':
    main()