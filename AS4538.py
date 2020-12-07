#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : topology discovery for AS4538, a.k.a. China 
#                           Education and Research Network Center
# * Last change   : 23:16:44 2020-12-07
# * Author        : Yihao Chen
# * Email         : chenyiha17@mails.tsinghua.edu.cn
# * License       : www.opensource.org/licenses/bsd-license.php
# **********************************************************************

import subprocess
import json
import pickle
import ipaddress as ipa
from pathlib import Path
from topology_discovery import *
from tqdm import tqdm
from glob import glob

output_dir = Path(__file__).resolve().parent / "output"
if not output_dir.exists(): print(f"create output dir: {output_dir}")
output_dir.mkdir(exist_ok=True, parents=True)

def get_prefixes(): # NOTE: IPv6 included as well
    print("get prefixes...")
    prefix_path = output_dir / "prefixes"

    if prefix_path.exists():
        prefixes = json.load(open(prefix_path, "r"))
    else:
        target = "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS4538"
        resp = json.loads(subprocess.check_output(["curl", "-s", target]).decode())
        prefixes = [r["prefix"] for r in resp["data"]["prefixes"]]
        json.dump(prefixes, open(prefix_path, "w"))
        print(f"save prefixes at {prefix_path}")

    print(f"{len(prefixes)} in total")
    return prefixes

def trace_prefixes(prefixes):
    print("tracing prefixes...")
    def trace_prefix(p):
        trace_path = output_dir / f"trace_{p.replace('/', '-')}"
        if not trace_path.exists():
            json.dump(trace_gateway(p), open(trace_path, "w"))
    for prefix in tqdm(prefixes): trace_prefix(prefix)

def load_all_traces():
    print("loading traces...")
    peer_map = {}
    for f in tqdm(glob(str(output_dir / "trace_*"))):
        get_peer_map(json.load(open(f, "r")), peer_map=peer_map)
    return peer_map

def get_emb(G):
    emb_path = output_dir / "emb"
    if emb_path.exists():
        print("loading emb...")
        emb = pickle.load(open(emb_path, "rb"))
    else:
        print("training emb...")
        emb = cluster(G)
        pickle.dump(emb, open(emb_path, "wb"))
    return emb


if __name__ == "__main__":
    prefixes = list(filter(lambda x: ipa.ip_network(x).version == 4, get_prefixes()))
    trace_prefixes(prefixes)

    peer_map = load_all_traces()
    # G = expand_subnet(get_network_graph(peer_map))
    G = get_network_graph(peer_map)
    emb = get_emb(G)

    # Draw graph
    fig = plt.figure(figsize=(4, 4))

    ax = fig.add_subplot(111)
    draw_prefixes(ax, prefixes)
    # drawG(ax, G)
    # draw_scatter(ax, G, emb)

    fig.tight_layout()
    fig.savefig("tmp.pdf", bbox_inches="tight")
