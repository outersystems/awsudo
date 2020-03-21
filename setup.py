#!/usr/bin/env python

from setuptools import setup

setup(
    name='awsudo',
    description='sudo-like utility to manage AWS credentials',
    url='https://github.com/makethunder/awsudo',
    packages=['awsudo'],
    entry_points={
        'console_scripts': [
            'awsudo = awsudo.main:main',
            'awsudo2 = awsudo.awsudo2:main',
            'awsrotate = awsudo.rotate:main',
        ],
    },
    install_requires=[
        'botocore',
        'retrying',
        'awscli',
        'boto3',
        'pytz'
    ],
)
