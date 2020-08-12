import TCP
import socket as sock

#cSideProxyPort - port that the proxy is listening on.
#sSideProxyPort - port that the proxy uses to connect to the server.
#sSideServerIP - IP address of the server.
#sSideServerPort - port that the server is listening on.

TCP.clearLog()
tcpProxy = TCP.proxy(80, 8550, sock.gethostbyname('example.com'), 80)
tcpProxy.start()
while(True):
    if input('') == 'stop':
        tcpProxy.stop()