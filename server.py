"""
This is main file of application
"""
from socket import *
import sys, os
from imp import reload
import simple_logger as LOGGER
import defines as DEF
reload(DEF)
reload(LOGGER)
import time
import datetime
import select
import threading
import config_parser as PARSER
####################################################################
##########################LOGIC#####################################
####################################################################
def CreateUDPSock():
    """
    This function creates UDP socket.
    """
    try:
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST,1)

    except error as e:
        msg = "Can not create socket. Function:" + CreateUDPSock.__name__+"\nError:" + str(e)
        LOGGER.log(msg, DEF.LOG_FILENAME)
        sys.exit(-1)

    return sock

def CreateTCPSockServer(_port):
    """
    This function creates TCP socket for server.
    """
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(("", _port))
        sock.listen(DEF.MAX_LISTEN_COUNT)

    except error as e:
        LOGGER.log("Can't create socket. Function:" + CreateTCPSockServer.__name__ + "\nError:" + str(e), DEF.LOG_FILENAME)
        sys.exit(-1)

    return sock

def CreateTCPSockClient(_port):
    """
    This function creates TCP socket for client.
    """
    try:
        sock = socket(AF_INET, SOCK_STREAM)

    except error as e:
        LOGGER.log("Can't' create socket. Function:" + CreateTCPSockClient().__name__+"\nError:" + str(e), DEF.LOG_FILENAME)
        sys.exit(-1)

    return sock

def ReadData(fd):
    """
    Read data from socket fd.
    """
    result = ""
    try:
        stop = False
        while not stop:
            tmp_str = fd.recv(1024).decode('utf-8')
            if not tmp_str:
                stop = True
            if IsEndOfMessage(tmp_str):
                result += tmp_str.split('\0')[0].replace('\0\0', '\0')
                stop = True
            else:
                result += tmp_str.split('\0')[0].replace('\0\0', '\0')

    except error as e:
        LOGGER.log("Can't read data from server. Function:" + ReadData.__name__ + "\nError:" + str(e), DEF.LOG_FILENAME)
        return ""

    return result

def WriteData(fd, msg):
    """
    Write data into socket fd. If server is dead, functions returns False,
    else - True.
    """
    try:
        global is_main
        msg = CheckString(msg)
        while len(msg)>0:
            written = fd.send(msg.encode('utf-8'))
            msg = msg[written:]
    except error as e:
        LOGGER.print_test("Can't send data to server")
        LOGGER.log("Can't send data to server'. Function:" + WriteData.__name__ + "\nError:" + str(e), DEF.LOG_FILENAME)
        return False

    return True

def CheckString(old_str):
    """
    This function checks old_str and replaces symbol '\0' on '\0\0'.
    """
    result = ""
    for i in range(len(old_str)):
        if old_str[i] == '\0':
            result += '\0'+'\0'
        else:
            result += old_str[i]

    return result + '\0'

def IsEndOfMessage(old_str):
    """
    This function checks old_str and if old_str contains '\0' and next symbol after '\0'
    not equal '\0' or if '\0' is last symbol in string than returns True.
    """
    i = 0
    while i < len(old_str):
        if old_str[i] == '\0':
            if i == len(old_str)-1:
                return True
            elif old_str[i+1] != '\0':
                return True
            elif old_str[i+1] == '\0':
                i+=2
        i+=1

    return False

def MassMailing(message):
    """
    This function sends message for all clients.
    """
    if not message:
        LOGGER.log ("Message is empty. Function:" +MassMailing.__name__, DEF.LOG_FILENAME)
    else:
        global connections, is_main
        for key in connections.keys():
            if not WriteData(connections[key], message):
                LOGGER.log("Bad WriteData into sock with fd "+str(key), DEF.LOG_FILENAME)

        LOGGER.log ("Sending message complete. Function:" + MassMailing.__name__, DEF.LOG_FILENAME)

def SendBroadcast(msg, _port, fd):
    """
    Make one broadcast message with text msg
    """
    try:
        fd.sendto(msg.encode('utf-8'), ("255.255.255.255", _port))
    except error as e:
        LOGGER.log("Sendto failed. Function:" + SendBroadcast.__name__ + "\nError:" + str(e), DEF.LOG_FILENAME)
        if str(e) == "[Errno 101] Network is unreachable":
            LOGGER.print_test("Network is unreachable.")
            OnDeadProgram()

def MainServerBroadcast(msg, _port, fd):
    """
    This is function for main client.
    For other clients can see that , main client there is already.
    """
    global is_main
    while is_main:
        SendBroadcast(msg, _port, fd)
        time.sleep(DEF.BROADCAST_DELAY)

    LOGGER.print_test("Thread-broadcast stopped")

def GetDateStructFromMessage(message, sep_msg, sep_date):
    """
    This function return date(yyyy#mm#dd#hh#mm#ss) from message
    """
    temp_lst = message.strip().split(sep_msg)

    return temp_lst[len(temp_lst)-1]

def CompareDates(one_date, two_date):
    """
    This function compares two dates in format yyyy#mm#dd#hh#mm#ss
    and returns true if one_date less two_date.
    """
    str1 = one_date.strip().split('#')
    str2 = two_date.strip().split('#')

    if (int(str1[0])<=int(str2[0]) and int(str1[1])<=int(str2[1]) and
       int(str1[2])<=int(str2[2]) and int(str1[3])<=int(str2[3]) and
       int(str1[4])<=int(str2[4]) and int(str1[5])<=int(str2[5])):
           return True

    return False

def CaptureOfPower(_port, fd):
    """
    Client will be call this function if server died.
    fd - udp socket. _port - udp port.
    """
    try:
        stop_at = time.time() + DEF.BROADCAST_TIMEOUT
        global date_of_starting, tcp_sock, epoll_sock, is_main, server_addr
        tcp_sock.shutdown(1)
        tcp_sock.close()
        msg = DEF.CANDIDATE_MESSAGE+"MY_TIME="+date_of_starting
        is_not_main = False
        # Trying to become the main client
        while time.time() < stop_at:
            SendBroadcast(msg, _port, fd)
            lst = ListenUdpPort(_port)
            if lst and DEF.CANDIDATE_MESSAGE in lst[0]:
                    date = GetDateStructFromMessage(lst[0], "MY_TIME=", "#")
                    # if it is younger
                    if not CompareDates(date_of_starting, date):
                        is_not_main = True
                        break
        # expect the main client
        if is_not_main:
            stop_at = time.time() + DEF.BROADCAST_TIMEOUT
            while time.time() < stop_at:
                lst = ListenUdpPort(_port)
                LOGGER.print_test(lst)
                if lst and lst[0]==DEF.SERVER_MESSAGE:
                    server_addr = lst[1]
                    tcp_sock = CreateTCPSockClient(DEF.TCP_PORT)
                    tcp_sock.setblocking(True)
                    tcp_sock.connect((server_addr[0], DEF.TCP_PORT))
                    LOGGER.print_test("Connected to the new main client.")
                    thread_listener = threading.Thread(target=ListenTCPSock, args=(tcp_sock,))
                    thread_listener.start()
                    LOGGER.print_test("Thread-listener started.")
                    return False

        # if here - you the main client
        is_main = True
        tcp_sock = CreateTCPSockServer(DEF.TCP_PORT)
        LOGGER.log("I main client", DEF.LOG_FILENAME)
        # Create broadcast-thread
        thread_broadcast = threading.Thread(target=MainServerBroadcast, args=(DEF.SERVER_MESSAGE, _port, fd))
        thread_broadcast.start()
        LOGGER.print_test("Thread-broadcast started.")
        # Create epoll-listener-thread
        thread_epoll = threading.Thread(target=StartingEpoll, args=(tcp_sock, epoll_sock))
        thread_epoll.start()
        LOGGER.print_test("Thread-epoll started.")

        #while not user_exit:
        #    LOGGER.print_test("MAIN. Type message for sending or type 0 for exit:")
        #    msg = input()
        #    LOGGER.print_test(">>"+msg+"\n")
        #    MassMailing(msg)
    except error as e:
        LOGGER.log("Error in function " + CaptureOfPower.__name__ + ".\nError:" + str(e), DEF.LOG_FILENAME)


def ListenUdpPort(_port):
    """
    This funcion listen port _port and return old post.
    """
    try:
        sock = CreateUDPSock()
        sock.bind(("", _port))
        sock.settimeout(DEF.BROADCAST_TIMEOUT)

        (msg, addr) = sock.recvfrom(1024)
        lst = [msg.decode('utf-8'), addr]
        sock.close()
        return lst
    except error as e:
        sock.close()
        LOGGER.log("Error in function " + ListenUdpPort.__name__ + ".\nError:" + str(e), DEF.LOG_FILENAME)

def ListenTCPSock(fd):
    """
    This function listen tcp socket fd and return old post.
    """
    global tcp_sock, user_exit, udp_sock, is_main
    while not user_exit:
        reading_data = ReadData(fd)
        if reading_data:
            LOGGER.print_test(">>"+reading_data+"\n")
        else:
            if not user_exit:
                LOGGER.log("Server is dead. Function:"+ListenTCPSock.__name__, DEF.LOG_FILENAME)
                LOGGER.print_test("Server is dead.")
            break

    # if here - server is died
    if not user_exit:
        CaptureOfPower(DEF.UDP_PORT, udp_sock)


def CheckWhoMainServer(_port, fd):
    """
    If main client is there then connect to them.
    Else it will be main client.
    """
    try:
        global server_addr, tcp_sock
        stop_at = time.time() + DEF.BROADCAST_TIMEOUT
        while time.time() < stop_at:
            SendBroadcast(DEF.MESSAGE_FROM_RUNNING, _port, fd)
            lst = ListenUdpPort(_port)
            if lst and lst[0]==DEF.SERVER_MESSAGE:
                server_addr = lst[1]
                tcp_sock.connect((server_addr[0], DEF.TCP_PORT))
                return False

    except error as e:
        LOGGER.log("Can not connect socket. Function:" + CheckWhoMainServer.__name__+"\nError:" + str(e), DEF.LOG_FILENAME)
        sys.exit(-1)

    return True

def StartingEpoll(server, epoll_sock):
    """
    This function creates epoll and monitoring all socket in epoll +
    adds new sockets + removes dead sockets.
    """
    epoll_sock.register(server.fileno(), select.EPOLLIN)

    try:
        global connections, is_main
        while is_main:
            if not epoll_sock:
                break
            events = epoll_sock.poll(1)
            for fileno, event in events:
                if fileno == server.fileno():
                    try:
                        conn, addr = server.accept()
                        conn.setblocking(True)
                        epoll_sock.register(conn.fileno(), select.EPOLLIN)
                        connections[conn.fileno()] = conn
                        LOGGER.log("Add client. Function:"+StartingEpoll.__name__, DEF.LOG_FILENAME)
                        LOGGER.print_test("Add client.")
                    except error:
                        pass

                elif event & select.EPOLLIN:
                    reading_data = ReadData(connections[fileno])
                    if not reading_data:
                        epoll_sock.unregister(fileno)
                        connections[fileno].shutdown(1)
                        connections[fileno].close()
                        del connections[fileno]
                        LOGGER.log("One client is disconnected. Function:" + StartingEpoll.__name__, DEF.LOG_FILENAME)
                        continue
                    LOGGER.print_test(">>"+reading_data+"\n")
                    MassMailing(reading_data)

    except error as e:
        LOGGER.log("There are errors. Function:" + StartingEpoll.__name__+"\nError:" + str(e), DEF.LOG_FILENAME)
    finally:
        LOGGER.print_test("Thread-epoll stopped")

def GetStartingTime():
	"""
	This function saves current date and current time into string.
	Program will be call this function when she starting.
	"""
	now_date = datetime.date.today()
	now_time = datetime.datetime.now()
	
	return (str(now_date.year)+"#"+str(now_date.month)+"#"+str(now_date.day)+"#"+
		    str(now_time.hour)+"#"+str(now_time.minute)+"#"+str(now_time.second))

def OnDeadProgram():
    """
    It is destructor for program.
    """
    global connections, tcp_sock, udp_sock, epoll_sock, server_addr
    udp_sock.close()
    tcp_sock.shutdown(1)
    tcp_sock.close()
    epoll_sock.close()
    #del connections, server_addr, tcp_sock, udp_sock, epoll_sock
    LOGGER.log("Bye-bye...", DEF.LOG_FILENAME)
    exit(0)
####################################################################
####################################################################
####################################################################

if __name__=="__main__":
    PARSER.ParseConfig("configuration.cfg")
    #######################DATA FOR SERVER##############################
    connections = {}
    server_addr = ()
    udp_sock = CreateUDPSock()
    tcp_sock = CreateTCPSockClient(DEF.TCP_PORT)
    epoll_sock = select.epoll()
    user_exit = False
    date_of_starting = GetStartingTime()
    is_main = False
    ####################################################################
    try:
        LOGGER.log("Now i kill you!", DEF.LOG_FILENAME)
        os.remove(DEF.LOG_FILENAME)

        if CheckWhoMainServer(DEF.UDP_PORT, udp_sock):
            is_main = True
            LOGGER.log("I main client", DEF.LOG_FILENAME)
            # Create broadcast-thread
            thread_broadcast = threading.Thread(target=MainServerBroadcast, args=(DEF.SERVER_MESSAGE, DEF.UDP_PORT, udp_sock))
            thread_broadcast.start()
            LOGGER.print_test("Thread-broadcast started.")
            # Create epoll-listener-thread
            tcp_sock.close()
            tcp_sock = CreateTCPSockServer(DEF.TCP_PORT)
            thread_epoll = threading.Thread(target=StartingEpoll, args=(tcp_sock, epoll_sock))
            thread_epoll.start()
            LOGGER.print_test("Thread-epoll started.")

            while threading.active_count() > 1:
                time.sleep(0.5)
            #    LOGGER.print_test("MAIN.Type message for sending or type 0 for exit:")
            #    msg = input()
            #    LOGGER.print_test(">>"+msg+"\n")
            #    MassMailing(msg)
        else:
            # create tcp-socket-listener-thread
            tcp_sock.setblocking(True)
            thread_listener = threading.Thread(target=ListenTCPSock, args=(tcp_sock,))
            thread_listener.start()
            LOGGER.print_test("Thread-listener started.")
            LOGGER.print_test("NOT_MAIN.Type message for sending or type 0 for exit:")

            while not is_main:
                msg = input()
                if msg:
                    WriteData(tcp_sock, msg)

    except:
        user_exit = True
        is_main = False
        LOGGER.print_test("Exit...")
        OnDeadProgram()






