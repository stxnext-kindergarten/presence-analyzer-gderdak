# -*- coding: utf-8 -*-
"""
Updates local users.xml.
"""
import os
import urllib2

from main import app


def update_xml_file():
    """
    Downloads users.xml file with users data then updates local users.xml file.
    """
    app.config.from_pyfile(
        os.path.join(
            os.path.dirname(__file__), '..', '..', 'parts', 'etc', 'deploy.cfg'
        )
    )
    xml_file = urllib2.urlopen(app.config['XML_URL'])
    with open(app.config['DATA_XML'], 'w') as local_xml:
        local_xml.write(xml_file.read())
