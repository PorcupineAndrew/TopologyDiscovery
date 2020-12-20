#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : ip asset scanning for Tsinghua
# * Last change   : 14:45:52 2020-12-20
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

import matplotlib.pyplot as plt
import numpy as np

def current_date():
    return time.strftime("%Y-%m-%d", time.localtime())

# output_dir = Path(__file__).resolve().parent / "output" / "ip_asset" / current_date()
output_dir = Path(__file__).resolve().parent / "output" / "ip_asset" / "2020-12-19"
if not output_dir.exists(): print(f"create output dir: {output_dir}")
output_dir.mkdir(exist_ok=True, parents=True)

tsinghua_prefixes = list(map(ipa.IPv4Network, [
    "59.66.0.0/16",
    "101.5.0.0/16",
    "101.6.0.0/16",
    "118.229.0.0/19",
    "166.111.0.0/16",
    "183.172.0.0/15",
    # "202.112.39.2/32",
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
        n_worker = min(len(v), 256)
        with ThreadPoolExecutor(max_workers=n_worker) as executor:
            details = executor.map(nmap, v)
        detail_ip[k] = list(details)
    return detail_ip

def item_count(detail_ip):
    counts = {}

    def get_dict(line):
        return dict([i.split(": ") for i in line.split("; ")])

    def update(d, i):
        if i == "ASUS": i = "Asus"
        if i not in d:
            d[i] = 1
        else:
            d[i] += 1

    for k, v in detail_ip.items():
        counts[k] = {"OS": dict(), "Device": dict()}
        for item in v:
            if "Service Info" in item:
                item.update(get_dict(item["Service Info"]))
            if "OS" in item:
                if "linux" in item["OS"]:
                    item["OS"] = "Linux"
            elif "Aggressive OS guesses" in item:
                target = item["Aggressive OS guesses"].split(", ")[0]
                if "Windows" in target:
                    item["OS"] = "Windows"
                else:
                    item["OS"] = target.split(" ")[0]
            if "OS" in item: update(counts[k]["OS"], item["OS"])
            if "Device" in item:
                update(counts[k]["Device"], item["Device"])
            if "Device type" in item:
                item["Device type"] = item["Device type"].split("|")
                for dt in item["Device type"]:
                    update(counts[k]["Device"], dt)
    return counts

def draw_active_ip(detail_ip):
    plt.clf()
    plt.figure(figsize=(12, 6))

    columns = list(map(str, sorted(tsinghua_prefixes, key=lambda x: x.num_addresses)))[::-1]
    rows = ["all", "inactive", "active"]

    y_active = np.array([len(detail_ip[i]) for i in columns])
    y_all = np.sort([i.num_addresses for i in tsinghua_prefixes])[::-1]
    y_inactive = y_all - y_active
    data = np.array([y_active, y_inactive-y_active, y_all-y_inactive])
    
    colors = plt.cm.BuPu(np.linspace(0.3, 0.5, len(rows)))

    index = np.arange(len(columns)) + 0.3
    bar_width = 0.4

    y_offset = np.zeros(len(columns))
    cell_text = []
    for row in range(len(data)):
        plt.bar(index, data[row], bar_width, bottom=y_offset, color=colors[row])
        y_offset = y_offset + data[row]
        cell_text.append([f"{int(x)}" for x in y_offset])

    colors = colors[::-1]
    cell_text.reverse()

    the_table = plt.table(cellText=cell_text, rowLabels=rows, rowColours=colors, colLabels=columns, loc="bottom")

    plt.subplots_adjust(left=0.2, bottom=0.2)

    plt.yscale("log", basey=10)
    plt.ylabel("Number")
    plt.xticks([])
    plt.title("Active IP Distribution")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("active_ip.pdf", bbox_inches="tight")
    plt.savefig("active_ip.png", bbox_inches="tight")

def draw_item_counts(item_counts):
    os_count, device_count = {}, {}
    for v in item_counts.values():
        for a,b in v["OS"].items():
            if a in os_count: os_count[a] += b
            else: os_count[a] = b
        for a,b in v["Device"].items():
            if a in device_count: device_count[a] += b
            else: device_count[a] = b

    def sort_count(c):
        name, cnt = np.array(list(c.items())).T
        cnt = cnt.astype(int)
        idx = np.argsort(cnt)[::-1]
        name = name[idx]
        cnt = cnt[idx]
        return name, cnt

    os_name, os_cnt = sort_count(os_count)
    dev_name, dev_cnt = sort_count(device_count)

    plt.clf()
    fig = plt.figure(figsize=(12, 12))
    ax0, ax1 = fig.subplots(2, 1)
    
    def draw_pie(ax, labels, data, title):
        wedges, texts = ax.pie(data, wedgeprops=dict(width=0.5, edgecolor='w'), startangle=-20)
        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

        split_idx = 6
        for i, p in enumerate(wedges[:split_idx]):
            ang = (p.theta2 - p.theta1)/2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            ax.annotate(labels[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                                    horizontalalignment=horizontalalignment, **kw)
        ax.legend(wedges[split_idx:], labels[split_idx:], bbox_to_anchor=(1, 0, 0.3, 1), loc="lower right", prop=dict(size=10))
        ax.set_title(title)

    draw_pie(ax0, dev_name, dev_cnt, "Device Type Distribution")
    draw_pie(ax1, os_name, os_cnt, "OS Distribution")

    fig.tight_layout()
    fig.savefig("item_count.pdf", bbox_inches="tight")
    fig.savefig("item_count.png", bbox_inches="tight")


if __name__ == "__main__":
    detail_ip_path = output_dir / "detail_ip.json"
    if detail_ip_path.exists():
        detail_ip = json.load(open(detail_ip_path, "r"))
    else:
        active_ip = scan_active_ip()
        detail_ip = scan_ip_detail(active_ip)
        json.dump(detail_ip, open(detail_ip_path, "w"))
    del detail_ip["202.112.39.2/32"]

    draw_active_ip(detail_ip)

    item_counts = item_count(detail_ip)
    draw_item_counts(item_counts)
