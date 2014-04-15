from simple_logger import print_test, log
import sys
import defines

def CreateWordsDict(file_content):
    """
    This function creates dictionary.
    Key is left part of string in file, value is right part.
    Return value - dictionary
    """
    dictionary = {}
    for i in range(len(file_content)):
        temp_lst = file_content[i].strip().split('=')
        temp_lst = [x.strip() for x in temp_lst]
        if len(temp_lst)>1:
            dictionary[temp_lst[0]] = temp_lst[1]

    return dictionary

def ParseConfig(file_name):
    """
    This function parses configuration file with name configuration.cfg
    and sets value for variables in module defines.py
    """
    f = open(file_name)
    if not f:
        print_test("Can't open file " + file_name)
        print_test("Exit...")
        sys.exit()

    dictionary = CreateWordsDict(f.readlines())
    for key in dictionary:
        if key.lower() == "tcp_port":
            defines.TCP_PORT = int(dictionary[key])
        elif key.lower() == "udp_port":
            defines.UDP_PORT = int(dictionary[key])
        elif key.lower() == "log_name":
            defines.LOG_FILENAME = str(dictionary[key])
        elif key.lower() == "max_listeners":
            defines.MAX_LISTEN_COUNT = int(dictionary[key])
        elif key.lower() == "broadcast_timeout":
            defines.BROADCAST_TIMEOUT = float(dictionary[key])
        elif key.lower() == "broadcast_delay":
            defines.BROADCAST_DELAY = float(dictionary[key])
        elif key.lower() == "server_message":
            defines.SERVER_MESSAGE = str(dictionary[key])
        elif key.lower() == "message_from_running":
            defines.MESSAGE_FROM_RUNNING  =str(dictionary[key])
        elif key.lower() == "candidate_mesage":
            defines.CANDIDATE_MESSAGE = str(dictionary[key])
        elif key.lower() == "my_color":
            defines.MY_COLOR = str(dictionary[key])
        elif key.lower() == "other_color":
            defines.OTHER_COLOR= str(dictionary[key])
        elif key.lower() == "buf_flag":
            defines.BUF_FLAG= int(dictionary[key])


if __name__=="__main__":
    print_test("Testing mode.")
    ParseConfig("configuration.cfg")
    defines.TraceDump()

