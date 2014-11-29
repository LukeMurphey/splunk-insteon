'''
File:
        pyinsteon.py

Description:
        InsteonPLM Home Automation Protocol library for Python (Smarthome 2412N, 2412S, 2412U)
        
        For more information regarding the technical details of the PLM:
                http://www.smarthome.com/manuals/2412sdevguide.pdf

Author(s): 
         Pyjamasam@github <>
         Jason Sharpee <jason@sharpee.com>  http://www.sharpee.com


        Based loosely on the Insteon_PLM.pm code:
        -       Expanded by Gregg Liming <gregg@limings.net>

License:
    This free software is licensed under the terms of the GNU public license, Version 1     

Usage:
    - Instantiate InsteonPLM by passing in an interface
    - Call its methods
    - ?
    - Profit

Example: (see bottom of PyInsteon.py file) 

Notes:
    - Supports both 2412N and 2412S right now
    - 
    - Todo: Read Style Guide @: http://www.python.org/dev/peps/pep-0008/

Created on Mar 26, 2011
'''
import select
import traceback
import threading
import time
import binascii
import struct
import sys
import string
import hashlib
from collections import deque
from ha_common import *
#import serial
import logging
from logging import handlers

def _byteIdToStringId(idHigh, idMid, idLow):
    return '%02X.%02X.%02X' % (idHigh, idMid, idLow)
    
def _cleanStringId(stringId):
    return stringId[0:2] + stringId[3:5] + stringId[6:8]

def _stringIdToByteIds(stringId):
    return binascii.unhexlify(_cleanStringId(stringId))
    
def _buildFlags():
    #todo: impliment this
    return '\x0f'
    
def hashPacket(packetData):
    return hashlib.md5(packetData).hexdigest()

def simpleMap(value, in_min, in_max, out_min, out_max):
    #stolen from the arduino implimentation.  I am sure there is a nice python way to do it, but I have yet to stublem across it                
    return (float(value) - float(in_min)) * (float(out_max) - float(out_min)) / (float(in_max) - float(in_min)) + float(out_min);



class InsteonPLM(HAInterface):
    
    def __init__(self, interface):
        super(InsteonPLM, self).__init__(interface)
        
        self.logger = logging.getLogger('pyinsteon')
        
        self.__modemCommands = {'60': { #plm_info
                                    'responseSize':7,
                                    'callBack':self.__process_PLMInfo
                                  },
                                '62': { #insteon_send
                                    'responseSize':7,
                                    'callBack':self.__process_StandardInsteonMessagePLMEcho
                                  },
                                '50': { #insteon_received
                                    'responseSize':9,
                                    'callBack':self.__process_InboundStandardInsteonMessage
                                  },
                                '51': { #insteon_ext_received
                                    'responseSize':23,
                                    'callBack':self.__process_InboundExtendedInsteonMessage
                                  },
                                '52': { #x10_received
                                    'responseSize':4,
                                    'callBack':self.__process_InboundX10Message
                                 },
                                '58': { #all_link_clean_status
                                    'responseSize':1,
                                    'callBack':self.__process_StandardInsteonMessageAllLinkCleanStatus
                                  },
                                '63': { #x10_send
                                    'responseSize':4,
                                    'callBack':self.__process_StandardX10MessagePLMEcho
                                  },
                                '61': { #all_link_send
                                    'responseSize':4,
                                    'callBack':self.__process_StandardInsteonMessageAllLinkSend
                                  },
                                '69': { #Get First ALL-Link Record 
                                    'responseSize':1,
                                    'callBack':self.__process_GetFirstAllLinkRecord
                                  },
                                '6A': { #Get Next ALL-Link Record
                                    'responseSize':1,
                                    'callBack':self.__process_GetNextAllLinkRecord
                                  },
                                 '57': { #ALL-Link Record Response
                                    'responseSize':8,
                                    'callBack':self.__process_AllLinkRecordResponse
                                  },
                                 '7D': {
                                    'responseSize':2,
                                    'callBack':self.__process_command_7D
                                  }
                            }
        
        self.__insteonCommands = {
                                    #Direct Messages/Responses
                                    'SD03': {        #Product Data Request (generally an Ack)                            
                                        'callBack' : self.__handle_StandardDirect_IgnoreAck
                                    },
                                    'SD0D': {        #Get InsteonPLM Engine                            
                                        'callBack' : self.__handle_StandardDirect_EngineResponse,
                                        'validResponseCommands' : ['SD0D']
                                    },
                                    'SD0F': {        #Ping Device                        
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD0F']
                                    },
                                    'SD10': {        #ID Request    (generally an Ack)                        
                                        'callBack' : self.__handle_StandardDirect_IgnoreAck,
                                        'validResponseCommands' : ['SD10', 'SB01']
                                    },    
                                    'SD11': {        #Devce On                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD11']
                                    },                                    
                                    'SD12': {        #Devce On Fast                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD12']
                                    },                                    
                                    'SD13': {        #Devce Off                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD13']
                                    },                                    
                                    'SD14': {        #Devce Off Fast                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD14']                                    
                                    },
                                    'SD15': {        #Brighten one step
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD15']                                    
                                    },    
                                    'SD16': {        #Dim one step
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD16']                                    
                                    },                                
                                    'SD19': {        #Light Status Response                                
                                        'callBack' : self.__handle_StandardDirect_LightStatusResponse,
                                        'validResponseCommands' : ['SD19']
                                    },    
                                    #Broadcast Messages/Responses                                
                                    'SB01': {    
                                                    #Set button pushed                                
                                        'callBack' : self.__handle_StandardBroadcast_SetButtonPressed
                                    },                                   
                                }
        
        self.__x10HouseCodes = Lookup(zip((
                            'm',
                            'e',
                            'c',
                            'k',
                            'o',
                            'g',
                            'a',
                            'i',
                            'n',
                            'f',
                            'd',
                            'l',
                            'p',
                            'h',
                            'n',
                            'j' ),xrange(0x0, 0xF)))
        
        self.__x10UnitCodes = Lookup(zip((
                             '13',
                             '5',
                             '3',
                             '11',
                             '15',
                             '7',
                             '1',
                             '9',
                             '14',
                             '6',
                             '4',
                             '12',
                             '16',
                             '8',
                             '2',
                             '10'
                             ),xrange(0x0,0xF)))
        
        self._allLinkDatabase = dict()
        
        self.__shutdownEvent = threading.Event()
        self.__interfaceRunningEvent = threading.Event()
        
        self.__commandLock = threading.Lock()
        self.__outboundQueue = deque()
        self.__outboundCommandDetails = dict()
        self.__retryCount = dict()        
        
        self.__pendingCommandDetails = dict()        
        
        self.__commandReturnData = dict()
        
        self.__intersend_delay = 0.15 #150 ms between network sends
        self.__lastSendTime = 0

#        print "Using %s for PLM communication" % serialDevicePath
#       self.__serialDevice = serial.Serial(serialDevicePath, 19200, timeout = 0.1)     
        self.__interface = interface   

        self.__x10Callback = None
        self.__insteonCallback = None
        
        self.__all_record_request_nack = False
        self.__run_loop_error_callback = None
    
    def shutdown(self):
        if self.__interfaceRunningEvent.isSet():
            self.__shutdownEvent.set()

            #wait 2 seconds for the interface to shut down
            self.__interfaceRunningEvent.wait(2000)
            
    def run(self):
        
        try:
            self.__interfaceRunningEvent.set();
            
            #for checking for duplicate messages received in a row
            lastPacketHash = None
            
            while not self.__shutdownEvent.isSet():
                
                #check to see if there are any outbound messages to deal with
                
                self.__commandLock.acquire()
                
                if (len(self.__outboundQueue) > 0) and (time.time() - self.__lastSendTime > self.__intersend_delay):
                    commandHash = self.__outboundQueue.popleft()
                    
                    commandExecutionDetails = self.__outboundCommandDetails[commandHash]
                    
                    bytesToSend = commandExecutionDetails['bytesToSend']
                    self.logger.debug( "> ", hex_dump(bytesToSend, len(bytesToSend)))
    
                    self.__interface.write(bytesToSend)                    
                    
                    self.__pendingCommandDetails[commandHash] = commandExecutionDetails                
                    del self.__outboundCommandDetails[commandHash]
                    
                    self.__lastSendTime = time.time()
                       
                self.__commandLock.release()
                
                #check to see if there is anything we need to read            
                firstByte = self.__interface.read(1)
                
                if len(firstByte) == 1:
                    #got at least one byte.  Check to see what kind of byte it is (helps us sort out how many bytes we need to read now)
                    
                    if firstByte[0] == '\x02':
                        #modem command (could be an echo or a response)
                        #read another byte to sort that out
                        secondByte = self.__interface.read(1)
                                            
                        responseSize = -1
                        callBack = None
                        
                        modemCommand = binascii.hexlify(secondByte).upper()
                        if self.__modemCommands.has_key(modemCommand):
                            if self.__modemCommands[modemCommand].has_key('responseSize'):                                                                    
                                responseSize = self.__modemCommands[modemCommand]['responseSize']                            
                            if self.__modemCommands[modemCommand].has_key('callBack'):                                                                    
                                callBack = self.__modemCommands[modemCommand]['callBack']
                        
                        
                        
                        if responseSize != -1:                        
                            remainingBytes = self.__interface.read(responseSize)
                            
                            self.logger.debug( "< ", hex_dump(firstByte + secondByte + remainingBytes, len(firstByte + secondByte + remainingBytes)))
                            
                            currentPacketHash = hashPacket(firstByte + secondByte + remainingBytes)
                            if lastPacketHash and lastPacketHash == currentPacketHash:
                                #duplicate packet.  Ignore
                                pass
                            else:                        
                                if callBack:
                                    callBack(firstByte + secondByte + remainingBytes)    
                                else:
                                    self.logger.warn( "No callBack defined for for modem command %s" % modemCommand )
                            
                            lastPacketHash = currentPacketHash            
                            
                        else:
                            self.logger.warn( "No responseSize defined for modem command %s" % modemCommand )          
                    elif firstByte[0] == '\x15':
                        self.logger.warn( "Received a Modem NAK!" )
                    else:
                        self.logger.critical( "Unknown first byte %s" % binascii.hexlify(firstByte[0]) )
                else:
                    #print "Sleeping"
                    #X10 is slow.  Need to adjust based on protocol sent.  Or pay attention to NAK and auto adjust
                    #time.sleep(0.1)
                    time.sleep(0.5)
            
            self.__interfaceRunningEvent.clear()
        except Exception as e:
            self.logger.exception("Exception occurred within the run loop")
            
            # Call the error callback handler so that the caller can deal with the mess            
            if self.__run_loop_error_callback is not None:
                self.__run_loop_error_callback(e)
                                
    def __sendModemCommand(self, modemCommand, commandDataString = None, extraCommandDetails = None):        
        
        returnValue = False
        
        try:                
            bytesToSend = '\x02' + binascii.unhexlify(modemCommand)            
            if commandDataString != None:
                bytesToSend += commandDataString                            
            commandHash = hashPacket(bytesToSend)
                        
            self.__commandLock.acquire()
            if self.__outboundCommandDetails.has_key(commandHash):
                #duplicate command.  Ignore
                pass
                
            else:                
                waitEvent = threading.Event()
                
                basicCommandDetails = { 'bytesToSend': bytesToSend, 'waitEvent': waitEvent, 'modemCommand': modemCommand }                                                                                                                        
                
                if extraCommandDetails != None:
                    basicCommandDetails = dict(basicCommandDetails.items() + extraCommandDetails.items())                        
                
                self.__outboundCommandDetails[commandHash] = basicCommandDetails
                
                self.__outboundQueue.append(commandHash)
                self.__retryCount[commandHash] = 0
                
                self.logger.debug( "Queued %s" % commandHash )
                
                returnValue = {'commandHash': commandHash, 'waitEvent': waitEvent}
                
            self.__commandLock.release()                        
                    
        except Exception, ex:
            self.logger.exception()
            
        finally:
            
            #ensure that we unlock the thread lock
            #the code below will ensure that we have a valid lock before we call release
            self.__commandLock.acquire(False)
            self.__commandLock.release()
                    
        return returnValue    
        
        
        
    def __sendStandardP2PInsteonCommand(self, destinationDevice, commandId1, commandId2):                
        self.logger.debug( "Command: %s %s %s" % (destinationDevice, commandId1, commandId2) )
        return self.__sendModemCommand('62', _stringIdToByteIds(destinationDevice) + _buildFlags() + binascii.unhexlify(commandId1) + binascii.unhexlify(commandId2), extraCommandDetails = { 'destinationDevice': destinationDevice, 'commandId1': 'SD' + commandId1, 'commandId2': commandId2})

    def __getX10UnitCommand(self,deviceId):
        "Send just an X10 unit code message"
        deviceId = deviceId.lower()
        return "%02x00" % ((self.__x10HouseCodes[deviceId[0:1]] << 4) | self.__x10UnitCodes[deviceId[1:2]])

    def __getX10CommandCommand(self,deviceId,commandCode):
        "Send just an X10 command code message"
        deviceId = deviceId.lower()
        return "%02x80" % ((self.__x10HouseCodes[deviceId[0:1]] << 4) | int(commandCode,16))
    
    def __sendStandardP2PX10Command(self,destinationDevice,commandId1, commandId2 = None):
        # X10 sends 1 complete message in two commands
        self.logger.debug( "Command: %s %s %s" % (destinationDevice, commandId1, commandId2) )
        self.logger.debug( "C: %s" % self.__getX10UnitCommand(destinationDevice) )
        self.logger.debug( "c1: %s" % self.__getX10CommandCommand(destinationDevice, commandId1) )
        self.__sendModemCommand('63', binascii.unhexlify(self.__getX10UnitCommand(destinationDevice)))
        
        return self.__sendModemCommand('63', binascii.unhexlify(self.__getX10CommandCommand(destinationDevice, commandId1)))
            
    def __waitForCommandToFinish(self, commandExecutionDetails, timeout = None):
                
        if type(commandExecutionDetails) != type(dict()):
            self.logger.debug( "Unable to wait without a valid commandExecutionDetails parameter" )
            return False
            
        waitEvent = commandExecutionDetails['waitEvent']
        commandHash = commandExecutionDetails['commandHash']
        
        realTimeout = 2 #default timeout of 2 seconds
        if timeout:
            realTimeout = timeout
            
        timeoutOccured = False
        
        if sys.version_info[:2] > (2,6):
            #python 2.7 and above waits correctly on events
            timeoutOccured = not waitEvent.wait(realTimeout)
        else:
            #< then python 2.7 and we need to do the waiting manually
            while not waitEvent.isSet() and realTimeout > 0:
                time.sleep(0.1)
                realTimeout -= 0.1
                
            if realTimeout == 0:
                timeoutOccured = True
        
        if not timeoutOccured:    
            if self.__commandReturnData.has_key(commandHash):
                return self.__commandReturnData[commandHash]
            else:
                return True
        else:            
            #re-queue the command to try again
            
            self.__commandLock.acquire()
            
            if self.__retryCount[commandHash] >= 5:
                #too many retries.  Bail out
                self.__commandLock.release()
                
                return False
                
            self.logger.debug( "Timed out for %s - Requeueing (already had %d retries)" % (commandHash, self.__retryCount[commandHash]) )
            
            requiresRetry = True
            if self.__pendingCommandDetails.has_key(commandHash):
                
                self.__outboundCommandDetails[commandHash] = self.__pendingCommandDetails[commandHash]
                del self.__pendingCommandDetails[commandHash]
            
                self.__outboundQueue.append(commandHash)
                self.__retryCount[commandHash] += 1
            else:
                self.logger.debug( "Interesting.  timed out for %s, but there is no pending command details" % commandHash )
                #to prevent a huge loop here we bail out
                requiresRetry = False
            
            self.__commandLock.release()
            
            if requiresRetry:
                return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)
            else:
                return False
        
            




    #low level processing methods
    def __process_PLMInfo(self, responseBytes):                
        (modemCommand, idHigh, idMid, idLow, deviceCat, deviceSubCat, firmwareVer, acknak) = struct.unpack('xBBBBBBBB', responseBytes)        
        
        foundCommandHash = None        
        #find our pending command in the list so we can say that we're done (if we are running in syncronous mode - if not well then the caller didn't care)
        for (commandHash, commandDetails) in self.__pendingCommandDetails.items():                        
            if binascii.unhexlify(commandDetails['modemCommand']) == chr(modemCommand):
                #Looks like this is our command.  Lets deal with it.                
                self.__commandReturnData[commandHash] = { 'id': _byteIdToStringId(idHigh,idMid,idLow), 'deviceCategory': '%02X' % deviceCat, 'deviceSubCategory': '%02X' % deviceSubCat, 'firmwareVersion': '%02X' % firmwareVer }    
                
                waitEvent = commandDetails['waitEvent']
                waitEvent.set()
                
                foundCommandHash = commandHash
                break
                
        if foundCommandHash:
            del self.__pendingCommandDetails[foundCommandHash]
        else:
            self.logger.debug( "Unable to find pending command details for the following packet:" + hex_dump(responseBytes, len(responseBytes)) )
            
    def __process_command_7D(self, responseBytes):
        pass
            
    def __process_AllLinkRecordResponse(self, responseBytes):
        
        if self.__insteonCallback is not None:
            
            try:
                (insteonCommand, recordFlags, all_link_group, toIdHigh, toIdMid, toIdLow, linkData1, linkData2, linkData3) = struct.unpack('xBBBBBBBBB', responseBytes)
            except:
                self.logger.exception("Error when parsing bytes in __process_AllLinkRecordResponse")
                return
            
            recordInUse = recordFlags & (1 << 7) == (1 << 7)
            isController = recordFlags & (1 << 6) == (1 << 6)
            hasBeenUsedBefore = recordFlags & (1 << 1) == (1 << 1)
            
            params = {
                        'broadcast'          : True,
                        'direct'             : False,
                        'all_link'           : True,
                        'extended'           : False,
                        'modem_command'      : 'ALL-Link Record Response',
                        'to'                 : self.__addressToStr(toIdHigh, toIdMid, toIdLow),
                        'all_link_group'     : all_link_group,
                        'link_data_1'        : format(linkData1, 'x'),
                        'link_data_2'        : format(linkData2, 'x'),
                        'link_data_3'        : format(linkData3, 'x'),
                        'record_in_use'      : recordInUse,
                        'controller'         : isController,
                        'record_used_before' : hasBeenUsedBefore,
                        'modem_command_code' : format(insteonCommand, 'x')
            }
            
            #run the callback if one is defined
            self.__insteonCallback( params )
            
    def __process_GetFirstAllLinkRecord(self, responseBytes):
        
        if self.__insteonCallback is not None:
            try:
                (insteonCommand, status) = struct.unpack('xBB', responseBytes)
            except:
                self.logger.exception("Error when parsing bytes in __process_GetFirstAllLinkRecord")
                return
            
            nack = False
            ack = False
            
            # NAK
            if status == int("15", 16):
                nack = True
                
            # ACK
            elif status == int("6", 16):
                ack = True
            
            params = {
                        'broadcast'          : True,
                        'direct'             : False,
                        'all_link'           : True,
                        'extended'           : False,
                        'ack'                : ack,
                        'nack'               : nack,
                        'modem_command'      : 'Get First ALL-Link Record',
                        'modem_command_code' : format(insteonCommand, 'x')
            }
            
            #run the callback if one is defined
            self.__insteonCallback( params )
            
    def __process_GetNextAllLinkRecord(self, responseBytes):
        
        if self.__insteonCallback is not None:
            try:
                (insteonCommand, status) = struct.unpack('xBB', responseBytes)
            except:
                self.logger.exception("Error when parsing bytes in __process_GetFirstAllLinkRecord")
                return
            
            # NAK
            nack = False
            ack = False
            self.__all_record_request_nack = False
            
            if status == int("15", 16):
                nack = True
                self.__all_record_request_nack = True
                self.logger.debug("Last all-link record observed")
                
            # ACK
            elif status == int("6", 16):
                ack = True
            
            params = {
                        'broadcast'          : True,
                        'direct'             : False,
                        'all_link'           : True,
                        'extended'           : False,
                        'ack'                : ack,
                        'nack'               : nack,
                        'modem_command'      : 'Get Next ALL-Link Record',
                        'modem_command_code' : format(insteonCommand, 'x')
            }
            
            #run the callback if one is defined
            self.__insteonCallback( params )
            
    def __process_StandardInsteonMessageAllLinkSend(self, responseBytes):

        if self.__insteonCallback is not None:
            self.logger.debug( "__process_StandardInsteonMessageAllLinkSend packet:" + hex_dump(responseBytes, len(responseBytes)) )
            
            try:
                (insteonCommand, all_link_group, command1, command2, status) = struct.unpack('xBBBBB', responseBytes)
            except:
                self.logger.exception("Error when parsing bytes in __process_StandardInsteonMessageAllLinkSend")
                return
            
            nack = False
            ack = False
            
            # NAK
            if status == int("15", 16):
                nack = True
                
            # ACK
            elif status == int("6", 16):
                ack = True
            
            #self.logger.debug("__process_StandardInsteonMessageAllLinkSend:" + str(len(responseBytes)))
            params = {
                        'all_link_group'     : all_link_group,
                        'cmd1'               : format(command1, 'x'),
                        'cmd2'               : format(command2, 'x'),
                        'broadcast'          : True,
                        'direct'             : False,
                        'ack'                : ack,
                        'nack'               : nack,
                        'all_link'           : True,
                        'extended'           : False,
                        'modem_command'      : 'ALL-Link Send',
                        'modem_command_code' : format(insteonCommand, 'x')
            }
            
            #run the callback if one is defined
            self.__insteonCallback( params )
    
    def __process_StandardInsteonMessageAllLinkCleanStatus(self, responseBytes):
        
        #self.logger.debug( "__process_StandardInsteonMessageAllLinkCleanStatus packet:" + hex_dump(responseBytes, len(responseBytes)) )
            
        if self.__insteonCallback is not None:
            
            try:
                (insteonCommand, status) = struct.unpack('xBB', responseBytes)
            except:
                self.logger.exception("Error when parsing bytes in __process_StandardInsteonMessageAllLinkCleanStatus")
                return
            
            nack = False
            ack = False
            
            # NAK
            if status == int("15", 16):
                nack = True
                
            # ACK
            elif status == int("6", 16):
                ack = True
            
            #self.logger.debug("__process_StandardInsteonMessageAllLinkSend:" + str(len(responseBytes)))
            params = {
                        'status'             : status,
                        'broadcast'          : True,
                        'direct'             : False,
                        'ack'                : ack,
                        'nack'               : nack,
                        'all_link'           : True,
                        'extended'           : False,
                        'modem_command'      : 'ALL-Link Cleanup',
                        'modem_command_code' : format(insteonCommand, 'x')
            }
            
            #run the callback if one is defined
            self.__insteonCallback( params )
            
    def __process_StandardInsteonMessagePLMEcho(self, responseBytes):
        
        (insteonCommand, toIdHigh, toIdMid, toIdLow, messageFlags, command1, command2, ack_byte ) = struct.unpack('xBBBBBBBB', responseBytes)        
        
        if self.__insteonCallback is not None:
            
            #check to see what kind of message this was (based on message flags)
            isBroadcast = messageFlags & (1 << 7) == (1 << 7)
            isDirect = not isBroadcast
            isAck = messageFlags & (1 << 5) == (1 << 5)
            isNak = isAck and isBroadcast
            isAllLink = messageFlags & (1 << 6) == (1 << 6)
            
            #self.logger.debug( hex_dump(responseBytes, len(responseBytes)) )
            
            params = {
                    'to'                 : self.__addressToStr(toIdHigh, toIdMid, toIdLow),
                    'cmd1'               : format(command1, 'x'),
                    'cmd2'               : format(command2, 'x'),
                    'broadcast'          : isBroadcast,
                    'direct'             : isDirect,
                    'ack'                : isAck,
                    'nack'               : isNak,
                    'all_link'           : isAllLink,
                    'extended'           : False,
                    'modem_command'      : 'Send Message',
                    'modem_command_code' : format(insteonCommand, 'x')
                }
        
            #run the callback if one is defined
            self.__insteonCallback( params )
        
        #we don't do anything here.  Just eat the echoed bytes
        #pass
            
    def __process_StandardX10MessagePLMEcho(self, responseBytes):
        # Just ack / error echo from sending an X10 command
        pass
        
    def __validResponseMessagesForCommandId(self, commandId):
        if self.__insteonCommands.has_key(commandId):
            commandInfo = self.__insteonCommands[commandId]
            if commandInfo.has_key('validResponseCommands'):
                return commandInfo['validResponseCommands']
        
        return False
        
    def __addressToStr(self, addressHigh, addressMid, addressLow):
        return "{0:0{3}x}.{1:0{3}x}.{2:0{3}x}".format(addressHigh, addressMid, addressLow, 2)
    
    def __executeCallback(self, fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, command1, command2, insteonCommand, insteonCommandDescription, isBroadcast, isDirect, isAck, isNak, isAllLink, extended, data=None):
        
        if self.__insteonCallback is not None:
            
            params = {
                'from'               : self.__addressToStr(fromIdHigh, fromIdMid, fromIdLow),
                'cmd1'               : format(command1, 'x'),
                'broadcast'          : isBroadcast,
                'direct'             : isDirect,
                'ack'                : isAck,
                'nack'               : isNak,
                'all_link'           : isAllLink,
                'extended'           : extended,
                'modem_command'      : insteonCommandDescription,
                'modem_command_code' : format(insteonCommand, 'x')
            }
            
            # determine if this is a linking request and parse the address as the meta-data
            if isBroadcast and not extended and command1 in [1, 2]:
                params['device_category'] = format(toIdHigh, 'x')
                params['device_subcategory'] = format(toIdMid, 'x')
                params['device_revision'] = format(toIdLow, 'x')
                
            # all-link messages store the group number in the command 2 field
            if isAllLink:
                params['all_link_group'] = command2
            # otherwise the cmd2 is an actual command
            else:
                params['cmd2'] = format(command2, 'x')
                
            # broadcast all link messages use the to field to store the all-link group number
            if isBroadcast and isAllLink:
                params['alg_to'] = self.__addressToStr(toIdHigh, toIdMid, toIdLow)
                
            # otherwise, the address is the actual address
            else:
                params['to'] = self.__addressToStr(toIdHigh, toIdMid, toIdLow)
                
                
            # add the data field if provided
            if data is not None:
                params['data'] = data.encode("hex")
            
            #run the callback if one is defined
            self.__insteonCallback( params )
        
    def __process_InboundStandardInsteonMessageNoop(self, responseBytes):
        self.__process_InboundStandardInsteonMessage(responseBytes, noop=True)
            
    def __process_InboundStandardInsteonMessage(self, responseBytes, noop=False):
        self.logger.debug("Standard message received, length=%r", len(responseBytes))
        (insteonCommand, fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, messageFlags, command1, command2) = struct.unpack('xBBBBBBBBBB', responseBytes)        
        
        foundCommandHash = None            
        waitEvent = None
        
        #check to see what kind of message this was (based on message flags)
        isBroadcast = messageFlags & (1 << 7) == (1 << 7)
        isDirect = not isBroadcast
        isAck = messageFlags & (1 << 5) == (1 << 5)
        isNak = isAck and isBroadcast
        isAllLink = messageFlags & (1 << 6) == (1 << 6)
        
        insteonCommandCode = "%02X" % command1
        if isBroadcast:
            #standard broadcast
            insteonCommandCode = 'SB' + insteonCommandCode
        else:
            #standard direct
            insteonCommandCode = 'SD' + insteonCommandCode
            
        if insteonCommandCode == 'SD00':
            #this is a strange special case...
            #lightStatusRequest returns a standard message and overwrites the cmd1 and cmd2 bytes with "data"
            #cmd1 (that we use here to sort out what kind of incoming message we got) contains an 
            #"ALL-Link Database Delta number that increments every time there is a change in the addressee's ALL-Link Database"
            #which makes is super hard to deal with this response (cause cmd1 can likley change)
            #for now my testing has show that its 0 (at least with my dimmer switch - my guess is cause I haven't linked it with anything)
            #so we treat the SD00 message special and pretend its really a SD19 message (and that works fine for now cause we only really
            #care about cmd2 - as it has our light status in it)
            insteonCommandCode = 'SD19'
        
        #run the callback if one is defined
        self.__executeCallback(fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, command1, command2, insteonCommand, 'Standard Message', isBroadcast, isDirect, isAck, isNak, isAllLink, False)                 
        
        # Just run the callback
        if noop:
            return
        
        #find our pending command in the list so we can say that we're done (if we are running in synchronous mode - if not well then the caller didn't care)
        for (commandHash, commandDetails) in self.__pendingCommandDetails.items():
            
            #since this was a standard insteon message the modem command used to send it was a 0x62 so we check for that
            if binascii.unhexlify(commandDetails['modemCommand']) == '\x62':                                                                        
                originatingCommandId1 = None
                if commandDetails.has_key('commandId1'):
                    originatingCommandId1 = commandDetails['commandId1']    
                    
                validResponseMessages = self.__validResponseMessagesForCommandId(originatingCommandId1)
                if validResponseMessages and len(validResponseMessages):
                    #Check to see if this received command is one that this pending command is waiting for
                    if validResponseMessages.count(insteonCommandCode) == 0:
                        #this pending command isn't waiting for a response with this command code...  Move along
                        continue
                else:
                    self.logger.debug( "Unable to find a list of valid response messages for command %s" % originatingCommandId1 )
                    continue
                        
                    
                #since there could be multiple insteon messages flying out over the wire, check to see if this one is from the device we send this command to
                destDeviceId = None
                if commandDetails.has_key('destinationDevice'):
                    destDeviceId = commandDetails['destinationDevice']
                        
                if destDeviceId:
                    if destDeviceId == _byteIdToStringId(fromIdHigh, fromIdMid, fromIdLow):
                                                                        
                        returnData = {} #{'isBroadcast': isBroadcast, 'isDirect': isDirect, 'isAck': isAck}
                        
                        #try and look up a handler for this command code
                        if self.__insteonCommands.has_key(insteonCommandCode):
                            if self.__insteonCommands[insteonCommandCode].has_key('callBack'):
                                (requestCycleDone, extraReturnData) = self.__insteonCommands[insteonCommandCode]['callBack'](responseBytes)
                                                        
                                if extraReturnData:
                                    returnData = dict(returnData.items() + extraReturnData.items())
                                
                                if requestCycleDone:                                    
                                    waitEvent = commandDetails['waitEvent']                                    
                            else:
                                self.logger.debug( "No callBack for insteon command code %s" % insteonCommandCode )
                        else:
                            self.logger.debug( "No insteonCommand lookup defined for insteon command code %s" % insteonCommandCode )
                                
                        if len(returnData):
                            self.__commandReturnData[commandHash] = returnData
                                                                                                                
                        foundCommandHash = commandHash
                        break
            
        if foundCommandHash == None:
            #self.logger.debug( "Unhandled packet (couldn't find any pending command to deal with it)" )
            #self.logger.debug( "This could be an unsolicited broadcast message" )
            pass
        
        if waitEvent and foundCommandHash:
            waitEvent.set()            
            del self.__pendingCommandDetails[foundCommandHash]
            
            self.logger.debug( "Command %s completed" % foundCommandHash )
    
    def __process_InboundExtendedInsteonMessage(self, responseBytes):
        #51 
        #17 C4 4A     from
        #18 BA 62     to
        #50         flags
        #FF         cmd1
        #C0         cmd2
        #02 90 00 00 00 00 00 00 00 00 00 00 00 00    data
        (insteonCommand, fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, messageFlags, command1, command2, data) = struct.unpack('xBBBBBBBBBB14s', responseBytes)        
        
        #check to see what kind of message this was (based on message flags)
        isBroadcast = messageFlags & (1 << 7) == (1 << 7)
        isDirect = not isBroadcast
        isAck = messageFlags & (1 << 5) == (1 << 5)
        isNak = isAck and isBroadcast
        
        isAllLink = messageFlags & (1 << 6) == (1 << 6)
        
        insteonCommandCode = "%02X" % command1
        if isBroadcast:
            #extended broadcast
            insteonCommandCode = 'EB' + insteonCommandCode
        else:
            #extended direct
            insteonCommandCode = 'ED' + insteonCommandCode

        #run the callback if one is defined
        self.__executeCallback(fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, command1, command2, insteonCommand, "Extended Message", isBroadcast, isDirect, isAck, isNak, isAllLink, False, data=data)                 
        
    def __process_InboundX10Message(self, responseBytes):        
        "Receive Handler for X10 Data"
        #X10 sends commands fully in two separate messages. Not sure how to handle this yet
        #TODO not implemented
        unitCode = None
        commandCode = None
        self.logger.debug( "X10> ", hex_dump(responseBytes, len(responseBytes)) )
 #       (insteonCommand, fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, messageFlags, command1, command2) = struct.unpack('xBBBBBBBBBB', responseBytes)        
#        houseCode =     (int(responseBytes[4:6],16) & 0b11110000) >> 4 
 #       houseCodeDec = X10_House_Codes.get_key(houseCode)
#        keyCode =       (int(responseBytes[4:6],16) & 0b00001111)
#        flag =          int(responseBytes[6:8],16)
        
        
                
    #insteon message handlers
    def __handle_StandardDirect_IgnoreAck(self, messageBytes):
        #just ignore the ack for what ever command triggered us
        #there is most likley more data coming for what ever command we are handling
        return (False, None)
        
    def __handle_StandardDirect_AckCompletesCommand(self, messageBytes):
        #the ack for our command completes things.  So let the system know so
        return (True, None)                            
                                                    
    def __handle_StandardBroadcast_SetButtonPressed(self, messageBytes):        
        #02 50 17 C4 4A 01 19 38 8B 01 00
        (idHigh, idMid, idLow, deviceCat, deviceSubCat, deviceRevision) = struct.unpack('xxBBBBBBxxx', messageBytes)
        
        return (True, {'deviceType': '%02X%02X' % (deviceCat, deviceSubCat), 'deviceRevision':'%02X' % deviceRevision})
            
    def __handle_StandardDirect_EngineResponse(self, messageBytes):        
        #02 50 17 C4 4A 18 BA 62 2B 0D 01        
        engineVersionIdentifier = messageBytes[10]            
        return (True, {'engineVersion': engineVersionIdentifier == '\x01' and 'i2' or 'i1'})
            
    def __handle_StandardDirect_LightStatusResponse(self, messageBytes):
        #02 50 17 C4 4A 18 BA 62 2B 00 00
        lightLevelRaw = messageBytes[10]    
        
        #map the lightLevelRaw value to a sane value between 0 and 1
        normalizedLightLevel = simpleMap(ord(lightLevelRaw), 0, 255, 0, 1)
                    
        return (True, {'lightStatus': round(normalizedLightLevel, 2) })
        
        
        
        
        
    #public methods
    def getFirstAllLinkRecord(self, timeout = None):        
        commandExecutionDetails = self.__sendModemCommand('69')
          
        #return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)
    
    def isAllRecordRequestDone(self):
        return self.__all_record_request_nack
    
    def getNextAllLinkRecord(self, timeout = None):
        self.__all_record_request_nack = False
        commandExecutionDetails = self.__sendModemCommand('6A')
            
        #return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout) 
    
    def getPLMInfo(self, timeout = None):        
        commandExecutionDetails = self.__sendModemCommand('60')
            
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)                            
            
    def pingDevice(self, deviceId, timeout = None):        
        startTime = time.time()
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '0F', '00')                

        #Wait for ping result
        commandReturnCode = self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
        endTime = time.time()
        
        if commandReturnCode:
            return endTime - startTime
        else:
            return False

    def setLogger(self, logger):
        self.logger = logger
        
        if self.__interface is not None:
            self.__interface.setLogger(logger)

    def onReceivedInsteon(self, callback):
        self.__insteonCallback = callback
        
    def onRunLoopError(self, callback):
        self.__run_loop_error_callback = callback
            
    def idRequest(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '10', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
        
    def getInsteonEngineVersion(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '0D', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
    
    def getProductData(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '03', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
            
    def lightStatusRequest(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '19', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)        
                    
    def command(self, device, command, timeout = None):
        command = command.lower()
        if isinstance(device, InsteonDevice):
            self.logger.debug( "InsteonA" )
            commandExecutionDetails = self.__sendStandardP2PInsteonCommand(device.deviceId, "%02x" % (HACommand()[command]['primary']['insteon']), "%02x" % (HACommand()[command]['secondary']['insteon']))
        elif isinstance(device, X10Device):
            self.logger.debug( "X10A" )
            commandExecutionDetails = self.__sendStandardP2PX10Command(device.deviceId,"%02x" % (HACommand()[command]['primary']['x10']))
        else:
            self.logger.debug( "stuffing" )
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)            
        
    def onCommand(self,callback):
        pass
    
    def turnOn(self, deviceId, timeout = None):        
        if len(deviceId) != 2: #insteon device address
            commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '11', 'ff')                        
        else: #X10 device address
            commandExecutionDetails = self.__sendStandardP2PX10Command(deviceId,'02')
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)            

    def turnOff(self, deviceId, timeout = None):
        if len(deviceId) != 2: #insteon device address
            commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '13', '00')
        else: #X10 device address
            commandExecutionDetails = self.__sendStandardP2PX10Command(deviceId,'03')
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)
    
    def turnOnFast(self, deviceId, timeout = None):        
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '12', 'ff')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)            

    def turnOffFast(self, deviceId, timeout = None):
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '14', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
            
    def dimTo(self, deviceId, level, timeout = None):
        
        #organize what dim level we are heading to (figgure out the byte we need to send)
        lightLevelByte = simpleMap(level, 0, 1, 0, 255)
        
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '11', '%02x' % lightLevelByte)                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)        
            
    def brightenOneStep(self, deviceId, timeout = None):
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '15', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)
    
    def dimOneStep(self, deviceId, timeout = None):
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '16', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)


######################
# EXAMPLE            #
######################


def x10_received(houseCode, unitCode, commandCode):
    print 'X10 Received: %s%s->%s' % (houseCode, unitCode, commandCode)

def insteon_received(*params):
    print 'InsteonPLM Received:', params
    
if __name__ == "__main__":

   #Lets get this party started
    insteonPLM = InsteonPLM(TCP('192.168.13.146',9761))
#    insteonPLM = InsteonPLM(Serial('/dev/ttyMI0'))

    jlight = InsteonDevice('19.05.7b',insteonPLM)
    jRelay = X10Device('m1',insteonPLM)

    insteonPLM.start()

    jlight.set('faston')
    jlight.set('fastoff')
    jRelay.set('on')
    jRelay.set('off')
    
    # Need to get a callback implemented
    #    insteon.onReceivedInsteon(insteon_received)

    #sit and spin, let the magic happen
    select.select([],[],[])
