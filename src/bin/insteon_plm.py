
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
from insteon_app.modular_input import Field, IntegerField, FieldValidationException, ModularInput

import logging
from logging import handlers
import sys
import time
import os
import splunk
import re

from insteon_app.pytomation.pyinsteon import *
from insteon_app.pytomation.ha_common import *

def setup_logger():
    """
    Setup a logger.
    """
    
    logger = logging.getLogger('insteon_plm_modular_input')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(logging.DEBUG)
    
    file_handler = handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', 'insteon_plm_modular_input.log']), maxBytes=25000000, backupCount=5)
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
        
class PortField(IntegerField):
    
    def to_python(self, value):
        
        v = IntegerField.to_python(self, value)
        
        if v is not None and (v < 0 or v > 65535 ):
            raise FieldValidationException("Port must be at least 0 and less than 65536")
        else:
            return v

class InsteonPLMInput(ModularInput):
    """
    The insteon modular input connects to an Insteon PLM in order to monitor the status of Insteon or X10 devices.
    """
    
    def __init__(self, **kwargs):

        scheme_args = {'title': "Insteon PLM",
                       'description': "Retrieve information from an Insteon PLM (such as the Insteon Hub)",
                       'use_external_validation': "true",
                       'streaming_mode': "xml",
                       'use_single_instance': "true"}
        
        args = [
                Field("plm_host", "PLM Host Address", "The IP address or domain name of the PLM (such as an Insteon Hub)", empty_allowed=False),
                PortField("plm_port", "PLM Port", "The port on the PLM to connect to (usually is 9761)", empty_allowed=False),
                ]
          
        self.plm = None
        self.plm_connection_restart = False
        self.interface = None
        self.running_all_link_dump = False
        
        # These are values that are persisted so that the PLM callback has the data to output the event correctly
        self.sourcetype = "insteon_plm"
        self.index = "default"
        self.source = None
        self.stanza = None
        
        ModularInput.__init__( self, scheme_args, args )
    
            
    def do_shutdown(self):
        
        # Shut down the PLM
        try:
            if self.plm is not None:
                self.plm.shutdown()
        except:
            logger.exception("Exception generated while shutting down the PLM")
        
        # Shut down the TCP interface
        try:
            if self.interface is not None:
                self.interface.shutdown()
        except:
            logger.exception("Exception generated while shutting down the PLM interface")
    
    def insteon_received(self, params):
        
        #logger.debug("Receiving an Insteon message")
        
        try:
            # Convert the "True" and "False" values to 1 and 0
            for k in params:
                
                if params[k] == True:
                    params[k] = 1
                
                elif params[k] == False:
                    params[k] = 0
            
            # Output the event
            self.output_event(params, self.stanza, index=self.index, sourcetype=self.sourcetype, source=self.source)
            
            #logger.debug("Processed an Insteon message")
        except:
            logger.exception("Error when attempting to process an Insteon message")
    
    def getAllLinkRecords(self, checkpoint_dir, stanza):
        self.running_all_link_dump = True
        
        try:
            logger.info("Getting all link records")
            self.plm.getFirstAllLinkRecord()
            time.sleep(5)
            self.plm.getNextAllLinkRecord()
            time.sleep(5)
            
            # Retrieve each all record request
            count = 0
            while not self.plm.isAllRecordRequestDone() and count < 50:
                self.plm.getNextAllLinkRecord()
                time.sleep(5)
                count = count + 1
            
            self.save_checkpoint_data(checkpoint_dir, stanza, {'last_run' : int(time.time()) })
            logger.info("Done getting all link records")
        
        finally:
            self.running_all_link_dump = False
        
    def onErrorCallback(self, exception):
        logger.warning("Error detected; connection will be restarted")
        self.plm_connection_restart = True
        
    def run(self, stanza, cleaned_params, input_config):
        
        # Make the parameters
        plm_host                = cleaned_params["plm_host"]
        plm_port                = cleaned_params.get("plm_port", 9761)
        
        sourcetype              = cleaned_params.get("sourcetype", "insteon_plm")
        index                   = cleaned_params.get("index", "default")
        all_link_dump_interval  = cleaned_params.get("all_link_dump_interval", 0)
        source                  = stanza
        
        # Make sure that all-link dump frequency is valid
        try:
            all_link_dump_interval = int(all_link_dump_interval)
        except:
            logger.error("all_link_dump_interval is invalid; will default to 86400 (24 hours)")
            all_link_dump_interval = 86400
        
        #logger.debug("Entering the modular input run loop")
        
        try:
            # Run a dump of the all-link database if needed 
            if self.plm is not None and not self.running_all_link_dump and all_link_dump_interval > 0 and self.needs_another_run(input_config.checkpoint_dir, stanza, all_link_dump_interval):
                self.getAllLinkRecords(input_config.checkpoint_dir, stanza)
            
            # Restart the PLM connection if requested
            if self.plm is not None and self.plm_connection_restart:
                logger.info("Restarting the PLM connection")
                self.do_shutdown()
                self.plm = None
            
            # Start the connection to the PLM to begin intercepting messages
            if self.plm is None:
                
                self.plm_connection_restart = False
                logger.info("Initiating a connection to the PLM, plm_host=%s, plm_port=%r", plm_host, plm_port)
                
                self.interface = TCP(plm_host, plm_port)
                self.plm = InsteonPLM(self.interface)
                self.plm.setLogger(logger)
                
                # Setup the callbacks
                self.plm.onRunLoopError(self.onErrorCallback)
                self.plm.onReceivedInsteon(self.insteon_received)
                
                self.plm.start()
                
                logger.info("Established a connection to the PLM, plm_host=%s, plm_port=%r", plm_host, plm_port)
                
        except socket.error as e:
            logger.warning("Network error while attempting to start a PLM connection, plm_host=%s, plm_port=%r, message=%s", plm_host, plm_port, str(e))
            
        except Exception as e:
            logger.exception("Exception while attempting to start a PLM connection, plm_host=%s, plm_port=%r", plm_host, plm_port)
            
if __name__ == '__main__':
    
    try:
        insteon_input = InsteonPLMInput()
        insteon_input.execute()
        sys.exit(0)
    except Exception:
        logger.exception("Unhandled exception was caught, this may be due to a defect in the script") # This logs general exceptions that would have been unhandled otherwise (such as coding errors)
        raise