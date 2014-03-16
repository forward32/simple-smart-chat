from server import CreateUDPSock, SendBroadcast, CreateTCPSockServer
from defines import *
import threading
import socket
import time


def Accepting(fd):
    conn, addr = fd.accept()

tmp_fd = CreateUDPSock()
sock = CreateTCPSockServer(TCP_PORT)

th = threading.Thread(target=Accepting, args=(sock,))
th.daemon = True
th.start()

while True:
    SendBroadcast(SERVER_MESSAGE, UDP_PORT, tmp_fd)


