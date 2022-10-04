
from ipaddress import ip_address
from ip2asn import IP2ASN


ip2a_v4 = None
ip2a_v6 = None


def load(fn):
    global ip2a_v4
    global ip2a_v6

    if not ip2a_v4:
        ip2a_v4 = IP2ASN(fn, ipversion=4)
    if 'ip2asn-v4' in fn and not ip2a_v6:
        fn = fn.replace("ip2asn-v4", "ip2asn-v6")
        ip2a_v6 = IP2ASN(fn, ipversion=6)

def _ip2asn(ip_string):
    if not ip2a_v4 and ip2a_v6:
        raise LookupError("No data loaded")
    try:
        ip = ip_address(ip_string)
        if ip.is_private:
            raise ValueError("IP addr is private")
        # per default we use ipv4
        ip2a = ip2a_v4
        # switch to ipv6 when ip str is in ipv6 format
        if ip.version == 6:
            ip2a = ip2a_v6
        result = ip2a.lookup_address(ip_string)
        number = result.get('ASN', 0)
        return f"AS{number}"
    except:
        pass
    return "AS0"

def ip2asn(ip_string):
    asn = _ip2asn(ip_string)
    asn = asn.replace("AS208294", "AS60729") # replace CIA TRIAD SECURITY LLC with ZWIEBELFREUNDE because ip2asn does not report it correctly
    return asn

def asn_to_int(asn):
    if isinstance(asn, str):
        number_str = asn.strip("AS")
        asn = int(number_str)
    return asn
    
def get_as_property(asn, attr):
    if not ip2a_v4 and ip2a_v6:
        raise LookupError("No data loaded")

    asn = asn_to_int(asn)
    
    # try v4
    try:
        result = ip2a_v4.lookup_asn(asn, limit=1)
        return result[0][attr]
    except:
        pass
    # fallback v6
    try:
        result = ip2a_v6.lookup_asn(asn, limit=1)
        return result[0][attr]
    except:
        pass
    # else return nothing
    return ""

def get_as_name(asn):
    return get_as_property(asn, 'owner')

def get_as_country(asn):
    return get_as_property(asn, 'country')
