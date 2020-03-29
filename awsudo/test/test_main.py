import sys
import os
import pytest

from awsudo import main


def test_no_args(capsys, monkeypatch):
    '''With no arguments, awsudo exits with usage.'''
    monkeypatch.setattr(sys, 'argv', ['awsudo'])

    with pytest.raises(SystemExit):
        main.main()

    out, err = capsys.readouterr()
    assert 'Usage:' in err


def test_only_option(capsys, monkeypatch):
    '''With only options, awsudo exits with usage.'''
    monkeypatch.setattr(sys, 'argv', ['awsudo', '-u', 'default'])

    with pytest.raises(SystemExit):
        main.main()

    out, err = capsys.readouterr()
    assert 'Usage:' in err


def test_parseArgs_env_profile(monkeypatch):
    '''Env vars is taken if no option are given.'''
    environ = {
        'AWS_PROFILE': 'profile'
    }
    monkeypatch.setattr(os, 'environ', environ)
    monkeypatch.setattr(sys, 'argv', ['awsudo', 'command'])

    profile, args = main.parseArgs()

    assert profile == 'profile'
    assert args == ['command']


def test_parseArgs_option_over_environ(monkeypatch):
    '''Options values are taken even if environment variables are set.'''
    environ = {
        'AWS_PROFILE': 'profile-environ'
    }
    monkeypatch.setattr(os, 'environ', environ)
    monkeypatch.setattr(sys, 'argv', ['awsudo', '-u', 'profile-option', 'command'])

    profile, args = main.parseArgs()

    assert profile == 'profile-option'
    assert args == ['command']


def test_cleanEnvironment(monkeypatch):
    '''cleanEnvironment strips AWS and boto configuration.'''
    environ = {
        'AWS_SECRET': 'password1',
        'BOTO_CONFIG': 'please work',
        'HOME': 'ward bound',
    }
    monkeypatch.setattr(os, 'environ', environ)

    main.cleanEnvironment()

    assert 'AWS_SECRET' not in environ
    assert 'BOTO_CONFIG' not in environ
    assert environ['HOME'] == 'ward bound'
