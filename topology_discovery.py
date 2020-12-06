#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : topology discovery
# * Last change   : 20:42:20 2020-12-06
# * Author        : Yihao Chen
# * Email         : chenyiha17@mails.tsinghua.edu.cn
# * License       : www.opensource.org/licenses/bsd-license.php
# **********************************************************************

import subprocess
import ipaddress as ipa 
from concurrent.futures import ThreadPoolExecutor
from itertools import product

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

def trace_route(ip_addr): # NOTE: could raise error
    cmd = ["traceroute", "-4nI", "-q", "1", "-w", "2", str(ip_addr)]
    output = subprocess.run(cmd, stdout=subprocess.PIPE)
    route, delay, reachable = [], [], True
    for l in output.stdout.decode().strip().split("\n")[1:]:
        items = l.strip().split()
        if items[1] == "*":
            reachable = False
            break
        ipa.IPv4Address(items[1])
        route.append(items[1])
        delay.append(float(items[2]))
    return {
        "target": str(ip_addr),
        "route": route,
        "delay": delay,
        "reachable": reachable,
    } if route else None

def trace_gateway(prefix): # trace the gateway of each /24 subnet
    prefix = ipa.IPv4Network(prefix)
    prefixlen = prefix.prefixlen 
    assert prefixlen <= 24
    subnets = prefix.subnets(new_prefix=24)

    def worker(subnet):
        try: return trace_route(subnet[1])
        except: return None

    n_worker = min(2**(24-prefix.prefixlen), 256) # one thread for each trace (no more than 256)
    with ThreadPoolExecutor(max_workers=n_worker) as executor:
        traces = list(filter(lambda x: x is not None, executor.map(worker, subnets)))

    return traces

def get_peer_map(traces):
    peer_map = {}
    def create_if_not_exist(node):
        if node not in peer_map:
            peer_map[node] = set()
    for trace in traces:
        route = trace["route"]
        for a, b in zip(route[:-1], route[1:]):
            create_if_not_exist(a)
            create_if_not_exist(b)
            peer_map[a].add(b)
            peer_map[b].add(a)
    return peer_map

def get_network_graph(peer_map):
    G = nx.Graph()
    for node, peers in peer_map.items():
        G.add_edges_from(product([node], peers))
    return G

def get_color_for_ip(ip_str):
    return [int(x) for x in ip_str.split(".")][:3]

def drawG(ax, G):
    nodes, degrees = np.array(list(map(list, G.degree))).T
    nodes = nodes.astype(str)
    degrees = degrees.astype(int)
    node_size = degrees / degrees.max() * 100
    node_color = np.array([get_color_for_ip(i) for i in nodes]) / 255.0
    nx.draw(G, ax=ax, node_size=node_size, node_color=node_color, width=0.5, linewidths=None)

if __name__ == "__main__":
    import json
    trace_file = ["trace_101.5.0.0-16", "trace_101.6.0.0-16", "trace_166.111.0.0-16", "trace_183.172.0.0-16", "trace_183.173.0.0-16", "trace_59.66.0.0-16"]
    traces_list = map(lambda x: json.load(open(f"./tmp/{x}", "r")), trace_file)
    traces = [t for traces in traces_list for t in traces]
    del  traces_list, trace_file

    peer_map = get_peer_map(traces)
    G = get_network_graph(peer_map)


    # Draw graph
    fig = plt.figure(figsize=(4, 4))

    ax = fig.add_subplot(111)
    drawG(ax, G)

    fig.savefig("tmp.pdf")
