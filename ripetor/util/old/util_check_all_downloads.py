# TODO move to ripetor after cleanup


import json
import os

#RUN = "20191231-135031"
import ripetor.atlas

RUNS = ['20200104-183935']

for RUN in RUNS:

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
                with open(filename, "r+") as fp:
                    res_old = json.load(fp)
                    print("%s %d exists with %d results" % (case, m_id, len(res_old)))
                    res_new = ripetor.atlas.retrieve_measurement(m_id)
                    if len(res_new) > len(res_old):
                        print("new result is larger with %d results ... saving new file" % len(res_new))
                        fp.seek(0)
                        json.dump(res_new, fp, indent=2)
                        fp.truncate()
            else:
                r = ripetor.atlas.retrieve_measurement(m_id)
                with open(filename, "w") as fp:
                    json.dump(r, fp, indent=2)
                print("%s %d downloaded" % (case, m_id))
