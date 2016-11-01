from sqlalchemy import create_engine,and_,or_,func,Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,DateTime,String,ForeignKey,UniqueConstraint
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy_utils import ChoiceType

Base = declarative_base()#生成基类

#把账户与组关联起来，比把主机与组关联起来有更精细的控制
#账户与组是多对多的关系，所以建立第三张表
HostUser2Group = Table('host_user_group',Base.metadata,
                       Column('host_user_id',ForeignKey('host_user.id'),primary_key=True),
                       Column('group_id',ForeignKey('groups.id'),primary_key=True)
                       )
#堡垒机用户和组也是多对多的关系
UserProfile2Croup = Table('user_profile_group',Base.metadata,
                          Column('user_profile_id',ForeignKey('user_profile.id'),primary_key=True),
                          Column('group_id', ForeignKey('groups.id'), primary_key=True))
#堡垒机用户还能与主机用户直接关联，也是多对多的关系
UserProfile2HostUser = Table('user_profile_host_user',Base.metadata,
                             Column('user_profile_id',ForeignKey('user_profile.id'),primary_key=True),
                             Column('host_user_id',ForeignKey('host_user.id'),primary_key=True))

class Host(Base):
    __tablename__ = 'hosts'
    id = Column(Integer,primary_key=True,autoincrement=True)
    hostname = Column(String(64),unique=True,nullable=False)
    ip_addr = Column(String(128),unique=True,nullable=False)
    port = Column(Integer,default=22)

    def __repr__(self):#格式化输出方法
        return '<id=%s, hostname=%s, ip_addr=%s>' % (self.id,
                                                     self.hostname,
                                                     self.ip_addr)

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer,primary_key=True)
    name = Column(String(64),unique=True,nullable=False)

    def __repr__(self):#格式化输出方法
        return '<id=%s, name=%s>' % (self.id,self.name)

class UserProfile(Base):
    __tablename__ = 'user_profile'
    id = Column(Integer,primary_key=True)
    username = Column(String(64),nullable=False,unique=True)
    password = Column(String(255),nullable=False)

    # 多对多中，与组建立关联,方便查询
    groups = relationship('Group',
                          secondary=HostUser2Group,
                          backref='user_list')#从组对象里调这个字段可以找到这张表
    # 多对多中，与主机用户建立关联，方便查询
    host_list = relationship('HostUser',
                              secondary=UserProfile2HostUser,
                              backref='user_list')#从组对象里调这个字段可以找到这张表

    def __repr__(self):
        return '<id=%s, name=%s>' % (self.id,self.username)

#主机上的各种账户密码表，一个主机上可以有多个账号，同样的账号也可以在多台主机上
#但同一台主机上的任意两个账号名不能重复
class HostUser(Base):
    __tablename__ = 'host_user'
    id = Column(Integer, primary_key=True)
    #与主机建立外键
    host_id = Column(Integer,ForeignKey('hosts.id'))
    username = Column(String(64), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    #用户登录方式
    AuthTypes = [
        (u'ssh-passwd',u'SSH/Password'),
        (u'ssh-key',u'SSH/KEY')
    ]
    auth_type = Column(ChoiceType(AuthTypes))

    #与组建立关联,方便查询
    groups = relationship('Group',
                          secondary=HostUser2Group,
                          backref='host_list')#从组对象里调这个字段可以找到这张表
    #唯一约束
    __table_args__ = (UniqueConstraint('host_id','username',name='_host_username_uc'),)

    def __repr__(self):
        return '<host_id=%s, username=%s, password=%s>' % (self.host_id,self.username,self.password)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer,primary_key=True)
    user_profile_id = Column(Integer,ForeignKey('user_profile.id'))
    host_user_id = Column(Integer,ForeignKey('host_user.id'))
    action_choices = [#这个不好用
        (0,'CMD'),
        (1,'Login'),
        (2,'Logout'),
        (3,'GetFile'),
        (4,'SendFile'),
        (5,'Exception')
    ]
    action_choices2 = [
        (u'cmd',u'CMD'),
        (u'login',u'Login'),
        (u'logout',u'Logout'),
    ]
    action_type = Column(ChoiceType(action_choices2))
    cmd = Column(String(255))
    date = Column(DateTime)
    user_profile = relationship('UserProfile')
    host_user = relationship('HostUser')

engine = create_engine('mysql+pymysql://root:111@localhost/jumpserver',echo=True,max_overflow=5)
Base.metadata.create_all(engine)