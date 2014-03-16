"""
This is server part for application
"""
from socket import *
from simple_logger import log
from defines import *
import sys
import time

##########################LOGIC#####################################
def CreateUDPSock():
    """
    This function creates UDP socket
    """
    try:
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST,1)

    except error:
        msg = "Can not create socket. Function:" + CreateUDPSock.__name__
        log(msg, LOG_FILENAME)
        sys.exit(-1)

    return sock

def CreateTCPSockServer(_port):
    """
    This function creates TCP socket
    """
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR,1)
        sock.bind(("", _port))
        sock.listen(MAX_LISTEN_COUNT)

    except error:
        msg = "Can not create socket. Function:" + CreateTCPSockServer.__name__
        log(msg, LOG_FILENAME)
        sys.exit(-1)

    return sock

def CreateTCPSockClient(_port):
    """
    This function creates TCP socket
    """
    try:
        sock = socket(AF_INET, SOCK_STREAM)

    except error:
        msg = "Can not create socket. Function:" + CreateTCPSockClient().__name__
        log(msg, LOG_FILENAME)
        sys.exit(-1)

    return sock

def ReadData(fd):
    """
    Read data from socket fd
    """
    result = ""
    while True:
        result += fd.recv(1024)

    return result.decode('utf-8')

def WriteData(fd, msg):
    """
    Write data into socket fd
    """
    while (len(msg)>0):
        written = fd.send(msg.encode('utf-8'))
        msg = msg[written:]

    return true

def SendBroadcast(msg, _port, fd):
    """
    Make one broadcast message with text msg
    """
    try:
        fd.sendto(msg.encode('utf-8'), ("255.255.255.255", _port))
    except error:
        msg = "Sendto failed. Function:" + SendBroadcast.__name__
        log(msg, LOG_FILENAME)

def MainServerBroadcast(msg, _port, fd):
    """
    This is function for main server.
    For other clients can see that , main server there is already.
    """
    while True:
        SendBroadcast(msg, _port, fd)
        time.sleep(BROADCAST_DELAY)

def ListenUdpPort(_port):
    """
    This funcion listen port _port and return old post
    """
    try:
        sock = CreateUDPSock()
        sock.bind(("", _port))
        sock.settimeout(1)

        (msg, addr) = sock.recvfrom(1024)
        lst = [msg.decode('utf-8'), addr]
        sock.close()
        return lst

    except error:
        msg = "Socket error. Function:" + ListenUdpPort.__name__
        log(msg, LOG_FILENAME)

    finally:
        sock.close()

    return []


def CheckWhoMainServer(_port, fd):
    """
    If main server is there then connect to them.
    Else it will be main server.
    """
    try:
        stop_at = time.time() + BROADCAST_TIMEOUT
        while time.time() < stop_at:
            SendBroadcast(MESSAGE_FROM_RUNNING, _port, fd)
            lst = ListenUdpPort(_port)
            if (lst and lst[0]==SERVER_MESSAGE):
                global server_addr
                server_addr = lst[1]
                global tcp_sock
                print(server_addr[0])
                tcp_sock.connect((server_addr[0], TCP_PORT))
                return False

    except error as e:
        msg = "Can not connect socket. Function:" + CheckWhoMainServer.__name__
        msg += "\nError:" + str(e)
        log(msg, LOG_FILENAME)


    return True
####################################################################


#############################TESTING################################
if __name__=="__main__":
    #######################DATA FOR SERVER##############################
    сonnections = {} # this is dictionary; key = fd, value = connection
    server_addr = () # server address
    udp_sock = CreateUDPSock()
    tcp_sock = CreateTCPSockClient(TCP_PORT)
    ####################################################################
    try:
        if (udp_sock and tcp_sock):
            print("Success.")

        #while True:
        #    SendBroadcast(SERVER_MESSAGE, UDP_PORT, udp_sock)
        if CheckWhoMainServer(UDP_PORT, udp_sock):
            print("Good")
        else:
            print("Bad")

    except KeyboardInterrupt:
        print("Normal exit.")
        udp_sock.close()
        tcp_sock.close()
        sys.exit(0)

