from modbus_tk import modbus_tcp
import os
from time import sleep

path='python main.py'
m=os.system(path)
master = modbus_tcp.TcpMaster(host='127.0.0.1',port=1004,timeout_in_sec=5.0)
while True:
    sleep(60)
    try:
        try:
            master.execute(1, 3, 0, 3)
        except ConnectionRefusedError:
            m = os.system(path)
    except:
        master = modbus_tcp.TcpMaster(host='127.0.0.1', port=1004, timeout_in_sec=5.0)
