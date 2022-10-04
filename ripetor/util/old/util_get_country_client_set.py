# TODO move to ripetor after cleanup

from ripetor import data
import logging


def get_c_as(as_set, probes_j):
    c_as = {"probes": [], "addresses": [], "asn":[]}
    probes = [p for p in probes_j["objects"] if p["status_name"] == "Connected"]

    for asn in as_set:
        my_probes = [p for p in probes if p["asn_v4"] == int(asn[2:])]

        skip = ['AS6830', 'AS3209'] # TODO DIRTY HACK ... PROBES OF THIS AS ARE NOT WORKING ... TAKE THE SECOND ONE

        for p in my_probes:
            if "address_v4" in p and p["address_v4"]:

                # TODO DIRTY HACK ... PROBES OF THIS AS ARE NOT WORKING ... TAKE THE SECOND ONE
                if asn in skip:
                    skip.remove(asn)
                    continue

                c_as["asn"].append(asn)
                c_as["probes"].append(p["id"])
                c_as["addresses"].append( p["address_v4"]+":0") # TODO THIS ONLY WORKS WITH ICMP TRACEROUTES

                logging.info("C_AS add %s %8d %15s    %s" % (asn, p["id"], p["address_v4"], p["is_public"]))
                break

    logging.info("C_AS %s" % c_as)
    return c_as


if __name__ == '__main__':

    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s')

    probes = data.load_probes(
        "run/20200102-210452/data/probes.json")

    # SET described in Paper
    tranco_set = ['AS3320', 'AS6830', 'AS31334', 'AS8881', 'AS3209', 'AS6805', 'AS553', 'AS680', 'AS8422', 'AS9145']

    d_as = get_c_as(sorted(list(tranco_set), key=lambda x:int(x[2:])), probes)
