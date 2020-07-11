import TCP
import socket as sock

tcpProxy = TCP.proxy(8550, 80, sock.gethostbyname('example.com'), 80)
tcpProxy.start()