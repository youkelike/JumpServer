from config import settings
import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError as ex:
    from yaml import Loader,Dumper

def print_err(msg,quit=False):
    output = '****Error: %s****' % msg
    if quit:
        exit(output)
    else:
        print(output)

def yaml_parser(yml_filename):
    try:
        yaml_file = open(yml_filename, 'r')
        data = yaml.load(yaml_file)
        return data
    except Exception as ex:
        print(ex)