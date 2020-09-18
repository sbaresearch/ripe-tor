from bisect import bisect
from ipaddress import ip_address


lower = []
upper = []
as_nr = []
as_names = dict()


def load(fn):
    if not lower:
        with open(fn) as ip_fp:
            for i in ip_fp.readlines():
                split = i.strip("\n").split("\t")

                lower.append(ip_address(split[0]))
                upper.append(ip_address(split[1]))
                as_nr.append("AS"+split[2])
                as_names["AS"+split[2]] = split[4]


def ip2asn(ip_string):
    if not lower:
        raise LookupError("No data loaded")

    try:
        ip = ip_address(ip_string)
    except ValueError:
        return "AS0"

    if ip.is_private:
        return "AS0"

    idx = bisect(lower, ip) - 1

    if lower[idx] < ip < ip_address(upper[idx]):
        return as_nr[idx]
    else:
        return "AS0"


def get_as_name(asn):
    if not lower:
        raise LookupError("No data loaded")

    return as_names.get(asn, "")

