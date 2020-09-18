import argparse
import json
import os

from datetime import datetime
from operator import itemgetter
import subprocess


def calculate_basic_tor_relay_stats(details):

    # Implemented it like Tor website
    max_time = max(datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") for r in details["relays"])
    relays = [r for r in details["relays"] if datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") >= max_time]

    stats = dict()

    stats["rc"] = len(relays)
    stats["rasn"] = len({i["as"] for i in relays if "as" in i})
    stats["rbw"] = sum([i["advertised_bandwidth"] for i in relays]) / 1000 / 1000 / 1000 * 8

    # Changed to exit Probability > 0
    # exits = [r for r in relays if "Exit" in r["flags"]]
    exits = [r for r in relays if r["exit_probability"] > 0]
    stats["ec"] = len(exits)
    stats["easn"] = len({i["as"] for i in exits if "as" in i})
    stats["ebw"] = sum([i["advertised_bandwidth"] for i in exits]) / 1000 / 1000 / 1000 * 8

    # Changed to guard Probability > 0
    # guards = [r for r in relays if "Guard" in r["flags"]]
    guards = [r for r in relays if r["guard_probability"] > 0]
    stats["gc"] = len(guards)
    stats["gasn"] = len({i["as"] for i in guards if "as" in i})
    stats["gbw"] = sum([i["advertised_bandwidth"] for i in guards]) / 1000 / 1000 / 1000 * 8

    return stats


def print_basic_stats(s):
    print("Basic Statistics (Table 1)")
    print("--------------------------")
    print("  All Relays & {rc:4d} & {rasn:4d} & {rbw:2.2f} \\\\".format(**s))
    print(" Exit Relays & {ec:4d} & {easn:4d} & {ebw:2.2f} \\\\".format(**s))
    print("Guard Relays & {gc:4d} & {gasn:4d} & {gbw:2.2f} \\\\".format(**s))


def calculate_basic_ripe_stats(probes):
    connected_probes = [p for p in probes["objects"] if p["status_name"] == "Connected"]

    probes_per_as = dict()
    for p in connected_probes:
        probes_per_as.setdefault(p["asn_v4"], []).append(p)

    stats = dict()
    stats["connected_probes"] = connected_probes
    stats["probes_per_as"] = probes_per_as

    return stats


def print_basic_ripe_stats(stats):
    print("Basic RIPE Statistics")
    print("---------------------")
    print("Connected probes: %6d" % len(stats["connected_probes"]))
    print("in different AS:  %6d" % len(stats["probes_per_as"]))


def generate_gnuplot_dat_files(details, probes):
    print("Generate gnuplot .dat Files")
    print("---------------------------")

    # TODO Change File structure to save in other directory structure
    # Implemented it like Tor website
    max_time = max(datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") for r in details["relays"])
    relays = [r for r in details["relays"] if datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") >= max_time]

    probes_as = {"AS" + str(p["asn_v4"]) for p in probes["objects"] if p["status_name"] == "Connected"}

    for flag in ("exit", "guard"):
        filtered_relays = [r for r in relays if r[flag+"_probability"] > 0]
        relays_per_as = dict()
        for r in filtered_relays:
            if "as" in r:
                relays_per_as.setdefault(r["as"], []).append(r)

        as_values = [(asn,
                      sum([r["%s_probability" % flag] for r in relays if "%s_probability" % flag.lower() in r]),
                      len(relays)
                      ) for asn, relays in relays_per_as.items()]
        as_values.sort(key=itemgetter(1), reverse=True)

        with open("gnuplot/%s_as.dat" % flag, "w") as as_fp:
            _, s_p, s_c = zip(*as_values)
            summed_values = [(idx+1, sum(s_p[:idx+1]), sum(s_c[:idx+1])) for idx in range(len(s_p))]
            as_fp.write("0 0 0\n")
            as_fp.write("\n".join("%d %f %d" % line for line in summed_values))

        with open("gnuplot/%s_probes_as.dat" % flag, "w") as as_probes_fp:
            _, s_p, s_c = zip(* filter(lambda x: x[0] in probes_as, as_values))
            summed_values = [(idx+1, sum(s_p[:idx + 1]), sum(s_c[:idx + 1])) for idx in range(len(s_p))]
            as_probes_fp.write("0 0 0\n")
            as_probes_fp.write("\n".join("%d %f %d" % line for line in summed_values))


def execute_gnuplot():
    print("Execute gnuplot")
    print("---------------")

    p = subprocess.Popen(["gnuplot", "exit_as.gnuplot"], cwd="gnuplot")
    p.wait()

    p = subprocess.Popen(["gnuplot", "guard_as.gnuplot"], cwd="gnuplot")
    p.wait()


def calculate_top_as_without_ripe_probe(details, probes):
    # Implemented it like Tor website
    max_time = max(datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") for r in details["relays"])
    relays = [r for r in details["relays"] if datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") >= max_time]
    probes_as = {"AS" + str(p["asn_v4"]) for p in probes["objects"] if p["status_name"] == "Connected"}

    relays_wo_probe_per_as = dict()

    for r in relays:
        if "as" in r and r["as"] not in probes_as:
            relays_wo_probe_per_as.setdefault(str(r["as"]), []).append(r)

    top_as = [{"as": asn,
               "nr_relays": len(relays),
               "bw_sum": sum([r["advertised_bandwidth"] for r in relays]) / 1000/1000/1000*8 ,
               "exit_sum": sum([r["exit_probability"] for r in relays if "exit_probability" in r]),
               "guard_sum": sum([r["guard_probability"] for r in relays if "guard_probability" in r])
               }
              for asn, relays in relays_wo_probe_per_as.items()]

    return {"exit": sorted(top_as, key=itemgetter("exit_sum"), reverse=True),
            "guard": sorted(top_as, key=itemgetter("guard_sum"), reverse=True)}


def print_top_as_without_ripe_probe(top_exit, top_guard):
    print("Top AS without RIPE Probe")
    print("-------------------------")
    print("    AS\\# & Nr. Relays & Sum BW (Gbit/s) & Exit prob. & Guard prob. \\\\ \\hline\\hline")
    for s in top_exit[:5]:
        print("%8s & %10d & %6.2f & %10.3f & %11.3f \\\\" %
              (s["as"], s["nr_relays"], s["bw_sum"], s["exit_sum"], s["guard_sum"]))
    print("\\hline")
    for s in top_guard[:5]:
        print("%8s & %10d & %6.2f & %10.3f & %11.3f \\\\" %
              (s["as"], s["nr_relays"], s["bw_sum"], s["exit_sum"], s["guard_sum"]))

    print("Sum exit prob for %d AS if RIPE installed: %.3f" % (5, sum(s["exit_sum"] for s in top_exit[:5])))
    print("Sum exit prob for %d AS if RIPE installed: %.3f" % (10, sum(s["exit_sum"] for s in top_exit[:10])))


def print_country_statistic(details, probes):
    # TODO Split details and probes, since they are not depending
    print("Country statistics")
    print("------------------")

    probes_per_country = {}

    for p in probes["objects"]:
        if p["status_name"] == "Connected":
            probes_per_country.setdefault(p["country_code"], []).append(p)

    sorted_ppc = sorted([(k, len(v)) for k, v in probes_per_country.items()], key=itemgetter(1), reverse=True)

    print(f"Top probe countries: {sorted_ppc[:10]}")

    # TODO Only take running relays for stats (see basic-statistics)
    relays_per_country = {}
    for r in details["relays"]:
        if "country" in r:
            relays_per_country.setdefault(r["country"], []).append(r)

    sorted_rpc = sorted([(k, len(v)) for k, v in relays_per_country.items()], key=itemgetter(1), reverse=True)
    print(f"Top relay countries: {sorted_rpc[:10]}")


def main():
    """Print statistics depending on provided files"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--details", type=str, help="details .json file from onioo")
    parser.add_argument("-p", "--probes", type=str, help="probes .json file from onioo")
    args = parser.parse_args()

    # Open Detail file
    if args.details and os.path.isfile(args.details):
        with open(args.details, 'r') as f:
            details = json.load(f)
    else:
        details = None
        print("No valid details file")

    # Open Probes file
    if args.probes and os.path.isfile(args.probes):
        with open(args.probes, 'r') as f:
            probes = json.load(f)
    else:
        probes = None
        print("No valid probes file")

    # Print Basic Stats
    if details:
        basic_stats = calculate_basic_tor_relay_stats(details)
        print_basic_stats(basic_stats)
        print()

    # Print Stats for Probes
    if probes:
        ripe_stats = calculate_basic_ripe_stats(probes)
        print_basic_ripe_stats(ripe_stats)
        print()

    # Execute Gnuplot and Calculate Top AS
    if details and probes:
        generate_gnuplot_dat_files(details, probes)
        execute_gnuplot()
        print()

        top = calculate_top_as_without_ripe_probe(details, probes)
        print_top_as_without_ripe_probe(top["exit"], top["guard"])
        print()

        print_country_statistic(details, probes)
        print()


if __name__ == '__main__':
    main()