#!python3
#pip install the following:
#   configparser
#   influxdb
#   pyW215
import asyncio
import configparser
from pyW215.pyW215 import SmartPlug, ON, OFF
from influxdb import InfluxDBClient
import os
import random
import time
import math
import statistics


async def get_current_consumption(switch: configparser,
                                  q: asyncio.Queue) -> None:
    while True:
        start_time = time.time()
        smart_plug = SmartPlug(switch['ip'],
                               switch['pin'],
                               use_legacy_protocol=True)
        end_time = time.time()
        measurement_time = int(
            math.floor(statistics.mean([start_time, end_time])))
        await q.put((str(switch['mac']), str(smart_plug.current_consumption),
                     int(measurement_time)))
        if int(math.ceil(time.time())) < (measurement_time + 60):
            sleep_time = 60 - (measurement_time % 60)
            await asyncio.sleep(sleep_time)
            print(switch['mac'] + " sleeping for " + str(sleep_time))
    return


async def log_to_influxdb(q: asyncio.Queue) -> None:
    while True:
        await asyncio.sleep(random.choice([17, 19, 23]))
        mac, current_consumption, measurement_time = await q.get()
        print(str(mac) + " " + str(current_consumption) + " " + str(measurement_time))
    return


async def main():
    random.seed(444)

    switchcfg = configparser.ConfigParser()
    switchcfg.read('switches.cfg')

    q = asyncio.Queue()
    producers = [
        asyncio.create_task(get_current_consumption(switchcfg[switch], q))
        for switch in switchcfg.sections()
    ]
    consumers = [
        asyncio.create_task(log_to_influxdb(q))
        for switch in switchcfg.sections()
    ]

    await asyncio.gather(*producers)
    await q.join()
    for c in consumers:
        c.cancel()


asyncio.run(main())
