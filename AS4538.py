#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : topology discovery for AS4538, a.k.a. China 
#                           Education and Research Network Center
# * Last change   : 20:32:55 2020-12-06
# * Author        : Yihao Chen
# * Email         : chenyiha17@mails.tsinghua.edu.cn
# * License       : www.opensource.org/licenses/bsd-license.php
# **********************************************************************

import subprocess
import json
from pathlib import Path
from topology_discovery import trace_gateway
from tqdm import tqdm

output_dir = Path(__file__).resolve().parent / "output"
if not output_dir.exists(): print(f"create output dir: {output_dir}")
output_dir.mkdir(exist_ok=True, parents=True)

def get_prefixes():
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


if __name__ == "__main__":
    prefixes = get_prefixes()
    trace_prefixes(prefixes)
