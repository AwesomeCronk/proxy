from threading import Thread
import socket as sock
from termcolor import colored
import os, traceback
os.system('color')

from dbgTools.cleanup import cleaner

def pPrint(strIn, end = '\n'):
    strOut = colored('proxy: {}'.format(strIn), 'yellow') + end
    print(strOut)
    writeLog(strOut)
        
def cPrint(strIn, end = '\n'):
    strOut = colored('clientSide: {}'.format(strIn), 'green') + end
    print(strOut)
    writeLog(strOut)

def sPrint(strIn, end = '\n'):
    strOut = colored('serverSide: {}'.format(strIn), 'cyan') + end
    print(strOut)
    writeLog(strOut)

def ePrint(strIn, end = '\n'):
    strOut = colored('cleanup: {}'.format(strIn), 'red') + end
    print(strOut)
    writeLog(strOut)

def writeLog(strIn):
    with open('eventLog.txt', 'a') as logFile:
        logFile.write(strIn)

def clearLog():
    with open('eventLog.txt', 'w') as logFile:
        logFile.write('')

class proxy():        #80              8550            example.com    80
    def __init__(self, cSideProxyPort, sSideProxyPort, sSideServerIP, sSideServerPort, connections = 1, packetSize = 4096, maxIterations = -1):
        self.cSideProxyPort = cSideProxyPort
        self.sSideProxyPort = sSideProxyPort
        self.sSideServerIP = sSideServerIP
        self.sSideServerPort = sSideServerPort
        self.connections = connections
        self.packetSize = packetSize
        self.proxyIP = sock.gethostbyname(sock.gethostname())
        self.stopFlag = False
        self.stopped = False
        pPrint('initializing cSide...')
        self.cSide = clientSide(self, self.cSideProxyPort)
        pPrint('cSide initialized')
        pPrint('initializing sSide...')
        self.sSide = serverSide(self, self.sSideProxyPort, self.sSideServerIP, self.sSideServerPort)
        pPrint('sSide initiaized')
        pPrint('Ip address of the proxy is: {}'.format(self.proxyIP))

    def start(self):
        self.cSide.start()
        pPrint('started cSide')
        self.sSide.start()
        pPrint('started sSide')

    def stop(self):
        pPrint("Stopping...")
        self.cSide.stop()
        self.sSide.stop()
        #join cSide and sSide threads
        with cleaner(self, action = pPrint, args = ("Could not join cSide thread.",), printer = ePrint):
            pPrint("Joining cSide thread...")
            self.cSide.join()
            pPrint("cSide thread joined.")

        try:
            pPrint("Joining sSide thread...")
            self.sSide.join()
            pPint("sSide thread joined.")
        except:
            pPrint("Could not join sSide thread.")
        
        pPrint("Stopped.")

    def sendToClient(self, data):
        pPrint("Forwarding data to client.")
        self.cSide.sendall(data)

    def sendToServer(self, data):
        pPrint("Forwarding data to server.")
        self.sSide.sendall(data)

class clientSide(Thread):       #print in green
    def __init__(self, parentProxy, port):
        Thread.__init__(self)
        cPrint('__init__ called',)
        self.stopFlag = False
        #self.initialized = False
        self.hasConnection = False
        self.parentProxy = parentProxy
        self.port = port

        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        cPrint('socket created')
        self.socket.bind(('', self.port))
        cPrint('socket bound')
        self.socket.listen(self.parentProxy.connections)
        cPrint('socket listening')
        #self.initialized = True

    def run(self):
        cPrint('run called')
        
        with cleaner(self, action = self.parentProxy.stop, printer = ePrint):
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
            while(not self.stopFlag):
                try:
                    data = self.client.recv(self.parentProxy.packetSize)    #Get the data and process it
                    if data:
                        cPrint('received data from client:\n{}'.format(data))
                        self.parentProxy.sendToServer(data)

                except ConnectionAbortedError:
                    cPrint('client disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop()
            cPrint('loop broken')

    def stop(self):
        cPrint("Stopping...")
        try:
            self.client.close()
        except:
            cPrint("Cannot close socket.")
        self.hasConnection = False
        cPrint("Closed client connection.")
        self.stopFlag = True

    def sendall(self, data):
        cPrint('sendall called')
        cPrint('sending data to client:\n{}'.format(data))
        self.client.sendall(data)
        cPrint('data sent')

class serverSide(Thread):       #print in blue or cyan
    def __init__(self, parentProxy, port, serverIP, serverPort):
        Thread.__init__(self)
        sPrint('__init__ called')
        self.stopFlag = False
        #self.initialized = False
        self.connected = False
        self.parentProxy = parentProxy
        self.port = port
        self.serverIP = serverIP
        self.serverPort = serverPort

        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        sPrint('socket created')
        self.socket.bind(('', self.port))
        sPrint('socket bound')
        #self.initialized = True

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
        
            while(not self.stopFlag):
                try:
                    data = self.socket.recv(4096)
                    if data:
                        sPrint('received data from server:\n{}'.format(data))
                        self.parentProxy.sendToClient(data)
                except ConnectionAbortedError:
                    sPrint('Server disconnected. Calling parentProxy.stop().')
                    self.parentProxy.stop()
            sPrint('loop broken')
        
    def stop(self):
        sPrint("Stopping...")
        self.socket.close()
        self.connected = False
        sPrint("Disconnected from server.")
        self.stopFlag = True

    def sendall(self, data):
        while(not self.connected):
            pass
        sPrint('sendall called')
        sPrint('sending data to server:\n{}'.format(data))
        self.socket.sendall(data)