#from datetime import datetime
#import sys
#import yaml
#from netmiko import ConnectHandler
#from netmiko.ssh_exception import *
#
#def ly(filename):
#   with open(filename) as _:
#       return yaml.load(_)
#from glapp import *

def run_commands(teststr, mylabel):
    print("str = ",teststr)
    print("running super().testMethod(output)")
    output = "myoutput!"
    mylabel.configure(text=teststr)
    return
