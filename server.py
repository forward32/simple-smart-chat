"""
This is main file of application
"""
import os
import sys
import time
import datetime
import select
import threading

from socket import *
from PyQt5 import QtWidgets, QtGui, QtCore, uic

import simple_logger as LOGGER
import config_parser as PARSER
import defines as DEF

from importlib import reload
reload(DEF)
reload(LOGGER)
####################################################################
##########################LOGIC#####################################
####################################################################
def CreateUDPSock():
    """
    This function creates UDP socket.
    """
    try:
        sock = socket(AF_INET, SOCK_DGRAM)
        #sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST,1)

    except error as e:
        LOGGER.log("Can not create socket. Function:" + CreateUDPSock.__name__+"\nError:" + str(e), DEF.LOG_FILENAME)
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

static_str="" # only for function ReadData
def ReadData(fd):
    """
    Read data from socket fd.
    """
    global static_str
    try:
        result = ""
        index = -1
        if static_str:
            index = GetEndOfMessage(static_str)
            if index != -1:
                result = static_str[:index].replace('\0\0','\0')
                static_str = static_str[index+1:]
                return result
            else:
                result = static_str

        stop = False
        while not stop:
            tmp_str = fd.recv(256).decode('utf-8')
            if not tmp_str:
                stop = True
            else:
                index = GetEndOfMessage(tmp_str)
                if index != -1:
                    result += tmp_str[:index].replace('\0\0','\0')
                    static_str = tmp_str[index+1:]
                    stop = True
                else:
                    result += tmp_str.replace('\0\0', '\0')

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

def GetEndOfMessage(old_str):
    """
    This function checks old_str and if old_str contains '\0' and next symbol after '\0'
    not equal '\0' or if '\0' is last symbol in string than returns True.
    """
    i = 0
    while i < len(old_str):
        if old_str[i] == '\0':
            if i == len(old_str)-1:
                return i
            elif old_str[i+1] != '\0':
                return i
            elif old_str[i+1] == '\0':
                i+=1
        i+=1

    return -1

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
        LOGGER.log("Warning in function " + ListenUdpPort.__name__ + ".\nWarning:" + str(e), DEF.LOG_FILENAME)

def ListenTCPSock(fd, window):
    """
    This function listen tcp socket fd and return old post.
    """
    global tcp_sock, user_exit, udp_sock
    while not user_exit:
        reading_data = ReadData(fd)

        if reading_data:
            CheckBuf(reading_data)
        else:
            if not user_exit:
                LOGGER.log("Server is dead. Function:"+ListenTCPSock.__name__, DEF.LOG_FILENAME)
                LOGGER.print_test("Server is dead.")
            break

    # if here - server is died
    if not user_exit:
        CaptureOfPower(DEF.UDP_PORT, udp_sock, window)
    else:
        LOGGER.print_test("Thread-listener stopped.")

def SendBroadcast(msg, _port, fd):
    """
    Make one broadcast message with text msg
    """
    try:
        fd.sendto(msg.encode('utf-8'), ("255.255.255.255", _port))
    except error as e:
        LOGGER.log("Sendto failed. Function:" + SendBroadcast.__name__ + "\nError:" + str(e), DEF.LOG_FILENAME)
        if "Errno 101" in str(e):
            global window
            QtWidgets.QMessageBox.about(window, "Информация", "Нет соединения с интернетом.")
            sys.exit(-1)

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

def MassMailing(message, room):
    """
    This function sends message for all clients.
    """
    if not message:
        LOGGER.log ("Message is empty. Function:" +MassMailing.__name__, DEF.LOG_FILENAME)
    else:
        global connections, rooms
        for key in connections.keys():
            if room == rooms[key]:
                if not WriteData(connections[key], message):
                    LOGGER.log("Bad WriteData into sock with fd "+str(key), DEF.LOG_FILENAME)

        LOGGER.log ("Sending message complete. Function:" + MassMailing.__name__, DEF.LOG_FILENAME)

def SendListRooms(room_lst, client_sock):
    """
    This function sends to client list of available rooms.
    """
    for_send_lst = []
    for i in room_lst:
        if not room_lst[i] in for_send_lst:
            for_send_lst.append(room_lst[i])

    WriteData(client_sock, DEF.ROOMS_LIST_SEND_MESSAGE)
    for i in range(len(for_send_lst)):
        WriteData(client_sock, for_send_lst[i])
    WriteData(client_sock, DEF.ROOMS_LIST_SEND_MESSAGE+"-END")

def GetListOfRooms(fd):
    """
    This function for client.
    Reading list available rooms from fd.
    """
    try:
        reading_data = ReadData(fd)
        lst = []
        if reading_data == DEF.ROOMS_LIST_SEND_MESSAGE:
            while True:
                reading_data = ReadData(fd)
                if not reading_data or reading_data == DEF.ROOMS_LIST_SEND_MESSAGE+"-END":
                    break
                else:
                    lst.append(reading_data)

        return lst

    except error as e:
        LOGGER.log("Error in function" + GetListOfRooms.__name__, "\nError:"+str(e), DEF.LOG_FILENAME)

def CaptureOfPower(_port, fd, window):
    """
    Client will be call this function if server died.
    fd - udp socket. _port - udp port.
    """
    try:
        stop_at = time.time() + DEF.BROADCAST_TIMEOUT
        global date_of_starting, tcp_sock, epoll_sock, is_main, server_addr, room_name
        tcp_sock.shutdown(1)
        tcp_sock.close()
        msg = DEF.CANDIDATE_MESSAGE+"MY_TIME="+date_of_starting
        is_not_main = False
        count_trying = DEF.MAX_TRYING_COUNT

        while count_trying > 0:
            # Trying to become the main client
            while time.time() < stop_at:
                SendBroadcast(msg, _port, fd)
                lst = ListenUdpPort(_port)
                if lst and DEF.CANDIDATE_MESSAGE in lst[0]:
                        date = GetDateStructFromMessage(lst[0], "MY_TIME=", "#")
                        # if it is younger
                        if not CompareDates(date_of_starting, date):
                            LOGGER.print_test("Main client found.")
                            is_not_main = True
                            break
            # expect the main client
            if is_not_main:
                count_trying -= 1
                stop_at = time.time() + DEF.BROADCAST_TIMEOUT
                while time.time() < stop_at:
                    lst = ListenUdpPort(_port)
                    if lst and lst[0] == DEF.SERVER_MESSAGE:
                        server_addr = lst[1]
                        tcp_sock = CreateTCPSockClient(DEF.TCP_PORT)
                        tcp_sock.setblocking(True)
                        tcp_sock.connect((server_addr[0], DEF.TCP_PORT))
                        rooms_lst = GetListOfRooms(tcp_sock) # this function get list of rooms from server
                        AddToRoomWindow(rooms_lst)
                        WriteData(tcp_sock, room_name)
                        thread_listener = threading.Thread(target=ListenTCPSock, args=(tcp_sock, window))
                        thread_listener.start()
                        LOGGER.print_test("Thread-listener started.")
                        return False
            else:
                break

        if count_trying <= 0:
            LOGGER.log("Two or more clients have equal data of starting.", DEF.LOG_FILENAME)
            OnDeadProgram()

        # if here - you the main client
        is_main = True
        tcp_sock = CreateTCPSockServer(DEF.TCP_PORT)
        LOGGER.log("I main client", DEF.LOG_FILENAME)
        # Create broadcast-thread
        thread_broadcast = threading.Thread(target=MainServerBroadcast, args=(DEF.SERVER_MESSAGE, _port, fd))
        thread_broadcast.start()
        LOGGER.print_test("Thread-broadcast started.")
        # Create epoll-listener-thread
        thread_epoll = threading.Thread(target=StartingEpoll, args=(tcp_sock, epoll_sock, window))
        thread_epoll.start()
        LOGGER.print_test("Thread-epoll started.")

    except error as e:
        LOGGER.log("Error in function " + CaptureOfPower.__name__ + ".\nError:" + str(e), DEF.LOG_FILENAME)

def CheckWhoMainServer(_port, fd):
    """
    If main client is there then connect to them.
    Else it will be main client.
    """
    try:
        global server_addr, tcp_sock, room_name
        stop_at = time.time() + DEF.BROADCAST_TIMEOUT
        while time.time() < stop_at:
            SendBroadcast(DEF.MESSAGE_FROM_RUNNING, _port, fd)
            lst = ListenUdpPort(_port)
            if lst and lst[0]==DEF.SERVER_MESSAGE:
                server_addr = lst[1]
                tcp_sock.connect((server_addr[0], DEF.TCP_PORT))
                rooms_lst = GetListOfRooms(tcp_sock) # this function get list of rooms from server
                AddToRoomWindow(rooms_lst)
                return False

    except error as e:
        LOGGER.log("Can't connect socket. Function:" + CheckWhoMainServer.__name__+"\nError:" + str(e), DEF.LOG_FILENAME)
        sys.exit(-1)

    return True

def StartingEpoll(server, epoll_sock, window):
    """
    This function creates epoll and monitoring all socket in epoll +
    adds new sockets + removes dead sockets.
    """
    epoll_sock.register(server.fileno(), select.EPOLLIN)

    try:
        global connections, is_main, rooms, room_name
        rooms[server.fileno()] = room_name
        while is_main:
            if not epoll_sock:
                break
            events = epoll_sock.poll(1)
            for fileno, event in events:
                if fileno == server.fileno():
                    conn, addr = server.accept()
                    conn.setblocking(True)
                    epoll_sock.register(conn.fileno(), select.EPOLLIN)
                    connections[conn.fileno()] = conn
                    # send list of rooms to client
                    SendListRooms(rooms, conn)
                    # reading room-name here
                    reading_data = ReadData(conn)
                    rooms[conn.fileno()] = reading_data.strip()
                    LOGGER.log("Add client. Function:"+StartingEpoll.__name__, DEF.LOG_FILENAME)

                elif event & select.EPOLLIN:
                    reading_data = ReadData(connections[fileno])
                    if not reading_data:
                        epoll_sock.unregister(fileno)
                        if fileno in list(connections.keys()):
                            LOGGER.print_test("Cleaning after disconnecting.")
                            connections[fileno].close()
                            del connections[fileno]
                        if fileno in list(rooms.keys()):
                            del rooms[fileno]
                        LOGGER.log("One client is disconnected. Function:" + StartingEpoll.__name__, DEF.LOG_FILENAME)
                        continue
                    # if room client and your room is equal
                    if rooms[server.fileno()] == rooms[fileno]:
                        CheckBuf(reading_data)
                    MassMailing(reading_data, rooms[fileno])

    except error as e:
        LOGGER.log("There are errors. Function:" + StartingEpoll.__name__+"\nError:" + str(e), DEF.LOG_FILENAME)
    finally:
        LOGGER.print_test("Thread-epoll stopped.")

def GetStartingTime():
    """
    This function saves current date and current time into string.
    Program will be call this function when she starting.
    """
    now_date = datetime.date.today()
    now_time = datetime.datetime.now()

    return (str(now_date.year)+"#"+str(now_date.month)+"#"+str(now_date.day)+"#"+
            str(now_time.hour)+"#"+str(now_time.minute)+"#"+str(now_time.second))

def GetTimeForMessage():
    """
    This function return date and time for inserting into message.
    """
    now_date = datetime.date.today()
    now_time = datetime.datetime.now()

    return (str(now_date.year)+":"+str(now_date.month)+":"+str(now_date.day)+" "+
            str(now_time.hour)+":"+str(now_time.minute)+":"+str(now_time.second))

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

    return

def CheckBuf(msg):
    """
    This function call before output data in chat-textbox
    """
    global status, message_buf
    if status == DEF.STATUS_FREE:
        AppendString(msg)
    else:
        if DEF.BUF_FLAG == 1:
            if len(message_buf) > DEF.MAX_BUFFER_SIZE:
                message_buf.clear()
                LOGGER.print_test("Len(buf) > MAX_BUFFER_SIZE. Cleaning data in message buffer.")
            else:
                message_buf.append(msg)

def OnDeadProgram():
    """
    It is destructor for program.
    """
    try:
        global connections, tcp_sock, udp_sock, epoll_sock, server_addr, rooms
        udp_sock.close()
        tcp_sock.shutdown(1)
        tcp_sock.close()
        epoll_sock.close()
        del connections, rooms, udp_sock, tcp_sock, epoll_sock
        LOGGER.log("Bye-bye...", DEF.LOG_FILENAME)
        LOGGER.print_test("Cleaning finished.")
        exit(0)
    except error as e:
        LOGGER.log("Warning in function " + OnDeadProgram.__name__+"\nWarning:"+str(e),DEF.LOG_FILENAME)

#---------------------------User interface------------------
def SendMessageSlot(window, tcp_sock):
    global room_name, user_name
    message = window.edt_msg.toPlainText()
    if message:
        message = GetTimeForMessage()+"#"+user_name+":"+message
        if not message:
            QtWidgets.QMessageBox.about(window, "Информация","Сообщение пустое.\nПожалуйста, введите сообщение в поле ввода и повторите попытку.")
        # if you is main client--
        elif is_main:
            CheckBuf(message)
            MassMailing(message, room_name)
        # if you is not main client--
        else:
            WriteData(tcp_sock, message)
        window.edt_msg.clear()
        window.edt_msg.setFocus()

def CloseSlot():
    global user_exit, is_main, room_window, window
    room_window.close()
    window.close()
    user_exit = True
    is_main = False
    OnDeadProgram()

def AppendString(msg):
    global user_name, window
    date_str = msg.split('#')[0]
    msg = msg[len(date_str)+1:]
    nickname = msg.split(':')[0]
    message = msg[len(nickname)+1:]
    if nickname == user_name:
        window.edt_chat.append(str("<font color="+DEF.MY_COLOR+"><b>"+"["+date_str+"] "+nickname+" написал:</b></font color="+DEF.MY_COLOR+">"))
        window.edt_chat.append(str(message))
    elif message:
         window.edt_chat.append(str("<font color="+DEF.OTHER_COLOR+"><b>"+"["+date_str+"] "+nickname+" написал:</b></font color="+DEF.OTHER_COLOR+">"))
         window.edt_chat.append(str(message))
    else:
        window.edt_chat.append(str(msg))

def ChangeItemSlot():
    global window, message_buf, status
    pixmap = QtGui.QPixmap() # declare
    if window.cmb_status.currentIndex() == 0:
        pixmap = QtGui.QPixmap("status_ok.png")
        status = DEF.STATUS_FREE
        if DEF.BUF_FLAG == 1:
            for i in range(len(message_buf)):
                AppendString(message_buf[i])
            message_buf.clear()
    else:
        status = DEF.STATUS_BUSY
        pixmap = QtGui.QPixmap("status_bad.png")

    scaledPixmap = pixmap.scaled(window.lbl_color.width(), window.lbl_color.height(), QtCore.Qt.KeepAspectRatio)
    window.lbl_color.setPixmap(scaledPixmap);

def AboutSlot():
    global window
    QtWidgets.QMessageBox.about(window, "Информация", "Отказоустойчивый клиент обмена сообщениями.\nPython3 + PyQT5")

def AddToRoomWindow(rooms_lst):
    global room_window
    for i in range(len(rooms_lst)):
        room_window.cmb_rooms.addItem(str(rooms_lst[i]))

def SelectRoomSlot(tcp_sock):
    global room_name, room_window, window
    room_name = room_window.cmb_rooms.currentText()
    window.lbl_room.setText(str("Комната: "+room_name))
    if not room_name:
        QtWidgets.QMessageBox.about(window, "Информация", "Не выбрана комната.")
    else:
        if not is_main:
            WriteData(tcp_sock, room_name)
            # create tcp-socket-listener-thread
            tcp_sock.setblocking(True)
            thread_listener = threading.Thread(target=ListenTCPSock, args=(tcp_sock,window))
            thread_listener.start()
            LOGGER.print_test("Thread-listener started.")
        else:
            LOGGER.log("I main client", DEF.LOG_FILENAME)
            # Create broadcast-thread
            thread_broadcast = threading.Thread(target=MainServerBroadcast, args=(DEF.SERVER_MESSAGE, DEF.UDP_PORT, udp_sock))
            thread_broadcast.start()
            LOGGER.print_test("Thread-broadcast started.")
            # Create epoll-listener-thread
            tcp_sock.close()
            tcp_sock = CreateTCPSockServer(DEF.TCP_PORT)
            thread_epoll = threading.Thread(target=StartingEpoll, args=(tcp_sock, epoll_sock, window))
            thread_epoll.start()
            LOGGER.print_test("Thread-epoll started.")

        room_window.close()

def AddRoomSlot():
    global room_name, room_window
    new_name = ""

    while not new_name:
        new_name, ok = QtWidgets.QInputDialog.getText(room_window, 'Добавление', 'Введите название комнаты:')
        if not ok:
            break

    if new_name:
        room_name = new_name
        AddToRoomWindow([room_name])
#-------------------------------------------------------------------
####################################################################
####################################################################
####################################################################
if __name__=="__main__":
    PARSER.ParseConfig("configuration.cfg")
    DEF.TraceDump()
    #######################DATA FOR SERVER##############################
    connections = {}
    rooms = {}
    server_addr = ()
    udp_sock = CreateUDPSock()
    tcp_sock = CreateTCPSockClient(DEF.TCP_PORT)
    epoll_sock = select.epoll()
    user_exit = False
    date_of_starting = GetStartingTime()
    is_main = False
    room_name = ""
    user_name = ""
    status = DEF.STATUS_FREE
    message_buf = []
    ####################################################################
    try:
        LOGGER.log("Now i kill you!", DEF.LOG_FILENAME)
        os.remove(DEF.LOG_FILENAME)

        # create ui here
        app = QtWidgets.QApplication(sys.argv)
        tray = QtWidgets.QSystemTrayIcon(QtGui.QIcon("chat.bmp"), app)
        tray.show()
        window = uic.loadUi("gui.ui") # main window of application
        window.setWindowIcon(QtGui.QIcon("chat.bmp"))
        pixmap = QtGui.QPixmap("status_ok.png")
        status = DEF.STATUS_FREE
        scaledPixmap = pixmap.scaled(window.lbl_color.width(), window.lbl_color.height(), QtCore.Qt.KeepAspectRatio)
        window.lbl_color.setPixmap(scaledPixmap);

        window.edt_chat.setReadOnly(True)
        window.edt_msg.setFocus()
        window.btn_send.clicked.connect(lambda:SendMessageSlot(window, tcp_sock))
        window.btn_exit.clicked.connect(CloseSlot)
        window.cmb_status.currentIndexChanged.connect(ChangeItemSlot)
        window.action.triggered.connect(CloseSlot)
        window.action_2.triggered.connect(AboutSlot)

        room_window = uic.loadUi("rooms.ui") # room-list window
        room_window.setWindowIcon(QtGui.QIcon("chat.bmp"))
        room_window.btn_accept.clicked.connect(lambda:SelectRoomSlot(tcp_sock))
        room_window.btn_add.clicked.connect(AddRoomSlot)
        room_window.btn_exit.clicked.connect(CloseSlot)
        # set windows to center
        geom = QtWidgets.QApplication.desktop().screenGeometry()
        x = (geom.width()-room_window.width()) / 2
        y = (geom.height()-room_window.height()) / 2
        room_window.move(int(x), int(y))
        x = (geom.width()-window.width()) / 2
        y = (geom.height()-window.height()) / 2
        window.move(int(x), int(y))

        # get nickname here--
        while not user_name:
            user_name, ok = QtWidgets.QInputDialog.getText(window, 'Ввод ника', 'Введите ваше имя или прозвище:')
            if not ok:
                sys.exit(0)

        # find main server(client)
        if CheckWhoMainServer(DEF.UDP_PORT, udp_sock):
            is_main = True

        window.show()
        room_window.show()
        sys.exit(app.exec_())

    except:
        user_exit = True
        is_main = False
        OnDeadProgram()
