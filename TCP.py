from threading import Thread
import socket as sock
import os
os.system('color')
from termcolor import colored
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
            with cleaner(self, action = pPrint, args = ('Exception in self.manageData.',), printer = ePrint):
                self.manageData()

        self._stop()

    def stop(self, sender):
        pPrint('Stop requested by {}'.format(sender))
        self.stopFlag = True

    def _stop(self):         #Stop the cSide and sSide
        pPrint("Stopping...")
        
        #Tell the cSide and sSide to stop.
        self.cSide.stop()
        self.sSide.stop()

        #Join the cSide and sSide threads.
        with cleaner(self, action = pPrint, args = ("Could not join cSide thread.",), printer = ePrint):
            pPrint("Joining cSide thread...")
            self.cSide.join()
            pPrint("cSide thread joined.")

        with cleaner(self, action = pPrint, args = ("Could not join sSide thread.",), printer = ePrint):
            pPrint("Joining sSide thread...")
            self.sSide.join()
            pPrint("sSide thread joined.")
        
            self.stopped = True
        pPrint("Stopped.")

    def manageData(self):       #Move data to the cSide and sSide if the buffer has data and they are not busy
        if len(self.cBuffer) > 0 and not cSide.busy:
            pPrint("Moving data from cBuffer to cSide.sendBuffer.")
            cSide.send(self.cBuffer[0])
        if len(self.sBuffer) > 0 and not sSide.busy:
            pPrint("Moving data from cBuffer to sSide.sendBuffer.")
            sSide.send(self.sBuffer[0])

    def sendToClient(self, data):       #Forward data to the client
        pPrint("Appending data to cBuffer.")
        self.cBuffer.append(data)

    def sendToServer(self, data):       #Forward data to the server
        pPrint("Appending data to sBuffer.")
        self.sBuffer.append(data)

class clientSide(Thread):       #print in green
    def __init__(self, parentProxy, port):
        Thread.__init__(self)
        cPrint('__init__ called')

        #Recording arguments
        self.parentProxy = parentProxy
        self.port = port

        #Declaring variables
        self.stopFlag = False
        self.stopped = False
        self.busy = False
        self.hasConnection = False
        self.sendBuffer = []    #Buffers for sending and receiving data
        self.recvBuffer = []

        #Initialize and bind the socket
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        cPrint('socket created')
        self.socket.bind(('', self.port))
        cPrint('socket bound')
        self.socket.listen(self.parentProxy.connections)
        cPrint('socket listening')

    def run(self):          #Main loop
        cPrint('run called')
        
        with cleaner(self, action = self.parentProxy.requestStop, args = (self,), printer = ePrint):
            #Get a connection from the client
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

            #Main loop
            cPrint("Entering main loop.")
            self.client.settimeout(2)
            while(not self.stopFlag):
                #Receive data and forward it to proxy.sBuffer
                try:
                    data = self.client.recv(self.parentProxy.packetSize)
                    if data:
                        cPrint('received data from client:\n{}'.format(data))
                        self.parentProxy.sendToServer(data)
                except sock.timeout:
                    pass
                except ConnectionAbortedError:
                    cPrint('client disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop()

                #Check if there is data in the send buffer and send it to the client
                try:
                    if len(self.sendBuffer) > 0:
                        cPrint('Sending data to client:\n{}'.format(self.sendBuffer[0]))
                        self.client.sendall(data)
                except ConnectionAbortedError:
                    cPrint('client disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop()

            cPrint('loop broken')
            self._stop()

    def stop(self):
        self.stopFlag = True

    def _stop(self):
        cPrint("Stopping...")
        try:
            self.client.close()
        except:
            cPrint("Cannot close socket.")
        self.hasConnection = False
        cPrint("Closed client connection.")

    def send(self, data):
        self.sendBuffer.append(data)

    def _send(self, data):
        self.busy = True
        cPrint('sendall called')
        cPrint('sending data to client:\n{}'.format(data))
        self.client.sendall(data)
        self.busy = False
        cPrint('data sent')

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
        self.connected = False
        self.sendBuffer = []

        #Initiate and bind the socket
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        sPrint('socket created')
        self.socket.bind(('', self.port))
        sPrint('socket bound')

    def connect(self):
        sPrint('connecting socket...')
        self.socket.connect((self.serverIP, self.serverPort))
        sPrint('socket connected')
        self.connected = True

    def run(self):
        sPrint('run called')
        
        with cleaner(self, action = self.parentProxy.stop, printer = ePrint):
            sPrint('waiting for client to get connection...  ')
            while(not self.parentProxy.cSide.hasConnection):
                pass

            self.connect()
        
            #Main loop
            while(not self.stopFlag):
                #Receive data and forward it to proxy.cBuffer
                try:
                    data = self.socket.recv(4096)
                    if data:
                        sPrint('received data from server:\n{}'.format(data))
                        self.parentProxy.sendToClient(data)
                except ConnectionAbortedError:
                    sPrint('Server disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop()
                
                #Check if there is data in self.sendBuffer and send it to the server
                try:


            sPrint('loop broken')
            self._stop()
        
    def stop(self):
        self.stopFlag = True
        sPrint('Stop flag set.')

    def _stop(self):
        sPrint("Stopping...")
        self.socket.close()
        self.connected = False
        sPrint("Disconnected from server.")

    def send(self, data):
        self.sendBuffer.append(data)

    def _send(self):
        sPrint('Sending data to server:\n{}'.format(self.sendBuffer[0]))
        self.socket.sendall(self.sendBuffer[0])