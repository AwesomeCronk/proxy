from threading import Thread
import socket as sock
from termcolor import colored
import os
os.system('color')

def pPrint(strIn):
    print(colored('proxy: {}'.format(strIn), 'yellow'))
def cPrint(strIn):
    print(colored('clientSide: {}'.format(strIn), 'green'))
def sPrint(strIn):
    print(colored('serverSide: {}'.format(strIn), 'cyan'))
def ePrint(strIn):
    print(colored('cleanup: {}'.format(strIn), 'red'))

class cleanup():
    def __init__(self, action):
        self.action = action
    def __enter__(self):
        return
    def __exit__(self, *args):
        ePrint('cleaning up with args {}'.format(args))
        self.action()

class proxy():                  #print in yellow
    def __init__(self, cSideProxyPort, sSideProxyPort, sSideServerIP, sSideServerPort, connections = 1, packetSize = 4096, maxIterations = -1):
        self.cSideProxyPort = cSideProxyPort
        self.sSideProxyPort = sSideProxyPort
        self.sSideServerIP = sSideServerIP
        self.sSideServerPort = sSideServerPort
        self.connections = connections
        self.packetSize = packetSize
        pPrint('initializing cSide...')
        self.cSide = clientSide(self, self.cSideProxyPort)
        pPrint('cSide initialized')
        pPrint('initializing sSide...')
        self.sSide = serverSide(self, self.sSideProxyPort, self.sSideServerIP, self.sSideServerPort)
        pPrint('sSide initiaized')

    def start(self):
        self.cSide.start()
        pPrint('started cSide')
        self.sSide.start()
        pPrint('started sSide')
        self.cSide.join()
        self.sSide.join()

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
        cPrint('Ip address of the proxy is: {}'.format(sock.gethostbyname(sock.gethostname())))
        self.socket.listen(self.parentProxy.connections)
        cPrint('socket listening')
        #self.initialized = True

    def run(self):
        cPrint('run called')
        cPrint('waiting for client connection...')
        self.client, self.clientAddr = self.socket.accept()
        cPrint('connection from {}'.format(self.clientAddr))
        self.hasConnection = True
        while(not self.parentProxy.sSide.connected):
            pass
        try:
            while(True):
                if self.stopFlag:
                    break
                #if self.initialized:
                data = self.client.recv(self.parentProxy.packetSize)
                if data:
                    cPrint('received data from client:\n{}'.format(data))
                    self.parentProxy.sSide.sendall(data)
            cPrint('loop broken')
        except ConnectionAbortedError:
            cPrint('client disconnected')

    def close(self):
        self.client.close()
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
        sPrint('waiting for client to get connection...  ')
        while(not self.parentProxy.cSide.hasConnection):
            pass
        self.connect()
        try:
            while(True):
                if self.stopFlag:
                    break
                #if self.initialized:

                data = self.socket.recv(4096)
                if data:
                    sPrint('received data from server:\n{}'.format(data))
                    self.parentProxy.cSide.sendall(data)

            sPrint('loop broken')
        except ConnectionAbortedError:
            sPrint('server disconnected')

    def close(self):
        self.socket.close()
        self.stopFlag = True

    def sendall(self, data):
        sPrint('sendall called')
        sPrint('sending data to server:\n{}'.format(data))
        self.socket.sendall(data)