
from collections import OrderedDict
from ripetor import data, ip2as
import socket
N = 750

ip2as.load("data/2022/ip2asn-v4.tsv")

probes = data.load_probes("data/2022/probes.json")
ripe_asn_v4 = {p["asn_v4"] for p in probes["objects"] if p["status_name"] == "Connected"}
ripe_asn_v6 = {p["asn_v6"] for p in probes["objects"] if p["status_name"] == "Connected"}

stat_v4 = []
stat_v6 = []

def get_ip_addr(domain, ip_version="ipv4"):
    addr_fam = socket.AF_INET
    if ip_version == "ipv6":
        addr_fam = socket.AF_INET6 
    port = 0
    addr_set = set()
    try:
        results = socket.getaddrinfo(domain, port, addr_fam)
        for r in results:
            addr_set.add(r[4][0]) # just add teh ip addr
    except:
        pass
    return addr_set

def get_asn_info(domain, ip_version="ipv4"):
    addrs = get_ip_addr(domain, ip_version)
    ret = []
    for a in addrs:
        asn = ip2as.ip2asn(a)
        as_name = ip2as.get_as_name(asn)
        as_country = ip2as.get_as_country(asn)
        ret.append((a, asn, as_name, as_country))
    return ret

def has_ripe_probe(asn, ip_version="ipv4"):
    asn = ip2as.asn_to_int(asn)
    if ip_version == "ipv6":
        return asn in ripe_asn_v6
    return asn in ripe_asn_v4

def print_stat(stat):
    print("From Top %s" % N)
    print("resolved %d" % len(stat))
    print("in Diff AS %d" % len({x[2] for x in stat}))

    stat_with_probe = [x for x in stat if x[4]]
    print("Found %d" % len(stat_with_probe))
    print("in Diff AS %d" % len({x[2] for x in stat_with_probe}))

    asn_with_probe = list(OrderedDict.fromkeys(x[2] for x in stat_with_probe).keys()) # retains order, was changed from {x[2] for x in stat_with_probe}
    print("ASN with Probe:", asn_with_probe)
    for asn in asn_with_probe:
        print("\nasn %s %s:" % (asn, ip2as.get_as_name(asn)))
        print("\n".join([" ".join(s[:3]) for s in stat if s[2] == asn]))

with open("data/2022/top-1m.csv") as fp:
    for dest in [x.split(",")[1].strip() for x in [next(fp) for x in range(N)]]:
        addr_v4 = addr_v6 = None
        asn_v4 = asn_v6 = None
        as_name_v4 = as_name_v6 = None
        
        ret_v4 = get_asn_info(dest, "ipv4")
        ret_v6 = get_asn_info(dest, "ipv6")

        if not ret_v4:
            print("%20s Error IPv4" % dest)
        if not ret_v6:
            print("%20s Error IPv6" % dest)

        for addr_v4, asn_v4, as_name, as_country in ret_v4:
            hasp = has_ripe_probe(asn_v4, "ipv4")
            if as_country in ["UA", "RU"] or True:
                stat_v4.append((dest, addr_v4, asn_v4, as_name, hasp))
            print("%20s%32s%11s%35s  %s" % (dest, addr_v4, asn_v4, as_name[:30], hasp))

        for addr_v6, asn_v6, as_name, as_country in ret_v6:
            hasp = has_ripe_probe(asn_v6, "ipv6")
            if as_country in ["UA", "RU"] or True:
                stat_v6.append((dest, addr_v6, asn_v6, as_name, hasp))
            print("%20s%32s%11s%35s  %s" % (dest, addr_v6, asn_v6, as_name[:30], hasp))

if __name__ == '__main__':
    print_stat(stat_v4)
    print_stat(stat_v6)