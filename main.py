import OWeather, modbusslave
import pandas as pd
import time
import threading

startflag = 0
# 启动modbus从站
modbusThread = threading.Thread(target=modbusslave.main)
modbusThread.start()
modbusThread.join(1)


# 获取需要查询的城市列表，及modbus地址
def getTarCityList():
    TCL = r'tarcitylist.csv'
    data = pd.read_csv(TCL, engine='python')
    data = data.dropna()
    TarCityList = {}
    for name, address in zip(data['地名'], data['地址']):
        TarCityList[name] = str(address)
    return TarCityList


# 获取所有的城市列表，及相应的天气预报代码
def getCityList():
    CL = r'citylist.csv'
    data = pd.read_csv(CL, engine='python')
    data = data.dropna()
    CityList = {}
    for name, code in zip(data['地名'], data['代码']):
        CityList[name] = code
    return CityList


# 写入实时天气的线程
def RT():
    for name in cities:
        cities[name].getRTData()
        cities[name].setRTData()
        time.sleep(2)


# 写入24小时天气的线程
def h24beforstart():
    for name in cities:
        cities[name].get24Data()
        cities[name].set24Data()
        time.sleep(2)


# 当零时刷新天气信息，再把天气信息写入log文件，以供备份
def h24zeroclock():
    for name in cities:
        cities[name].get24Data()
        time.sleep(2)
        cities[name].set24Data()


# 当本程序重启后，从log文件恢复当天的24小时天气数据
def restart():
    for name in cities:
        cities[name].getRTData()
        cities[name].setRTData()
        cities[name].get24Data()
        cities[name].set24Data()
        time.sleep(2)


# 按城市建立类
class City:
    def __init__(self, CityName, CityCode, slave):
        self.CityName = CityName
        self.CityCode = CityCode
        self.CitySlave = int(slave)

    def getRTData(self):
        self.CityRTWeather = OWeather.getRTWeather(self.CityCode)

    def get24Data(self):
        self.City24Weather = OWeather.get24Weather(self.CityCode)
        print(self.City24Weather)
        try:
            hour24temp = open('log\\%shour24temp.log' % (self.CityName), 'r')
            temp = hour24temp.readlines()
            temp = list(map(int, temp))
            hour24temp.close()
        except:
            temp = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            print('未能恢复24h数据')
        hourflag = self.City24Weather[0][0]
        i = 0
        if 0 <= hourflag < 24:
            while i < (24-hourflag):
                temp[0 + hourflag+i] = self.City24Weather[0][i]
                temp[24 + hourflag+i] = self.City24Weather[1][i]
                temp[48 + hourflag+i] = self.City24Weather[2][i]
                temp[72 + hourflag+i] = self.City24Weather[3][i]
                i += 1
        tempwrite = ''
        for item in temp:
            tempwrite = tempwrite + str(item) + '\n'
        hour24temp = open('log\\%shour24temp.log' % (self.CityName), 'w')
        hour24temp.write(tempwrite)
        hour24temp.close()

    def setRTData(self):
        modbusslave.setRTData(self.CityName, self.CitySlave, self.CityRTWeather)

    def set24Data(self):
        hour24temp = open('log\\%shour24temp.log' % (self.CityName), 'r')
        temp = hour24temp.readlines()
        sortout = [[], [], [], []]
        j = 0
        for item in sortout:
            i = 0
            while i < 24:
                item.append(int(temp[j]))
                i += 1
                j += 1
        hour24temp.close()
        modbusslave.set24Data(self.CityName, self.CitySlave, sortout)


# 获得需要查询的城市列表
TarCityList = getTarCityList()
CityList = getCityList()
cities = {}
# 将目标城市写入字典
for name in TarCityList:
    cities[name] = City(name, CityList[name], TarCityList[name])
restart()  # 重启程序后从log文件中恢复24小时数据

while True:
    # 每到31分8秒时刷新实时数据
    time_now1 = time.strftime("%M:%S", time.localtime())
    if time_now1 == "31:08":
        RTThread = threading.Thread(target=RT)
        RTThread.start()
        RTThread.join(1)

    # 24小时预报2小时更新
    # 每到0时50分10秒时刷新24小时数据
    time_now3 = time.strftime("%H:%M:%S", time.localtime())
    if time_now3 == "00:50:10":
        h24Thread = threading.Thread(target=h24zeroclock)
        h24Thread.start()
        h24Thread.join(1)

    # 每2小时40分10秒时刷新24小时数据
    checktime = ["06:40:10", "08:40:10", "10:40:10", "12:40:10", "14:40:10",
                 "16:40:10", "18:40:10", "20:40:10", ]
    if time_now3 in checktime:
        h24Thread = threading.Thread(target=h24beforstart)
        h24Thread.start()
        h24Thread.join(1)

    time.sleep(0.5)
