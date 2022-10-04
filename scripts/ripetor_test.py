# Test script to reimplement the downloading
# Basically was just a small programming exercise to understand the ripe api
# ripetor.py is implemented in a similar but already more optimized fashion

import json
import logging
import pathlib
import time

from ripetor import measurements, atlas
from ripetor.util.common import get_console_logger


class RIPETorTest:

    def __init__(self):
        self.__fixed_measurements = []
        self.__sleep_time = 30

        self.__log = get_console_logger("RIPETorTest")
        self.__log.setLevel(logging.DEBUG)
        self.__basepath = pathlib.Path("/tmp/ripetor/")

        self.response_path = self.__basepath.joinpath("measurement-responses")
        self.result_path = self.__basepath.joinpath('measurement-results')

    def __create_directories(self):
        self.__log.info("Creating necessary directories")
        self.response_path.mkdir(parents=True, exist_ok=True)
        self.result_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def __load_measurement_definition():
        # Load test similar to test case 2 but with altered target address
        with open('run/test_data/case3_0.json', 'r') as test_case:
            test_json = json.load(test_case)
            return test_json

    def __do_measurements(self, definition):
        self.__log.info("Start executing RIPE measurements")

        responses = {'running': [], 'downloaded': [], 'finished': [], 'failed': [], 'download_failed': []}

        measurement_number = measurements.calculate_number_of_measurements(definition)
        self.__log.info(f'Number measurements: {measurement_number}')

        if len(self.__fixed_measurements) == 0:
            self.__log.info(f'Sending definition to RIPE')
            # response is already a parsed json -> dict!
            response = atlas.start_definition(definition)

            if response is None:
                self.__log.error(f'POSTing definition has failed!')
                exit(2)

            # Definitions have been successfully pushed, check response for measurement IDs to download!
            self.__log.info(f'Dumping response to json')
            case_response_path = self.response_path.joinpath(f'case3_0_response.json')
            with open(case_response_path, "w") as f:
                json.dump(response, f, indent=2)

            # grab the array of measurement IDs from RIPE
            measurement_ids = response["measurements"]
            responses['running'].extend(measurement_ids)
        else:
            self.__log.info(f'Using existing measurements')
            responses['running'] = self.__fixed_measurements

        # run through all measurements, check if they are done and download them
        max_iterations = 20
        running_ids = len(responses['running'])
        while running_ids > 0:

            for measurement_id in responses['running']:
                response = atlas.get_measurement_status(measurement_id, update=True)
                if response is None:
                    self.__log.warning(f'Could not get status for measurement_id {measurement_id}')
                    continue

                measurement_status = int(response['status']['id'])
                self.__log.debug(f'Status for {measurement_id} is {measurement_status}')

                if measurement_status < 4:
                    # measurement is still running
                    pass
                elif measurement_status == 4:
                    # measurement is finished
                    responses['finished'].append(measurement_id)
                    responses['running'].remove(measurement_id)
                else:
                    # measurement failed
                    responses['failed'].append(measurement_id)
                    responses['running'].remove(measurement_id)

            # download finished measurements
            download_responses = self.__download_measurements(responses['finished'])
            if download_responses is not None:
                responses['downloaded'].extend(download_responses['downloaded'])
                responses['download_failed'].extend(download_responses['download_failed'])
                responses['finished'].clear()

            running_ids = len(responses['running'])

            if running_ids > 0:
                self.__log.info(f'{running_ids} IDs still running, waiting for them')
                time.sleep(self.__sleep_time)
                max_iterations -= 1

            if max_iterations < 0:
                self.__log.error(f'Max iterations reached! Stopping!')
                running_ids = 0
                responses['failed'].extend(responses['running'])
                responses['running'].clear()

        return responses

    def __download_measurements(self, measurement_ids):
        if len(measurement_ids) == 0:
            return

        result_dict = {
            'downloaded': [],
            'download_failed': []
        }

        for measurement_id in measurement_ids:
            self.__log.debug(f'Trying to download result for {measurement_id}')
            result = atlas.retrieve_measurement(measurement_id)
            if result is None:
                self.__log.error(f'Could not get result for measurement {measurement_id}')
                result_dict['download_failed'].append(measurement_id)
                continue

            result_path = self.result_path.joinpath(f'{measurement_id}_result.json')
            with open(result_path, 'w') as result_file:
                json.dump(result, result_file)
            self.__log.debug(f'Successfully downloaded result for {measurement_id}')
            result_dict['downloaded'].append(measurement_id)

        return result_dict

    def main(self):
        self.__create_directories()
        definitions = self.__load_measurement_definition()
        responses = self.__do_measurements(definitions)
        self.__log.info(f'Finished measurements with results:')
        self.__log.info(f'{json.dumps(responses, indent=4)}')


if __name__ == '__main__':
    ripetor_test = RIPETorTest()
    ripetor_test.main()
