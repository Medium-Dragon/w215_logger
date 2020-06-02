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
        t1 = time.time()
        sp = SmartPlug(switch['ip'], switch['pin'], use_legacy_protocol=True)
        t2 = time.time()
        t = int(math.floor(statistics.mean([t1, t2])))
        await q.put((str(switch['mac']), str(sp.current_consumption), int(t)))
        if int(math.ceil(time.time())) < (t + 60):
            t = 60 - (t1 % 60)
            await asyncio.sleep(t)
            print(switch['mac'] + " sleeping for " + str(t))
    return


async def log_to_influxdb(q: asyncio.Queue) -> None:
    while True:
        await asyncio.sleep(random.choice([17, 19, 23]))
        mac, current_consumption, t = await q.get()
        print(str(mac) + " " + str(current_consumption) + " " + str(t))
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
