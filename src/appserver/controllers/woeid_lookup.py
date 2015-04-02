import logging
import os
import sys
import json
import cherrypy
import urllib

from splunk import AuthorizationFailed, ResourceNotFound
import splunk.appserver.mrsparkle.controllers as controllers
import splunk.appserver.mrsparkle.lib.util as util
from splunk.appserver.mrsparkle.lib import jsonresponse
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
import splunk.clilib.bundle_paths as bundle_paths
from splunk.util import normalizeBoolean as normBool
from splunk.appserver.mrsparkle.lib.decorators import expose_page
from splunk.appserver.mrsparkle.lib.routes import route

def setup_logger(level):
    """
    Setup a logger for the REST handler.
    """

    logger = logging.getLogger('splunk.appserver.insteon.controllers.WoeidLookup')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', 'insteon_woeid_controller.log']), maxBytes=25000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger(logging.DEBUG)

class WOEIDLookup(controllers.BaseController):
    '''
    Weather ID lookup Controller
    '''
 
    @expose_page(must_login=True, methods=['GET']) 
    def getPotentialWOEIDs(self, location):
        """
        Get potential weather IDs for a given location
        """
        
        #url = 'http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20geo.places%20where%20text%3D%22Wadsworth%22&format=json'
        url = 'http://query.yahooapis.com/v1/public/yql'
        
        params = urllib.urlencode({
            'q': "select * from geo.places where text='" + location + "'",
            'format': 'json'
        })
        
        data = urllib.urlopen(url, params).read()
        
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return data