from ripetor import data, statistics, measurements, atlas
import os
import json
from datetime import datetime
import logging
import time

BASEDIR = "run/"
DATEFORMAT = "%Y%m%d-%H%M%S"


def download(base_path):
    logging.info("Start download")

    # Download fresh data
    data_path = base_path + "/data/"
    os.makedirs(data_path)

    # summary = ripetor_data.load_summary(data_path + "summary.json")
    details = data.load_details(data_path + "details.json")
    probes = data.load_probes(data_path + "probes.json")
    data.download_ip2asn(data_path + "ip2asn-v4.tsv")

    logging.info("Stop download")

    return details, probes


def print_statistics(details, probes):
    logging.info("Start statistics")
    s = statistics.calculate_basic_tor_relay_stats(details)
    statistics.print_basic_stats(s)
    s = statistics.calculate_basic_ripe_stats(probes)
    statistics.print_basic_ripe_stats(s)
    logging.info("Stop statistics")


def create_sets_f(details, probes, c_as, d_as, base_path):
    logging.info("Start creating sets")

    g_as = measurements.create_guard_set(details)
    e_as = measurements.create_exit_set(details)
    g_as_r = measurements.create_guard_with_ripe_probes_set(details, probes)
    e_as_r = measurements.create_exit_with_ripe_probes_set(details, probes)

    sets = {"g_as": g_as, "e_as": e_as, "g_as_r": g_as_r, "e_as_r": e_as_r, "c_as": c_as, "d_as": d_as}

    set_path = base_path + "/measurement-sets/"
    os.makedirs(set_path)

    # Write all 4 sets to disk
    for k, v in sets.items():
        with open(set_path + "%s.json" % k, "w") as f:
            json.dump(v, f, indent=2)

    logging.info("Stop creating sets")

    return sets


def create_measurement_definitions(measurement_sets, now_string, base_path):
    logging.info("Start creating RIPE measurements")

    definitions_path = base_path + "/measurement-definitions/"
    os.makedirs(definitions_path)

    logging.info("Total theoretical cost c1: %d c2: %d c3: %d c4: %d total: %d" %
                 measurements.calculate_costs_for_measurement_set(measurement_sets))

    measurement_definitions = dict()
    if measurement_sets["c_as"]:
        measurement_definitions["case1"] = measurements.create_case1(now_string,
                                                                     measurement_sets["c_as"],
                                                                     measurement_sets["g_as"])
        measurement_definitions["case4"] = measurements.create_case4(now_string,
                                                                     measurement_sets["g_as_r"],
                                                                     measurement_sets["c_as"])

    if measurement_sets["d_as"]:
        measurement_definitions["case2"] = measurements.create_case2(now_string,
                                                                     measurement_sets["e_as_r"],
                                                                     measurement_sets["d_as"])
        measurement_definitions["case3"] = measurements.create_case3(now_string,
                                                                     measurement_sets["d_as"],
                                                                     measurement_sets["e_as"])

    for case_description, definition_list in measurement_definitions.items():
        for idx, single_measurement in enumerate(definition_list):
            logging.debug("Created measurement definition for %s part %d" % (case_description, idx))
            with open(definitions_path + "%s_%d.json" % (case_description, idx), "w") as f:
                json.dump(single_measurement, f, indent=2)

    logging.info("Stop creating RIPE measurements")
    return measurement_definitions


def start_executing_measurements(measurement_definitions, base_path):
    logging.info("Start executing RIPE measurements")

    response_path = base_path + "/measurement-responses/"
    os.makedirs(response_path)

    result_path = base_path + "/measurement-results/"
    os.makedirs(result_path, exist_ok=True)

    measurement_responses = {"downloaded": [], "finished": [], "case1": [], "case2": [], "case3": [], "case4": []}

    for case_description, definition_list in measurement_definitions.items():
        for idx, single_measurement in enumerate(definition_list):

            # Wait before setting up a new measurement
            atlas.wait_and_download(result_path,
                                            measurement_responses,
                                            nr_measurement=measurements.calculate_number_of_measurements(single_measurement))

            # Start the new measurement
            response = atlas.start_definition(single_measurement)
            time.sleep(15)
            logging.debug("Response for %s part %d: %s" % (case_description, idx, response))
            with open(response_path + "%s_%d_response.json" % (case_description, idx), "w") as f:
                json.dump(response, f, indent=2)
            measurement_responses[case_description].extend(response["measurements"])

    logging.info("Stop executing RIPE measurements")
    return measurement_responses


def download_results(measurement_responses, base_path):
    logging.info("Start downloading results")

    result_path = base_path + "/measurement-results/"
    os.makedirs(result_path, exist_ok=True)

    atlas.download_everything(result_path, measurement_responses)

    logging.info("Stop downloading results")


def main():
    now_string = datetime.now().strftime(DATEFORMAT)
    base_path = BASEDIR + now_string
    os.makedirs(base_path)

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=base_path + "/%s.log" % now_string,
                        filemode="w")

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
    logging.getLogger('').addHandler(console)

    logging.info("Start run on %s" % now_string)

    if atlas.get_measurements_running()["count"] > 0:
        logging.error("There are measurements running, dont execute")
        return

    # DOWNLOAD
    details, probes = download(base_path)

    # STATISTICS
    print_statistics(details, probes)

    # ADD MEASUREMENT DATA
    # c_as = {"probes": [26895], "addresses": ["185.81.215.146:0"]}  # Nextlayer / sba-research.org

    # Germany
    germany_top = ['AS3320', 'AS6830', 'AS31334', 'AS8881', 'AS3209', 'AS6805', 'AS553', 'AS680', 'AS8422', 'AS9145']

    usa_top = ['AS7922', 'AS701', 'AS7018', 'AS209', 'AS20115', 'AS22773', 'AS5650', 'AS20001', 'AS10796', 'AS11427']

    # c_as = util_get_country_client_set.get_c_as(germany_top, probes)
    # TODO

    c_as = {
        "probes": [
            10188,
            31727,
            10838,
            10654,
            30149,
            12935,
            19802,
            11185,
            11176,
            15736
        ],
        "addresses": [
            "217.240.17.218:0",
            "5.147.65.89:0",
            "90.187.19.21:0",
            "87.123.196.40:0",
            "88.72.105.133:0",
            "77.180.112.74:0",
            "141.7.123.70:0",
            "139.18.11.1:0",
            "78.34.181.94:0",
            "91.248.152.26:0"
        ],
        "asn": [
            "AS3320",
            "AS6830",
            "AS31334",
            "AS8881",
            "AS3209",
            "AS6805",
            "AS553",
            "AS680",
            "AS8422",
            "AS9145"
        ]
    }




    d_as = {}

    # SET described in Paper
    # tranco_set = {'AS3', 'AS15169', 'AS4837', 'AS24940', 'AS36351', 'AS14618', 'AS16509', 'AS14907', 'AS3356', 'AS7941'}
    # from util_get_tranco_dest_set import get_d_as
    # d_as = get_d_as(tranco_set, probes)


    # SET FOR SINGLE TEST
    # d_as = {"probes": [50609],
    #        "addresses": ["88.198.220.88:0"]}  # Hetzner / torproject.org

    # logging.info("destination set set to %s" % d_as)

    # CREATE SETS
    measurement_sets = create_sets_f(details, probes, c_as, d_as, base_path)

    # CREATE MEASUREMENT DEFINITIONS
    measurement_definitions = create_measurement_definitions(measurement_sets, now_string, base_path)

    # START MEASUREMENTS
    measurement_responses = start_executing_measurements(measurement_definitions, base_path)

    # START WAIT FOR RESULTS
    download_results(measurement_responses, base_path)

    logging.info("Run stopped")


if __name__ == '__main__':
    main()
