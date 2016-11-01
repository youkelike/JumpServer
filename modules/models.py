from sqlalchemy import create_engine,Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,ForeignKey,UniqueConstraint,UnicodeText,DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import or_,and_
from sqlalchemy import func
from sqlalchemy_utils import ChoiceType,PasswordType

Base = declarative_base()

#多对多关系中的第三张表用对象的方式创建
BindHost2Group = Table('bindhost_2_group',Base.metadata,
                       Column('bind_host_id',ForeignKey('bind_host.id'),primary_key=True),
                       Column('group_id',ForeignKey('groups.id'),primary_key=True))
BindHost2UserProfile = Table('bindhost_2_userprofile',Base.metadata,
                             Column('bind_host_id',ForeignKey('bind_host.id'),primary_key=True),
                             Column('user_profile_id',ForeignKey('user_profile.id'),primary_key=True))
Group2UserProfile = Table('group_2_userprofile',Base.metadata,
                          Column('group_id',ForeignKey('groups.id'),primary_key=True),
                          Column('user_profile_id',ForeignKey('user_profile.id'),primary_key=True))


class UserProfile(Base):
    __tablename__ = 'user_profile'
    id = Column(Integer,primary_key=True,autoincrement=True)
    username = Column(String(32),unique=True,nullable=False)
    password = Column(String(128),nullable=False)
    #堡垒机用户与组是多对多的关系
    groups = relationship('Group',secondary=Group2UserProfile,backref='user_profiles')
    #堡垒机用户与主机用户是多对多的关系
    bind_hosts = relationship('BindHost',secondary=BindHost2UserProfile,backref='user_profiles')
    #堡垒机用户与日志是一对多的关系
    audit_logs = relationship('AuditLog',backref='user_profile')

    def __repr__(self):
        return '<UserProfile(id=%s, username=%s)>' % (self.id,self.username)

class RemoteUser(Base):
    __tablename__ = 'remote_user'
    AuthTypes = [
        (u'ssh-passwd',u'SSH/Passwd'),
        (u'ssh-key',u'SSH/KEY')
    ]
    id = Column(Integer,primary_key=True,autoincrement=True)
    auth_type = Column(ChoiceType(AuthTypes))
    username = Column(String(64),nullable=False)
    password = Column(String(255))
    #远程用户和主机用户是一对多的关系
    bind_host = relationship('BindHost',backref='remote_user')

    __table_args_ = (UniqueConstraint('auth_type','username','password',name='_user_password_uc'),)

    def __repr__(self):
        return '<RemoteUser(id=%s, auth_type=%s, username=%s)>' % (self.id,self.auth_type,self.username)

class Host(Base):
    __tablename__ = 'host'
    id = Column(Integer,autoincrement=True,primary_key=True)
    hostname = Column(String(64),unique=True,nullable=False)
    ip_addr = Column(String(128),unique=True,nullable=False)
    port = Column(Integer,default=22)
    #主机与主机用户是多对多的关系
    bind_hosts = relationship('BindHost',backref='host')

    def __repr__(self):
        return '<Host(id=%s, hostname=%s, ip_addr=%s, port=%s)>' % (self.id,self.hostname,self.ip_addr,self.port)

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer,primary_key=True,autoincrement=True)
    name = Column(String(64),unique=True,nullable=False)
    #组与主机用户是多对多的关系
    bind_hosts = relationship('BindHost',secondary=BindHost2Group,backref='groups')
    #组与堡垒机用户是多对多的关系,在UserProfile中已经定义backref,就不用在这里重复定义关系了

    def __repr__(self):
        return '<Group(id=%s, name=%s)>' % (self.id,self.name)

class BindHost(Base):
    __tablename__ = 'bind_host'
    id = Column(Integer,primary_key=True,autoincrement=True)
    #与主机是多对一的关系，建立外键，多的一方就不用再建立关系了(在另一边设置backref)
    host_id = Column(Integer,ForeignKey('host.id'))
    #与远程用户是多对一的关系，建立外键，多的一方就不用再建立关系了(在另一边设置backref)
    remote_user_id = Column(Integer,ForeignKey('remote_user.id'))

    #与组还有多对多的关系，但在Group中已经定义backref，这里不用重复定义关系
    #与堡垒机用户还有多对多的关系，但在UserProfile中已经定义backref，这里不用重复定义关系

    #与日志是一对多的关系
    audit_logs = relationship('AuditLog',backref='bind_host')

    __table_args_ = (UniqueConstraint('host_id','remote_user_id',name='_host_and_removeuser_uc'),)

    def __repr__(self):
        return '<BindHost(id=%s, host_id=%s, remote_user_id=%s)>' % (self.id,self.host_id,self.remote_user_id)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer,autoincrement=True,primary_key=True)
    # 与堡垒机用户是多对一的关系，建立外键，多的一方就不用再建立关系了(在另一边设置backref)
    user_id = Column(Integer,ForeignKey('user_profile.id'))
    # 与主机用户是多对一的关系，建立外键，多的一方就不用再建立关系了(在另一边设置backref)
    bind_host_id = Column(Integer,ForeignKey('bind_host.id'))
    action_choice = [
        (u'cmd',u'CMD'),
        (u'login',u'Login'),
        (u'logout',u'Logout'),
        (u'getfile',u'GetFile'),
        (u'sendfile',u'SendFile')
    ]
    action_type = Column(ChoiceType(action_choice))
    cmd = Column(String(255))
    date = Column(DateTime)



