'''

File:
        ha_common.py

Description:
        Library of Home Automation code for Python


Author(s): 
         Jason Sharpee <jason@sharpee.com>  http://www.sharpee.com
        Pyjamasam <>

License:
    This free software is licensed under the terms of the GNU public license, Version 1     

Usage:
    - 


Example: (see bottom of file) 


Notes:
    - Common functionality between all of the classes I am implementing currently.

Created on Apr 3, 2011

@author: jason
'''

import threading
import traceback
import socket
import binascii
import keepalive
#import serial

class Lookup(dict):
    """
    a dictionary which can lookup value by key, or keys by value
    # tested with Python25 by Ene Uran 01/19/2008    http://www.daniweb.com/software-development/python/code/217019
    """
    def __init__(self, items=[]):
        """items can be a list of pair_lists or a dictionary"""
        dict.__init__(self, items)
    def get_key(self, value):
        """find the key as a list given a value"""
        if type(value) == type(dict()):
            items = [item[0] for item in self.items() if item[1][value.items()[0][0]] == value.items()[0][1]]
        else:
            items = [item[0] for item in self.items() if item[1] == value]
        return items[0]   
     
    def get_keys(self, value):
        """find the key(s) as a list given a value"""
        return [item[0] for item in self.items() if item[1] == value]
    def get_value(self, key):
        """find the value given a key"""
        return self[key]
   
class Interface(object):
    def __init__(self):
        super(Interface,self).__init__()
        self.logger = None
        
    def read(self,bufferSize):
        raise NotImplemented

    def write(self,data):
        raise NotImplemented

    def setLogger(self, logger):
        self.logger = logger
    
class Interface_old(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.c = None
        
    def _send(self,Data):
        return None

    def onReceive(self, callback):
        self.c = callback
        return None    

class TCP(Interface):
    def __init__(self, host, port, logger=None):
        super(TCP, self).__init__()        
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print"connect %s:%s" % (host, port)
        
        # Setup a keep-alive to detect dead connections
        keepalive.set_keepalive(self.__s)
        self.__s.connect((host, port))
        self.__s.setblocking(False)
        
        self.setLogger(logger)
        
    def write(self,data):
        "Send raw binary"
        self.__s.send(data) 
        return None

    def read(self,bufferSize):
        "Read raw data"
        data = ''
        try:
            data = self.__s.recv(bufferSize)
        except socket.error, ex:
            
            if ex.errno in [35, 10035]: # Resource temporarily unavailable: no data to read yet
                return '' # We can ignore this exception. This just means no data was available to read yet.
            
            elif(self.logger is not None):
                self.logger.exception("Socket exception raised while attempting to read from the socket")
            
            # Raise the exception so that the caller knows something went wrong
            raise ex
            
        except Exception, ex:
            if(self.logger is not None):
                self.logger.exception("Exception raised while attempting to read from the socket")
            else:
                print "Exception:", type(ex)
                
            # Raise the exception so that the caller knows something went wrong
            raise ex
            
        return data
    
    def shutdown(self):
        "Shut down the socket"
        try:
            if self.__s is not None:
                self.__s.shutdown(socket.SHUT_RDWR)
                self.__s.close()
        except:
            self.logger.exception("Exception generated while shutting down the interface socket")
        
        
class TCP_old(Interface):
    def __init__(self, host, port):
        super(TCP_old, self).__init__()        
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print"connect %s:%s" % (host, port)
        self.__s.connect((host, port))
        self.start()

        
    def send(self, dataString):
        "Send raw HEX encoded String"
        print "Data Sent=>" + dataString
        data = binascii.unhexlify(dataString)
        self.__s.send(data) 
        return None
    
    def run(self):
        self._handle_receive()
        

        
    def _handle_receive(self):
        while 1:
            data = self.__s.recv(1024)
            self.c(data)
        self.__s.close()
        
class UDP(Interface_old):
    def __init__(self, fromHost, fromPort, toHost, toPort):
        super(UDP, self).__init__(fromHost,fromPort)   
        self.__ssend = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__ssend.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
#        self.__srecv = socket(socket.AF_INET, socket.SOCK_DGRAM)
#        self.__srecv.bind((fromHost,fromPort))
        self.__ssend.bind((fromHost,fromPort))
        self.__fromHost = fromHost
        self.__fromPort = fromPort
        self.__toHost = toHost
        self.__toPort = toPort
        self.start()

    def send(self, dataString):
        self.__ssend.sendto(dataString,(self.__toHost,self.__toPort))
        return None

    def _handle_receive(self):
        while 1:
#            data = self.__srecv.recv(2048)
            data = self.__ssend.recv(2048)
            print "received stuff", data
            if self.c != None:
                self.c(data)         

    def run(self):
        self._handle_receive()

class Serial(Interface):
    def __init__(self, serialDevicePath, serialSpeed = 19200, serialTimeout = 0.1):
        super(Serial,self).__init__()
        print "Using %s for PLM communication" % serialDevicePath
 #       self.__serialDevice = serial.Serial(serialDevicePath, 19200, timeout = 0.1) 
        self.__serialDevice = serial.Serial(serialDevicePath, serialSpeed, timeout = serialTimeout) 
    
    def read(self, bufferSize):
        return self.__serialDevice.read(bufferSize)
    
    def write(self, bytesToSend):
        self.__serialDevice.write(bytesToSend)

class USB(Interface): 
    pass
    def __init__(self, device):
        return None
    
class HADevice(object):

    def __init__(self,deviceId,interface = None):
        super(HADevice,self).__init__()
        self.interface = interface
        self.deviceId = deviceId
        
    def set(self, command):
        self.interface.command(self, command)
    
class InsteonDevice(HADevice):
    def __init__(self, deviceId, interface = None):
        super(InsteonDevice, self).__init__(deviceId, interface)

class X10Device(HADevice):    
    def __init__(self, deviceId, interface = None):
        super(X10Device, self).__init__(deviceId, interface)

class HACommand(Lookup):
    def __init__(self):
        super(HACommand,self).__init__({
                       'on'         :{'primary' : {
                                                    'insteon':0x11,
                                                    'x10':0x02,
                                                    'upb':0x00
                                                  }, 
                                     'secondary' : {
                                                    'insteon':0xff,
                                                    'x10':None,
                                                    'upb':None
                                                    },
                                     },
                       'faston'    :{'primary' : {
                                                    'insteon':0x12,
                                                    'x10':0x02,
                                                    'upb':0x00
                                                  }, 
                                     'secondary' : {
                                                    'insteon':0xff,
                                                    'x10':None,
                                                    'upb':None
                                                    },
                                     },
                       'off'         :{'primary' : {
                                                    'insteon':0x13,
                                                    'x10':0x03,
                                                    'upb':0x00
                                                  }, 
                                     'secondary' : {
                                                    'insteon':0x00,
                                                    'x10':None,
                                                    'upb':None
                                                    },
                                     },
        
                       'fastoff'    :{'primary' : {
                                                    'insteon':0x14,
                                                    'x10':0x03,
                                                    'upb':0x00
                                                  }, 
                                     'secondary' : {
                                                    'insteon':0x00,
                                                    'x10':None,
                                                    'upb':None
                                                    },
                                     },
                       'level'    :{'primary' : {
                                                    'insteon':0x11,
                                                    'x10':0x0a,
                                                    'upb':0x00
                                                  }, 
                                     'secondary' : {
                                                    'insteon':0x88,
                                                    'x10':None,
                                                    'upb':None
                                                    },
                                     },
                       }
                      )
        pass

class HAInterface(threading.Thread):
    "Base protocol interface"

    def __init__(self, interface):
        super(HAInterface,self).__init__()
    def onCommand(self,callback):
        raise NotImplemented
    def command(self,deviceId,command):
        raise NotImplemented
        
        
import time
import re

## {{{ http://code.activestate.com/recipes/142812/ (r1)
FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def hex_dump(src, length=8):
    N=0; result=''
    while src:
        s,src = src[:length],src[length:]
        hexa = ' '.join(["%02X"%ord(x) for x in s])
        s = s.translate(FILTER)
        result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
        N+=length
    return result

## end of http://code.activestate.com/recipes/142812/ }}}

def interruptibleSleep(sleepTime, interuptEvent):
    sleepInterval = 0.05
    
    #adjust for the time it takes to do our instructions and such
    totalSleepTime = sleepTime - 0.04
    
    while interuptEvent.isSet() == False and totalSleepTime > 0:
        time.sleep(sleepInterval)
        totalSleepTime = totalSleepTime - sleepInterval
        
        
def sort_nicely( l ): 
    """ Sort the given list in the way that humans expect. 
    """ 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    l.sort( key=alphanum_key )

    return l
    
def convertStringFrequencyToSeconds(textFrequency):
    frequencyNumberPart = int(textFrequency[:-1])
    frequencyStringPart = textFrequency[-1:].lower()
    
    if (frequencyStringPart == "w"):
        frequencyNumberPart *= 604800
    elif (frequencyStringPart == "d"):
        frequencyNumberPart *= 86400
    elif (frequencyStringPart == "h"):
        frequencyNumberPart *= 3600                        
    elif (frequencyStringPart == "m"):
        frequencyNumberPart *= 60
        
    return frequencyNumberPart
        