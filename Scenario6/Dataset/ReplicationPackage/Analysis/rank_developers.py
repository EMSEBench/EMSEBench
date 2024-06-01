# 1. get a set of core developers
# 2. See core/non-core developer group as a whole, from history, get the ratio
#of good-all. See if there is any difference between the quality of cm from
#core and non-core developers. Answer who writes bad commit messages
# 3. Take Month as the time unit, do core/non-core developers write more
#good commit messages over time?

# out of all the messages one writes in a week, how many are good?

import sys
import pandas as pd
from datetime import datetime, timedelta

projmeta_csv = sys.argv[1] # prediction results predmeta
project_name = sys.argv[2]
cur_dataset = pd.read_csv(projmeta_csv, encoding="Latin-1 ")
temp_thres = 0.5 # threshold for checking bots

author_ranking = dict()

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

bot_contributions = 0
total_contributions = 0
# calculate core vs non-core
for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    author_name = str(cur_line[3]).strip()
    total_contributions += 1
    if author_name in bots:
        bot_contributions += 1
    if author_name in author_ranking:
        author_ranking[author_name] += 1
    else:
        author_ranking[author_name] = 1

author_ranking = {k:v for k,v in sorted(author_ranking.items(), key=lambda item: item[1], reverse=True)}

cur_contributions = 0
core_developer_set = set() # core developers, others are non-core
for author in author_ranking.keys():
    cur_contributions += author_ranking[author]
    core_developer_set.add(author)
    if cur_contributions >= 0.8 * (total_contributions - bot_contributions):
        break

def Average(l):
    if len(l) == 0:
        return "No Message"
    avg = sum(l) / len(l)
    return avg

core_quality_all_why = [] # waiting to be averaged
core_quality_all_what = []
core_quality_all_good = []
noncore_quality_all_why = []
noncore_quality_all_what = []
noncore_quality_all_good = []

for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    author_name = str(cur_line[3]).strip()
    Why = int(cur_line[8])
    What = int(cur_line[9])
    Good = int(cur_line[10])

    if author_name in core_developer_set:
        core_quality_all_why.append(Why)
        core_quality_all_what.append(What)
        core_quality_all_good.append(Good)
    else:
        noncore_quality_all_why.append(Why)
        noncore_quality_all_what.append(What)
        noncore_quality_all_good.append(Good)

# # Throughout the history, what is the over quality of core/non-core
# with open('~/GoodCommitMessage/ApacheResults/Analyses/NewAuthorAnalysis/AllHistoryAuthors.csv', 'a') as f:
#     f.write("%s,%s,%s,%s,%s,%s"%(Average(core_quality_all_why), Average(core_quality_all_what), Average(core_quality_all_good),Average(noncore_quality_all_why), Average(noncore_quality_all_what), Average(noncore_quality_all_good)) + '\n')

first_date = None
monthly_core_why = []
monthly_core_what = []
monthly_core_good = []
monthly_noncore_why = []
monthly_noncore_what = []
monthly_noncore_good = []

core_why = []
core_what = []
core_good = []
noncore_why = []
noncore_what = []
noncore_good = []

#%Y-%m-%d OR
#%m/%d/%y
for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    author_name = str(cur_line[3]).strip()
    Why = int(cur_line[8])
    What = int(cur_line[9])
    Good = int(cur_line[10])
    Date = str(cur_line[4]).strip()

    if Date == "nan":
        continue
    if not first_date:
        first_date = Date

    date_processed = datetime.strptime(Date, "%m/%d/%y")
    first_date_processed = datetime.strptime(first_date, "%m/%d/%y")
    if (date_processed - first_date_processed).days > 7:
        first_date = None
        core_why.append(Average(monthly_core_why))
        core_what.append(Average(monthly_core_what))
        core_good.append(Average(monthly_core_good))

        noncore_why.append(Average(monthly_noncore_why))
        noncore_what.append(Average(monthly_noncore_what))
        noncore_good.append(Average(monthly_noncore_good))

        monthly_core_why = []
        monthly_core_what = []
        monthly_core_good = []
        monthly_noncore_why = []
        monthly_noncore_what = []
        monthly_noncore_good = []


    if author_name in core_developer_set:
        monthly_core_why.append(Why)
        monthly_core_what.append(What)
        monthly_core_good.append(Good)
    else:
        monthly_noncore_why.append(Why)
        monthly_noncore_what.append(What)
        monthly_noncore_good.append(Good)

end_week = 416
if len(core_why) >= 415:
    core_why = core_why[:415]
    core_what = core_what[:415]
    core_good = core_good[:415]
    noncore_why = noncore_why[:415]
    noncore_what = noncore_what[:415]
    noncore_good = noncore_good[:415]

if len(core_why) < 415:
    end_week = len(core_why) + 1

week_num = []
for i in range(1, end_week):
    week_num.append(i)

week_num_col = pd.DataFrame(week_num, columns = ['Week'])

core_why_col = pd.DataFrame(core_why, columns = ['Core Why'])
core_what_col = pd.DataFrame(core_what, columns = ['Core What'])
core_good_col = pd.DataFrame(core_good, columns = ['Core Good'])

noncore_why_col = pd.DataFrame(noncore_why, columns = ['NonCore Why'])
noncore_what_col = pd.DataFrame(noncore_what, columns = ['NonCore What'])
noncore_good_col = pd.DataFrame(noncore_good, columns = ['NonCore Good'])

weekly_result = pd.concat([week_num_col, core_why_col], axis=1)
weekly_result = pd.concat([weekly_result, core_what_col], axis=1)
weekly_result = pd.concat([weekly_result, core_good_col], axis=1)
weekly_result = pd.concat([weekly_result, noncore_why_col], axis=1)
weekly_result = pd.concat([weekly_result, noncore_what_col], axis=1)
weekly_result = pd.concat([weekly_result, noncore_good_col], axis=1)

weekly_csv = "~/GoodCommitMessage/EverythingNewModel/DeveloperChangeTrend/" + project_name + "_author_report.csv"
weekly_result.to_csv(weekly_csv, index=False)
