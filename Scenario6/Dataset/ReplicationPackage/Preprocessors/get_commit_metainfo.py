import sys
import pandas as pd
import subprocess

Pred_csv = sys.argv[1]
project_name = sys.argv[2]
cur_dataset = pd.read_csv(Pred_csv, encoding="Latin-1 ")
author_names = []
author_emails = []
commit_dates = []
for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    commit_id = cur_line[0].strip()

    author_name_cmd = 'cd ../GoodCommitMessage/Projects/' + str(project_name) + " ; " + "git log --format=\"%an\" " + str(commit_id) + "^!"
    author_name = subprocess.run(author_name_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout.strip()

    author_email_cmd = 'cd ../GoodCommitMessage/Projects/' + str(project_name) + " ; " + "git log --format=\"%ae\" " + str(commit_id) + "^!"
    author_email = subprocess.run(author_email_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout.strip()

    commit_date_cmd = 'cd ../GoodCommitMessage/Projects/' + str(project_name) + " ; " + "git log --format=\"%cs\" " + str(commit_id) + "^!"
    commit_date = subprocess.run(commit_date_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout.strip()

    author_names.append(author_name)
    author_emails.append(author_email)
    commit_dates.append(commit_date)

author_names_col = pd.DataFrame(author_names, columns = ['author names'])
author_emails_col = pd.DataFrame(author_emails, columns = ['author emails'])
commit_dates_col = pd.DataFrame(commit_dates, columns = ['commit dates'])

result = pd.concat([cur_dataset, author_names_col], axis=1)
result = pd.concat([result, author_emails_col], axis=1)
result = pd.concat([result, commit_dates_col], axis=1)

csv_name = '../GoodCommitMessage/model_preds/withmeta/' + project_name + "_predmeta.csv"
result.to_csv(csv_name, index=False)
