#!python3
#configparser
#influxdb
#pyW215
import asyncio
import configparser
from pyW215.pyW215 import SmartPlug, ON, OFF
from influxdb import InfluxDBClient
import itertools as it
import os
import random
import time

async def get_current_consumption(switch: configparser, q: asyncio.Queue) -> None:
    while True:
        t = time.time()
        sp = SmartPlug(switch['ip'], switch['pin'],use_legacy_protocol=True)
        await q.put((switch['mac'], sp.current_consumption, t))
        if time.time() < (t + 60.0 ): 
            await asyncio.sleep(60.0 - (t % 60) )
            print (switch['mac'] + " sleeping for " + str(60.0 - (t % 60) ))
    return

async def log_to_influxdb( q: asyncio.Queue ) -> None:
    while True:
        await asyncio.sleep(random.choice([2, 3, 5, 7, 11, 13, 17, 19, 23]))
        mac, current_consumption, t = await q.get()
        print(str(mac) + " " + str(current_consumption) + " " + str(t))
    return

async def main():
    random.seed(444)

    switchcfg = configparser.ConfigParser()
    switchcfg.read('switches.cfg')

    q = asyncio.Queue()
    producers = [asyncio.create_task( get_current_consumption(switchcfg[switch], q) ) for switch in switchcfg.sections() ] 
    consumers = [asyncio.create_task( log_to_influxdb( q ) ) for switch in switchcfg.sections() ]

    await asyncio.gather(*producers)
    await q.join()
    for c in consumers:
        c.cancel()

asyncio.run(main())

