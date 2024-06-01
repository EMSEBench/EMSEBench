import sys
import pandas as pd
import subprocess
from tqdm import tqdm
from datetime import datetime

window_size = sys.argv[1]
project_name = sys.argv[2]
window_size = int(window_size)
file_num_limit = 100 # the number of changed files in a commit should not exceed 100
temp_thres = 0.5 # threshold for checking bots

# Input: from commit-level results
commits_csv = "~/NewCommitMessageAnalysis/FileLevel/bugRef/" + project_name + "_bugRef.csv" # commit, bug introducing, ref.. <input>
cur_dataset = pd.read_csv(commits_csv, encoding="Latin-1")

#############
# If "bot column has been added, then comment out this part"
# Input: bot detection results
# bots_csv = "~/NewCommitMessageAnalysis/bots-all/bots_detection_results" + project_name + ".csv" #<input>
# bot_dataset = pd.read_csv(bots_csv, encoding="Latin-1")
# bots = set()
# for i in tqdm(range(0, bot_dataset.shape[0])):
#     cur_line = bot_dataset.iloc[i, :].values
#     author_email = str(cur_line[0]).strip()
#     bin_ratio = float(str(cur_line[3]).strip())
#     if bin_ratio < temp_thres:
#         bots.add(author_email)
#
# bots_record = []
# for i in tqdm(range(0, cur_dataset.shape[0])):
#     cur_line = cur_dataset.iloc[i, :].values
#     author_email = str(cur_line[3]).strip()
#     if author_email in bots:
#         bots_record.append(1)
#     else:
#         bots_record.append(0)
# bots_col = pd.DataFrame(bots_record, columns = ['bots'])
#
# result = pd.concat([cur_dataset, bots_col], axis=1)
# result.to_csv(commits_csv, index=False)
#
# #read again
# commits_csv = "~/NewCommitMessageAnalysis/FileLevel/bugRef/" + project_name + "_bugRef.csv" # <modified input>
# cur_dataset = pd.read_csv(commits_csv, encoding="Latin-1")
#################

def Intersection(lst1, lst2):
    return set(lst1).intersection(lst2)

ratios_why = []
ratios_what = []
ratios_good = []

commit_history = {}
commit_history_list = []
for i in tqdm(range(0, cur_dataset.shape[0])):
    cur_line = cur_dataset.iloc[i, :].values
    commit_id = str(cur_line[0]).strip()
    Why = int(str(cur_line[8]).strip())
    What = int(str(cur_line[9]).strip())
    Good = int(str(cur_line[10]).strip())
    Date = str(cur_line[4]).strip()
    bot = int(str(cur_line[13]).strip())
    commit_history[commit_id] = [Why, What, Good, Date, bot]
    commit_history_list.append(commit_id)

commit_history_list_wo_bots = []
for commit_id in commit_history_list:
    if commit_history[commit_id][4] != 1:
        commit_history_list_wo_bots.append(commit_id)



for i in tqdm(range(window_size, cur_dataset.shape[0])):
    cur_line = cur_dataset.iloc[i, :].values
    commit_id = str(cur_line[0]).strip()
    Why = int(str(cur_line[8]).strip())
    What = int(str(cur_line[9]).strip())
    Good = int(str(cur_line[10]).strip())
    bug_introducing = int(str(cur_line[11]).strip())
    refactoring = int(str(cur_line[12]).strip())

    if commit_history[commit_id][4] == 1:
        ratios_why.append("Bot")
        ratios_what.append("Bot")
        ratios_good.append("Bot")
        continue

    file_names_cmd = 'cd ~/ApacheProjects/' + project_name + " ; " + "git diff-tree --no-commit-id --name-only -r " + str(commit_id).strip()
    changed_files = subprocess.run(file_names_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout
    changed_files = changed_files.replace('\n', ' ')
    changed_files_list = changed_files.split()

    if len(changed_files_list) <= file_num_limit:
        all_traced_commits_list = []
        for changed_file in changed_files_list:
            changed_file = changed_file.strip()
            file_tracing_cmd = 'cd ~/ApacheProjects/' + project_name + " ; " + "git reset --hard " + str(commit_id).strip() + " ; " + "git log --format=%H --follow -- " + changed_file
            traced_commits = subprocess.run(file_tracing_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout
            traced_commits = traced_commits.replace('\n', ' ')
            traced_commits_list = traced_commits.split()
            #print(traced_commits_list)
            all_traced_commits_list += traced_commits_list

        all_traced_commits_list = list(set(all_traced_commits_list))
        final_traced_commits = Intersection(all_traced_commits_list, commit_history_list_wo_bots)
        final_traced_commits = sorted(final_traced_commits, key=lambda commit: commit_history[commit][3], reverse=True)
        windowed_traced_commits_list = final_traced_commits[:window_size]
        if len(windowed_traced_commits_list) <= 2:
            ratios_why.append("Not Applicable")
            ratios_what.append("Not Applicable")
            ratios_good.append("Not Applicable")
        else:
            tot = 0
            why_tot = 0
            what_tot = 0
            good_tot = 0
            for traced_commit in windowed_traced_commits_list:
                tot += 1
                why_tot += commit_history[traced_commit][0]
                what_tot += commit_history[traced_commit][1]
                good_tot += commit_history[traced_commit][2]
            ratios_why.append(why_tot/tot)
            ratios_what.append(what_tot/tot)
            ratios_good.append(good_tot/tot)
    else:
        ratios_why.append("Not Applicable")
        ratios_what.append("Not Applicable")
        ratios_good.append("Not Applicable")

ratios_why += ["Not Applicable"] * window_size
ratios_what += ["Not Applicable"] * window_size
ratios_good += ["Not Applicable"] * window_size
ratios_why_col = pd.DataFrame(ratios_why, columns = ['ratio_why'])
ratios_what_col = pd.DataFrame(ratios_what, columns = ['ratio_what'])
ratios_good_col = pd.DataFrame(ratios_good, columns = ['ratio_good'])

result = pd.concat([cur_dataset, ratios_why_col], axis=1)
result = pd.concat([result, ratios_what_col], axis=1)
result = pd.concat([result, ratios_good_col], axis=1)

output_csv = "~/NewCommitMessageAnalysis/FileLevel/FileRatio/" + project_name + '_File_ratio_' + str(window_size) + '.csv'
result.to_csv(output_csv, index=False)
