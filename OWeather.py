import json
import time
from datetime import datetime

import mysql.connector
import requests
from retrying import retry

LOCATION = '杭州'  # 所查询的位置，可以使用城市拼音、v3 ID、经纬度等


def checkDB(location):
    realtime = {'code': 0, "temperature": 0, "feels_like": 0, "pressure": 0, "humidity": 0, "visibility": 0,
                "wind_direction_degree": 0, "wind_speed": 0, "wind_scale": 0, "clouds": 0}
    fullday = {'code': 0, 'temperature': 0, 'humidity': 0}

    conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
    cur = conn.cursor()

    # 检查实时天气信息
    for key, value in realtime.items():
        sql = """SELECT value FROM realtime_info WHERE city='{0}' AND class='{1}' AND hour={2}
            """.format(location, key, -1)
        cur.execute(sql)
        isexcist = cur.fetchall()
        if len(isexcist):
            continue
        else:
            sql = """INSERT INTO realtime_info ( city,class,hour,value) VALUES ('{0}','{1}',{2},{3});
                """.format(location, key, -1, value)
            cur.execute(sql)

    # 检查全天天气信息
    for i in range(24):
        for key, value in fullday.items():
            sql = """SELECT value FROM realtime_info WHERE city='{0}' AND class='{1}' AND hour={2}
                """.format(location, key, i)
            cur.execute(sql)
            isexcist = cur.fetchall()
            if len(isexcist):
                continue
            else:
                sql = """INSERT INTO realtime_info ( city,class,hour,value) VALUES ('{0}','{1}',{2},{3});
                    """.format(location, key, i, value)
                cur.execute(sql)

    conn.commit()
    conn.close()


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
    else:
        result = {'code': int(float(nowtemp["code"])), "temperature": int(float(nowtemp["temperature"])),
                  "feels_like": int(float(nowtemp["feels_like"])), "pressure": int(float(nowtemp["pressure"])),
                  "humidity": int(float(nowtemp["humidity"])), "visibility": int(float(nowtemp["visibility"])),
                  "wind_direction_degree": int(float(nowtemp["wind_direction_degree"])),
                  "wind_speed": int(float(nowtemp["wind_speed"])), "wind_scale": int(float(nowtemp["wind_scale"])),
                  "clouds": int(float(nowtemp["clouds"]))}

        conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
        cur = conn.cursor()
        for key, value in result.items():
            sql = ''' UPDATE realtime_info SET value={3} WHERE city="{0}" AND class="{1}" AND hour={2}
                '''.format(location, key, -1, value)
            cur.execute(sql)
        conn.commit()
        conn.close()
        return result


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
    else:
        result = {}
        for item in hourstemp:
            timeformate = datetime.strptime(item["time"], "%Y-%m-%dT%H:%M:%S%z")
            loophour = int(datetime.strftime(timeformate, "%H"))
            nowhour = int(datetime.strftime(datetime.now(), "%H"))
            if nowhour > loophour:
                continue
            else:
                result[loophour] = {'code': item["code"], 'temperature': item["temperature"],
                                    "humidity": item["humidity"]}
        conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
        cur = conn.cursor()
        for hourkey, dickvalue in result.items():
            for key, value in dickvalue.items():
                sql = ''' UPDATE realtime_info SET value={3} WHERE city="{0}" AND class="{1}" AND hour={2}
                    '''.format(location, key, hourkey, value)
                cur.execute(sql)
        conn.commit()
        conn.close()
        return result


if __name__ == '__main__':
    checkDB(LOCATION)
    RTWeather = getRTWeather(LOCATION)
    print(RTWeather)
    Wea24 = get24Weather(LOCATION)
    print(Wea24)
