import argparse
import json
import logging
import os

try:
    from ripetor import ip2as
except:
    import ip2as

from datetime import datetime
from operator import itemgetter
import subprocess
from collections import OrderedDict
from ipaddress import ip_address, ip_network

def filter_ip_addrs(addr_list, ip_version="ipv4"):
    if ip_version == "ipv4":
        addrs_v4 = [addr for addr in addr_list if not "[" in addr]
        return addrs_v4
    elif ip_version == "ipv6":
        addrs_v6 = [addr for addr in addr_list if "[" in addr]
        return addrs_v6
    else:
        raise ValueError(f"invalid ip_version: {ip_version}")

def remove_port_from_addr_notation(addr_str):
    ip, separator, port = addr_str.rpartition(':')
    return ip

#allowed values for ip_version: "ipv4", "ipv6", "ipv4v6"
#allowwed values for filter_criteria: "entry", "exit"
def filter_relays(relays, ip_version="ipv4", filter_criteria="entry"):
    if "v4" in ip_version:
        relays = [r for r in relays if filter_ip_addrs(r.get("or_addresses", []), ip_version="ipv4")]
    if "v6" in ip_version:
        relays = [r for r in relays if filter_ip_addrs(r.get("or_addresses", []), ip_version="ipv6")]
    return relays


def get_current_relays(details):
    max_time = max(datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") for r in details["relays"])
    relays = [r for r in details["relays"] if datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S") >= max_time]

    # calculate summarized ipv6 probabilities (for normalization)
    relays_ipv6 = filter_relays(relays, "ipv6")
    ipv6_sum_guard_probability = sum(r.get('guard_probability', 0) for r in relays_ipv6)
    ipv6_sum_middle_probability = sum(r.get('middle_probability', 0) for r in relays_ipv6)
    ipv6_sum_exit_probability = sum(r.get('exit_probability', 0) for r in relays_ipv6)

    # add calculated ASN field and normalize v6 probability
    for r in relays:
        tor_asn = r.get("as")
        ips_v4 = filter_ip_addrs(r.get('or_addresses', []), ip_version="ipv4")
        ips_v6 = filter_ip_addrs(r.get('or_addresses', []), ip_version="ipv6")
        if ips_v4:
            ip_v4 = remove_port_from_addr_notation(ips_v4[0])
            ip_asn_v4 = ip2as.ip2asn(ip_v4)
            r['asn_v4_calculated'] = ip_asn_v4
        if ips_v6:
            ip_v6 = remove_port_from_addr_notation(ips_v6[0])
            ip_asn_v6 = ip2as.ip2asn(ip_v6.strip("[]"))
            r['asn_v6_calculated'] = ip_asn_v6
            
            # normalize ipv6 probabilities
            r['guard_probability_v6'] = r.get('guard_probability') / ipv6_sum_guard_probability
            r['middle_probability_v6'] = r.get('middle_probability') / ipv6_sum_middle_probability
            r['exit_probability_v6'] = r.get('exit_probability') / ipv6_sum_exit_probability

    relays_ipv4 = filter_relays(relays, "ipv4")
    relays_ipv6 = filter_relays(relays, "ipv6")
    relays_dualstack = filter_relays(relays, "ipv4v6")

    return relays, relays_ipv4, relays_ipv6, relays_dualstack


def calculate_basic_tor_relay_stats(relays):
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


def print_basic_stats(s, remark=""):
    print(f"{remark}Basic Statistics (Table 1)")
    print("--------------------------")
    print("  All Relays & {rc:4d} & {rasn:4d} & {rbw:2.2f} \\\\".format(**s))
    print(" Exit Relays & {ec:4d} & {easn:4d} & {ebw:2.2f} \\\\".format(**s))
    print("Guard Relays & {gc:4d} & {gasn:4d} & {gbw:2.2f} \\\\".format(**s))


def rank_probes_per_uptime(probes):
    # overall uptime or time since last boot?
    # sort by uptime to get goot probes first
    probes.sort(key=lambda x: x.get('total_uptime', 0),  reverse=True)
    return probes

def filter_probes(probes, ip_version="ipv4"):
    if "v4" in ip_version:
        probes = [p for p in probes if p["asn_v4"]]
    if "v6" in ip_version:
        probes = [p for p in probes if p["asn_v6"]]
    return probes

def get_probe_ips(probe):
    ip_v4 = probe.get("address_v4", None)
    ip_v6 = probe.get("address_v6", None)
    network_v4 = probe.get("prefix_v4") #prefix_v4': '84.114.0.0/15',
    network_v6 = probe.get("prefix_v6")

    # sometimes address_v4 and address_v6 are censored --> take prefix_v4': '84.114.0.0/15', 'prefix_v6': instead
    if not ip_v4 and network_v4:
        network = ip_network(network_v4)
        ip_v4 = str(next(network.hosts())) # just take the first host

    if not ip_v6 and network_v6:
        network = ip_network(network_v6)
        ip_v6 = str(next(network.hosts())) # just take the first host

    return ip_v4, ip_v6

def get_current_probes(probes):
    connected_probes = [p for p in probes["objects"] if p["status_name"] == "Connected"]
    connected_probes = rank_probes_per_uptime(connected_probes)

    # add calculated as field
    for p in connected_probes:
        asn_v4 = p.get('asn_v4') or 0
        asn_v6 = p.get('asn_v6') or 0
        asn_v4 = f"AS{asn_v4}"
        asn_v6 = f"AS{asn_v6}"

        ip_asn_v4, ip_asn_v6 = get_probe_ips(p)

        if ip_asn_v4:
            ip_asn_v4 = ip2as.ip2asn(ip_asn_v4)
            p['asn_v4_calculated'] = ip_asn_v4
            #if asn_v4 != ip_asn_v4:
            #    print(f"{asn_v4} != {ip_asn_v4}")
        if ip_asn_v6:
            ip_asn_v6 = ip2as.ip2asn(ip_asn_v6)
            p['asn_v6_calculated'] = ip_asn_v6
            #if asn_v6 != ip_asn_v6:
            #    print(f"{asn_v6} != {ip_asn_v6}")

    #map(lambda x: x['asn']=x['asn_v4'], connected_probes)
    connected_probes_v4 = filter_probes(connected_probes, "ipv4")
    connected_probes_v6 = filter_probes(connected_probes, "ipv6")
    connected_probes_dual_stack = filter_probes(connected_probes, "ipv4v6")

    return connected_probes, connected_probes_v4, connected_probes_v6, connected_probes_dual_stack

def get_ordered_dict_by_value_len(unordered_dict):
    ret = OrderedDict()
    # construct helper list with (key, rank, value)
    temp = list()
    for key, value in unordered_dict.items():
        new_elem = [key, len(value), value]
        temp.append(new_elem)
    # order helper list
    temp.sort(key=lambda x: x[1],  reverse=True)
    # insert in right order
    for key, rank, value in temp:
        ret[key] = value
    return ret

def get_propes_per_asn(probes):
    probes_per_as_v4 = dict()
    probes_per_as_v6 = dict()

    for p in probes:
        if p["asn_v4"]:
            probes_per_as_v4.setdefault(p["asn_v4"], []).append(p)
        if p["asn_v6"]:
            probes_per_as_v6.setdefault(p["asn_v6"], []).append(p)

    return get_ordered_dict_by_value_len(probes_per_as_v4), get_ordered_dict_by_value_len(probes_per_as_v6)

def get_probes_per_country(probes):
    probes_per_country = dict()
    for p in probes:
        if p.get("country_code"):
            probes_per_country.setdefault(p["country_code"], []).append(p)
    return get_ordered_dict_by_value_len(probes_per_country)

def get_probes_per_country_asn_ranked(probes, ip_version="ipv4"):
    ret_v4 = OrderedDict()
    ret_v6 = OrderedDict()

    probes_per_country = get_probes_per_country(probes)
    for country, country_probes in probes_per_country.items():
        probes_per_as_v4, probes_per_as_v6 = get_propes_per_asn(country_probes)
        ret_v4[country] = probes_per_as_v4
        ret_v6[country] = probes_per_as_v6
    return ret_v4 if ip_version=="ipv4" else ret_v6


def calculate_basic_ripe_stats(probes, ip_version="ipv4"):
    probes_per_as_v4, probes_per_as_v6 = get_propes_per_asn(probes)

    stats = dict()
    stats["connected_probes"] = probes
    stats["probes_per_as"] = probes_per_as_v4 if ip_version=="ipv4" else probes_per_as_v6

    return stats

def get_example_set_by_asn(probes, asn, ip_version="ipv4v6"):
    ret_set = {"probes": [], "addresses": [], "asn":[]}
    if isinstance(asn, str):
        asn = int(asn.strip("AS"))
    unfiltered, probes_v4, probes_v6, probes_ds = get_current_probes(probes)
    if ip_version == "ipv4":
        probes_per_as_v4, probes_per_as_v6 = get_propes_per_asn(probes_v4)
        per_asn = probes_per_as_v4
    elif ip_version == "ipv6":
        probes_per_as_v4, probes_per_as_v6 = get_propes_per_asn(probes_v6)
        per_asn = probes_per_as_v6
    elif ip_version == "ipv4v6":
        probes_per_as_v4, probes_per_as_v6 = get_propes_per_asn(probes_ds)
        per_asn = probes_per_as_v4 # take v4 because more reliable?

    matches = per_asn.get(asn, [])
    if not matches:
        print(f"no matches for AS{asn} and {ip_version}")
    for p in matches:
        id = p["id"]
        asn_v4 = p.get('asn_v4') or 0
        asn_v6 = p.get('asn_v6') or 0
        ip_v4, ip_v6 = get_probe_ips(p)

        addrs = []
        if ip_v4:
            addrs.append(f"{ip_v4}:0")
        if ip_v6:
            addrs.append(f"[{ip_v6}]:0")
        
        asn = asn_v4 if "v4" in ip_version else asn_v6

        ret_set["probes"].append(id)
        ret_set["addresses"].append(addrs) 
        ret_set["asn"].append(asn)
    
    return ret_set


        




def print_basic_ripe_stats(stats, remark=""):
    print(f"{remark}Basic RIPE Statistics")
    print("---------------------")
    print("Connected probes: %6d" % len(stats["connected_probes"]))
    print("in different AS:  %6d" % len(stats["probes_per_as"]))


def generate_gnuplot_dat_files(relays, probes, ipv6=False):
    print("Generate gnuplot .dat Files")
    print("---------------------------")

    # TODO Change File structure to save in other directory structure
    if not ipv6:
        logging.info(f'Creating plot data for IPv4')
        probes_as = {"AS" + str(p["asn_v4"]) for p in probes}
        proto = "ipv4"
    else:
        logging.info(f'Creating plot data for IPv6')
        probes_as = {"AS" + str(p["asn_v6"]) for p in probes}
        proto = "ipv6"

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

        with open(f"gnuplot/{flag}_{proto}_as.dat", "w+") as as_fp:
            _, s_p, s_c = zip(*as_values)
            summed_values = [(idx+1, sum(s_p[:idx+1]), sum(s_c[:idx+1])) for idx in range(len(s_p))]
            as_fp.write("0 0 0\n")
            as_fp.write("\n".join("%d %f %d" % line for line in summed_values))

        with open(f"gnuplot/{flag}_{proto}_probes_as.dat", "w+") as as_probes_fp:
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


def calculate_top_as_without_ripe_probe(relays, probes):
    probes_as = {"AS" + str(p["asn_v4"]) for p in probes}

    relays_wo_probe_per_as = dict()
    relays_total = dict()

    for r in relays:
        if "as" in r and r["as"] not in probes_as:
                relays_wo_probe_per_as.setdefault(str(r["as"]), []).append(r)
        relays_total.setdefault(str(r["as"]), []).append(r)

    top_as = [{"as": asn,
               "nr_relays": len(relays),
               "bw_sum": sum([r["advertised_bandwidth"] for r in relays]) / 1000/1000/1000*8 ,
               "exit_sum": sum([r["exit_probability"] for r in relays if "exit_probability" in r]),
               "guard_sum": sum([r["guard_probability"] for r in relays if "guard_probability" in r])
               }
              for asn, relays in relays_wo_probe_per_as.items()]

    top_as_total = [{"as": asn,
                "has_probe": 1 if asn in probes_as else 0 ,
                "as_name": ip2as.get_as_name(asn),
               "nr_relays": len(relays),
               "bw_sum": sum([r["advertised_bandwidth"] for r in relays]) / 1000/1000/1000*8 ,
               "exit_sum": sum([r["exit_probability"] for r in relays if "exit_probability" in r]),
               "guard_sum": sum([r["guard_probability"] for r in relays if "guard_probability" in r])
               }
              for asn, relays in relays_total.items()]

    return {"exit": sorted(top_as, key=itemgetter("exit_sum"), reverse=True),
            "guard": sorted(top_as, key=itemgetter("guard_sum"), reverse=True)},{"exit": sorted(top_as_total, key=itemgetter("exit_sum"), reverse=True),
            "guard": sorted(top_as_total, key=itemgetter("guard_sum"), reverse=True)}


def print_top_as_without_ripe_probe(top_exit, top_guard, remark=""):
    print(f"{remark}Top AS without RIPE Probe")
    print("-------------------------")
    print("    AS\\# & Nr. Relays & Sum BW (Gbit/s) & Exit prob. & Guard prob. \\\\ \\hline\\hline")
    for s in top_exit[:10]:
        print("%8s & %10d & %6.2f & %10.3f & %11.3f \\\\" %
              (s["as"], s["nr_relays"], s["bw_sum"], s["exit_sum"], s["guard_sum"]))
    print("\\hline")
    for s in top_guard[:5]:
        print("%8s & %10d & %6.2f & %10.3f & %11.3f \\\\" %
              (s["as"], s["nr_relays"], s["bw_sum"], s["exit_sum"], s["guard_sum"]))

    print("Sum exit prob for %d AS if RIPE installed: %.3f" % (5, sum(s["exit_sum"] for s in top_exit[:5])))
    print("Sum exit prob for %d AS if RIPE installed: %.3f" % (10, sum(s["exit_sum"] for s in top_exit[:10])))

def print_total_tor_as(total_exit,total_guard,remark=""):
    print(f"{remark}Top AS Probes")
    print("-------------------------")
    print("    AS\\# & RIPE &  AS Name & Nr. Relays & Sum BW (Gbit/s) & Exit prob. & Guard prob. \\\\ \\hline\\hline")
    for s in total_exit[:20]:
        print("%8s & %1d & %s & %10d & %6.2f & %10.3f & %11.3f \\\\" %
              (s["as"], s["has_probe"],s["as_name"],s["nr_relays"], s["bw_sum"], s["exit_sum"], s["guard_sum"]))


def print_country_statistic(relays, probes, remark=""):
    # TODO Split details and probes, since they are not depending
    print(f"{remark}Country statistics")
    print("------------------")

    probes_per_country = {}

    for p in probes:
        probes_per_country.setdefault(p["country_code"], []).append(p)

    sorted_ppc = sorted([(k, len(v)) for k, v in probes_per_country.items()], key=itemgetter(1), reverse=True)

    print(f"Top probe countries: {sorted_ppc[:10]}")

    # TODO Only take running relays for stats (see basic-statistics)
    relays_per_country = {}
    for r in relays:
        if "country" in r:
            relays_per_country.setdefault(r["country"], []).append(r)

    sorted_rpc = sorted([(k, len(v)) for k, v in relays_per_country.items()], key=itemgetter(1), reverse=True)
    print(f"Top relay countries: {sorted_rpc[:10]}")


def main():
    """Print statistics depending on provided files"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--details", type=str, help="details .json file from onioo")
    parser.add_argument("-p", "--probes", type=str, help="probes .json file")
    parser.add_argument("-i", "--ip2asn", type=str, help="ip2asn csv file")
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

    # Open Ip2asn file
    if args.ip2asn and os.path.isfile(args.ip2asn):
        ip2as.load(args.ip2asn)
    else:
        print("No valid ip2asn file")

    # Print Basic Stats
    if details:
        unfiltered, relays_v4, relays_v6, relays_ds = get_current_relays(details)

        basic_stats = calculate_basic_tor_relay_stats(relays_v4)
        print_basic_stats(basic_stats, "[IPv4] ")

        print()

        basic_stats = calculate_basic_tor_relay_stats(relays_v6)
        print_basic_stats(basic_stats, "[IPv6] ")

        print()

    # Print Stats for Probes
    if probes:
        unfiltered, probes_v4, probes_v6, probes_ds = get_current_probes(probes)

        ripe_stats = calculate_basic_ripe_stats(probes_v4, "ipv4")
        print_basic_ripe_stats(ripe_stats, "[IPv4] ")

        print()

        ripe_stats = calculate_basic_ripe_stats(probes_v6, "ipv6")
        print_basic_ripe_stats(ripe_stats, "[IPv6] ")

        print()

    # Execute Gnuplot and Calculate Top AS
    if details and probes:
        generate_gnuplot_dat_files(relays_v4, probes_v4)
        generate_gnuplot_dat_files(relays_v6, probes_v6, ipv6=True)
        # execute_gnuplot()
        print()

        top,top_total = calculate_top_as_without_ripe_probe(relays_v4, probes_v4)
        print_top_as_without_ripe_probe(top["exit"], top["guard"], "[IPv4] ")
        print_total_tor_as(top_total["exit"], top_total["guard"], "[IPv4] ")
        
        print()

        top_v6,top_v6_total = calculate_top_as_without_ripe_probe(relays_v6, probes_v6)
        print_top_as_without_ripe_probe(top_v6["exit"], top_v6["guard"], "[IPv6] ")
        
        print()

        print_country_statistic(relays_v4, probes_v4, "[IPv4] ")
        print()

        print_country_statistic(relays_v6, probes_v6, "[IPv6] ")
        print()

        ranked_v4 = get_probes_per_country_asn_ranked(probes_v4)
        ranked_v6 = get_probes_per_country_asn_ranked(probes_v6)

        print("GERMANY TOP v4")
        print(list(ranked_v4['DE'].keys())[0:10])
        print("GERMANY TOP v6")
        print(list(ranked_v6['DE'].keys())[0:10])

        print("USA TOP v4")
        print(list(ranked_v4['US'].keys())[0:10])
        print("USA TOP v6")
        print(list(ranked_v6['US'].keys())[0:10])

        print("RUSSIA TOP v4")
        print(list(ranked_v4['RU'].keys())[0:10])
        print("RUSSIA TOP v6")
        print(list(ranked_v6['RU'].keys())[0:10])



if __name__ == '__main__':
    main()
