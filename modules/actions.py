#_*_coding=utf-8_*_

from config import ac_registers
from modules import utils

def help_msg():
    print('Available commands: ')
    for key in ac_registers.actions:
        print(key)

def execute_from_command_line(argvs):
    if len(argvs) < 2:
        help_msg()
        exit()

    if argvs[1] not in ac_registers.actions:
        utils.print_err('Command [%s] does not exist!' % argvs[1],quit=True)

    ac_registers.actions[argvs[1]](argvs[1:])

