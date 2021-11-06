#!/var/www/webApp/spot_venv/bin/python3
from flask import Flask
#import Flask

app = Flask(__name__)
app.secret_key = "BROHCecHi989843!&%3dboBOLBL"

from app import routes
from app.util import filters
