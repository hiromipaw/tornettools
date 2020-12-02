import os
import logging
import datetime

from tornettools.util import *

def parse_resource_usage_logs(args):
    free_filepath = f"{args.prefix}/free.log"
    if not os.path.exists(free_filepath):
        free_filepath += ".xz"

    if not os.path.exists(free_filepath):
        logging.warning(f"Unable to find resource usage data at {free_filepath}")
        return False

    rusage = {}

    last_ts = None
    mem_header = None
    with open_readable_file(free_filepath) as inf:
        for line in inf:
            if line.count(':') == 2:
                dt = datetime.datetime.strptime(line.strip(), "%a %b %d %H:%M:%S %Z %Y")
                last_ts = dt.timestamp()
            elif 'total' in line and mem_header == None:
                mem_header = [p.strip() for p in line.strip().split()]
            elif "Mem:" in line:
                parts = [p.strip() for p in line.strip().split()]
                mem_counts = [int(p) for p in parts[1:]]

                memd = {f"mem_{mem_header[i]}": mem_counts[i] for i in range(len(mem_counts))}

                rusage.setdefault(last_ts, memd)

    if len(rusage) > 0:
        outpath = f"{args.prefix}/free.json.xz"
        dump_json_data(rusage, outpath, compress=True)
        return True
    else:
        logging.warning(f"Unable to parse resource data from {free_filepath}.")
        return False

def extract_resource_usage_plot_data(args):
    json_path = f"{args.prefix}/free.json"

    if not os.path.exists(json_path):
        json_path += ".xz"

    if not os.path.exists(json_path):
        logging.warning(f"Unable to find resource usage data at {json_path}.")
        return

    data = load_json_data(json_path)
    __extract_resource_usage(args, data)

def __extract_resource_usage(args, data):
    rusage = {"ram": __get_ram_usage(data), "run_time": __get_run_time(data)}
    outpath = f"{args.prefix}/plot.data/resource_usage.json"
    dump_json_data(rusage, outpath, compress=False)

def __get_ram_usage(data):
    used = {float(ts): data[ts]["mem_used"] for ts in data}

    mem_start = used[min(used.keys())] # mem used by OS, i.e., before starting shadow
    mem_max_bytes = max(used.values()) - mem_start # subtract mem used by OS
    mem_max_gib = mem_max_bytes/(1024.0**3)

    shadow_used = {ts: used[ts]-mem_start for ts in used}

    return {"max_bytes_used": mem_max_bytes, "max_gib_used": mem_max_gib, "used_over_time": shadow_used}

def __get_run_time(data):
    times = [float(k) for k in data.keys()]

    dt_min = datetime.datetime.fromtimestamp(min(times))
    dt_max = datetime.datetime.fromtimestamp(max(times))
    runtime = dt_max - dt_min

    return {"human": str(runtime), "seconds": runtime.total_seconds()}
