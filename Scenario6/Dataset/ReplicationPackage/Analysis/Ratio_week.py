import sys
import pandas as pd
from datetime import datetime, timedelta

result_csv = sys.argv[1] # predmeta, model predicted results csv
project_name = sys.argv[2]
cur_dataset = pd.read_csv(result_csv, encoding="Latin-1")
temp_thres = 0.5 # threshold for checking bots

ratio_why = [] # weekly ratio of good : all
ratio_what = []
ratio_good = []

author_why = dict()
author_what = dict()
author_good = dict()
author_commit_num = dict()

first_date = None

weekly_why = []
weekly_what = []
weekly_good = []
cur_author_why = dict()
cur_author_what = dict()
cur_author_good = dict()

weekly_commit_count = 0
weekly_commit_counts = [] # the number of commits in total for each week

# Input: bot detection results
bots_csv = "~/GoodCommitMessage/EverythingNewModel/bots-all/bots_detection_results" + project_name + ".csv"
bot_dataset = pd.read_csv(bots_csv, encoding="Latin-1")
bots = set()
for i in range(0, bot_dataset.shape[0]):
    cur_line = bot_dataset.iloc[i, :].values
    author_email = str(cur_line[0]).strip()
    bin_ratio = float(str(cur_line[3]).strip())
    if bin_ratio < temp_thres:
        bots.add(author_email)

def Average(l):
    avg = sum(l) / len(l)
    return avg

for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    author_name = str(cur_line[3]).strip()
    Why = int(cur_line[8])
    What = int(cur_line[9])
    Good = int(cur_line[10])
    Date = str(cur_line[4]).strip()

    if author_name in bots:
        continue

    if Date == "nan":
        continue
    if not first_date:
        first_date = Date
    #%Y-%m-%d OR
    #%m/%d/%y
    date_processed = datetime.strptime(Date, "%m/%d/%y")
    first_date_processed = datetime.strptime(first_date, "%m/%d/%y")
    if (date_processed - first_date_processed).days > 7:
        first_date = None
        weekly_commit_counts.append(weekly_commit_count)
        weekly_commit_count = 0

        if weekly_why:
            ratio_why.append(Average(weekly_why))
        weekly_why = []
        if weekly_what:
            ratio_what.append(Average(weekly_what))
        weekly_what = []
        if weekly_good:
            ratio_good.append(Average(weekly_good))
        weekly_good = []

        if cur_author_why:
            for author in cur_author_why:
                if author not in author_why:
                    author_why[author] = [Average(cur_author_why[author])]
                else:
                    author_why[author].append(Average(cur_author_why[author]))

        cur_author_why = dict()

        if cur_author_what:
            for author in cur_author_what:
                if author not in author_what:
                    author_what[author] = [Average(cur_author_what[author])]
                else:
                    author_what[author].append(Average(cur_author_what[author]))

        cur_author_what = dict()

        if cur_author_good:
            for author in cur_author_good:
                if author not in author_good:
                    author_good[author] = [Average(cur_author_good[author])]
                else:
                    author_good[author].append(Average(cur_author_good[author]))

            for author in cur_author_good:
                if author not in author_commit_num:
                    author_commit_num[author] = [len(cur_author_good[author])]
                else:
                    author_commit_num[author].append(len(cur_author_good[author]))

        cur_author_good = dict()

    weekly_commit_count += 1
    weekly_why.append(Why)
    weekly_what.append(What)
    weekly_good.append(Good)

    if author_name not in cur_author_why:
        cur_author_why[author_name] = [Why]
    else:
        cur_author_why[author_name].append(Why)

    if author_name not in cur_author_what:
        cur_author_what[author_name] = [What]
    else:
        cur_author_what[author_name].append(What)

    if author_name not in cur_author_good:
        cur_author_good[author_name] = [Good]
    else:
        cur_author_good[author_name].append(Good)

end_week = 416
print(len(ratio_why))
if len(ratio_why) >= 415:
    ratio_why = ratio_why[:415]
    ratio_what = ratio_what[:415]
    ratio_good = ratio_good[:415]
    weekly_commit_counts = weekly_commit_counts[:415]

if len(ratio_why) < 415:
    end_week = len(ratio_why) + 1

weekly_why_col = pd.DataFrame(ratio_why, columns = ['Why'])
weekly_what_col = pd.DataFrame(ratio_what, columns = ['What'])
weekly_good_col = pd.DataFrame(ratio_good, columns = ['Good'])
weekly_commit_counts_col = pd.DataFrame(weekly_commit_counts, columns=['Commit Counts'])

week_num = []
for i in range(1, end_week):
    week_num.append(i)

week_num_col = pd.DataFrame(week_num, columns = ['Week'])

weekly_result = pd.concat([week_num_col, weekly_why_col], axis=1)
weekly_result = pd.concat([weekly_result, weekly_what_col], axis=1)
weekly_result = pd.concat([weekly_result, weekly_good_col], axis=1)
weekly_result = pd.concat([weekly_result, weekly_commit_counts_col], axis=1)

weekly_csv = "~/GoodCommitMessage/EverythingNewModel/CommitChangeTrend/" + project_name + "_weekly_report.csv"
weekly_result.to_csv(weekly_csv, index=False)

# author_why_col = pd.DataFrame.from_dict(author_why)
# author_what_col = pd.DataFrame.from_dict(author_what)
# author_good_col = pd.DataFrame.from_dict(author_good)
#
# author_info = pd.concat([author_why_col, author_what_col], axis=1)
# author_info = pd.concat([author_info, author_good_col], axis=1)
#
# author_csv = "~/GoodCommitMessage/EverythingNewModel/" + project_name + "_authors_report.csv"
# author_info.to_csv(author_csv, index=False)
