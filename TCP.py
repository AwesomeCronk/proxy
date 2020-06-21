from threading import Thread
import socket as sock

class proxy():
    def __init__(self, cSidePort, sSideIP, sSidePort, connections = 1, packetSize = 4096):
        self.cSide = clientSide(self, cSidePort)
        self.sSide = serverSide(self, sSideIP, sSidePort)
        self.connections = connections

    def forwardToServer(self, data):
        self.sSide.sendToServer(data)

class clientSide(Thread):
    def __init__(self, paentProxy, port):
        self.parentProxy = parentProxy
        self.port = port
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.socket.bind(('', self.port))
        self.socket.listen(self.parentProxy.connections)
        self.conn, self.connAddr = self.socket.accept()

    def run(self):
        while(True):
            data = self.conn.recv(self.parentProxy.packetSize)
            if data:
                self.parentProxy.forwardToServer(data)

class serverSide(Thread):
    def __init__(self, serverIP, serverPort)