from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
from insteon_app.search_command import SearchCommand

import splunk.Intersplunk
import splunk.clilib.bundle_paths as bundle_paths
import shutil
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
    logger = setup_logger(logging.DEBUG, 'deploy_default_lookups_search_command')
    logger.info("Search command started")

class DeployDefaultLookupsSearchCommand(SearchCommand):
    
    def __init__(self):
        self.run_in_preview = False        
    
    def deploy_default_lookup_files(self):
        
        processed_files = []
        
        logger.debug( 'Examining directory="' + os.path.join(bundle_paths.get_base_path(), "insteon", "lookups") + '"' )
        
        for root, dirs, files in os.walk( os.path.join(bundle_paths.get_base_path(), "insteon", "lookups")):
            
            logger.debug("Found files=" + str(len(files)))
            
            for filename in files:
                
                processed_files.append({
                                        "file" : filename,
                                        "copied": self.copy_default_lookup(root, filename)
                                        })
                
        # Output the data indicating what was done
        self.output_results(processed_files)
    
    def copy_default_lookup(self, root, file):
        
        # Determine if the file is a default lookup file
        if file.endswith(".default"):
            
            # Make sure the file does not already exist
            fname = root + os.sep + file[0:-8]
            
            if os.path.isfile( fname ) == False:
                
                # Log that we are deploying a copy of the file
                if logger:
                    logger.info( 'Deploying copy of default lookup file, original_file="%s", new_file="%s"' % ( (root + os.sep + file), fname) )
                    
                # Deploy a copy of the file
                shutil.copyfile( root + os.sep + file, fname)
                
                return True # File was copied
            
            else:
                logger.info( 'Default lookup file already deployed and will be skipped, original_file="%s", existing_file="%s"' % ( (root + os.sep + file), fname) )
            
        return False # File was not copied
    
    def handle_results(self, results, session_key,  in_preview):
        """
        Call the function necessary to deploy lookup files.
        
        Arguments:
        results -- The results from Splunk to process
        in_preview -- Whether the search is running in preview
        session_key -- The session key to use for connecting to Splunk
        """
        
        self.deploy_default_lookup_files()
        
if __name__ == '__main__':
    try:
        DeployDefaultLookupsSearchCommand.execute()
        sys.exit(0)
    except Exception:
        logger.exception("Unhandled exception was caught, this may be due to a defect in the script") # This logs general exceptions that would have been unhandled otherwise (such as coding errors)
        raise