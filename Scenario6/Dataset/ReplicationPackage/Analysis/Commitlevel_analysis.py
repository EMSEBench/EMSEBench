import json
import sys
import pandas as pd
import scipy.stats as stats
import csv
from numpy import std, mean, sqrt
import numpy as np
import time

start = time.time()

def cohen_d(scores_feature_metric,scores_new_metric):
    nx = len(scores_feature_metric)
    ny = len(scores_new_metric)
    dof = nx + ny - 2
    return (mean(scores_feature_metric) - mean(scores_new_metric)) / sqrt(((nx-1)*std(scores_feature_metric, ddof=1) ** 2 + (ny-1)*std(scores_new_metric, ddof=1) ** 2) / dof)

bug_f = sys.argv[1] # SZZ result: bug-introducing json file
commits_csv = sys.argv[2] # predmeta, models' predictions
ref_f = sys.argv[3] # RefMiner result: refactoring json file
window_size = sys.argv[4] # window size
project_name = sys.argv[5] # project name
window_size = int(window_size)
temp_thres = 0.5 # threshold for checking bots

# bug-introducing commits
json_file = open(bug_f)

SZZresults = json.load(json_file)

bug_introducing_commits = set()
for SZZpair in SZZresults:
    bug_introducing_commit = SZZpair[1]
    bug_introducing_commits.add(bug_introducing_commit)

print("The number of bug introducing commits found: ", len(bug_introducing_commits))

# refactoring commits
ref_json = open(ref_f)
refactoring_info = json.load(ref_json)
refactorings = set()

for record in refactoring_info['commits']:
    if record["refactorings"]:
        refactorings.add(str(record["sha1"]).strip())

#bots
# Input: bot detection results
bots_csv = "~/NewCommitMessageAnalysis/bots-all/bots_detection_results" + project_name + ".csv"
bot_dataset = pd.read_csv(bots_csv, encoding="Latin-1")
bots = set()
for i in range(0, bot_dataset.shape[0]):
    cur_line = bot_dataset.iloc[i, :].values
    author_email = str(cur_line[0]).strip()
    bin_ratio = float(str(cur_line[3]).strip())
    if bin_ratio < temp_thres:
        bots.add(author_email)


cur_dataset = pd.read_csv(commits_csv, encoding="Latin-1")
bug_introducing_markers = []
refactoring_markers = []
bots_record = []
for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    commit_id = str(cur_line[0]).strip()
    author_email = str(cur_line[3]).strip()
    if commit_id in bug_introducing_commits:
        bug_introducing_markers.append(1)
    else:
        bug_introducing_markers.append(0)

    if commit_id in refactorings:
        refactoring_markers.append(1)
    else:
        refactoring_markers.append(0)

    if author_email in bots:
        bots_record.append(1)
    else:
        bots_record.append(0)


ratios_why = ["Not Applicable"] * window_size
ratios_what = ["Not Applicable"] * window_size
ratios_good = ["Not Applicable"] * window_size

commit_history_wo_bots = []
why_history = []
what_history = []
good_history = []
for i in range(window_size, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    commit_id = str(cur_line[0]).strip()
    author_email = str(cur_line[3]).strip()
    Why = int(str(cur_line[8]).strip())
    What = int(str(cur_line[9]).strip())
    Good = int(str(cur_line[10]).strip())

    if author_email not in bots:
        commit_history_wo_bots.append(commit_id)
        why_history.append(Why)
        what_history.append(What)
        good_history.append(Good)

for i in range(window_size, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    commit_id = str(cur_line[0]).strip()
    Why = int(str(cur_line[8]).strip())
    What = int(str(cur_line[9]).strip())
    Good = int(str(cur_line[10]).strip())
    author_email = str(cur_line[3]).strip()

    if author_email in bots:
        ratios_why.append("Bot")
        ratios_what.append("Bot")
        ratios_good.append("Bot")
        continue

    idx = commit_history_wo_bots.index(commit_id)
    if idx - window_size >= 0:
        left_idx = idx - window_size
    else:
        left_idx = 0
    ratios_why.append(sum(why_history[left_idx:idx]) / window_size)
    ratios_what.append(sum(what_history[left_idx:idx]) / window_size)
    ratios_good.append(sum(good_history[left_idx:idx]) / window_size)



markers_col = pd.DataFrame(bug_introducing_markers, columns = ['bug_introducing'])
ref_markers_col = pd.DataFrame(refactoring_markers, columns = ['refactoring'])
bots_col = pd.DataFrame(bots_record, columns = ['bots'])
ratios_why_col = pd.DataFrame(ratios_why, columns = ['ratios_why'])
ratios_what_col = pd.DataFrame(ratios_what, columns = ['ratios_what'])
ratios_good_col = pd.DataFrame(ratios_good, columns = ['ratios_good'])
result = pd.concat([cur_dataset, markers_col], axis=1)
result = pd.concat([result, ref_markers_col], axis=1)
result = pd.concat([result, ratios_why_col], axis=1)
result = pd.concat([result, ratios_what_col], axis=1)
result = pd.concat([result, ratios_good_col], axis=1)
# #print(result)

bugRef_csv = '~/NewCommitMessageAnalysis/bugintroducingrefactoringcsvs/' + project_name + '_bugRef_' + str(window_size) + '.csv'
result.to_csv(bugRef_csv, index=False)

bugref_dataset = pd.read_csv(bugRef_csv, encoding="Latin-1")
bug_introducing_ratios_why = []
bug_introducing_ratios_what = []
bug_introducing_ratios_good = []

clean_nonref_ratios_why = []
clean_nonref_ratios_what = []
clean_nonref_ratios_good = []


for i in range(window_size, bugref_dataset.shape[0]):
    cur_line = bugref_dataset.iloc[i, :].values
    bug_introducing = float(str(cur_line[8]).strip()) # fix
    refactoring = float(str(cur_line[9]).strip())
    ratio_why = str(cur_line[10]).strip()
    ratio_what = str(cur_line[11]).strip()
    ratio_good = str(cur_line[12]).strip()

    if refactoring == 1:
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

output_csv = '~/NewCommitMessageAnalysis/CommitLevelResults/' + project_name + '_statistics_' + str(window_size) + '.csv'
col_name=["Window size", "Mean bug-inducing Why","Mean clean Why","Mean bug-inducing What","Mean clean What","Mean bug-inducing Good",
          "Mean clean Good","Why t-test","What t-test","Good t-test","Cohen's D Why","Cohen's D What","Cohen's D Good"]
with open(output_csv, 'a') as csvFile:
    wr = csv.DictWriter(csvFile, fieldnames=col_name)
    wr.writeheader()
    for ele in analysis_results:
        wr.writerow(ele)
end = time.time()
print(end - start)
