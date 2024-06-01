import json
import sys
import pandas as pd
import scipy.stats as stats
import csv
from numpy import std, mean, sqrt
import numpy as np

window_size = sys.argv[1]

def cohen_d(scores_feature_metric,scores_new_metric):
    nx = len(scores_feature_metric)
    ny = len(scores_new_metric)
    dof = nx + ny - 2
    return (mean(scores_feature_metric) - mean(scores_new_metric)) / sqrt(((nx-1)*std(scores_feature_metric, ddof=1) ** 2 + (ny-1)*std(scores_new_metric, ddof=1) ** 2) / dof)

# All 238k commits together, we see differences between ratios of bug introducing and clean
bugRef_csv = '~/GoodCommitMessage/EverythingNewModel/CommitLevel/BIRatios/' + 'All_bugRef_' + str(window_size) + '.csv'

bugref_dataset = pd.read_csv(bugRef_csv, encoding="Latin-1")
bug_introducing_ratios_why = []
bug_introducing_ratios_what = []
bug_introducing_ratios_good = []

clean_nonref_ratios_why = []
clean_nonref_ratios_what = []
clean_nonref_ratios_good = []


for i in range(0, bugref_dataset.shape[0]):
    cur_line = bugref_dataset.iloc[i, :].values
    bug_introducing = float(str(cur_line[11]).strip()) # fix
    refactoring = float(str(cur_line[12]).strip())
    ratio_why = str(cur_line[13]).strip()
    ratio_what = str(cur_line[14]).strip()
    ratio_good = str(cur_line[15]).strip()

    if refactoring == 1:
        continue

    if ratio_why == "Not Applicable" or ratio_what == "Not Applicable" or ratio_good == "Not Applicable":
        continue
    if ratio_why == "Bot" or ratio_what == "Bot" or ratio_good == "Bot":
        continue
    else:
        ratio_why = float(ratio_why)
        ratio_what = float(ratio_what)
        ratio_good = float(ratio_good)

    if bug_introducing == 1:
        bug_introducing_ratios_why.append(ratio_why)
        bug_introducing_ratios_what.append(ratio_what)
        bug_introducing_ratios_good.append(ratio_good)
    else:
        clean_nonref_ratios_why.append(ratio_why)
        clean_nonref_ratios_what.append(ratio_what)
        clean_nonref_ratios_good.append(ratio_good)

print(bug_introducing_ratios_why)
#print(clean_nonref_ratios_why)

analysis_results = []
analysis_results.append({"Window size" : window_size,
    "Mean bug-inducing Why": sum(bug_introducing_ratios_why)/len(bug_introducing_ratios_why),
                         "Mean clean Why": sum(clean_nonref_ratios_why)/len(clean_nonref_ratios_why),
                         "Mean bug-inducing What": sum(bug_introducing_ratios_what)/len(bug_introducing_ratios_what),
                         "Mean clean What": sum(clean_nonref_ratios_what)/len(clean_nonref_ratios_what),
                         "Mean bug-inducing Good": sum(bug_introducing_ratios_good)/len(bug_introducing_ratios_good),
                         "Mean clean Good": sum(clean_nonref_ratios_good)/len(clean_nonref_ratios_good),
                         "Why t-test" : stats.ttest_ind(a=bug_introducing_ratios_why, b=clean_nonref_ratios_why, equal_var=False),
                         "What t-test" : stats.ttest_ind(a=bug_introducing_ratios_what, b=clean_nonref_ratios_what, equal_var=False),
                         "Good t-test" : stats.ttest_ind(a=bug_introducing_ratios_good, b=clean_nonref_ratios_good, equal_var=False),
                         "Cohen's D Why" : cohen_d(np.array(bug_introducing_ratios_why), np.array(clean_nonref_ratios_why)),
                         "Cohen's D What" : cohen_d(np.array(bug_introducing_ratios_what), np.array(clean_nonref_ratios_what)),
                         "Cohen's D Good" : cohen_d(np.array(bug_introducing_ratios_good), np.array(clean_nonref_ratios_good)),
                         })

output_csv = '~/GoodCommitMessage/EverythingNewModel/CommitLevel/All/' + 'All_statistics.csv'
col_name=["Window size", "Mean bug-inducing Why","Mean clean Why","Mean bug-inducing What","Mean clean What","Mean bug-inducing Good",
          "Mean clean Good","Why t-test","What t-test","Good t-test","Cohen's D Why","Cohen's D What","Cohen's D Good"]
with open(output_csv, 'a') as csvFile:
    wr = csv.DictWriter(csvFile, fieldnames=col_name)
    wr.writeheader()
    for ele in analysis_results:
        wr.writerow(ele)
