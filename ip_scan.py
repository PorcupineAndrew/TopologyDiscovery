#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : ip asset scanning based on masscan & nmap
# * Last change   : 20:04:44 2020-12-19
# * Author        : Yihao Chen
# * Email         : chenyiha17@mails.tsinghua.edu.cn
# * License       : www.opensource.org/licenses/bsd-license.php
# **********************************************************************

import re
import subprocess
import ipaddress as ipa

def masscan(prefix):
    cmd = ["masscan", str(prefix), "--rate", "10000", "-p80"]
    output = subprocess.run(cmd, stdout=subprocess.PIPE, timeout=60)
    ips = []
    for l in output.stdout.decode().strip().split("\n"):
        try:
            items = l.strip().split()
            if items[0] != "Discovered":
                continue
            ipa.IPv4Address(items[-1])
            ips.append(items[-1])
        except Exception as e:
            print(e)
            continue
    return ips


def nmap(ip_address):
    rx = re.compile(r"^([a-zA-Z0-9_ ]+):(.+)$")
    ret = {"ip": str(ip_address)}

    def parse_namp_result(line):
        result = rx.match(line.strip())
        if result:
            k = result.group(1).strip()
            v = result.group(2).strip()
            if not k or not v: return
            if k in ret: ret[k] += v
            else: ret[k] = v

    cmd = ["nmap", "-nFA", str(ip_address)]
    try:
        output = subprocess.run(cmd, stdout=subprocess.PIPE, timeout=120)
        paras = output.stdout.decode().strip().split("\n\n")
        for l in paras[0].split("\n")[3:]: parse_namp_result(l)
    except Exception as e:
        print(e)
    return ret
