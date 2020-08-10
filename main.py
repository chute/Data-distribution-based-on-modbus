import OWeather,modbusslave
import pandas as pd
import time
import threading
from retrying import retry


startflag=0
#启动modbus从站
modbusThread=threading.Thread(target=modbusslave.main)
modbusThread.start()
modbusThread.join(1)
#获取需要查询的城市列表，及modbus地址
def getTarCityList():
    TCL=r'tarcitylist.csv'
    data=pd.read_csv(TCL, engine='python')
    data = data.dropna()
    TarCityList={}
    for name,address in zip(data['地名'],data['地址']):
        TarCityList[name]=str(address)
    return TarCityList
#获取所有的城市列表，及相应的天气预报代码
def getCityList():
    CL = r'citylist.csv'
    data = pd.read_csv(CL, engine='python')
    data = data.dropna()
    CityList={}
    for name,code in zip(data['地名'],data['代码']):
        CityList[name]=code
    return CityList

#写入实时天气的线程
def RT():
    for name in cities:
        cities[name].getRTData()
        cities[name].setRTData()
        time.sleep(2)

#写入24小时天气的线程
def h24():
    for name in cities:
        cities[name].get24Data()
        cities[name].set24Data()
        time.sleep(2)

#按城市建立类
class City:
    def __init__(self,CityName,CityCode,slave):
        self.CityName=CityName
        self.CityCode=CityCode
        self.CitySlave = int(slave)

    def getRTData(self):
        self.CityRTWeather = OWeather.getRTWeather(self.CityCode)

    def get24Data(self):
        self.City24Weather = OWeather.get24Weather(self.CityCode)

    def setRTData(self):
        modbusslave.setRTData(self.CityName, self.CitySlave, self.CityRTWeather)

    def set24Data(self):
        modbusslave.set24Data(self.CityName, self.CitySlave, self.City24Weather)

TarCityList=getTarCityList()
CityList=getCityList()
cities={}
#将目标城市写入字典
for name in TarCityList:
    cities[name]=City(name,CityList[name],TarCityList[name])

while True:
    time_now = time.strftime("%H:%M:%S", time.localtime())
    if (time_now == "0:10:10") | (startflag < 2):
        RTThread = threading.Thread(target=RT)
        RTThread.start()
        startflag+=1
        RTThread.join(1)
    time_now = time.strftime("%M:%S", time.localtime())
    if (time_now == "8:8") | (startflag < 2):
        h24Thread = threading.Thread(target=h24)
        h24Thread.start()
        startflag += 1
        h24Thread.join(1)
    time.sleep(0.5)







