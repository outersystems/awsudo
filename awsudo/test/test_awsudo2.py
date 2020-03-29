import sys
import os
import pytest

from awsudo import awsudo2


def test_no_args(capsys, monkeypatch):
    '''With no arguments, awsudo2 exits with usage.'''
    monkeypatch.setattr(sys, 'argv', ['awsudo2'])

    with pytest.raises(SystemExit):
        awsudo2.main()

    out, err = capsys.readouterr()
    assert 'Usage:' in err


def test_only_option(capsys, monkeypatch):
    '''With only options, awsudo2 exits with usage.'''
    monkeypatch.setattr(sys, 'argv', ['awsudo2', '-u', 'default'])

    with pytest.raises(SystemExit):
        awsudo2.main()

    out, err = capsys.readouterr()
    assert 'Usage:' in err


def test_parse_args_env_profile(monkeypatch):
    '''Env vars is taken if no option are given.'''
    environ = {
        'AWS_PROFILE': 'profile'
    }
    monkeypatch.setattr(os, 'environ', environ)
    monkeypatch.setattr(sys, 'argv', ['awsudo2', 'command'])

    profile, args = awsudo2.parse_args()

    assert profile == 'profile'
    assert args == ['command']


def test_parse_args_option_over_environ(monkeypatch):
    '''Options values are taken even if environment variables are set.'''
    environ = {
        'AWS_PROFILE': 'profile-environ'
    }
    monkeypatch.setattr(os, 'environ', environ)
    monkeypatch.setattr(sys, 'argv', ['awsudo2', '-u', 'profile-option', 'command'])

    profile, args = awsudo2.parse_args()

    assert profile == 'profile-option'
    assert args == ['command']


def test_clean_env(monkeypatch):
    '''cleanEnvironment strips AWS and boto configuration.'''
    environ = {
        'AWS_SECRET': 'password1',
        'BOTO_CONFIG': 'please work',
        'HOME': 'ward bound',
    }
    monkeypatch.setattr(os, 'environ', environ)

    awsudo2.clean_env()

    assert 'AWS_SECRET' not in environ
    assert 'BOTO_CONFIG' not in environ
    assert environ['HOME'] == 'ward bound'

def test_is_session_valid_invalid(monkeypatch):
    invalid_session_creds = {
        'Credentials': {
            'Expiration': '2010-01-01 01:01:01+00:00'
        }
    }

    result = awsudo2.is_session_valid(invalid_session_creds)

    assert result == False


def test_is_session_valid_valid(monkeypatch):
    valid_session_creds = {
        'Credentials': {
            'Expiration': '9999-01-01 01:01:01+00:00'
        }
    }

    result = awsudo2.is_session_valid(valid_session_creds)

    assert result == True

