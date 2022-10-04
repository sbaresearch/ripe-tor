# TODO move to ripetor after cleanup

import json
import os

RUN = "20200104-012150"

response_dir = "run/" + RUN + "/measurement-responses/"
result_dir = "run/" + RUN + "/measurement-results/"

responses = {"case1": [], "case2": [], "case3": [], "case4": []}

for response_file in os.listdir(response_dir):
    with open(response_dir + response_file) as fp:
        responses[response_file[:5]].extend(json.load(fp)["measurements"])

for case, measurement_list in responses.items():
    for m_id in measurement_list:
        filename = result_dir + case + "/" + str(m_id) + ".json"
        if os.path.isfile(filename):
            with open(filename) as fp:
                results = json.load(fp)
                print(case + " " + str(m_id) + " " + str(len(results)) + " -", end=" ")
                for result in results:
                    print(len(result["result"]), end=" ")
                print()



