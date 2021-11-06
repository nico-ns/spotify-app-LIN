#!/usr/bin/python
activate_this = '/var/www/webApp/sp_venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/webApp/")

from app import app as application #THIS LOOK FOR app INSIDE THE __init__.py FILE IN THE webApp FOLDER
application.secret_key = 'BROHCecHi989843!&%3dboBOLBL'
