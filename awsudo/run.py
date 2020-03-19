#!/bin/env python3

import os
import pathlib
import json
import datetime
import dateutil.parser
import pytz
import boto3
import botocore
import getopt
import sys
import configparser

cache_dir = "~/.aws/awsudo/cache/"
user_cache_file = "user.session.json"

# import awsudo.main
# awsudo.main.main()

def usage():
    sys.stderr.write('''\
Usage: awsudo [-u USER] [--] COMMAND [ARGS] [...]

Sets AWS environment variables and then executes the COMMAND.
''')
    exit(1)


def parseArgs():
    try:
        options, args = getopt.getopt(sys.argv[1:], 'u:')
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        usage()

    if not (args):
        usage()

    profile = os.environ.get('AWS_PROFILE')
    for (option, value) in options:
        if option == '-u':
            profile = value
        else:
            raise Exception("unknown option %s" % (option,))

    return profile, args


def clean_env():
    """Delete from the environment any AWS or BOTO configuration.

    Since it's this program's job to manage this environment configuration, we
    can blow all this away to avoid any confusion.
    """
    for k in list(os.environ.keys()):
        if k.startswith('AWS_') or k.startswith('BOTO_'):
            del os.environ[k]


def run(args, extraEnv):
    env = os.environ.copy()
    env.update(extraEnv)
    try:
        os.execvpe(args[0], args, env)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        raise SystemExit("%s: command not found" % (args[0],))


def fetch_user_token():
    """Query AWS to get temporary credentials of a user with an MFA."""

    config = configparser.ConfigParser()
    config.read([os.path.expanduser("~/.aws/config")])
    
    duration_string = config.get("profile default", 'duration_seconds')
    durationSeconds = int(duration_string)

    # Using the mfa_serial from the profile named default
    mfaSerial = config.get("profile default", 'mfa_serial')

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


def fetch_assume_role_creds(role_arn, user_session_token):
    import configparser

    config = configparser.ConfigParser()
    config.read([os.path.expanduser("~/.aws/config")])
    
    duration_string = config.get("profile default", 'duration_seconds')

    sts = boto3.client('sts',
        aws_access_key_id=user_session_token['Credentials']['AccessKeyId'],
        aws_secret_access_key=user_session_token['Credentials']['SecretAccessKey'],
        aws_session_token=user_session_token['Credentials']['SessionToken'],
        region_name="eu-central-1")

    role_session = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="ARN_ROLE_SESSION_NAME",
        DurationSeconds=3600)

    return(role_session['Credentials'])

def get_from_profile(profile):

    config = configparser.ConfigParser()
    config.read([os.path.expanduser("~/.aws/config")])
    
    try:
        role_arn = config.get("profile %s" % profile, 'role_arn')
    except configparser.NoSectionError as e:
        print("Profile %s not found in config file." % profile)
        exit(1)
    except configparser.NoOptionError as e:
        role_arn = None

    try:
        region   = config.get("profile %s" % profile, 'region')
    except configparser.NoOptionError as e:
        region = None
    
    return(role_arn, region)

def create_aws_env_var(profile, region, creds):
    
    env = {}
    env['AWS_ACCESS_KEY_ID']     = creds['AccessKeyId']
    env['AWS_SECRET_ACCESS_KEY'] = creds['SecretAccessKey']
    env['AWS_SESSION_TOKEN']     = creds['SessionToken']
    env['AWS_SECURITY_TOKEN']    = creds['SessionToken']
    env['AWS_DEFAULT_REGION']    = region
    env['AWS_PROFILE']           = profile

    return(env)

def is_arn_role(arn):
    import re

    if arn:
        pattern = re.compile(":role/")
        return(pattern.search(arn))
    
    return False

def main():

    profile, args = parseArgs()
    clean_env()

    session_creds = get_last_session(cache_dir, user_cache_file)
    
    if not is_session_valid(session_creds):
        session_creds = refresh_session(cache_dir + user_cache_file)

    role_arn, region = get_from_profile(profile)


    if is_arn_role(role_arn):
        role_creds = fetch_assume_role_creds(role_arn, session_creds)
    else:
        role_creds = session_creds['Credentials']

    env = create_aws_env_var(profile, region, role_creds)

    run(args, env)

if __name__ == '__main__':
    main()