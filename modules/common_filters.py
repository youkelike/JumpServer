from modules import models
from modules.db_conn import engine,session
from modules.utils import print_err

def bind_hosts_filter(vals):
    print('**** bind_hosts> ', vals.get('bind_hosts'))
    #只是为了找出host表中是否有指定的主机名，直接找host表就行
    bind_hosts = session.query(models.BindHost).filter(models.Host.hostname.in_(vals.get('bind_hosts'))).all()
    if not bind_hosts:
        print_err('none of [%s] exists in bind_host table.' % vals.get('bind_hosts'),quit=True)
    else:
        return bind_hosts

def groups_filter(vals):
    print('**** groups> ', vals.get('groups'))
    groups = session.query(models.Group).filter(models.Group.name.in_(vals.get('groups'))).all()
    if not groups:
        print_err('none of [%s] exists in group table.' % vals.get('groups'), quit=True)
    else:
        return groups

def user_profiles_filter(vals):
    print('**** user_profiles> ', vals.get('user_profiles'))
    user_profiles = session.query(models.UserProfile).filter(models.UserProfile.username.in_(vals.get('user_profiles'))).all()
    if not user_profiles:
        print_err('none of [%s] exists in user_profile table.' % vals.get('user_profiles'),quit=True)
    else:
        return user_profiles