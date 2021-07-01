import sys
import time
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
import ctypes
from copy import deepcopy

# 设定默认值
CityName = '错误'
SlaveNum = 0
SlaveData = [[0], [0], [0], [0]]
checktime = ["06:40", "08:40", "10:40", "12:40", "14:40",
             "16:40", "18:40", "20:40", ]
hour = num = tem = hum = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
slaveupdate = []


# 写入实时数据
def setRTData(Name, Slave, Data):
    global CityName, SlaveNum, SlaveData, slaveupdate
    CityName = Name
    SlaveNum = Slave
    SlaveData = Data
    SlaveData.insert(0, SlaveNum)
    print(CityName, SlaveNum, SlaveData)
    RTlog = open('log\\RT.log', mode='a')
    RTlog.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n' + str(CityName) + str(SlaveNum) + str(
        SlaveData) + '\n')
    RTlog.close()
    i = 0
    while i < len(SlaveData):
        SlaveData[i] = ctypes.c_uint16(SlaveData[i]).value
        i = i + 1
    slaveupdate[Slave - 1].set_values(str(Slave), 0, SlaveData)


# 写入24h数据
def set24Data(Name, Slave, Data):
    global CityName, SlaveNum, SlaveData, hour, num, tem, hum, slaveupdate, checktime
    CityName = Name
    SlaveNum = Slave
    SlaveData = Data
    for item in SlaveData:
        print(item)
    if SlaveData[0][0] == 0:
        hour = SlaveData[0]
        num = SlaveData[1]
        tem = SlaveData[2]
        hum = SlaveData[3]
    nummax = max(num)
    temmax = max(tem)
    temmin = min(tem)
    temavg = int(sum(tem) / len(tem))
    humavg = int(sum(hum) / len(hum))
    temavgday = int(sum(tem[8:16]) / 8)
    i = 0
    tem16 = []
    while i < len(tem):
        tem16.append(ctypes.c_uint16(tem[i]).value)
        i = i + 1
    temmax16 = ctypes.c_uint16(temmax).value
    temmin16 = ctypes.c_uint16(temmin).value
    temavg16 = ctypes.c_uint16(temavg).value
    temavgday16 = ctypes.c_uint16(temavgday).value

    slaveupdate[Slave - 1].set_values(str(Slave), 25, [nummax, temmax16, temmin16, temavg16, humavg, temavgday16])
    slaveupdate[Slave - 1].set_values(str(Slave), 35, num)
    slaveupdate[Slave - 1].set_values(str(Slave), 59, tem16)
    slaveupdate[Slave - 1].set_values(str(Slave), 83, hum)
    slaveupdate[Slave - 1].set_values(str(Slave), 107, hour)

    temAmplitude = temmax - temmin
    Yvaluemax = int(temmax + temAmplitude * 0.4)
    Yvaluemin = int(temmin - temAmplitude * 0.4)
    YAmplitude = Yvaluemax - Yvaluemin
    if YAmplitude == 0:
        YAmplitude = 1
    Ycoordinate = []
    for item in tem:
        Ycoordinate.append(int((item - Yvaluemin) / YAmplitude * 100))
    Yvaluemax16 = ctypes.c_uint16(Yvaluemax).value
    Yvaluemin16 = ctypes.c_uint16(Yvaluemin).value
    YAmplitude16 = ctypes.c_uint16(YAmplitude).value
    Ycoordinate16 = Ycoordinate
    i = 0
    while i < len(Ycoordinate):
        Ycoordinate16[i] = ctypes.c_uint16(Ycoordinate[i]).value
        i = i + 1
    slaveupdate[Slave - 1].set_values(str(Slave), 169, [Yvaluemax16, Yvaluemin16, YAmplitude16])
    slaveupdate[Slave - 1].set_values(str(Slave), 173, Ycoordinate16)
    H24log = open('log\\H24.log', mode='a')
    H24log.write(
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n' + CityName + '\t' + str(SlaveNum) + '\t' +
        str(nummax) + '\t' + str(temmax) + '\t' + str(temmin) + '\t' + str(temavg) + '\t' + str(humavg) + '\n' +
        str(temavgday) + '\n' + str(hour) + '\n' + str(num) + '\n' + str(tem) + '\n' + str(hum) + '\n\n')
    H24log.close()


# modbus主体
def main():
    global tem, hum, slaveupdate
    logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")

    try:
        # Create the server
        server = modbus_tcp.TcpServer(port=1004)
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
            slave[i - 1].add_block(str(i), cst.HOLDING_REGISTERS, 0, 1000)
            slaveupdate[i - 1] = server.get_slave(i)
            i += 1

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
