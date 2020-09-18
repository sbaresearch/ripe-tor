import json
from datetime import datetime
import os

MAX_ELEMENTS_PER_CASE = 1000
CHUNK_SIZE = 30  # Because 100 is the limit, and some do not finish, 30 are for sure free
COST_PER_TRACEROUTE = 20  # Because OneOff = True


def template_measurement():
    return {
        "definitions": [],
        "probes": [],
        "is_oneoff": True
    }


def template_definition():
    return {
        "target": "TARGET",
        "description": "DESCRIPTION",
        "type": "traceroute",
        "af": 4,
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


def create_one_to_many(measurement_name, endpoint_set, relay_set):
    relay_set_items = list(relay_set.items())[:MAX_ELEMENTS_PER_CASE]

    measurement_list = []

    for chunked_relay_set_items in chunks(relay_set_items, CHUNK_SIZE):
        measurement = template_measurement()

        for asn, o in chunked_relay_set_items:

            ip, port = o["relays"][0]["or_addresses"].split(":")

            definition = template_definition()
            definition["target"] = ip
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


def create_many_to_one(measurement_name, probe_set, endpoint_set):
    measurement = template_measurement()

    for ip, port in [v.split(":") for v in endpoint_set["addresses"]]:
        definition = template_definition()
        definition["target"] = ip
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


def create_case1(measurement_name, c_as, g_as):
    return create_one_to_many(measurement_name + "-c1", c_as, g_as)


def create_case2(measurement_name, e_as_r, d_as):
    return create_many_to_one(measurement_name + "-c2", e_as_r, d_as)


def create_case3(measurement_name, d_as, e_as):
    return create_one_to_many(measurement_name + "-c3", d_as, e_as)


def create_case4(measurement_name, g_as_r, c_as):
    return create_many_to_one(measurement_name + "-c4", g_as_r, c_as)


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


def create_probes_set(probes):
    probes_per_as = dict()
    for p in probes["objects"]:
        if p["status_name"] == "Connected":
            probes_per_as.setdefault("AS" + str(p["asn_v4"]), []).append(p["id"])
    return probes_per_as


def create_guard_set(details):
    """Create (ii) g-as."""
    return create_simple_set(details, "Guard")


def create_exit_set(details):
    """Create (iv) e-as."""
    return create_simple_set(details, "Exit")


def create_simple_set(details, filtr):
    relay_per_as = {}
    for r in details["relays"]:
        if filtr in r["flags"]:
            if "as" in r:
                relay_per_as.setdefault(str(r["as"]), {"relays": []})["relays"].append({"fingerprint": r["fingerprint"],
                                                                                        "or_addresses":
                                                                                            r["or_addresses"][0]})
    return relay_per_as


def create_guard_with_ripe_probes_set(details, probes):
    """Create (iii) g-as-r."""
    return create_set_with_ripe_probes(details, probes, "Guard")


def create_exit_with_ripe_probes_set(details, probes):
    """Create (v) e-as-r."""
    return create_set_with_ripe_probes(details, probes, "Exit")


def create_set_with_ripe_probes(details, probes, filtr):
    relay_per_as = create_simple_set(details, filtr)
    probes = create_probes_set(probes)

    as_to_delete = []

    for asn in relay_per_as.keys():
        if asn in probes:
            relay_per_as[asn]["ids"] = probes[asn]
        else:
            as_to_delete.append(asn)

    for asn in as_to_delete:
        del relay_per_as[asn]

    return relay_per_as