import json
import logging
from datetime import datetime
import os
from ipaddress import ip_address

MAX_ELEMENTS_PER_CASE = 1000
CHUNK_SIZE = 30  # Because 100 is the limit, and some do not finish, 30 are for sure free
COST_PER_TRACEROUTE = 20  # Because OneOff = True


def template_measurement():
    return {
        "definitions": [],
        "probes": [],
        "is_oneoff": True
    }


def template_definition(ip_version="ipv4"):
    return {
        "target": "TARGET",
        "description": "DESCRIPTION",
        "type": "traceroute",
        "af": 6 if ip_version == "ipv6" else 4,
        "is_public": True,
        "protocol": "ICMP",
        "response_timeout": 20000,
        "is_oneoff": True,
        "packets": 1  # Just use one packet to have less costs
    }


def template_probe_list():
    return {
        "requested": 1,
        "type": "probes",
        "value": "PROBESLIST"  # Enter Probes here
    }


def template_probe_asn():
    return {
        "requested": 1,
        "type": "asn",
        "value": "ASN"  # Enter Probes here
    }


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def create_one_to_many(measurement_name, endpoint_set, relay_set, ip_version="ipv4"):
    relay_set_items = list(relay_set.items())[:MAX_ELEMENTS_PER_CASE]

    measurement_list = []

    for chunked_relay_set_items in chunks(relay_set_items, CHUNK_SIZE):
        measurement = template_measurement()

        for asn, o in chunked_relay_set_items:
            ip, separator, port = o["relays"][0]["or_addresses"].rpartition(':')

            definition = template_definition(ip_version)
            definition["target"] = ip.strip("[]") #strip brackets for ipv6
            if port and port != "0":
                definition["port"] = int(port)
            definition["description"] = measurement_name

            measurement["definitions"].append(definition)

        probe = template_probe_list()
        probe["requested"] = len(endpoint_set["probes"])
        probe["value"] = ",".join(map(str, endpoint_set["probes"]))

        measurement["probes"].append(probe)

        measurement_list.append(measurement)

    return measurement_list


def create_many_to_one(measurement_name, probe_set, endpoint_set, ip_version="ipv4"):
    measurement = template_measurement()

    for addrs in endpoint_set["addresses"]:
        target_addrs_v4 = [addr for addr in addrs if "[" not in addr]
        target_addrs_v6 = [addr for addr in addrs if "[" in addr]
        target_addrs = target_addrs_v6 if ip_version == "ipv6" else target_addrs_v4

        if len(target_addrs) == 0:
            logging.warning(f'No target addresses found!')
            continue

        addr = target_addrs[0]
        ip, separator, port = addr.rpartition(':')
        definition = template_definition(ip_version)
        definition["target"] = ip.strip("[]")
        if port and port != "0":
            definition["port"] = int(port)
        definition["description"] = measurement_name

        measurement["definitions"].append(definition)

    for asn, o in probe_set.items():
        probe = template_probe_asn()
        probe["requested"] = 1  # Only use one probe of each AS
        probe["value"] = int(asn[2:])

        measurement["probes"].append(probe)

    return [measurement]


def create_case1(measurement_name, c_as, g_as, ip_version="ipv4"):
    return create_one_to_many(measurement_name + "-c1", c_as, g_as, ip_version)


def create_case2(measurement_name, e_as_r, d_as, ip_version="ipv4"):
    return create_many_to_one(measurement_name + "-c2", e_as_r, d_as, ip_version)


def create_case3(measurement_name, d_as, e_as, ip_version="ipv4"):
    return create_one_to_many(measurement_name + "-c3", d_as, e_as, ip_version)


def create_case4(measurement_name, g_as_r, c_as, ip_version="ipv4"):
    return create_many_to_one(measurement_name + "-c4", g_as_r, c_as, ip_version)


def calculate_costs_for_measurement_set(measurement_set):
    """Calculate the costs of RIPE Atlas credits for the complete measurement based on the measurement set"""
    ms = measurement_set

    case1 = 20 * len(ms["c_as"]) * len(ms["g_as"])
    case2 = 20 * len(ms["e_as_r"]) * len(ms["d_as"])
    case3 = 20 * len(ms["d_as"]) * len(ms["e_as"])
    case4 = 20 * len(ms["g_as_r"]) * len(ms["c_as"])
    total = case1 + case2 + case3 + case4
    return case1, case2, case3, case4, total


def calculate_costs_for_definition(definition):
    """
    Calculate the cost of one RIPE Atlas measurement definition

    This is not perfect, just: 20 * nr_definitions * requested_probes (so no packets, ...)
    """
    return 20 * len(definition["definitions"]) * sum([p["requested"] for p in definition["probes"]])


def calculate_number_of_measurements(definition):
    return len(definition["definitions"])


def main():
    # TODO ADOPT MAIN
    measurement_name = datetime.now().strftime("%Y%m%d-%H%M%S")
    measurement_dir = 'ripe-measurements/' + measurement_name + "/"
    os.mkdir(measurement_dir)

    c_probe = [26895]  # My Client
    d_ip = ["1.2.3.4:80"]  # Destination IP # TODO Freitag 20/12
    d_probe = [12345]  # TODO Freitag 20/12
    c_ip = ["23.12.12.12:80"]  # TODO Freitag 20/12

    g_as_fp = open("run/20191221-1422/measurement-sets/g_as.json")
    e_as_fp = open("run/20191221-1422/measurement-sets/e_as.json")
    g_as_r_fp = open("run/20191221-1422/measurement-sets/g_as_r.json")
    e_as_r_fp = open("run/20191221-1422/measurement-sets/e_as_r.json")

    g_as = json.load(g_as_fp)
    e_as = json.load(e_as_fp)
    g_as_r = json.load(g_as_r_fp)
    e_as_r = json.load(e_as_r_fp)

    with open(measurement_dir+"case1.json", "w") as case4_fp:
        json.dump(create_case1(measurement_name, c_probe, g_as), fp=case4_fp, indent=2)

    with open(measurement_dir+"case2.json", "w") as case2_fp:
        json.dump(create_case2(measurement_name, e_as_r, d_ip), fp=case2_fp, indent=2)

    with open(measurement_dir+"case3.json", "w") as case3_fp:
        json.dump(create_case3(measurement_name, d_probe, e_as), fp=case3_fp, indent=2)

    with open(measurement_dir+"case4.json", "w") as case4_fp:
        json.dump(create_case4(measurement_name, g_as_r, c_ip), fp=case4_fp, indent=2)

    g_as_fp.close()
    e_as_fp.close()
    g_as_r_fp.close()
    e_as_r_fp.close()


if __name__ == '__main__':
    main()


def create_probes_set(probes, ip_version="ipv4"):
    probes_per_as_v4 = dict()
    probes_per_as_v6 = dict()
    for p in probes["objects"]:
        if p["status_name"] == "Connected":
            as_ipv4 = f"AS{p['asn_v4']}"
            as_ipv6 = f"AS{p['asn_v6']}"
            if as_ipv4:
                probes_per_as_v4.setdefault(as_ipv4, []).append(p["id"])
            if as_ipv6:
                probes_per_as_v6.setdefault(as_ipv6, []).append(p["id"])
    return probes_per_as_v6 if ip_version == "ipv6" else probes_per_as_v4


def create_guard_set(details, ip_version):
    """Create (ii) g-as."""
    return create_simple_set(details, "Guard", ip_version)


def create_exit_set(details, ip_version):
    """Create (iv) e-as."""
    return create_simple_set(details, "Exit", ip_version)


def create_simple_set(details, filtr, ip_version="ipv4"):
    relay_per_as_v4 = {}
    relay_per_as_v6 = {}
    for r in details["relays"]:
        if filtr in r["flags"]:
            if "as" in r:
                r_addrs = r["or_addresses"]
                # remove brackets at ipv6 addrs since we parse them anyway
                #r_addrs = [addr.strip("[]") for addr in r_addrs]
                #ipv4_addrs = [addr for addr in r_addrs if ip_address(addr).version == 4]
                #ipv6_addrs = [addr for addr in r_addrs if ip_address(addr).version == 6]
                ipv4_addrs = [addr for addr in r_addrs if not "[" in addr]
                ipv6_addrs = [addr for addr in r_addrs if "[" in addr]
                if ipv4_addrs:
                    relay_per_as_v4.setdefault(str(r["as"]), {"relays": []})["relays"].append({"fingerprint": r["fingerprint"],
                                                                                        "or_addresses":
                                                                                            ipv4_addrs[0]})
                if ipv6_addrs:
                    relay_per_as_v6.setdefault(str(r["as"]), {"relays": []})["relays"].append({"fingerprint": r["fingerprint"],
                                                                                        "or_addresses":
                                                                                            ipv6_addrs[0]})
    return relay_per_as_v6 if ip_version == "ipv6" else relay_per_as_v4

def create_guard_with_ripe_probes_set(details, probes, ip_version):
    """Create (iii) g-as-r."""
    return create_set_with_ripe_probes(details, probes, "Guard", ip_version)


def create_exit_with_ripe_probes_set(details, probes, ip_version):
    """Create (v) e-as-r."""
    return create_set_with_ripe_probes(details, probes, "Exit", ip_version)


def create_set_with_ripe_probes(details, probes, filtr, ip_version):
    relay_per_as = create_simple_set(details, filtr, ip_version)
    probes = create_probes_set(probes, ip_version)

    as_to_delete = []

    for asn in relay_per_as.keys():
        if asn in probes:
            relay_per_as[asn]["ids"] = probes[asn]
        else:
            as_to_delete.append(asn)

    for asn in as_to_delete:
        del relay_per_as[asn]

    return relay_per_as