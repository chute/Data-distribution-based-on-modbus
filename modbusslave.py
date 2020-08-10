import sys
import time
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp

# 设定默认值
CityName = '错误'
SlaveNum = 0
SlaveData = [[0],[0],[0],[0]]

hour=num=tem =hum = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
slaveupdate=[]

# 写入实时数据
def setRTData(Name, Slave, Data):
    global CityName, SlaveNum, SlaveData,slaveupdate
    CityName = Name
    SlaveNum = Slave
    SlaveData = Data
    temp=(SlaveNum,)
    SlaveData=temp+SlaveData
    print(CityName, SlaveNum, SlaveData)
    slaveupdate[Slave-1].set_values(str(Slave), 0, SlaveData)
    RTlog=open('RT.log',mode='a')
    RTlog.write(str(CityName)+str(SlaveNum)+str(SlaveData)+'\n')
    RTlog.close()
# 写入24h数据
def set24Data(Name, Slave, Data):
    global CityName, SlaveNum, SlaveData,hour,num, tem, hum, slaveupdate
    CityName = Name
    SlaveNum = Slave
    SlaveData = Data
    for item in SlaveData:
        print(item)
    hourflag=SlaveData[0][0]

    hour = SlaveData[0][:24-hourflag]
    num=SlaveData[1][:24-hourflag]
    tem=SlaveData[2][:24-hourflag]
    hum=SlaveData[3][:24-hourflag]
    slaveupdate[Slave-1].set_values(str(Slave), 11+hourflag, hour)
    slaveupdate[Slave - 1].set_values(str(Slave), 35+hourflag, num)
    slaveupdate[Slave - 1].set_values(str(Slave), 59+hourflag, tem)
    slaveupdate[Slave - 1].set_values(str(Slave), 83+hourflag, hum)
    nummax = max(num)
    temmax = max(tem)
    temmin = min(tem)
    temavg = int(sum(tem)/len(tem))
    humavg = int(sum(hum)/len(hum))
    slaveupdate[Slave - 1].set_values(str(Slave), 3, [nummax,temmax,temmin,temavg,humavg])

    H24log=open('H24.log',mode='a')
    H24log.write(CityName+'\t'+str(SlaveNum)+'\t'+str(nummax)+'\t'+str(temmax)+'\t'\
                 +str(temmin)+'\t'+str(temavg)+'\t'+str(humavg)+'\n'+str(hour)+'\n'\
                 +str(num)+'\n'+str(tem)+'\n'+str(hum)+'\n\n')
    H24log.close()

# modbus主体
def main():
    global tem, hum, slaveupdate
    logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")

    try:
        # Create the server
        server = modbus_tcp.TcpServer()
        logger.info("running...")
        logger.info("enter 'quit' for closing the server")

        server.start()
        slave = []
        slaveupdate = []
        i = 1
        while i < 25:
            slave.append(i)
            slaveupdate.append(i)
            slave[i - 1] = server.add_slave(i)
            slave[i - 1].add_block(str(i), cst.HOLDING_REGISTERS, 0, 200)
            slaveupdate[i - 1] = server.get_slave(i)
            i += 1

        '''
        slave1 = server.add_slave(1)
        slave2 = server.add_slave(2)
        slave1.add_block('1', cst.HOLDING_REGISTERS, 0, 800)
        slave2.add_block('2', cst.HOLDING_REGISTERS, 0, 200)
        
        slave0 = server.get_slave(1)
        '''
        while True:
            cmd = sys.stdin.readline()
            args = cmd.split(' ')

            print('flag')
            print(tem)
            if cmd.find('quit') == 0:
                sys.stdout.write('bye-bye\r\n')
                break

            elif args[0] == 'add_slave':
                slave_id = int(args[1])
                server.add_slave(slave_id)
                sys.stdout.write('done: slave %d added\r\n' % slave_id)

            elif args[0] == 'add_block':
                slave_id = int(args[1])
                name = args[2]
                block_type = int(args[3])
                starting_address = int(args[4])
                length = int(args[5])
                slave = server.get_slave(slave_id)
                slave.add_block(name, block_type, starting_address, length)
                sys.stdout.write('done: block %s added\r\n' % name)

            elif args[0] == 'set_values':
                slave_id = int(args[1])
                name = args[2]
                address = int(args[3])
                values = []
                for val in args[4:]:
                    values.append(int(val))
                slave = server.get_slave(slave_id)
                slave.set_values(name, address, values)
                values = slave.get_values(name, address, len(values))
                sys.stdout.write('done: values written: %s\r\n' % str(values))

            elif args[0] == 'get_values':
                slave_id = int(args[1])
                name = args[2]
                address = int(args[3])
                length = int(args[4])
                slave = server.get_slave(slave_id)
                values = slave.get_values(name, address, length)
                sys.stdout.write('done: values read: %s\r\n' % str(values))

            else:
                sys.stdout.write("unknown command %s\r\n" % args[0])
            time.sleep(0.5)
    finally:
        server.stop()


if __name__ == "__main__":
    main()
