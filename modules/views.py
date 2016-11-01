from modules import models
from modules.db_conn import engine,session
from modules.utils import print_err,yaml_parser
from modules import common_filters
from modules import ssh_login
import getpass

def parse_argvs(argvs,msg):
    if '-f' in argvs:
        return argvs[argvs.index('-f')+1]
    else:
        print_err('invalid usage, should be: create_users -f <%s>' % msg,quit=True)

def auth():
    count = 0
    while count < 3:
        username = input('Username: ').strip()
        if len(username) == 0:continue
        password = getpass.getpass(prompt='Password: ')
        #password = input('Password: ').strip()
        if len(password) == 0:continue
        user_obj = session.query(models.UserProfile).filter(models.UserProfile.username==username,
                                                            models.UserProfile.password==password).first()
        if user_obj:
            return user_obj
        else:
            print('****wrong username or password, you have %s more chances.' % (3-count-1))
            count += 1
    else:
        print_err('****too many attempts.****')

def welcome_msg(user):
    msg = '''
    -----------Welcome [%s] login LittleFinger-----------
    ''' % user.username
    print(msg)

def log_recording(logs):
    print('**** logs: %s ****' % logs)
    session.add_all(logs)
    session.commit()

def start_session(argvs):
    print('****going to start session****')
    user = auth()
    if user:
        welcome_msg(user)
        exit_flag = False
        while not exit_flag:
            #打印登录用户关联的未分组主机
            if user.bind_hosts:
                print('ungrouped hosts(%s)' % len(user.bind_hosts))
            #打印登录用户关联的组
            if user.groups:
                for index,group in enumerate(user.groups):
                    print('%s.\t%s(%s)' % (index,group.name,len(group.bind_hosts)))

            #提示用户输入，选择组
            choice = input('[%s]: ' % user.username).strip()
            if len(choice) == 0:continue
            if choice == 'z':
                print('---------- Group: ungrouped hosts ------------')
                for index,bind_host in enumerate(user.bind_hosts):
                    print('%s.\t%s@%s(%s)' % (index,
                                              bind_host.remote_user.username,
                                              bind_host.host.hostname,
                                              bind_host.host.ip_addr
                                              ))
                print('---------- End ----------')
                # 再次提示用户输入，选择未分组的主机
                while not exit_flag:
                    user_option = input('[(b)ack, (q)uit, select host to login]: ').strip()
                    if len(user_option) == 0: continue
                    if user_option == 'q': exit_flag = True
                    if user_option == 'b': break
                    if user_option.isdigit():
                        user_option = int(user_option)
                        if user_option < len(user.bind_hosts):
                            ssh_login.ssh_login(user,
                                                user.bind_hosts[user_option],
                                                session,
                                                log_recording)
                        else:
                            print('**** no this option ****')

            elif choice.isdigit():
                choice = int(choice)
                if choice < len(user.groups):
                    print('---------- Group: %s ------------' % user.groups[choice].name)
                    for index,bind_host in enumerate(user.groups[choice].bind_hosts):
                        print('%s.\t%s@%s(%s)' % (index,
                                                  bind_host.remote_user.username,
                                                  bind_host.host.hostname,
                                                  bind_host.host.ip_addr))
                    print('---------- End ----------')
                    #再次提示用户输入，选择组中的主机
                    while not exit_flag:
                        user_option = input('[(b)ack, (q)uit, select host to login]: ').strip()
                        if len(user_option) == 0:continue
                        if user_option == 'q': exit_flag = True
                        if user_option == 'b':break
                        if user_option.isdigit():
                            user_option = int(user_option)
                            # print('user_option',user_option)
                            # print(len(user.groups[choice].bind_hosts))
                            if user_option < len(user.groups[choice].bind_hosts):

                                ssh_login.ssh_login(user,
                                                    user.groups[choice].bind_hosts[user_option],
                                                    session,
                                                    log_recording)
                            else:
                                print('**** no this option1 ****')
                else:
                    print('**** no this option2 ****')

def stop_server(argvs):
    pass

def create_users(argvs):
    msg = 'the new users file'
    user_file = parse_argvs(argvs, msg)

    source = yaml_parser(user_file)
    if source:
        for key,val in source.items():
            obj = models.UserProfile(username=key,password=val.get('password'))
            if val.get('groups'):#多对多关系
                groups = common_filters.groups_filter(val)
                obj.groups = groups
            if val.get('bind_hosts'):#多对多关系
                bind_hosts = common_filters.bind_hosts_filter(val)
                obj.bind_hosts = bind_hosts
            session.add(obj)
        session.commit()

def create_groups(argvs):
    msg = 'the new groups file'
    group_file = parse_argvs(argvs, msg)
    source = yaml_parser(group_file)
    if source:
        for key,val in source.items():
            obj = models.Group(name=key)
            if val.get('bind_hosts'):#多对多关系
                bind_hosts = common_filters.bind_hosts_filter(val)
                obj.bind_hosts = bind_hosts
            if val.get('user_profiles'):#多对多关系
                user_profiles = common_filters.user_profiles_filter(val)
                obj.user_profiles = user_profiles
            session.add(obj)
        session.commit()

#主机可独立创建,其他表与它的关系是同过bind_host表建立的
def create_hosts(argvs):
    msg = 'the new hosts file'
    host_file = parse_argvs(argvs, msg)
    #print(host_file)
    source = yaml_parser(host_file)
    if source:
        for key,val in source.items():
            obj = models.Host(hostname=key,ip_addr=val.get('ip_addr'),port=val.get('port') or 22)
            session.add(obj)
        session.commit()

#它是主机和远程用户多对多关系的第三张表，它直接和组、堡垒机用户关联
# 这个关系比较特殊，因为其它多对多关系的第三张表都跟别的表没直接关系
def create_bindhosts(argvs):
    msg = 'the new bind_hosts file'
    bindhost_file = parse_argvs(argvs, msg)
    source = yaml_parser(bindhost_file)
    if source:
        for key,val in source.items():
            host_obj = session.query(models.Host).filter(models.Host.hostname==val.get('hostname')).first()
            assert host_obj
            for item in val['remote_users']:
                assert item.get('auth_type')
                if item.get('auth_type') == 'ssh-passwd':
                    remoteuser_obj = session.query(models.RemoteUser).filter(models.RemoteUser.username==item.get('username'),
                                                                             models.RemoteUser.password==item.get('password')).first()
                else:
                    remoteuser_obj = session.query(models.RemoteUser).filter(models.RemoteUser.username==item.get('username'),
                                                                             models.RemoteUser.auth_type==item.get('auth_type')).first()
                # print('>>>>',host_obj,remoteuser_obj)
                bindhost_obj = models.BindHost(host_id=host_obj.id,remote_user_id=remoteuser_obj.id)
                session.add(bindhost_obj)

                if source[key].get('groups'):
                    groups = common_filters.groups_filter(source[key])
                    bindhost_obj.groups = groups
                if source[key].get('user_profiles'):
                    user_profiles = common_filters.user_profiles_filter(source[key])
                    bindhost_obj.user_profiles = user_profiles

        session.commit()

#远程用户可独立创建,其他表与它的关系是同过bind_host表建立的
def create_remoteusers(argvs):
    msg = 'the new remote users file'
    remoteuser_file = parse_argvs(argvs, msg)
    source = yaml_parser(remoteuser_file)
    if source:
        for key,val in source.items():
            obj = models.RemoteUser(username=val.get('username'),auth_type=val.get('auth_type'),password=val.get('password'))
            session.add(obj)
        session.commit()

def syncdb(argvs):
    print('****Syncing database...****')
    models.Base.metadata.create_all(engine)