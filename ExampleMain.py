#!/usr/bin/python
import sys
import traceback
import select
import time
import os
import os.path
from snapconnect import snap

#----------------------------------------------------------------------------
def setupSynapseImportDirectory():
#----------------------------------------------------------------------------
    cwd = os.path.dirname(sys.argv[0])
    if cwd == '':
        cwd = '.'
    try:
        os.mkdir(cwd + '/synapse')
    except:
        pass
    open(cwd + '/synapse/__init__.py', 'w').write('#')
    open(cwd + '/synapse/snapsys.py', 'w').write("platform = 'snapconnect'")

#----------------------------------------------------------------------------
def cleanupSynapseImportDirectory():
#----------------------------------------------------------------------------
    cwd = os.path.dirname(sys.argv[0])
    if cwd == '':
        cwd = '.'
    os.system('rm -rf ' + cwd + '/synapse')

setupSynapseImportDirectory()

#----------------------------------------------------------------------------
def server_auth(realm, username):
#----------------------------------------------------------------------------
    if username == "public":
        return "public"

#============================================================================
class CallbackHandler:
#============================================================================
    """
    This class is to make managing rpc callbacks simpler
    """
    #------------------------------------------------------------------------
    def __init__(self, snapConnect, callbackRpcName='gencallback'):
    #------------------------------------------------------------------------
        self.returnMap = {}
        self.snapConnect = snapConnect
        self.callbackContainer = [CallbackHandler.callbackstub]
        self.gencallback = self.getCallback()
        self.snapConnect.add_rpc_func(callbackRpcName, self.gencallback)

    @staticmethod
    #------------------------------------------------------------------------
    def callbackstub(snapConnect, returnMap, *args, **kwargs):
    #------------------------------------------------------------------------
        print "Call back container not initialized yet"
        print "%s: *%s, **%s" % (snapConnect.rpcSourceAddr().encode('hex-codec'), repr(args), repr(kwargs))

    #------------------------------------------------------------------------
    def getCallback(self):
    #------------------------------------------------------------------------
        def inner(*args, **kwargs):
            return self.callbackContainer[0](self.snapConnect, self.returnMap, *args, **kwargs)
        return inner

    #------------------------------------------------------------------------
    def setCallback(self, function):
    #------------------------------------------------------------------------
        self.callbackContainer[0] = function
    
    #------------------------------------------------------------------------
    def poll(self):
    #------------------------------------------------------------------------
        pass

#============================================================================
class BridgeRadio:
#============================================================================
    """
    Keeps track of the mac address and platform of the serially connected radio module
    """
    #------------------------------------------------------------------------
    def __init__(self, snapConnect, callbackRpcName='gencallback'):
    #------------------------------------------------------------------------
        self.radioAddress = None
        self.radioPlatform = 'unknown'
        self.snapConnect = snapConnect
        self.callbackRpcName = callbackRpcName
        self.callbackHandler = CallbackHandler(self.snapConnect, callbackRpcName)
        self.snapConnect.mcastRpc(1, 1, 'callback', callbackRpcName, 'loadNvParam', 41)
        self.callbackHandler.setCallback(BridgeRadio.radioAddress)

    @staticmethod
    #------------------------------------------------------------------------
    def radioAddress(snapConnect, returnMap, *args, **kwargs):
    #------------------------------------------------------------------------
        if snapConnect.rpc_source_interface().intf_type == snap.INTF_TYPE_SERIAL:
            radioAddress = snapConnect.rpcSourceAddr()
            returnMap['radioAddress'] = radioAddress
            returnMap['radioPlatform'] = args[0]

    #------------------------------------------------------------------------
    def poll(self):
    #------------------------------------------------------------------------
        returnMap = self.callbackHandler.returnMap
        if len(returnMap) > 0:
            if 'radioAddress' in returnMap:
                self.radioAddress = returnMap['radioAddress']
                self.radioPlatform = returnMap['radioPlatform']
                del returnMap['radioAddress']
                print 'radioAddress = ' + self.radioAddress.encode('hex-codec')
                print 'radioPlatform = ' + self.radioPlatform

#============================================================================
class PollLoopVisualization:
#============================================================================
    """
    Visualization to indicate how fast the polling loop is running
    """

    #------------------------------------------------------------------------
    def __init__(self, size=20):
    #------------------------------------------------------------------------
        self.index = 0
        self.enabled = False
        self.sequence = []
        for i in range(0, size):
            self.sequence.append('*' * i + ' '*(size-i))
        for i in range(0, size):
            self.sequence.append('*' * (size-i) + ' '*i)

    #------------------------------------------------------------------------
    def update(self):
    #------------------------------------------------------------------------
        if self.enabled:
            sys.stderr.write(self.sequence[self.index] + '\r')
            self.index = (self.index + 1) % len(self.sequence)


#----------------------------------------------------------------------------
def processUserCommand(snapConnect, bridgeRadio, visualization, line):
#----------------------------------------------------------------------------
    helpText = """
h   - help
d/D - increase/decrease polling loop delay
X   - send reboots
z/Z - enable/disable polling loop visualization
c   - set SNAP RF channel (0-15)
p   - print state
q   - quit
"""

    cmd, param = line[0], line[1:]
    if cmd.lower() == 'h':
        print helpText
    elif cmd == 'm':
        print 'Call %s.mcastTest("foo", "bar")' %  SNAPpyModule.__name__
        SNAPpyModule.mcastTest("foo", "bar")
    elif cmd == 'c':
        try:
            channel = int(param)
            if channel < 0 or channel > 15:
                raise Exception("Invalid channel number")
        except:
            print "Invalid channel"
        else:
            print "Changing channel to %i" % channel
            snapConnect.rpc(bridgeRadio.radioAddress, 'setChannel', int(channel))
            snapConnect.rpc(bridgeRadio.radioAddress, 'saveNvParam', 4, int(channel))
    # The 'x' command is for sending a whole bunch of 'reboot' rpc command over the air.
    # This is usefull if you have 'sleepy' nodes that you need to catch when they are awake
    elif cmd == 'x':
        reboots = int(param)
        print "sending %i reboots" % reboots
        for i in range(reboots):
            snapConnect.mcastRpc(1, 5, 'reboot')
        print "done sending reboots"
    elif cmd == 'z':
        visualization.enabled = True
    elif cmd == 'Z':
        visualization.enabled = False
    elif cmd in ['p', 'd', 'D']:
        # These commands are not handled here
        pass
    elif cmd == 'q':
        cleanupSynapseImportDirectory()
        exit(0)
    else:
        print 'unhandled command: ' + repr(cmd)
    return cmd, param

#----------------------------------------------------------------------------
def main(module, serialPort='/dev/ttyS1'):
#----------------------------------------------------------------------------
 
    snapConnect = snap.SNAPcom()
    # The module needs to have the snap connect instance in order to be able to emulate some functions (i.e. rpc, mcastRpc)
    module.snapConnect = snapConnect
    print "Address: " + repr(snapConnect.local_addr().encode('hex-codec'))

    # Lock down our routes (we are a stationary device)
    snapConnect.save_nv_param(snap.NV_MESH_ROUTE_AGE_MAX_TIMEOUT_ID, 0)

    # Don't allow others to change our NV Parameters
    snapConnect.save_nv_param(snap.NV_LOCKDOWN_FLAGS_ID, 0x2)

    snapConnect.add_rpc_func('ping', module.ping)
    snapConnect.add_rpc_func('pingMcast', module.pingMcast)
    snapConnect.add_rpc_func('mcastTest', module.mcastTest)

    snapConnect.accept_tcp(server_auth)
    snapConnect.open_serial(1, serialPort)


    delay = 0.001
    visualization = PollLoopVisualization()

    lastlooptime = time.time()
    looptimes = [0]*20
    looptimeidx = 0

    bridgeRadio = BridgeRadio(snapConnect)
    
    # Run SNAP Connect until shutdown
    while True:
        # Check for any input on stdin from user and process
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            line = line.strip()
            if line:
                cmd, param = processUserCommand(snapConnect, bridgeRadio, visualization, line)
                line = ""

                # Commands that depend on local variables so they can't be processed by processUserCommand
                # Print various variables for a 'p' command
                if cmd == 'p':
                    print "Print state"
                    print "delay = " + repr(delay)
                    print "Average loop latency: " + repr(sum(looptimes)/len(looptimes))
                    print
                # A series of d's or D's will adjust the delay ('d': *= 2, 'dd': *= 4 , 'DD' /= 4)
                elif cmd == 'd':
                    delay *= 2**(1+len(param))
                    print 'Loop delay = ' + repr(delay)
                elif cmd == 'D':
                    delay /= 2**(1+len(param))
                    print 'Loop delay = ' + repr(delay)
        
        snapConnect.poll()
        # Need to poll bridgeRadio in order to get the radioAddress member updated
        bridgeRadio.poll()

        currenttime = time.time()
        looptimes[looptimeidx] = currenttime - lastlooptime
        lastlooptime = currenttime
        looptimeidx = (looptimeidx + 1) % len(looptimes)

        visualization.update()

        time.sleep(delay)


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(msecs)03d %(levelname)-8s %(name)-8s %(message)s', datefmt='%H:%M:%S')

    import Example as SNAPpyModule

    main(SNAPpyModule, sys.argv[1])

