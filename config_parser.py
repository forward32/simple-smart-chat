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
        if key == "TCP_PORT":
            defines.TCP_PORT = int(dictionary[key])
        elif key == "UDP_PORT":
            defines.UDP_PORT = int(dictionary[key])
        elif key == "LOG_NAME":
            defines.LOG_FILENAME = str(dictionary[key])
        elif key == "MAX_LISTENERS":
            defines.MAX_LISTEN_COUNT = int(dictionary[key])
        elif key == "BROADCAST_TIMEOUT":
            defines.BROADCAST_TIMEOUT = float(dictionary[key])
        elif key == "BROADCAST_DELAY":
            defines.BROADCAST_DELAY = float(dictionary[key])
        elif key == "SERVER_MESSAGE":
            defines.SERVER_MESSAGE = str(dictionary[key])
        elif key == "MESSAGE_FROM_RUNNING":
            defines.MESSAGE_FROM_RUNNING  =str(dictionary[key])


if __name__=="__main__":
    print_test("Testing mode.")
    ParseConfig("configuration.cfg")
    defines.TraceDump()

