import pandas as pd

input_csv = "~/GoodCommitMessage/EverythingNewModel/Allcrawled/jclouds_crawled.csv"

cur_dataset = pd.read_csv(input_csv, encoding="Latin-1")

concatenated_messages = []

for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    new_message1 = str(cur_line[1]).strip()
    issue_content = str(cur_line[5]).strip()
    pr_content = str(cur_line[6]).strip()
    concatenated_message = new_message1
    if issue_content != "nan" and new_message1.lower().find("<issue_link>") >= 0:
        concatenated_message = concatenated_message.replace("<issue_link>", issue_content)
    if pr_content != "nan" and new_message1.lower().find("<issue_link>") >= 0:
        concatenated_message = concatenated_message.replace("<issue_link>", pr_content)
    # index_pr = new_message1.lower().find("<pr_link>")
    concatenated_messages.append(concatenated_message)

concatenated_messages_col = pd.DataFrame(concatenated_messages, columns = ['Concatenated_Messages'])

result = pd.concat([cur_dataset, concatenated_messages_col], axis=1)
result.to_csv("~/GoodCommitMessage/EverythingNewModel/concatenated_apache/jclouds_messages.csv", index=False)
