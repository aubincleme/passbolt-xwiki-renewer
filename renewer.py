#!/usr/bin/env python3
import json
import logging
import requests
import sys

from config import GPG_HOME, SERVER_URL, USER_FINGERPRINT, SERVER_FINGERPRINT

from requests_gpgauthlib import GPGAuthSession
from requests_gpgauthlib.utils import create_gpg

from requests.auth import HTTPBasicAuth
from requests.utils import dict_from_cookiejar

from secrets import token_urlsafe

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize the gpg keyring
gpg = create_gpg(GPG_HOME)

# Initialize the authenticated session
ga = GPGAuthSession(
    gpg=gpg,
    server_url=SERVER_URL,
    auth_uri='/auth/',
    user_fingerprint=USER_FINGERPRINT
)
assert ga.server_fingerprint == SERVER_FINGERPRINT
ga.authenticate()

# Fetch the list of accessible resources, this will also allow us to get the CSRF token
response = ga.get(ga.build_absolute_uri('/resources.json'), params={'contain[secret]': 1})
# Save the cookie
csrfToken = dict_from_cookiejar(ga.cookies)['csrfToken']
logger.debug('CSRF Token : {}'.format(csrfToken))

# Load the file containing the resources to update
with open('passwords.list', 'r') as f:
    rawPasswordList = f.readlines()
# Sanitize the content
passwordList = []
for element in rawPasswordList:
    passwordList.append(element.rstrip())
logger.debug('Selected passwords for renewal : {}'.format(passwordList))

all_resources = response.json()['body']
logger.debug('Found {} accessible resources.'.format(len(all_resources)))

for resource in all_resources:
    if resource['Resource']['id'] in passwordList:
        resourceID = resource['Resource']['id']
        resourceName = resource['Resource']['name']
        resourceUsername = resource['Resource']['username']
        resourceURI = resource['Resource']['uri']
        logger.info('Updating resource {} - {}'.format(resourceID, resourceName))
        logger.debug(resource)

        # Get the old password, and generate a new one
        oldPassword = gpg.decrypt(resource['Secret'][0]['data'])
        logger.debug('Old password : {}'.format(oldPassword))
        newPassword = token_urlsafe(32)
        logger.debug('New password : {}'.format(newPassword))

        # Update the XWiki user with a new password
        result = requests.put(
            '{}/rest/wikis/xwiki/spaces/XWiki/pages/{}/objects/XWiki.XWikiUsers/0/properties/password'.format(
                resourceURI, resourceUsername
            ),
            data=newPassword,
            auth=HTTPBasicAuth(resourceUsername, oldPassword))

        if result.status_code == 202:
            logger.info('Password successfully updated on XWiki, pushing to Passbolt ...')

            # Generate the payload
            payload = {
                'secrets': [
                    {
                        'user_id': resource['Secret'][0]['user_id'],
                        'data': gpg.encrypt(newPassword, USER_FINGERPRINT).data.decode('utf-8')
                    }
                ]
            }
            logger.debug(payload)

            headers = {
                'X-CSRF-TOKEN': csrfToken,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Send it to Passbolt
            response = ga.put(
                ga.build_absolute_uri('/resources/{}.json'.format(resourceID)),
                data=json.dumps(payload),
                headers=headers
            )
            logger.debug(response.content)
