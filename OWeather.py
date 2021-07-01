import requests
import re
from retrying import retry
import time
import json
import datetime

LOCATION = 'WTMKQ069CCJ7'  # 所查询的位置，可以使用城市拼音、v3 ID、经纬度等


# 获取实时天气
@retry(stop_max_attempt_number=5, wait_fixed=1000, stop_max_delay=10000)  # 如果API出错，将重试
def getRTWeather(location):
    KEY = 'S9dZ3n9ixsyqBuwfQ'  # API key
    API = 'https://api.seniverse.com/v3/weather/now.json'  # API URL，可替换为其他 URL
    UNIT = 'c'  # 单位
    LANGUAGE = 'zh-Hans'  # 查询结果的返回语言
    result = requests.get(API, params={
        'key': KEY,
        'location': location,
        'language': LANGUAGE,
        'unit': UNIT
    }, timeout=4)
    jsontemp = json.loads(result.text)
    nowtemp = jsontemp["results"][0]["now"]
    errorflag = result.text.find("status_code")
    if errorflag > -1:
        error = open('error.log', mode='a')
        localtime = time.asctime(time.localtime(time.time()))
        error.write(localtime + '\n' + result.text + '\n\n')
        error.close()
        raise Exception('APIerror')
    else:

        try:
            weanumnow = float(nowtemp["code"])
            weatemnow = float(nowtemp["temperature"])
            weafeelslike = float(nowtemp["feels_like"])
            weapressure = float(nowtemp["pressure"])
            weahumidity = float(nowtemp["humidity"])
            weavisibility = float(nowtemp["visibility"])
            weawind_direction_degree = float(nowtemp["wind_direction_degree"])
            weawind_speed = float(nowtemp["wind_speed"])
            weawind_scale = float(nowtemp["wind_scale"])
            weaclouds = float(nowtemp["clouds"])
            x = [int(weanumnow), int(weatemnow), int(weafeelslike), int(weapressure),
                 int(weahumidity), int(weavisibility), int(weawind_direction_degree),
                 int(weawind_speed), int(weawind_scale), int(weaclouds)]

        except:

            x = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    return x


# 获取24小时天气
@retry(stop_max_attempt_number=5, wait_fixed=1000, stop_max_delay=10000)  # 如果API出错，将重试
def get24Weather(location):
    KEY = 'S9dZ3n9ixsyqBuwfQ'  # API key
    API = 'https://api.seniverse.com/v3/weather/hourly.json'  # API URL，可替换为其他 URL
    UNIT = 'c'  # 单位
    LANGUAGE = 'zh-Hans'  # 查询结果的返回语言
    result = requests.get(API, params={
        'key': KEY,
        'location': location,
        'language': LANGUAGE,
        'unit': UNIT
    }, timeout=4)
    get24temp = json.loads(result.text)
    hourstemp = get24temp["results"][0]["hourly"]
    errorflag = result.text.find("status_code")
    if errorflag > -1:
        error = open('log\\error.log', mode='a')
        localtime = time.asctime(time.localtime(time.time()))
        error.write(localtime + '\n' + result.text + '\n\n')
        error.close()
        raise Exception('APIerror')
    else:
        # 解析时间点
        WeaHour = []
        for item in hourstemp:
            timeformate = datetime.datetime.strptime(item["time"], "%Y-%m-%dT%H:%M:%S%z")
            WeaHour.append(int(datetime.datetime.strftime(timeformate, "%H")))

        # 解析逐小时天气
        WeaNum = []
        for item in hourstemp:
            WeaNum.append(int(item["code"]))

        # 解析逐小时温度
        WeaTem = []
        for item in hourstemp:
            WeaTem.append(int(item["temperature"]))

        # 解析逐小时湿度
        WeaHum = []
        for item in hourstemp:
            WeaHum.append(int(item["humidity"]))
    return WeaHour, WeaNum, WeaTem, WeaHum


if __name__ == '__main__':
    RTWeather = getRTWeather(LOCATION)
    print(RTWeather)
    Wea24 = get24Weather(LOCATION)
    print(Wea24)
