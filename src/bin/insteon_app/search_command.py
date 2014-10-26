
import splunk.Intersplunk
import sys
import os
import logging
import logging.handlers
from splunk import SplunkdConnectionException

def setup_logger(level, name=None):
    """
    Setup a logger for the search command
    """
    
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)
    
    file_handler = logging.handlers.RotatingFileHandler(os.environ['SPLUNK_HOME'] + '/var/log/splunk/' + name + '.log', maxBytes=25000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger
        
# Setup the handler
try:
    logger
except NameError:
    logger = setup_logger(logging.INFO, 'search_command')
    logger.info("Logger created")

class SearchCommand(object):
    
    # List of valid parameters
    PARAM_RUN_IN_PREVIEW = "run_in_preview"
    PARAM_DEBUG = "debug"
    
    VALID_PARAMS = [ PARAM_RUN_IN_PREVIEW, PARAM_DEBUG ]
    
    def __init__(self, run_in_preview=False):
        self.run_in_preview = False        
    
    @classmethod
    def parse_argument(cls, argument):
        """
        Parses an argument in the form of name=value and returns the name and value as two arguments
        
        Arguments:
        argument -- The argument that should be split into a name/value pair (i.e. name=value)
        """
        
        # Find the character that splits the name from the value (returns -1 if it cannot be found)
        splitter = argument.find('=')
        
        # If no equal-sign was found then initialize the value to None
        if splitter < 0:
            name = argument
            value = None
            
        # If a splitter was found, then parse the value
        else:
            name = argument[0:splitter]
            value = argument[splitter+1:len(argument)]
        
        # Return the results
        return name, value

    @classmethod
    def get_arguments(cls):
        """
        Get the arguments as args and kwargs so that they can be processed into a constructor call to a search command.
        """
        
        kwargs = {}
        args = []
        
        # Iterate through the arguments and initialize the corresponding argument
        if len(sys.argv) > 1:
            
            # Iterate through each argument
            for a in sys.argv[1:]:
                
                # Parse the argument
                name, value = cls.parse_argument( a ) 
                
                # If the argument has no value then it was an unnamed argument. Put it in the arguments array
                if value is None:
                    args.append(value)
                    
                else:
                    # Put the argument in a dictionary
                    kwargs[name] = value
                
        return args, kwargs
    

    @classmethod
    def make_instance(cls):
        """
        Produce an instance of the search command with arguments from the command-line.
        """
        
        args, kwargs = cls.get_arguments()
        logger.info("args" + str(args))
        return cls(*args, **kwargs)
    
    @classmethod
    def execute(cls):
        """
        Initialize an instance and run it.
        """
        
        try:
        
            instance = cls.make_instance()
            instance.run()
        
        except Exception as e:
            splunk.Intersplunk.parseError( str(e) )
            logger.exception("Search command threw an exception")
        
    def run(self, results=None):
        
        try:
            
            # Get the results from Splunk (unless results were provided)
            if results is None:
                results, dummyresults, settings = splunk.Intersplunk.getOrganizedResults()
                session_key = settings.get('sessionKey', None)
                
                # Don't write out the events in preview mode
                in_preview = settings.get('preview', '0')
                
                # If run_in_preview is undefined, then just continue
                if self.run_in_preview is None:
                    pass
                
                # Don't do anything if the command is supposed to run in preview but the results are not preview results
                elif self.run_in_preview and in_preview == "0":
                    
                    # Don't run in non-preview mode since we already processed the events in preview mode
                    if len(results) > 0:
                        logger.info( "Search command is set to run in preview, ignoring %d results provided in non-preview mode" % ( len(results) ) )
                    
                    return None
                
                # Don't do anything if the command is NOT supposed to run in preview but the results are previewed results
                elif not self.run_in_preview and not in_preview == "0":
                    return None
                    
            else:
                settings = None
                
            # Execute the search command
            logger.info("handleresults()")
            self.handle_results(results, session_key, in_preview)
                
        except Exception as e:
            splunk.Intersplunk.parseError( str(e) )
            logger.exception("Search command threw an exception")
            
    def output_results(self, results):
        """
        Output results to Splunk.
        
        Arguments:
        results -- A dictionary of fields/values to send to Splunk.
        """
        
        splunk.Intersplunk.outputResults(results)
            
    def handle_results(self, results, in_preview, session_key):
        """
        
        Arguments:
        results -- The results from Splunk to process
        in_preview -- Whether the search is running in preview
        session_key -- The session key to use for connecting to Splunk
        """
        
        raise Exception("handle_results needs to be implemented")