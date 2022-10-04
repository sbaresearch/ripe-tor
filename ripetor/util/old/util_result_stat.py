# TODO move to ripetor after cleanup

import os
import json

BASE_DIR = "run/20191229-204350/measurement-results"

ccomplx = 0

for case in os.listdir(BASE_DIR):
    print("### CASE ###")
    cmplx = 0
    for r_fn in os.listdir(BASE_DIR+"/"+case):
        with open(BASE_DIR+"/"+case+"/"+r_fn) as fp:
            results = json.load(fp)
            print(case, r_fn, len(results))
            for idx, result in enumerate(results):
                hops = result["result"]
                print( "i%3d hops:%2d" % (idx, len(hops)), end=": ")
                h_cmplx = False
                for hop in hops:
                    print(len(hop["result"]), end=" ")
                    if len(hop["result"]) > 1:
                        h_cmplx = True
                if h_cmplx:
                    cmplx += 1

                print()

    ccomplx += cmplx
    print("complex %d" % cmplx)

print("gesamt complex: %d" % ccomplx)