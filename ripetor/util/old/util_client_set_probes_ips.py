import ip2asn
from ripetor import data

ip2asn.load("data/ip2asn-v4.tsv")
probes = data.load_probes("20200102-210452/data/probes.json")

probes = [p for p in probes["objects"] if p["status_name"] == "Connected" and p["asn_v4"]]

probes_per_country = dict()
for p in probes:
    probes_per_country.setdefault(p["country_code"], []).append(p)

for country, probe_list in sorted([x for x in probes_per_country.items()], key=lambda x: len(x[1])):
    print("%s: %d probes, %d ASN" % (country, len(probe_list), len({p["asn_v4"] for p in probe_list})))

print("\n\n\ntake austria  ")
austria = dict()
for p in probes_per_country["AT"]:
    austria.setdefault(p["asn_v4"],[]).append(p)

for asn, probe_list in sorted([x for x in austria.items()], key=lambda x: len(x[1]), reverse=True)[:10]:
    print(asn, ip2asn.get_as_name("AS%s"%asn), len(probe_list), any([p["is_anchor"] for p in probe_list]))

print("\n\n\ntake germany  ")
germany = dict()
for p in probes_per_country["DE"]:
    germany.setdefault(p["asn_v4"],[]).append(p)

for asn, probe_list in sorted([x for x in germany.items()], key=lambda x: len(x[1]), reverse=True)[:10]:
    print(asn, ip2asn.get_as_name("AS%s"%asn), len(probe_list), any([p["is_anchor"] for p in probe_list]))

print(["AS"+str(asn) for asn, probe_list in sorted([x for x in germany.items()], key=lambda x: len(x[1]), reverse=True)[:10]])


print("\n\n\ntake USA  ")
germany = dict()
for p in probes_per_country["US"]:
    germany.setdefault(p["asn_v4"],[]).append(p)

for asn, probe_list in sorted([x for x in germany.items()], key=lambda x: len(x[1]), reverse=True)[:10]:
    print(asn, ip2asn.get_as_name("AS%s"%asn), len(probe_list), any([p["is_anchor"] for p in probe_list]))

print(["AS"+str(asn) for asn, probe_list in sorted([x for x in germany.items()], key=lambda x: len(x[1]), reverse=True)[:10]])


# print(json.dumps(probes_per_country, indent=2))
