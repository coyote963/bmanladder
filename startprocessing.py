import threading
import json
from bm_parser import start_parser
from helpers import get_socket
from rcontypes import rcon_event, rcon_receive
from exampleapp import example_functions
from current_match import CurrentMatch
def get_execute_functionlist(example_functions):
    def execute_functionlist(event_id, message_string, sock, cm):
        for f in example_functions:
            f(event_id, message_string, sock, cm)
    return execute_functionlist

if __name__ == "__main__":
    # add in additional gamemodes if hosting multiple servers
    gamemodes = ['svl1', 'svl2', 'svl3']
    # this holds all the threads
    threaddict = {}
    for mode in gamemodes:
        sock = get_socket(mode)
        cm = CurrentMatch("")
        threaddict[mode] = threading.Thread(target = start_parser, args = (sock, cm, get_execute_functionlist(example_functions)))
        
    
    for mode, thread in threaddict.items():
        thread.start()

    for mode, thread in threaddict.items():
        thread.join()