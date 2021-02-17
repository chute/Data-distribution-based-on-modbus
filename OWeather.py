import requests
import re
from retrying import retry
import time

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
    errorflag = result.text.find("status_code")
    if errorflag > -1:
        error = open('error.log', mode='a')
        localtime = time.asctime(time.localtime(time.time()))
        error.write(localtime + '\n' + result.text + '\n\n')
        error.close()
        raise Exception('APIerror')
    else:

        try:
            weanumnow = re.search(r'"code":"[0-9-]+[."]', result.text)
            weanumnow = re.search(r'[0-9-]+', weanumnow.group())
            weatemnow = re.search(r'"temperature":"[0-9-]+[."]', result.text)
            weatemnow = re.search(r'[0-9-]+', weatemnow.group())
            weafeelslike = re.search(r'"feels_like":"[0-9-]+[."]', result.text)
            weafeelslike = re.search(r'[0-9-]+', weafeelslike.group())
            weapressure = re.search(r'"pressure":"[0-9-]+[."]', result.text)
            weapressure = re.search(r'[0-9-]+', weapressure.group())
            weahumidity = re.search(r'"humidity":"[0-9-]+[."]', result.text)
            weahumidity = re.search(r'[0-9-]+', weahumidity.group())
            weavisibility = re.search(r'"visibility":"[0-9-]+[."]', result.text)
            weavisibility = re.search(r'[0-9-]+', weavisibility.group())
            weawind_direction_degree = re.search(r'"wind_direction_degree":"[0-9-]+[."]', result.text)
            weawind_direction_degree = re.search(r'[0-9-]+', weawind_direction_degree.group())
            weawind_speed = re.search(r'"wind_speed":"[0-9-]+[."]', result.text)
            weawind_speed = re.search(r'[0-9-]+', weawind_speed.group())
            weawind_scale = re.search(r'"wind_scale":"[0-9-]+[."]', result.text)
            weawind_scale = re.search(r'[0-9-]+', weawind_scale.group())
            weaclouds = re.search(r'"clouds":"[0-9-]+[."]', result.text)
            weaclouds = re.search(r'[0-9-]+', weaclouds.group())
            x = [int(weanumnow.group()), int(weatemnow.group()), int(weafeelslike.group()), int(weapressure.group()), \
                 int(weahumidity.group()), int(weavisibility.group()), int(weawind_direction_degree.group()), \
                 int(weawind_speed.group()), int(weawind_scale.group()), int(weaclouds.group())]
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
    errorflag = result.text.find("status_code")
    if errorflag > -1:
        error = open('log\\error.log', mode='a')
        localtime = time.asctime(time.localtime(time.time()))
        error.write(localtime + '\n' + result.text + '\n\n')
        error.close()
        raise Exception('APIerror')
    else:
        # 解析时间点
        WeaHour24 = re.findall(r'"time":".*?",', result.text)
        WeaHour = []
        for item in WeaHour24:
            WeaHour.append(int((re.search(r'(?<=T)\d+', item)).group()))

        # 解析逐小时天气
        WeaNum24 = re.findall(r'"code":"[0-9-]+",', result.text)
        WeaNum = []
        for item in WeaNum24:
            WeaNum.append(int((re.search(r'[0-9-]+', item)).group()))

        # 解析逐小时温度
        WeaTem24 = re.findall(r'"temperature":"[0-9-]+",', result.text)
        WeaTem = []
        for item in WeaTem24:
            WeaTem.append(int((re.search(r'[0-9-]+', item)).group()))

        # 解析逐小时湿度
        WeaHum24 = re.findall(r'"humidity":"[0-9-]+",', result.text)
        WeaHum = []
        for item in WeaHum24:
            WeaHum.append(int((re.search(r'[0-9-]+', item)).group()))
    return WeaHour, WeaNum, WeaTem, WeaHum


if __name__ == '__main__':
    RTWeather = getRTWeather(LOCATION)
    print(RTWeather)
    Wea24 = get24Weather(LOCATION)
    print(Wea24)
