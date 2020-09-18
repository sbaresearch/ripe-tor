# TODO Refactor messed up file

from ripetor import data
import json
import os

import ip2asn
import logging

BASE_DIR = "../run/"


def load_as_statistic(details):
    """Load the AS Statistic from details... Sum up the guard/exit probability from all Relays in one AS"""
    logging.info("Load AS statistics from details")
    relays = details["relays"]
    stat = {"guard":{}, "exit":{}}

    for r in relays:
        if "as" in r:
            asn = r["as"]
            if "guard_probability" in r and r["guard_probability"] != 0:
                stat["guard"][asn] = stat["guard"].get(asn, 0) + r["guard_probability"]
            if "exit_probability" in r and r["exit_probability"] != 0:
                stat["exit"][asn] = stat["exit"].get(asn, 0) + r["exit_probability"]

    return stat


def open_result(download_dir, measurement_id):
    """Helper, opens a single json result"""
    fn = download_dir + str(measurement_id) + ".json"
    if not os.path.isfile(fn):
        logging.error("Measurement File: %s not there" % fn)
        return {}
    else:
        with open(fn) as fp:
            result = json.load(fp)
            return result


def get_probability_for_route(as_statistic, case, asn):
    """Depending on case, return guard or exit probability of one AS"""
    # case 1 guard probability of IP of relay of as
    if case in ("case1", "case4"):
        p = "guard"
    elif case in ("case2", "case3"):
        p = "exit"
    else:
        raise KeyError

    if asn in as_statistic[p]:
        logging.debug("%s %s is %f" % (asn, p, as_statistic[p][asn]))
        return as_statistic[p][asn]
    else:
        logging.warning("ASN %s not in AS Statistic - take 0 probability" % asn)
        return 0


def analyze_case(as_statistic, run_name, case):
    """Load and analyze one full case based on all downloaded results"""

    logging.info("Start analyzing measurement %s %s" % (run_name, case))

    measurement_dir = BASE_DIR + run_name + "/"
    download_dir = measurement_dir + "measurement-results/" + case + "/"

    basic_logger = logging.getLogger("basic_logger")
    basic_logger.info("Start " + run_name + " " + case)

    result_filenames = os.listdir(download_dir)

    basic_logger.info("%d filenames" % len(result_filenames))
    # TODO --- basic logger sollte mir die gesammelten größen ausgeben, damit ich verstehe wie die statistik zu rechnen ist....

    logging.info("Found %d results" % len(result_filenames))

    case_statistics = dict()

    # Each measurement has some form of guard or exit probability with that ASN ... that can be calculated
    for measurement_id in [filename.split(".")[0] for filename in result_filenames]:
        logging.debug("-" * 50)
        logging.info("Start Analyzing result %s" % measurement_id)

        results = open_result(download_dir, measurement_id)

        if len(results) > 1:
            if case in ("case2", "case4"):
                logging.info("Measurement %s has %d results" % (measurement_id, len(results)))
            else:
                logging.warning("Measurement %s has %d results" % (measurement_id, len(results)))
        elif len(results) == 0:
            logging.warning("Measurement %s has 0 results")

        # This is necessary for case2 and case4 where all results are in one measurement
        for result in results:

            # Get the ASN set from the traceroute result
            ip_list = get_asn_set_from_traceroute(result)
            asn_list = translate_ips_to_asn(ip_list)
            asn_set = set()
            asn_uniq_list = [x for x in asn_list if x != "AS0" and not (x in asn_set or asn_set.add(x))]

            ass_logger = logging.getLogger("as_set")
            ass_logger.info("%s m_id %s - size %d - %s" % (case, measurement_id, len(asn_set), asn_uniq_list))

            # For Case1 and Case3 the probability depends on the Destination
            if case in ("case1", "case3"):  # Check the AS of the measurement
                # TODO Check ob mit dst_adr möglich oder anders notwendig
                route_asn = ip2asn.ip2asn(result["dst_addr"])
                multidestasn = ip2asn.ip2asn(result["from"])

                logging.info("%s dst: %15s - ASN: %8s - %s  from: %15s - ASN: %8s - %s" % (case,
                                                                                           result["dst_addr"], route_asn, ip2asn.get_as_name(route_asn)[:20],
                                                                                           result["from"], multidestasn, ip2asn.get_as_name(multidestasn)[:20]))

            # For Case2 and Case4 the probability depends on the From Address
            elif case in ("case2", "case4"):
                route_asn = ip2asn.ip2asn(result["from"])
                multidestasn = ip2asn.ip2asn(result["dst_addr"])

                logging.info("%s From: %15s - ASN: %8s - %s   dst: %15s - ASN: %8s - %s" % (case,
                                                                                            result["from"], route_asn, ip2asn.get_as_name(route_asn)[:20],
                                                                                            result["dst_addr"], multidestasn, ip2asn.get_as_name(multidestasn)[:20]))
            else:
                logging.error("Case Error")
                raise RuntimeError

            if route_asn == "AS0":
                logging.warning("Did not find probability for Measurement %s %s" % (case, run_name))

            probability = get_probability_for_route(as_statistic, case, route_asn)
            logging.info("Probability for %8s-%30s is %f" % (route_asn, ip2asn.get_as_name(route_asn)[:30], probability))

            for asn in asn_set:
                # If AS appears on that route, sum it to the table
                # if asn in case_statistics:
                #     case_statistics["asn"] += probability

                case_statistics.setdefault(multidestasn, dict()).setdefault(asn, dict())[route_asn] = probability


    return case_statistics



def write_case_table(run_name, case, as_statistic, multiple_case_stat):



    if case in ("case1", "case4", "guard"):
        p = "guard"
    elif case in ("case2", "case3", "exit"):
        p = "exit"
    else:
        raise KeyError

    for target, case_stat in multiple_case_stat.items():

        fn = BASE_DIR + "/" + run_name + "/stat/" + case + "_" + target + "_table.tsv"
        logging.debug("Write %s statistic to %s" % (case, fn))

        asn_headers = sorted(as_statistic[p].keys(), key=lambda x: int(x[2:]))

        with open(fn, "w") as fp:
            fp.write("AS      \tSum     \tRoutes  \t" + "\t".join("%-8s" % s for s in asn_headers) + "\n")
            for asn in sorted(case_stat.keys(), key=lambda x: int(x[2:])):
                fp.write("%-8s\t%-8f\t%-8d\t" % (asn, sum(case_stat[asn].values()), len(case_stat[asn])))
                for h in asn_headers:
                    v = case_stat[asn].get(h, 0)
                    if v == 0:
                        fp.write("0       \t")
                    else:
                        fp.write("%8f\t" % v)
                fp.write("\n")


def write_case_stats(run_name, case, as_statistic, multiple_case_stat):

    if case in ("case1", "case4", "guard"):
        p = "guard"
    elif case in ("case2", "case3", "exit"):
        p = "exit"
    else:
        raise KeyError

    for target, case_stat in multiple_case_stat.items():

        fn = BASE_DIR + "/" + run_name + "/stat/" + case + "_" + target + "_stats.tsv"
        logging.debug("Write %s statistic to %s" % (case, fn))

        with open(fn, "w") as fp:
            fp.write("AS      \tAS Name             \tGain    \tOwn     \tSum     \tRoutes  \n")
            for asn in sorted(case_stat.keys(), key=lambda x: (sum(case_stat[x].values()), x), reverse=True):
                if {d:v for d,v in case_stat[asn].items() if v > 0}:  # Just print it if there is at least one route
                    fp.write("%-8s\t%-20s\t%-8f\t%-8f\t%-8f\t%-8d\t%s\n" % (asn,
                                                                            ip2asn.get_as_name(asn)[:20],
                                                                            sum(case_stat[asn].values()) - as_statistic[p].get(asn, 0),
                                                                            as_statistic[p].get(asn, 0),
                                                                            sum(case_stat[asn].values()),
                                                                            len({d:v for d,v in case_stat[asn].items() if v > 0}),  # Just remove the 0 values
                                                                            {d:"%8f"%v for d,v in case_stat[asn].items() if v > 0}))  # Just remove the 0 values


def write_latex_table(run_name, case, as_statistic, multiple_case_stat):

    if case in ("case1", "case4", "guard"):
        p = "guard"
    elif case in ("case2", "case3", "exit"):
        p = "exit"
    else:
        raise KeyError

    for target, case_stat in multiple_case_stat.items():

        fn = BASE_DIR + "/" + run_name + "/stat/" + case + "_" + target + "_latex_table.tex"
        logging.debug("Write %s statistic to %s" % (case, fn))

        with open(fn, "w") as fp:
            fp.write(" AS      & AS Name             & Direction  &Probability    & Prob. Relays     & Prob. Routes     & Number Routes  \\\\ \n")
            for asn in sorted(case_stat.keys(), key=lambda x: (sum(case_stat[x].values()), x), reverse=True):
                if {d:v for d,v in case_stat[asn].items() if v > 0}:  # Just print it if there is at least one route
                    prob = sum(case_stat[asn].values())
                    gain = prob - as_statistic[p].get(asn, 0)
                    nr_routes = len({d:v for d,v in case_stat[asn].items() if v > 0})
                    if prob > 0.025 or gain > 0.01 or nr_routes > 5:
                        fp.write("%-8s  & " % asn)
                        fp.write("%-10s  & " % ip2asn.get_as_name(asn)[:10])
                        fp.write("%-6s  & " % p)
                        fp.write("%-.3f  & " % prob if prob > 0 else "-         & ")
                        fp.write("%-.3f  & " % as_statistic[p].get(asn, 0) if as_statistic[p].get(asn, 0) > 0 else "-         & " )
                        fp.write("%-.3f  & " % gain if gain > 0 else "-         & ")
                        fp.write("%-3d  \\\\ \n" % nr_routes)


def write_data_for_guard_top(run_name, case, as_statistic, multiple_case_stat):

    if case in ("case1", "case4", "guard"):
        p = "guard"
    elif case in ("case2", "case3", "exit"):
        p = "exit"
    else:
        raise KeyError

    fn = BASE_DIR + "/" + run_name + "/stat/guard_data.txt"
    with open(fn, "w") as fp:

        final_stat = []  #   AS:  [prob value, prob value ... from different origins]

        for target, case_stat in multiple_case_stat.items():
            for asn in sorted(case_stat.keys(), key=lambda x: (sum(case_stat[x].values()), x), reverse=True):
                if {d:v for d,v in case_stat[asn].items() if v > 0}:  # Just print it if there is at least one route
                    prob = sum(case_stat[asn].values())
                    final_stat.append((asn, prob))

        for a,p in sorted(final_stat):
           fp.write("%s %f\n" % (a, p))


def write_double_latex_table( run_name, as_statistic, name, entry_stat, exit_stat):

    all_asn = set(entry_stat.keys()) | set(exit_stat.keys())

    fn = BASE_DIR + "/" + run_name + "/stat/combined_" +  name +"latex_table.tex"

    with open(fn, "w") as fp:
        fp.write("AS      & AS Name             & P on entry    & P on exit  & Combined  \\\\ \n")

        finstat = []

        for asn in sorted(set(entry_stat.keys()) | set(exit_stat.keys())):

            stat = dict()

            stat["asn"] = asn
            stat["asname"] = ip2asn.get_as_name(asn)[:10]
            stat["g_prob"] = sum(entry_stat.get(asn,{}).values())
            stat["e_prob"] = sum(exit_stat.get(asn,{}).values())
            stat["comb"] = stat["g_prob"] * stat["e_prob"]
            stat["nr_g_routes"] = len({d:v for d,v in entry_stat.get(asn,{}).items() if v > 0})
            stat["nr_e_routes"] = len({d: v for d, v in exit_stat.get(asn,{}).items() if v > 0})

            finstat.append(stat)

        finstat.sort(key=lambda x: x["comb"], reverse=True)

        for stat in finstat:
            fp.write("%-8s  & " % stat["asn"])
            fp.write("%-10s  & " % stat["asname"])
            fp.write("%-.3f  & " % stat["g_prob"]if stat["g_prob"] > 0  else "-       & ")
            fp.write("%-.3f  & " % stat["e_prob"] if stat["e_prob"] > 0 else "-       & ")
            fp.write("%-.3f  \\\\ \n" % stat["comb"] if stat["comb"] > 0     else "-       \\\\ \n")



def get_asn_set_from_traceroute(traceroute):
    """
    Retrieves the ASN out of the traceroute result object

    Args:
        traceroute: traceroute result object from RIPE measurement

    Returns: Set of ASN

    """
    logging.debug("Start getting ASN set from traceroute for measurement %s" % traceroute["msm_id"])

    f_src = traceroute["from"]
    logging.debug("From: %s" % f_src)

    f_dst = traceroute["dst_addr"]
    logging.debug("Dst: %s" % f_dst)

    logging.debug("Number Hops: %d" % len(traceroute["result"]))

    # If there is any error in the hops
    for hop in traceroute["result"]:
        if "error" in hop:
            logging.debug("Errors in Hop %s" % str(hop))

    # Does this traceroute contain timeouts
    timeouts = len([hop for hop in traceroute["result"] if "x" in hop.get("result")[0]])
    if timeouts > 0:
        logging.debug("Includes %d timeout" % timeouts)

    # Check how many result sections are in each hop
    len_list = [len(hop.get("result")) for hop in traceroute["result"]]

    # There are only simple result sections with one IP each
    if set(len_list) == {1}:
        f_hops = [hop["result"][0]["from"] for hop in traceroute["result"] if "from" in hop["result"][0]]
        logging.debug("Simple Traceroute, only %d hops with 1 result each and %d IPs: %s" % (len(traceroute["result"]), len(f_hops), f_hops))

    else:
        logging.debug("Complex Traceroute: Results are %s", str(len_list))

        f_hops = []
        # a 0 Approach - erstes Element im Array -> Scheisse
        # b All Approach - schauen wie sich das auswirkt
        # c Late verwerfen - dup verwerfen - icmpext verwerfen
        # d Schaun was stimmt?

        complex_logger = logging.getLogger("complex")
        complex_logger.info("Measurement %s" % traceroute["msm_id"])

        for idx, hop in enumerate(traceroute["result"]):
            if len(hop["result"]) == 1 and "from" in hop["result"][0]:
                f_hops.append(hop["result"][0]["from"])
            elif len(hop["result"]) > 1:
                complex_logger.info("hop %d has %d results: %s" % (idx, len(hop["result"]), hop))

                # If they are all the same, add it
                hop_r_set = {x["from"] for x in hop["result"] if "from" in x}
                if len(hop_r_set) == 1:
                    complex_logger.info("All Froms are the same, easy ... add %s" % hop["result"][0]["from"])
                    f_hops.append(hop["result"][0]["from"])
                else:
                    complex_logger.warning("Dont know what to do, add all IPs")
                    f_hops.extend([x["from"] for x in hop["result"] if "from" in x])

    # Add Source and Destination to List of IPs
    ips = [f_src, *f_hops, f_dst]
    return ips


def translate_ips_to_asn(ips):
    # Add a set of all ASN for that list of IPs
    # Private IP Ranges should be AS0, so discard it afterwards
    as_list = [ip2asn.ip2asn(ip) for ip in ips]
    logging.debug("Found %s for traceroute" % str(as_list))

    return as_list


def analyze_measurement(measurement):
    """
    Analyze one full measurement which consists of 4 cases
    """

    # CREATE STAT DIR

    stat_dir = BASE_DIR + "/" + measurement + "/stat"

    os.makedirs(stat_dir, exist_ok=True)


    # Add loggers for various aspects
    ass_logger = logging.getLogger("as_set")
    file_handler = logging.FileHandler(stat_dir + "/as_set.log", mode='w')
    file_handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
    ass_logger.addHandler(file_handler)

    basic_logger = logging.getLogger("basic_logger")
    file_handler = logging.FileHandler(stat_dir + "/basic_logger.log", mode='w')
    file_handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
    basic_logger.addHandler(file_handler)

    complex_logger = logging.getLogger("complex")
    file_handler = logging.FileHandler(stat_dir + "/complex.log", mode='w')
    file_handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
    complex_logger.addHandler(file_handler)

    # Load the datafiles
    logging.info("Load data files")
    ip2asn.load(BASE_DIR + "/" + measurement + "/data/ip2asn-v4.tsv")
    details = data.load_details(BASE_DIR + "/" + measurement + "/data/details.json")
    as_statistic = load_as_statistic(details)
    logging.info("... loaded")

    # Find for which cases there are directories
    cases = [c for c in os.listdir(BASE_DIR+"/"+measurement+"/measurement-results") if c.startswith("case")]
    logging.info("Found results for following cases: %s" % ", ".join(cases))

    stats = {}

    # Analyze these cases
    for case in cases:
        stats[case] = analyze_case(as_statistic, measurement, case)
        # write_case_table(measurement, case, as_statistic, stats[case])
        write_case_stats(measurement, case, as_statistic, stats[case])

#    logging.info("Origins: %d %d  -  Destinations %d %d" %(len(stats["case1"]), len(stats["case4"]), len(stats["case2"]), len(stats["case3"])))

    if "case1" in cases and "case4" in cases:
        res_g = combine_results(stats["case1"], stats["case4"])
        # write_case_table(measurement, "guard", as_statistic, res_g)
        write_case_stats(measurement, "guard", as_statistic, res_g)
        write_latex_table(measurement, "guard", as_statistic, res_g)
        write_data_for_guard_top(measurement, "guard", as_statistic, res_g)

    if "case2" in cases and "case3" in cases:
        res_e = combine_results(stats["case2"], stats["case3"])
        # write_case_table(measurement, "exit", as_statistic, res_e)
        write_case_stats(measurement, "exit", as_statistic, res_e)
        write_latex_table(measurement, "exit", as_statistic, res_e)

    # TODO Fast hack to get results now
    # if res_e.get("AS24940") and res_g.get("AS1764"):
    #     write_double_latex_table(measurement, as_statistic, "AS1764-AS24940", res_g.get("AS1764"), res_e.get("AS24940"))
    #
    for cas, cas_result in res_g.items():
        write_double_latex_table(measurement, as_statistic, "E-MAXSUM-FROM-"+cas, cas_result, res_e.get("MAXAND"))


def combine_results(s1, s2):
    if len(s1) == len(s2) == 0:
        return {}
    elif len(s1) == len(s2) == 1:

        name1, s1 = next(iter(s1.items()))
        name2, s2 = next(iter(s2.items()))
        if name1 != name2:
            raise KeyError

        result_table = dict()

        # For every row in either s1 or s2
        for asn in sorted(s1.keys() | s2.keys(), key=lambda x: int(x[2:])):

            s1v = s1.get(asn, {})
            s2v = s2.get(asn, {})

            result_table.setdefault(name1, dict())[asn] = {h: max(s1v.get(h, 0), s2v.get(h, 0)) for h in sorted(s1v.keys() | s2v.keys(), key=lambda x: int(x[2:]))}

        return result_table

    else:
        key_set = set(s1.keys()) | set(s2.keys())

        result_table = {"MAXAND": dict()}

        for name in key_set:
            ss1dict = s1.get(name, {})
            ss2dict = s2.get(name, {})

            for asn in sorted(ss1dict.keys() | ss2dict.keys(), key=lambda x: int(x[2:])):
                s1v = ss1dict.get(asn, {})
                s2v = ss2dict.get(asn, {})

                result_table.setdefault(name, dict())[asn] = {h: max(s1v.get(h, 0), s2v.get(h, 0)) for h in
                                                               sorted(s1v.keys() | s2v.keys(),
                                                                      key=lambda x: int(x[2:]))}

            for as_in_destination, gewichtungswerte in result_table[name].items():
                for gewichtungs_as, gewichtung in gewichtungswerte.items():
                    result_table["MAXAND"].setdefault(as_in_destination, dict())[gewichtungs_as] = gewichtung

        # TODO STILL ADD AN TOTAL OF ALL HERE ... HOW NOT KNOWN

        return result_table


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s')

   # analyze_measurement("20191231-044005")
    analyze_measurement("combined-top-de")




