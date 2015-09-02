# pylint: disable=duplicate-code
# -*- coding: utf-8 -*-
"""
Flask app initialization.
"""
from flask import Flask
from flask_mako import MakoTemplates

APP = Flask(__name__)
MAKO_TPL = MakoTemplates(APP)
