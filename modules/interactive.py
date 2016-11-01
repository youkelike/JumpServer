import socket,sys,datetime
from paramiko.py3compat import u
from modules import models

try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False

def interactive_shell(chan,user_obj,bind_host_obj,cmd_caches,log_recording):
    if has_termios:
        posix_shell(chan,user_obj,bind_host_obj,cmd_caches,log_recording)
    else:
        windows_shell(chan)

def posix_shell(chan,user_obj,bind_host_obj,cmd_caches,log_recording):
    import select
    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)
        cmd = ''

        tab_key = False
        while True:
            r,w,e = select.select([chan,sys.stdin],[],[])
            if chan in r:
                try:
                    x = u(chan.recv(1024))
                    if tab_key:
                        if x not in ('\x07','\r\n'):
                            cmd += x
                        tab_key = False

                    if len(x) == 0:
                        sys.stdout.write('\r\n**** EOF ****\r\n')
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass

            if sys.stdin in r:
                x = sys.stdin.read(1)
                if '\r' != x:
                    cmd += x
                else:
                    print('cmd->: ',cmd)
                    log_item = models.AuditLog(user_id=user_obj.id,
                                               bind_host_id=bind_host_obj.id,
                                               action_type='cmd',
                                               cmd=cmd,
                                               date=datetime.datetime.now())
                    cmd_caches.append(log_item)
                    cmd = ''
                    if len(cmd_caches) >= 10:#每10条命令刷写一次日志
                        log_recording(cmd_caches)
                        cmd_caches = []
                if '\t' == x:
                    tab_key = True
                if len(x) == 0:
                    break
                chan.send(x)
    finally:
        termios.tcsetattr(sys.stdin,termios.TCSADRAIN,oldtty)

def windows_shell(chan):
    import threading

    sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
                sys.stdout.flush()
                break
            sys.stdout.write(data.decode())
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass