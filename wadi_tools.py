import os
import sys
import shutil
import logging
import numpy as np
import os
from os.path import join
from colorama import init
from colorama import Fore, Style
init()

cwd = os.getcwd()
activate_log = True

# log filename
logfile = join(cwd,'wadi.log')

# True means the log file will be deleted every time the script starts to run
clearlog = True

# delete the log file, if necessary
if clearlog and os.path.isfile(logfile):
    os.remove(logfile)


logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p:')
logger = logging.getLogger(__name__)

# log text message to the logfile
def debuglog(text):
    if activate_log == True:
        logger.debug(text)

def errorlog(text):
    if activate_log == True:
        logger.error(text)

def infolog(text):
    if activate_log == True:
        logger.info(text)

# print python version
def which_python():
    print(sys.version)

def pwd():
    print(os.getcwd())

def nancount(data):
    return data.size - np.count_nonzero(np.isnan(data))

# pause the execution
def pause(value = None):
    if value:
        print(value)
    _pause = input('Press the [ENTER] key to continue...')

def copy_file(src_file, to):
    shutil.copy(src_file, to)

def print_bright(text):
    print(Style.BRIGHT + text + Style.RESET_ALL)
