#===============================================================================================================================
# Libraries to import                                                                                                           
#===============================================================================================================================
from synapse.snapsys import *

#===============================================================================================================================
# SNAPpyEmu hooks start here
#===============================================================================================================================
from synapse.snapsys import *
if platform == "snapconnect":
    from SNAPpyEmulation import *
    #sourceAddress = "\xFF\xFF\xFF"
    def rpcSourceAddr():
        return snapConnect.rpc_source_addr()
    def localAddr():
        return snapConnect.local_addr()
    def rpc(addr, func, *args):
        snapConnect.rpc(addr, func, *args)
    def loadNvParam(id):
        return snapConnect.loadNvParam(id)
    def mcastRpc(group, ttl, func, *args):
        return snapConnect.mcastRpc(group, ttl, func, *args)
    # Add any other functions from SNAPpy API used in your code here

#===============================================================================================================================
# Global Variables
#===============================================================================================================================

#===============================================================================================================================
# SNAPPY EVENT HOOKS
#===============================================================================================================================

#---------------------------------------------------------------
@setHook(HOOK_1S)
def Tick1S():
#---------------------------------------------------------------
    """
    This is the 1 second timer hook
    """
    pass


        
#---------------------------------------------------------------
@setHook(HOOK_100MS)
def Tick100MS():
#---------------------------------------------------------------
    """
    This is the 100 mS timer hook.
    """
    pass

#===============================================================================================================================
# Public API Functions
#===============================================================================================================================

#----------------------------------------------------------------------------
def ping(pingMsg):
#----------------------------------------------------------------------------
    sourceAddr = rpcSourceAddr()
    rpc(sourceAddr, "pong", hexWord(localAddr()) + ".Pong received ping(" + pingMsg + ") from " + hexWord(sourceAddr))
    
#----------------------------------------------------------------------------
def pingMcast(pingMsg):
#----------------------------------------------------------------------------
    sourceAddr = rpcSourceAddr()
    mcastRpc(1, 5, "pong", "Mcast pong from " + hexWord(localAddr()) + " in response to pingMcast(" + pingMsg + ") from " + hexWord(sourceAddr))
    #mcastRpc(1, 5, "pong", "XXX")

#----------------------------------------------------------------------------
def mcastTest(func, msg):
#----------------------------------------------------------------------------
    mcastRpc(1, 5, func, msg)

#----------------------------------------------------------------------------
def hexNibble(nibble):
#----------------------------------------------------------------------------
    '''Convert a numeric nibble 0x0-0xF to its ASCII string representation "0"-"F"'''
    hexStr = "0123456789ABCDEF"
    return hexStr[nibble & 0xF]

#----------------------------------------------------------------------------
def hexByte(byte):
#----------------------------------------------------------------------------
    '''convert a byte in hex - input is an integer, not a string'''
    hexStr =  hexNibble(byte >> 4)
    hexStr += hexNibble(byte & 0xF)
    return hexStr
    
#----------------------------------------------------------------------------
def hexWord(word):
#----------------------------------------------------------------------------

    '''convert a string of bytes into hex'''
    index = 0
    hexStr = ""
    while (index < len(word)):
        hexStr += hexByte(ord(word[index]))
        index += 1
    
    return hexStr
