import getpass
import os,sys,socket,traceback
from paramiko.py3compat import input
from modules import models
import datetime
import paramiko
try:
    import interactive
except ImportError:
    from . import interactive

def ssh_login(user_obj,bind_host_obj,mysql_engine,log_recording):
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        print('**** Connecting... ****')
        client.connect(bind_host_obj.host.ip_addr,
                       bind_host_obj.host.port,
                       bind_host_obj.remote_user.username,
                       bind_host_obj.remote_user.password,
                       timeout=30)
        cmd_caches = []

        chan = client.invoke_shell()
        print(repr(client.get_transport()))
        print('**** Here we go ****')

        #登录成功记录日志
        cmd_caches.append(models.AuditLog(user_id=user_obj.id,
                                          bind_host_id=bind_host_obj.id,
                                          action_type='login',
                                          date=datetime.datetime.now()
                                          ))
        log_recording(cmd_caches)

        #进入paramiko模拟的交互式shell
        interactive.interactive_shell(chan,user_obj,bind_host_obj,cmd_caches,log_recording)

        chan.close()
        client.close()
    except Exception as ex:
        print('**** Caught Exception: %s: %s ****' % (ex.__class___,ex))
        traceback.print_exec()
        try:
            client.close()
        except:
            pass
        sys.exit(1)