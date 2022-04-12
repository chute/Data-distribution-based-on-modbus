import threading
from datetime import datetime
import logging
import pandas as pd
import mysql.connector
import schedule
from time import sleep

import OWeather
import modbusslave

# 目标城市列表
city_list = {}
logging.basicConfig(filename='main.log', filemode='a', level=logging.INFO, format='%(asctime)s %(message)s')


# 从数据库读取城市列表
def get_target_cities():
    global city_list
    conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
    cur = conn.cursor()
    sql = "SELECT * FROM city_config"
    cur.execute(sql)
    allfetch = cur.fetchall()
    city_list = dict(allfetch)
    conn.close()
    logging.info('Get city list: %s' % allfetch)


# 将数据从实时表转储到历史表
def move_rt_data(cityname):
    conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
    cur = conn.cursor()
    sql = "SELECT class, value FROM realtime_info WHERE city='{}' AND hour=-1".format(cityname)
    cur.execute(sql)
    allfetch = cur.fetchall()
    logging.info('move_rt_data: get data length: %s' % len(allfetch))
    nowdtstamp = datetime.now()
    nowhour = datetime.strftime(nowdtstamp, '%H')
    for item in allfetch:
        sql = """INSERT INTO historyrt_info (city, class, hour, value, dtstamp) VALUES ('{}', '{}', {}, {}, '{}')
            """.format(cityname, item[0], nowhour, item[1], nowdtstamp)
        cur.execute(sql)
    receive_rows = conn.commit()
    conn.close()
    logging.info('move_rt_data: put data successful: %s rows' % receive_rows)


# 将数据从实时表转储到历史表
def move_24_data(cityname):
    conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
    cur = conn.cursor()
    for i in range(24):
        sql = "SELECT class, value FROM realtime_info WHERE city='{}' AND hour={}".format(cityname, i)
        cur.execute(sql)
        allfetch = cur.fetchall()
        logging.info('move_24_data: get data length: %s' % len(allfetch))
        nowdtstamp = datetime.now()
        for item in allfetch:
            sql = """INSERT INTO history24_info (city, class, hour, value, dtstamp) VALUES ('{}', '{}', {}, {}, '{}')
                    """.format(cityname, item[0], i, item[1], nowdtstamp)
            cur.execute(sql)
    receive_rows = conn.commit()
    conn.close()
    logging.info('move_24_data: put data successful: %s rows' % receive_rows)


# 将数据从实时表写入从站
def move_rt_slave(cityid, cityname):
    conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
    cur = conn.cursor()
    sql = "SELECT class, value FROM realtime_info WHERE city='{}' AND hour=-1".format(cityname)
    cur.execute(sql)
    allfetch = cur.fetchall()
    logging.info('move_rt_slave: get data length: %s' % len(allfetch))
    conn.close()
    info = dict(allfetch)
    infolist = [info['code'],
                info['temperature'],
                info['feels_like'],
                info['pressure'],
                info['humidity'],
                info['visibility'],
                info['wind_direction_degree'],
                info['wind_speed'],
                info['wind_scale'],
                info['clouds']]
    unit16list = modbusslave.setRTData(cityid, infolist)
    logging.info('move_rt_data: put slave successful: %s' % unit16list)


# 将数据从实时表写入从站
def move_24_slave(cityid, cityname):
    conn = mysql.connector.connect(host='localhost', user='root', passwd='dcny123', database="weather")
    cur = conn.cursor()
    sql = "SELECT class, hour, value FROM realtime_info WHERE city='{}' AND hour>-1".format(cityname)
    cur.execute(sql)
    allfetch = cur.fetchall()
    logging.info('move_24_slave: get data length: %s' % len(allfetch))
    info = {}
    for i in range(24):
        info[i] = {}
    # info的格式：{小时:{数据名称:数据值}}，如：{1:{'code':0}}
    for item in allfetch:
        info[item[1]][item[0]] = item[2]

    result = [[], [], [], []]
    for i in range(24):
        result[0].append(i)
        result[1].append(info[i]['code'])
        result[2].append(info[i]['temperature'])
        result[3].append(info[i]['humidity'])
    modbusslave.set24Data(cityid, result)
    logging.info('move_24_slave: put data successful')


# 获取所有的城市列表，及相应的天气预报代码
def getCityList():
    CL = r'citylist.csv'
    data = pd.read_csv(CL, engine='python')
    data = data.dropna()
    CityList = {}
    for name, code in zip(data['地名'], data['代码']):
        CityList[name] = code
    return CityList


def check_thread_alive(thread: threading.Thread):
    if not thread.is_alive():
        thread.start()
        logging.info('mudbusThread restart successful')


def main():
    for key, value in city_list.items():
        schedule.every(2).hours.do(OWeather.getRTWeather, location=value)
        schedule.every(2).hours.do(OWeather.get24Weather, location=value)
        schedule.every(2).hours.do(move_rt_data, cityname=value)
        schedule.every(2).hours.do(move_rt_slave, cityid=key, cityname=value)
        schedule.every(2).hours.do(move_24_slave, cityid=key, cityname=value)
        schedule.every().day.at("22:30").do(move_24_data, cityname=value)
    schedule.run_all()
    schedule.every(2).minutes.do(check_thread_alive, thread=modbusThread)
    logging.info('schedule start successful')
    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == "__main__":
    get_target_cities()  # 读取所有目标城市
    for value in city_list.values():
        OWeather.checkDB(value)  # 检查目标城市是否有相应的实时表
    citycounts = len(city_list)
    modbusThread = threading.Thread(target=modbusslave.main, args=(citycounts,))
    modbusThread.start()
    logging.info('mudbusThread start successful')

    main()
