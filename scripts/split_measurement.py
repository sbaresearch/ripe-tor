import argparse
import ip2asn
import json
from pathlib import Path


def get_asn_sets():
    tranco_set_historic = {'AS3', 'AS15169', 'AS4837', 'AS24940', 'AS36351', 'AS14618', 'AS16509', 'AS14907', 'AS3356',
                           'AS7941'}
    tranco_set_v4 = {'AS15169', 'AS16509', 'AS8075', 'AS4837', 'AS14907', 'AS55990', 'AS37963', 'AS132203',
                     'AS4134', 'AS4812', 'AS47764', 'AS29169', 'AS14618', 'AS396982'}
    tranco_set_v6 = {'AS15169', 'AS16509', 'AS14907', 'AS47764', 'AS63949', 'AS3', 'AS37963', 'AS197695', 'AS32',
                     'AS14618'}

    russia_censored_v4 = {'AS200350', 'AS15497', 'AS25532', 'AS207651', 'AS9123', 'AS28907', 'AS3326', 'AS197695',
                          'AS25521', 'AS12722'}

    tranco_set = set(tranco_set_v4 | tranco_set_v6 | tranco_set_historic)
    russia_set = russia_censored_v4
    return tranco_set, russia_set


def read_results(case_path: Path, ip2asn: ip2asn.IP2ASN):
    response_dict = {}
    for measurement_path in case_path.glob("*.json"):
        with open(measurement_path) as measurement_file:
            json_file = json.load(measurement_file)

            dst_addresses = set()
            msm_ids = set()
            for measurement in json_file:
                dst_addresses.add(measurement['dst_addr'])
                msm_ids.add(measurement['msm_id'])

            if len(dst_addresses) != 1:
                print(f'Found {len(dst_addresses)} instead of 1 in file {measurement_path}')
                continue

            dst_address = dst_addresses.pop()
            msm_id = msm_ids.pop()
            asn = ip2asn.lookup_address(dst_address)
            response_dict[msm_id] = asn['ASN']
    return response_dict

def main():

    tranco, russia = get_asn_sets()
    parser = argparse.ArgumentParser(description='Split measurement directory')
    parser.add_argument('-i', '--input', type=str, required=True, help='Path to measurement to split')
    parser.add_argument('-6', '--ipv6', action='store_true', help='Switch to IPv6 parsing')
    parser.add_argument('-a', '--ip2asn', type=str, required=True, help='Path to the IP2ASN file')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f'Path to input files does not exist!')
        exit(1)

    ip2asn_path = Path(args.ip2asn).absolute()
    if not ip2asn_path.exists() or not ip2asn_path.is_file():
        print(f'Path to ip2asn file does not exist!')
        exit(1)
    ip2asn_path = str(ip2asn_path)

    if args.ipv6:
        asn_lookup = ip2asn.IP2ASN(ip2asn_file=ip2asn_path, ipversion=6)
    else:
        asn_lookup = ip2asn.IP2ASN(ip2asn_file=ip2asn_path)

    split = {
        "c2": {
            'tranco': [], 'russia': []
        },
        "c3": {
            'tranco': [], 'russia': []
        }
    }

    input_path = input_path.joinpath('measurement-results')
    case2_path = input_path.joinpath("case2")
    print("CASE 2")
    response = read_results(case2_path, asn_lookup)

    for msm_id, asn in response.items():
        asn_str = f'AS{asn}'
        if asn_str in tranco:
            split['c2']['tranco'].append(msm_id)
        if asn_str in russia:
            split['c2']['russia'].append(msm_id)

    case3_path = input_path.joinpath("case3")
    print("CASE 3")
    response = read_results(case3_path, asn_lookup)
    for msm_id, asn in response.items():
        asn_str = f'AS{asn}'
        if asn_str in tranco:
            split['c3']['tranco'].append(msm_id)
        if asn_str in russia:
            split['c3']['russia'].append(msm_id)

    print(json.dumps(split, indent=4))


if __name__ == '__main__':
    main()
