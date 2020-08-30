from threading import Thread
import socket as sock
import os
os.system('color')
from dbgTools.cleanup import cleaner
from printing import initLogFile, clearLogFile, pPrint, cPrint, sPrint, ePrint

class proxy():        #80              8550            example.com    80
    def __init__(self, cSideProxyPort, sSideProxyPort, sSideServerIP, sSideServerPort, connections = 1, packetSize = 4096, maxIterations = -1):
        #Recording arguments
        self.cSideProxyPort = cSideProxyPort
        self.sSideProxyPort = sSideProxyPort
        self.sSideServerIP = sSideServerIP
        self.sSideServerPort = sSideServerPort
        self.connections = connections
        self.packetSize = packetSize

        #Declaring variables
        self.proxyIP = sock.gethostbyname(sock.gethostname())
        self.stopFlag = False
        self.stopped = False
        self.cBuffer = []
        self.sBuffer = []

        #Commands. These can be modified by whatever user-defined class inherits from TCP.proxy.
        #There must be a function to call for each command which takes no arguments except for self.
        #Recommended method for adding commands is self.commands.update(dictOfNewCommands)
        self.commands = {'dumpBuffers': self.dumpBuffers,
                         'stop': self.stop,
                         'null': self.nullCommand
                         }
        
        #Initialize the log file
        initLogFile('eventlog.txt')
        clearLogFile()

        #Initialize the cSide and sSide
        pPrint('initializing cSide...')
        self.cSide = clientSide(self, self.cSideProxyPort)
        pPrint('cSide initialized')
        pPrint('initializing sSide...')
        self.sSide = serverSide(self, self.sSideProxyPort, self.sSideServerIP, self.sSideServerPort)
        pPrint('sSide initiaized')
        pPrint('Ip address of the proxy is: {}'.format(self.proxyIP))

    def start(self):        #Start the cSide and sSide
        self.cSide.start()
        pPrint('started cSide')
        self.sSide.start()
        pPrint('started sSide')
        self.run()
        
    def run(self):
        while(not self.stopFlag):
            try:
                userInput = input().split()
                command = userInput[0]
                paramsIn = userInput[1:]
            except KeyboardInterrupt:
                command = 'null'
            try:
                self.commands[command](*paramsIn)
            except KeyError:
                pPrint("Invalid command - '{}'".format(commandIn))

        self._stop()

    #Base commands are defined here:
    def dumpBuffers(self):
        pPrint('Dumping contents of proxy.cBuffer:')
        for i in range(len(self.cBuffer)):
            pPrint('Item at address {}:\n'.format(i, self.cBuffer[i]))
        pPrint('Dumping contents of proxy.sBuffer:')
        for i in range(len(self.sBuffer)):
            pPrint('Item at address {}:\n'.format(i, self.sBuffer[i]))

    def nullCommand(self):
        pass

    def stop(self, sender = 'user'):
        pPrint('Stop requested by {}'.format(sender))
        self.stopFlag = True

    def _stop(self):         #Stop the cSide and sSide
        pPrint("Stopping...")
        
        #Tell the cSide and sSide to stop.
        self.cSide.stop()
        self.sSide.stop()

        #Join the cSide and sSide threads.
        with cleaner(self, badAction = pPrint, badArgs = ("Could not join cSide thread.",), okAction = pPrint, okArgs = ("Successfully joined cSide thread.",), printer = ePrint):
            pPrint("Joining cSide thread...")
            self.cSide.join()

        with cleaner(self, badAction = pPrint, badArgs = ("Could not join sSide thread.",), okAction = pPrint, okArgs = ("Successfully joined sSide thread.",), printer = ePrint):
            pPrint("Joining sSide thread...")
            self.sSide.join()
        
            self.stopped = True
        pPrint("Stopped.")


#    def manageData(self):       #Move data to the cSide and sSide if the buffer has data and they are not busy
#        if len(self.cBuffer) > 0 and not cSide.busy:
#            pPrint("Moving data from cBuffer to cSide.sendBuffer.")
#            cSide.send(self.cBuffer[0])
#            del(self.cBuffer[0])        #Make sure to remove the item from the buffer after sending it.
#        if len(self.sBuffer) > 0 and not sSide.busy:
#            pPrint("Moving data from sBuffer to sSide.sendBuffer.")
#            sSide.send(self.sBuffer[0])
#            del(self.sBuffer[0])        #Make sure to remove the item from the buffer after sending it.

    def cBufferAppend(self, data):       #Forward data to the client
        pPrint("Appending data to cBuffer.")
        self.cBuffer.append(data)

    def sBufferAppend(self, data):       #Forward data to the server
        pPrint("Appending data to sBuffer.")
        self.sBuffer.append(data)

class clientSide(Thread):       #print in green
    def __init__(self, parentProxy, port):
        Thread.__init__(self)
        cPrint('__init__ called')

        #Record arguments
        self.parentProxy = parentProxy
        self.port = port

        #Declare variables
        self.stopFlag = False
        self.stopped = False
        self.busy = False
        self.hasConnection = False

        #Initialize and bind the socket
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        cPrint('socket created')
        self.socket.bind(('', self.port))
        cPrint('socket bound')
        self.socket.listen(self.parentProxy.connections)
        cPrint('socket listening')

    def getConnection(self):
        cPrint('Waiting for client connection...')
        self.socket.settimeout(3)
        while(not self.stopFlag):
            try:
                self.client, self.clientAddr = self.socket.accept()
                cPrint('Connection from {}'.format(self.clientAddr))
                self.hasConnection = True
                break
            except sock.timeout:
                cPrint('Waiting for client connection...')

    def run(self):
        cPrint('run called')
        
        with cleaner(self, badAction = self.parentProxy.stop, badArgs = (self,), okAction = pPrint, okArgs = ("Main loop broke with no exceptions.",), printer = ePrint):
            #Get a connection from the client
            self.getConnection()

            #Main loop
            if not self.stopFlag:
                self.client.settimeout(2)
            cPrint("Entering main loop.")
            while(not self.stopFlag):
                #Receive data and forward it to proxy.sBuffer
                try:
                    cPrint('Waiting for data from client...')
                    data = self.client.recv(self.parentProxy.packetSize)
                    if data:
                        cPrint('received data from client:\n{}'.format(data.decode('utf-8', errors = 'ignore')))
                        self.parentProxy.sBufferAppend(data)
                except sock.timeout:
                    pass
                except ConnectionAbortedError:
                    cPrint('client disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop(self)

                #Check if there is data in the send buffer and send it to the client
                try:
                    if len(self.parentProxy.cBuffer) > 0:
                        self._send()
                except ConnectionAbortedError:
                    cPrint('client disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop(self)

        self._stop()

    def _send(self):
        self.busy = True
        cPrint('Sending data to client:\n{}'.format(self.parentProxy.cBuffer[0].decode('utf-8', errors = 'ignore')))
        self.client.sendall(self.parentProxy.cBuffer[0])
        del(self.parentProxy.cBuffer[0])     #Make sure to remove the item from the buffer after sending it.
        self.busy = False
        cPrint('Data sent')

    def stop(self):
        self.stopFlag = True
        cPrint('Stop flag set.')

    def _stop(self):
        if self.stopped:
            cPrint('Already stopped.')
            return
        cPrint("Stopping...")
        try:
            self.client.close()
        except:
            cPrint("Cannot close socket.")
        self.hasConnection = False
        cPrint("Closed client connection.")
        self.stopped = True

class serverSide(Thread):       #print in blue or cyan
    def __init__(self, parentProxy, port, serverIP, serverPort):
        Thread.__init__(self)
        sPrint('__init__ called')
        #Record arguments
        self.parentProxy = parentProxy
        self.port = port
        self.serverIP = serverIP
        self.serverPort = serverPort

        #Declare variables
        self.stopFlag = False
        self.stopped = False
        self.busy = False
        self.connected = False

        #Initialize and bind the socket
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        sPrint('socket created')
        self.socket.bind(('', self.port))
        sPrint('socket bound')

    def connect(self):
        sPrint('Connecting socket...')
        self.socket.settimeout(3)
        while(not self.stopFlag):
            try:
                self.socket.connect((self.serverIP, self.serverPort))
                sPrint('Socket connected.')
                self.connected = True
                break
            except sock.timeout:
                sPrint('Connecting Socket...')

    def run(self):
        sPrint('run called')
        
        with cleaner(self, badAction = self.parentProxy.stop, badArgs = (self,), okAction = sPrint, okArgs = ("Main loop broke with no exceptions.",), printer = ePrint):
            sPrint('Waiting for client to get connection...')
            while(not self.parentProxy.cSide.hasConnection and not self.stopFlag):
                pass

            self.connect()
        
            #Main loop
            self.socket.settimeout(2)
            sPrint('Entering main loop...')
            while(not self.stopFlag):
                #Receive data and forward it to proxy.cBuffer
                try:
                    sPrint('Waiting for data from server...')
                    data = self.socket.recv(4096)
                    if data:
                        sPrint('received data from server:\n{}'.format(data.decode('utf-8', errors = 'ignore')))
                        self.parentProxy.cBufferAppend(data)
                except sock.timeout:
                    pass
                except ConnectionAbortedError:
                    sPrint('Server disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop(self)
                
                #Check if there is data in the send buffer and send it to the server
                try:
                    if len(self.parentProxy.sBuffer) > 0:
                        self._send()
                except ConnectionAbortedError:
                    sPrint('Server disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop(self)

        sPrint('loop broken')
        self._stop()
        
    def stop(self):
        self.stopFlag = True
        sPrint('Stop flag set.')

    def _stop(self):
        if self.stopped:
            sPrint('Already stopped.')
            return
        sPrint("Stopping...")
        self.socket.close()
        self.connected = False
        sPrint("Disconnected from server.")
        self.stopped = True

    def _send(self):
        sPrint('Sending data to server:\n{}'.format(self.parentProxy.sBuffer[0].decode('utf-8', errors = 'ignore')))
        self.busy = True
        self.socket.sendall(self.parentProxy.sBuffer[0])
        del(self.parentProxy.sBuffer[0])
        self.busy = False
        sPrint('Data sent.')