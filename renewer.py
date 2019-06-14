#!/usr/bin/env python3
import json
import requests

from configparser import ConfigParser

from requests_gpgauthlib import GPGAuthSession
from requests_gpgauthlib.utils import create_gpg, get_workdir

config = ConfigParser()
config.read('config.ini')

SERVER_URL = config.get('server_url')

