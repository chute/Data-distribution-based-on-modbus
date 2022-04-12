import ctypes
from time import sleep
import math
import logging
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp

slavegroup = []
logging.basicConfig(filename='modbus.log', filemode='a', level=logging.INFO, format='%(asctime)s %(message)s')


# 计算含湿量
def getf_d(t=8, rh=95):
    x = 18.5916 - 3991.11 / (t + 233.84)
    p = 2 / 15 * math.exp(x)
    rhp = 0.01 * rh * p
    f_d = 622 * rhp / (101.325 - rhp)
    return f_d


# 写入实时数据
def setRTData(slave, data):
    slave_data = data
    slave_data.insert(0, slave)  # 将从站号插入数据的第一位
    unit16list = []
    for item in slave_data:
        unit16list.append(ctypes.c_uint16(item).value)
    slavegroup[slave - 1].set_values(str(slave), 0, unit16list)
    return unit16list


# 写入24h数据
def set24Data(slave, data):
    hour = data[0]
    num = data[1]
    tem = data[2]
    hum = data[3]

    # 计算最大值等数据
    nummax = max(num)
    temmax = max(tem)
    temmin = min(tem)
    temavg = int(sum(tem) / len(tem))
    humavg = int(sum(hum) / len(hum))
    temavgday = int(sum(tem[8:16]) / 8)

    # 将可能为负的数据转为有符号数
    tem16 = []
    for item in tem:
        tem16.append(ctypes.c_uint16(item).value)
    temmax16 = ctypes.c_uint16(temmax).value
    temmin16 = ctypes.c_uint16(temmin).value
    temavg16 = ctypes.c_uint16(temavg).value
    temavgday16 = ctypes.c_uint16(temavgday).value
    # 计算含湿量
    f_d = []
    for i in range(len(tem)):
        f_d.append(int(getf_d(tem[i], hum[i])))

    # 向从站更新值
    slavegroup[slave - 1].set_values(str(slave), 25, [nummax, temmax16, temmin16, temavg16, humavg, temavgday16])
    slavegroup[slave - 1].set_values(str(slave), 35, num)
    slavegroup[slave - 1].set_values(str(slave), 59, tem16)
    slavegroup[slave - 1].set_values(str(slave), 83, hum)
    slavegroup[slave - 1].set_values(str(slave), 107, hour)
    slavegroup[slave - 1].set_values(str(slave), 155 - len(f_d), f_d)

    # 计算动态坐标轴
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
    Ycoordinate16 = []
    for item in Ycoordinate:
        Ycoordinate16.append(ctypes.c_uint16(item).value)

    # 向从站更新值
    slavegroup[slave - 1].set_values(str(slave), 169, [Yvaluemax16, Yvaluemin16, YAmplitude16])
    slavegroup[slave - 1].set_values(str(slave), 173, Ycoordinate16)


# modbus主体
def main(counts):
    server = modbus_tcp.TcpServer(port=1004)
    server.start()
    for i in range(counts):
        namenum = i + 1
        slavegroup.append(server.add_slave(namenum))
        slavegroup[i].add_block(str(namenum), cst.HOLDING_REGISTERS, 0, 1000)
        slavegroup[i] = server.get_slave(namenum)
    master = modbus_tcp.TcpMaster(host='127.0.0.1', port=1004, timeout_in_sec=5.0)
    while True:
        try:
            master.execute(1, cst.READ_HOLDING_REGISTERS, 100, 12)
            sleep(10)
        except IOError:
            logging.info('modbus IO error')
            exit()
        except Exception as e:
            logging.info('Exception %s' % e)
            exit()
        except:
            logging.info('unknown error')
            exit()


if __name__ == "__main__":
    main(1)
