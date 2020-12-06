#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# **********************************************************************
# * Description   : get traces for ip prefix
# * Last change   : 19:52:01 2020-12-06
# * Author        : Yihao Chen
# * Email         : chenyiha17@mails.tsinghua.edu.cn
# * License       : www.opensource.org/licenses/bsd-license.php
# **********************************************************************

import click
import json
from pathlib import Path
from topology_discovery import trace_gateway

@click.command()
@click.option("--prefix", "-p", multiple=True, help="ip prefix to discovery, e.g. 192.168.0.0/16")
@click.option("--output-dir", "-o", type=Path, default=Path("./output"), help="file path to save traces output")
def main(prefix, output_dir, **kwargs):
    output_dir = output_dir.resolve()
    if not output_dir.exists(): print(f"create output dir: {output_dir}")
    output_dir.mkdir(exist_ok=True, parents=True)

    for p in prefix:
        print(f"getting traces for {p}...")
        trace_path = output_dir / f"trace_{p.replace('/', '-')}"
        json.dump(trace_gateway(p), open(trace_path, "w"))

if __name__ == "__main__":
    main()
