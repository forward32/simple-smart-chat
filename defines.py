from simple_logger import print_test

# This variables for server module.
# Values is default. They can be changed in module config_parser
LOG_FILENAME = "log.txt"
TCP_PORT = 20000
UDP_PORT = 20001
MAX_LISTEN_COUNT = 1024

BROADCAST_TIMEOUT = 5 # in sec
BROADCAST_DELAY = 0.2 # in sec

SERVER_MESSAGE = "I am main server."
MESSAGE_FROM_RUNNING = "I am started."
CANDIDATE_MESSAGE = "I will be the main."

ROOMS_LIST_SEND_MESSAGE = "LIST_OF_ROOMS"
MY_COLOR = "#0000FF"
OTHER_COLOR = "#FF0000"
STATUS_FREE = "Available"
STATUS_BUSY = "Busy"
BUF_FLAG = 1
MAX_BUFFER_SIZE = 512
MAX_TRYING_COUNT = 5

def TraceDump():
    """
    This function prints all variables in stdout
    """
    print_test("TCP:"+str(TCP_PORT))
    print_test("UDP:"+str(UDP_PORT))
    print_test("LOG:"+LOG_FILENAME)
    print_test("MAX_LISTENERS:"+str(MAX_LISTEN_COUNT))
    print_test("BRD_TMT:"+str(BROADCAST_TIMEOUT))
    print_test("BRD_DL:"+str(BROADCAST_DELAY))
    print_test("SRV_MSG:"+SERVER_MESSAGE)
    print_test("MSG_CLNT:"+MESSAGE_FROM_RUNNING)
    print_test("CNDT_MSG:"+CANDIDATE_MESSAGE)
    print_test("ROOMS_MSG:"+ROOMS_LIST_SEND_MESSAGE)
    print_test("My_CLR:"+MY_COLOR)
    print_test("OTHER_CLR:"+OTHER_COLOR)
    print_test("BUF_FLG:"+str(BUF_FLAG))
    print_test("BUF_SIZE:"+str(MAX_BUFFER_SIZE))

if __name__=="__main__":
    TraceDump()




