import sys
import pandas as pd
from tqdm import tqdm
import csv
import scipy.stats as stats
from numpy import std, mean, sqrt
import numpy as np

window_size = sys.argv[1]
project_name = sys.argv[2]
window_size = int(window_size)

def cohen_d(scores_feature_metric,scores_new_metric):
    nx = len(scores_feature_metric)
    ny = len(scores_new_metric)
    dof = nx + ny - 2
    return (mean(scores_feature_metric) - mean(scores_new_metric)) / sqrt(((nx-1)*std(scores_feature_metric, ddof=1) ** 2 + (ny-1)*std(scores_new_metric, ddof=1) ** 2) / dof)

analysis_csv = "~/GoodCommitMessage/EverythingNewModel/FileLevel/FileRatio/" + project_name + '_File_ratio_' + str(window_size) + '.csv'
cur_dataset = pd.read_csv(analysis_csv, encoding="Latin-1")

ratios_why_bug = []
ratios_what_bug = []
ratios_good_bug = []

ratios_why_nonrefclean = []
ratios_what_nonrefclean = []
ratios_good_nonrefclean = []

for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    bug_introducing = float(str(cur_line[11]).strip())  # fix
    refactoring = float(str(cur_line[12]).strip())
    ratio_why = str(cur_line[14]).strip()
    ratio_what = str(cur_line[15]).strip()
    ratio_good = str(cur_line[16]).strip()

    if refactoring == 1:
        continue

    if bug_introducing == 1:
        if ratio_why != "nan" and ratio_why != "Not Applicable" and ratio_why != "Bot":
            ratios_why_bug.append(float(ratio_why))
        if ratio_what != "nan" and ratio_what != "Not Applicable" and ratio_what != "Bot":
            ratios_what_bug.append(float(ratio_what))
        if ratio_good != "nan" and ratio_good != "Not Applicable" and ratio_good != "Bot":
            ratios_good_bug.append(float(ratio_good))
    else:
        if ratio_why != "nan" and ratio_why != "Not Applicable" and ratio_why != "Bot":
            ratios_why_nonrefclean.append(float(ratio_why))
        if ratio_what != "nan" and ratio_what != "Not Applicable" and ratio_what != "Bot":
            ratios_what_nonrefclean.append(float(ratio_what))
        if ratio_good != "nan" and ratio_good != "Not Applicable" and ratio_good != "Bot":
            ratios_good_nonrefclean.append(float(ratio_good))


analysis_results = []
analysis_results.append({"Window size" : window_size,
    "Mean bug-inducing Why": sum(ratios_why_bug)/len(ratios_why_bug),
                         "Mean clean Why": sum(ratios_why_nonrefclean)/len(ratios_why_nonrefclean),
                         "Mean bug-inducing What": sum(ratios_what_bug)/len(ratios_what_bug),
                         "Mean clean What": sum(ratios_what_nonrefclean)/len(ratios_what_nonrefclean),
                         "Mean bug-inducing Good": sum(ratios_good_bug)/len(ratios_good_bug),
                         "Mean clean Good": sum(ratios_good_nonrefclean)/len(ratios_good_nonrefclean),
                         "Why t-test" : stats.ttest_ind(a=ratios_why_bug, b=ratios_why_nonrefclean, equal_var=False),
                         "What t-test" : stats.ttest_ind(a=ratios_what_bug, b=ratios_what_nonrefclean, equal_var=False),
                         "Good t-test" : stats.ttest_ind(a=ratios_good_bug, b=ratios_good_nonrefclean, equal_var=False),
                         "Cohen's D Why" : cohen_d(np.array(ratios_why_bug), np.array(ratios_why_nonrefclean)),
                         "Cohen's D What" : cohen_d(np.array(ratios_what_bug), np.array(ratios_what_nonrefclean)),
                         "Cohen's D Good" : cohen_d(np.array(ratios_good_bug), np.array(ratios_good_nonrefclean)),
                         })

output_csv = "~/GoodCommitMessage/EverythingNewModel/FileLevel/FileAnalysis/" + project_name + 'filelevel_statistics' + '.csv'
col_name=["Window size", "Mean bug-inducing Why","Mean clean Why","Mean bug-inducing What","Mean clean What","Mean bug-inducing Good",
          "Mean clean Good","Why t-test","What t-test","Good t-test","Cohen's D Why","Cohen's D What","Cohen's D Good"]
with open(output_csv, 'a') as csvFile:
    wr = csv.DictWriter(csvFile, fieldnames=col_name) #, fieldnames=col_name
    wr.writeheader()
    for ele in analysis_results:
        wr.writerow(ele)
