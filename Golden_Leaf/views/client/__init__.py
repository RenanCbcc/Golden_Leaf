# A blueprint needs to be a package. That's why all folders needs to have a __init__.py
from flask import Blueprint

blueprint_client = Blueprint('blueprint_client', __name__)