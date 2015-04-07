
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
from insteon_app.modular_input import Field, DurationField, FieldValidationException, ModularInput

import logging
from logging import handlers
import sys
import time
import os
import splunk
import re

def setup_logger():
    """
    Setup a logger.
    """
    
    logger = logging.getLogger('weather_info_modular_input')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(logging.DEBUG)
    
    file_handler = handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', 'weather_info_modular_input.log']), maxBytes=25000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

class Timer(object):
    """
    This class is used to time durations.
    """
    
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs

class WeatherInfoInput(ModularInput):
    """
    The weather information modular input connects gets weather information from Yahoo.
    """
    
    def __init__(self, **kwargs):

        scheme_args = {'title': "Weather Information",
                       'description': "Retrieves weather information from Yahoo",
                       'use_external_validation': "true",
                       'streaming_mode': "xml",
                       'use_single_instance': "true"}
        
        args = [
                Field("woeid", "Where-on-Earth ID", "The WOEID code to get the information for (see http://woeid.rosselliot.co.nz/)", empty_allowed=False),
                DurationField("interval", "Interval", "How often to wait between each call to get weather information (in seconds)", empty_allowed=False)
                ]
        
        # These are values that are persisted so that the modular input callback has the data to output the event correctly
        self.sourcetype = "weather_info"
        self.index = "default"
        self.source = None
        self.stanza = None
        
        ModularInput.__init__( self, scheme_args, args)
    
    def get_weather_info(self, woeid):
        import urllib2, urllib, json
        
        baseurl = "https://query.yahooapis.com/v1/public/yql?" 
        yql_query = "select * from weather.forecast where woeid=" + woeid 
        yql_url = baseurl + urllib.urlencode({'q':yql_query}) + "&format=json" 
        result = urllib2.urlopen(yql_url).read()
        data = json.loads(result)
        
        return data['query']['results']
    
    def convert_dict_to_list(self, fields, node, parent_names):
        for key, item in node.items():
            if item is collection:
                self.convert_dict_to_list(fields, item, parent_names + "_" + key)
            else:
                fields[parent_names + "_" + key] = item
                
        return fields
    
    def output_weather_info(self, woeid, host, sourcetype, index, stanza, checkpoint_dir):
        import json
        
        weather_data = self.get_weather_info(woeid)
        #logger.debug(json.dumps(weather_data))
        
        # Get the fields to output
        data = {}
        
        data['city'] = weather_data['channel']['location']['city']
        data['country'] = weather_data['channel']['location']['country']
        data['region'] = weather_data['channel']['location']['region']
        
        data['wind_chill'] = weather_data['channel']['wind']['chill']
        data['temperature'] = weather_data['channel']['item']['condition']['temp']
        data['condition_text'] = weather_data['channel']['item']['condition']['text']
        data['condition_code'] = weather_data['channel']['item']['condition']['code']
        
        # Output the event
        self.output_event(data, stanza=stanza, index=index, sourcetype=sourcetype, source=stanza, host=host)
        
        # Save the checkpoint noting that the information was retrieved
        self.save_checkpoint_data(checkpoint_dir, stanza, {'last_run' : int(time.time()) })
        logger.info("Done getting weather information")
    
    def run(self, stanza, cleaned_params, input_config):
        
        # Make the parameters
        woeid                   = cleaned_params.get("woeid", None)
        interval                = cleaned_params.get("interval", 86400/2)
        sourcetype              = cleaned_params.get("sourcetype", "weather_info")
        host                    = cleaned_params.get("host", None)
        index                   = cleaned_params.get("index", "default")
        stanza                  = stanza
        
        # Make sure that the zip code is valid
        if woeid is None:
            return
        elif interval is not None and interval > 0 and self.needs_another_run(input_config.checkpoint_dir, stanza, interval):
            try:
                self.output_weather_info(woeid, host, sourcetype, index, stanza, input_config.checkpoint_dir)
            except Exception as e:
                logger.exception("Exception while attempting to get weather information, woeid=%s", woeid)
            
if __name__ == '__main__':
    
    try:
        insteon_input = WeatherInfoInput()
        insteon_input.execute()
        sys.exit(0)
    except Exception:
        logger.exception("Unhandled exception was caught, this may be due to a defect in the script") # This logs general exceptions that would have been unhandled otherwise (such as coding errors)
        raise