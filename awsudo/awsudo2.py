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
import getpass

aws_config_file = "~/.aws/config"
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


def parse_args():
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


def fetch_user_token(profile_config):
    """Query AWS to get temporary credentials of a user with an MFA."""

    durationSeconds = int(profile_config['duration_seconds'])

    mfaSerial = profile_config['mfa_serial']
    try:
        mfaToken = getpass.getpass(prompt="Enter MFA token: ")
    except KeyboardInterrupt as e:
        print(e)
        exit(1)

    sts = boto3.client('sts')
    try:
        return sts.get_session_token(
            DurationSeconds=durationSeconds,
            SerialNumber=mfaSerial,
            TokenCode=mfaToken)
    except Exception as e:
        print(e)
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


def refresh_session(filename, profile_config):
    """Refresh credentials and cache them."""
    session_creds = fetch_user_token(profile_config)

    with open(os.path.expanduser(filename), "w+") as json_file:
        json.dump(session_creds, json_file, indent=2, sort_keys=True, default=str)

    return session_creds


def fetch_assume_role_creds(user_session_token, profile_config):
    import configparser

    config = configparser.ConfigParser()
    config.read([os.path.expanduser(aws_config_file)])

    sts = boto3.client('sts',
        aws_access_key_id=user_session_token['Credentials']['AccessKeyId'],
        aws_secret_access_key=user_session_token['Credentials']['SecretAccessKey'],
        aws_session_token=user_session_token['Credentials']['SessionToken'],
        region_name=profile_config['region'])

    if profile_config['duration_seconds']:
        duration = int(profile_config['duration_seconds'])
    else:
        duration = 3600

    try:
        role_session = sts.assume_role(
            RoleArn=profile_config['role_arn'],
            RoleSessionName="awsudo",
            DurationSeconds=duration)
    except Exception as e:
        print(e)
        exit(1)

    return(role_session['Credentials'])


def get_profile_config(profile):

    config = configparser.ConfigParser()
    config.read([os.path.expanduser(aws_config_file)])

    config_element = dict()
    try:
        config_element['role_arn'] = config.get("profile %s" % profile, 'role_arn')
    except configparser.NoSectionError as e:
        print("Profile %s not found in config file." % profile)
        exit(1)
    except configparser.NoOptionError as e:
        config_element['role_arn'] = None

    try:
        config_element['region'] = config.get("profile %s" % profile, 'region')
    except configparser.NoOptionError as e:
        config_element['region'] = None

    try:
        config_element['duration_seconds'] = config.get("profile %s" % profile, 'duration_seconds')
    except configparser.NoOptionError as e:
        config_element['duration_seconds'] = None

    try:
        config_element['mfa_serial'] = config.get("profile %s" % profile, 'mfa_serial')
    except configparser.NoOptionError as e:
        config_element['mfa_serial'] = None

    return(config_element)


def create_aws_env_var(profile, profile_config, creds):

    env = dict()
    env['AWS_ACCESS_KEY_ID'] = creds['AccessKeyId']
    env['AWS_SECRET_ACCESS_KEY'] = creds['SecretAccessKey']
    env['AWS_SESSION_TOKEN'] = creds['SessionToken']
    env['AWS_SECURITY_TOKEN'] = creds['SessionToken']
    env['AWS_PROFILE'] = profile

    if profile_config['region']:
        env['AWS_DEFAULT_REGION'] = profile_config['region']
    else:
        env['AWS_DEFAULT_REGION'] = ""

    return(env)

def is_arn_role(arn):
    import re

    if arn:
        pattern = re.compile(":role/")
        return(pattern.search(arn))

    return False

def main():

    profile, args = parse_args()
    clean_env()

    session_creds = get_last_session(cache_dir, user_cache_file)

    if not is_session_valid(session_creds):
        profile_config = get_profile_config("default")
        session_creds = refresh_session(cache_dir + user_cache_file, profile_config)

    profile_config = get_profile_config(profile)

    if is_arn_role(profile_config['role_arn']):
        role_creds = fetch_assume_role_creds(
            session_creds,
            profile_config)
    else:
        role_creds = session_creds['Credentials']

    env = create_aws_env_var(profile, profile_config, role_creds)

    run(args, env)


if __name__ == '__main__':
    main()

