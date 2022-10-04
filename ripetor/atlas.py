import argparse
import json
import logging
import os
import pathlib
import time
import requests

BASE_URL = "https://atlas.ripe.net/api/v2/measurements/"  # "https://webhook.site/8d482d35-ee70-4d12-a4d2-1428fa32813d/"
API_KEY = os.getenv("RIPE_KEY")

if API_KEY is None:
    logging.error("No API key found at env variable 'RIPE_KEY'")
    exit(1)


def start_definition(definition):
    logging.info("Start definition")
    response = requests.post(BASE_URL + "?key=" + API_KEY, json=definition)
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


def get_measurement_status(measurement_id, update=False):
    """
    retrieves the status of the given measurement and returns the json if status == 200 otherwise None
    if update is set to True, it will also send a PATCH before to request a status update
    """
    measurement_id = str(measurement_id)
    measurement_id = measurement_id.strip()
    api_url = f'{BASE_URL}{measurement_id}'

    if update:
        patch_url = f'{api_url}?key={API_KEY}'
        response = requests.patch(patch_url)
        if response.status_code != 200:
            return None

    response = requests.get(api_url)
    if response.status_code != 200:
        return None

    return response.json()


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
        logging.error(f"{measurement_id} - HTTP Error {response.status_code}")
        logging.error(response.content)


def stop_measurement(measurement_id):
    logging.debug("DELETE " + BASE_URL + str(measurement_id))
    response = requests.delete(BASE_URL + str(measurement_id) + "?key=%s" % API_KEY)
    if response.ok:
        logging.debug("measurement %d deleted", measurement_id)
        logging.debug(response.content)
    else:
        logging.warning(f"{measurement_id} measurement delete error, maybe cannot be deleted")
        logging.warning(response.content)


def update_measurement(measurement_id):
    """Do this because RIPE Atlas sometimes does not update the measurement status until PATCH"""
    logging.debug("PATCH " + BASE_URL + str(measurement_id))
    response = requests.patch(BASE_URL + str(measurement_id) + "?key=%s" % API_KEY, json={"is_public": True})
    if response.ok:
        logging.debug(f"Measurement {measurement_id} patched")
    else:
        logging.error(f'Could not PATCH existing measurement:')
        logging.error(response.content)


def update_downloaded_finished(measurement_responses):
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
            # Send PATCH to update the current status as RIPE does not keep status continuously updated
            update_measurement(m_id)

    # Update downloaded list to remove the ones that have been finished
    measurement_responses["downloaded"] = [m for m in measurement_responses["downloaded"] if m not in measurement_responses["finished"]]


def download_everything(base_dir, measurement_responses):
    """
    Will try to download all running measurements exactly one time.
    This method will NOT retry to download, call method multiple times with some delay.
    Will do some housekeeping to keep track of running, downloaded and finished measurements.
    """
    base_path = pathlib.Path(base_dir)
    downloaded_files = 0

    # Check all measurements that have already been downloaded
    update_downloaded_finished(measurement_responses)

    for case, m_id_list in measurement_responses.items():
        # ignore helper categories
        if case in ["downloaded", "finished"]:
            continue

        # create our case directory from the base path
        case_dir = base_path.joinpath(case)
        case_dir.mkdir(parents=True, exist_ok=True)

        for m_id in m_id_list:
            # Replaced: fn = base_dir + "/" + case + "/" + str(m_id) + ".json"
            # Build filepath from case path
            file_name = str(m_id).strip()
            fn = case_dir.joinpath(f'{file_name}.json')

            # Grab the results for this measurement
            m_json = retrieve_measurement(m_id)
            # check if we actually got a result
            if m_json is None:
                logging.warning(f'Could not download measurement result {m_id}')
                continue
            elif isinstance(m_json, list) and len(m_json) == 0:
                # Removing logging for empty result, this just spams the console
                # apparently this case happens more often than thought
                # logging.warning(f'Got empty result for {m_id}')
                continue

            # If we already have downloaded some results for a measurement,
            # open the existing file and compare the results
            # if there are more responses in the new file than in the old one, keep the measurement as active
            # i.e. do not add the measurement into the downloaded helper category
            # if however we have the same number of results, we add the measurement to the downloaded category
            # thus sending a stop measurement to ripe
            if fn.is_file():
                # Should not happen anymore except for case2 and case4
                # if case in ("case1", "case3"):
                #     logging.warning("... check measurement for  %d ... exists" % m_id)
                #     measurement_responses["downloaded"].append(m_id)
                # else:
                logging.info(f'{m_id}: Updating existing result for {case}')

                with open(fn, "r+") as fp:
                    res_old = json.load(fp)
                    logging.debug(f'{m_id}: res old - new: {len(res_old)} - {len(m_json)}')

                    if isinstance(m_json, list) and len(m_json) > len(res_old):
                        # New result is larger than old one, keep the measurement as active
                        # Do NOT mark the measurement as downloaded or something
                        fp.seek(0)
                        json.dump(m_json, fp, indent=2)
                        fp.truncate()
                    elif isinstance(m_json, list) and len(m_json) == len(res_old):
                        # Result did not change, add to downloaded list
                        stop_measurement(m_id)
                        measurement_responses["downloaded"].append(m_id)
            else:
                # Found result for measurement, download it
                logging.debug("write result %s %d" % (case, m_id))
                with open(fn, "w") as f:
                    json.dump(m_json, f, indent=2)
                    downloaded_files += 1

                # logging.info(f'{m_id} ({case}) Stopping Measurement')
                # Quick Hack, I want case 2 and case4 to be checked more often
                # TODO If CAS OR DAS > 1
                # if case in ("case1", "case3"):
                #     stop_measurement(m_id)
                #     measurement_responses["downloaded"].append(m_id)

        # Update List of still running cases within each case
        measurement_responses[case] = [m for m in m_id_list if m not in measurement_responses["downloaded"]]

    total_responses = sum(map(len, measurement_responses.values()))
    logging.info(f"Downloaded {downloaded_files} new files (from {total_responses} responses at this time)")


def wait_and_download(result_dir, measurement_responses, nr_measurement=0):
    if nr_measurement:
        # MM: get ALL running measurements on the given API key
        # this does also include non-involved measurements
        running = get_measurements_running()
        while running["count"] + nr_measurement > MAX_MEASUREMENTS:
            logging.info(
                f'Waiting {WAIT_TIME_SECONDS} seconds; {running["count"]} running and {nr_measurement} to start'
            )
            time.sleep(WAIT_TIME_SECONDS)

            # MM: Try to download all currently running measurements
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
            update_measurement((m["id"]))

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
