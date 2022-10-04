# TODO move to ripetor after cleanup

from ripetor import data
import logging


def get_d_as(as_set, probes_j):
    d_as = {"probes": [], "addresses": [], "asn":[]}
    probes = [p for p in probes_j["objects"] if p["status_name"] == "Connected"]

    for asn in as_set:
        my_probes = [p for p in probes if p["asn_v4"] == int(asn[2:])]

        for p in my_probes:
            if "address_v4" in p:
                d_as["asn"].append(asn)
                d_as["probes"].append(p["id"])
                d_as["addresses"].append( p["address_v4"]+":0") # TODO THIS ONLY WORKS WITH ICMP TRACEROUTES

                logging.info("D_AS add %s %8d %15s" % (asn, p["id"], p["address_v4"]))
                break

    logging.info("D_AS %s" % d_as)
    return d_as


if __name__ == '__main__':

    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s')

    probes = data.load_probes("/run/20191230-195822/data/probes.json")

    # SET described in Paper
    tranco_set = {'AS3', 'AS15169', 'AS4837', 'AS24940', 'AS36351', 'AS14618', 'AS16509', 'AS14907', 'AS3356', 'AS7941'}

    tranco_set = {'AS16509', 'AS14907', 'AS47764', 'AS37963', 'AS29169', 'AS8075', 'AS55990', 'AS396982', 'AS132203', 'AS14618', 'AS15169'}

    d_as = get_d_as(sorted(list(tranco_set), key=lambda x:int(x[2:])), probes)
