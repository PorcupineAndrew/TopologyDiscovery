#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : ip asset scanning for Tsinghua
# * Last change   : 20:06:29 2020-12-19
# * Author        : Yihao Chen
# * Email         : chenyiha17@mails.tsinghua.edu.cn
# * License       : www.opensource.org/licenses/bsd-license.php
# **********************************************************************

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from ip_scan import *
import json
import time
import ipaddress as ipa

def current_date():
    return time.strftime("%Y-%m-%d", time.localtime())

output_dir = Path(__file__).resolve().parent / "output" / "ip_asset" / current_date()
if not output_dir.exists(): print(f"create output dir: {output_dir}")
output_dir.mkdir(exist_ok=True, parents=True)

tsinghua_prefixes = list(map(ipa.IPv4Network, [
    "59.66.0.0/16",
    "101.5.0.0/16",
    "101.6.0.0/16",
    "118.229.0.0/19",
    "166.111.0.0/16",
    "183.172.0.0/15",
    "202.112.39.2/32",
    "219.223.168.0/21",
    "219.223.176.0/20",
]))

def scan_active_ip():
    ret = {}
    for p in tsinghua_prefixes:
        print(f"scan active ip for {p}")
        ips = masscan(p)
        print(f"{len(ips)}")
        ret[str(p)] = ips
    return ret

def scan_ip_detail(active_ip):
    detail_ip = {}
    for k, v in active_ip.items():
        print(f"scan detail for {k}")
        n_worker = min(len(v), 48)
        with ThreadPoolExecutor(max_workers=n_worker) as executor:
            details = executor.map(nmap, v)
        detail_ip[k] = list(details)
    return detail_ip

if __name__ == "__main__":
    active_ip = scan_active_ip()
    detail_ip = scan_ip_detail(active_ip)
    json.dump(detail_ip, open(output_dir / "detail_ip.json", "w"))
