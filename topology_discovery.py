#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : topology discovery
# * Last change   : 21:26:44 2020-12-07
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
from sklearn.manifold import TSNE

def trace_route(ip_addr): # NOTE: could raise error
    cmd = ["traceroute", "-4nI", "-q", "1", "-w", "2", str(ip_addr)]
    output = subprocess.run(cmd, stdout=subprocess.PIPE, timeout=10)
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

def get_peer_map(traces, peer_map=None):
    if peer_map is None: peer_map = {}
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

def expand_subnet(G):
    nodes = list(G.nodes)
    for n in nodes:
        if n.split(".")[-1] == "1":
            G.add_edges_from(product([n], [f"{n[:-1]}{i}" for i in range(2, 255)]))
    return G

def get_color_for_ip(ip_str):
    return [int(x) for x in ip_str.split(".")][:3]

def get_vec_for_ip(ip_str):
    return np.array([int(bit) for x in ip_str.split(".") for bit in list(f"{int(x):08b}")])

def drawG(ax, G):
    nodes, degrees = np.array(list(map(list, G.degree))).T
    nodes = nodes.astype(str)
    degrees = degrees.astype(int)
    node_size = degrees / degrees.max() * 100
    node_color = np.array([get_color_for_ip(i) for i in nodes]) / 255.0
    nx.draw(G, ax=ax, node_size=node_size, node_color=node_color, width=0.5, linewidths=None)

def cluster(G):
    vecs = list(map(get_vec_for_ip, G.nodes))
    emb = dict(zip(G.nodes, TSNE(n_components=2, init='pca', n_jobs=8).fit_transform(vecs)))
    return emb

def draw_scatter(ax, nodes, emb):
    x, y = np.array([emb[i] for i in nodes]).T
    colors = np.array([get_color_for_ip(i) for i in nodes])
    c = colors / 255.0
    ax.scatter(x, y, c=c, s=5, marker=".", lw=0)
