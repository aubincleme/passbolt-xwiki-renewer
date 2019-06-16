# XWiki password renewer

This tools interfaces with a [Passbolt](https://passbolt.com) instance to automatically renew XWiki user passwords stored on the instance.

# Requirements

This tool uses the following components : 
* Python3
* Virtualenv (to install Python dependencies)
* GnuPG, for the management of PGP keys associated with the Passbolt server

# Installation

* Clone the repository :

```
git clone https://github.com/aubincleme/passbolt-xwiki-renewer.git
cd passbolt-xwiki-renewer
```

* Setup the virtual environment :
```
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install -r requirements.txt
```

You're good to go ! To re-use the script in a new shell, simply do `source venv/bin/activate` before running the script.

# Usage

The script will look for a file named `passwords.list`, with a list of Passbolt resources IDs to synchronize with their corresponding XWiki instances.
