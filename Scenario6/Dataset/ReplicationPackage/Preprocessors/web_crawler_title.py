from bs4 import BeautifulSoup
from urllib.request import Request
from urllib.request import urlopen
from github import Github
import pandas as pd
import sys
from tqdm import tqdm
import re

auth_token_1 = sys.argv[1]
auth_token_2 = sys.argv[2]
# auth_token_3 = sys.argv[3]
# auth_token_4 = sys.argv[4]
csv_file = sys.argv[3]
project_org = sys.argv[4]
project_name = sys.argv[5]

def find_pr_issue_link(url, access_token):
    try:
        headers = {'Authorization': 'token ' + access_token}
        req = Request(url, headers=headers)
        response = urlopen(req).read()
        soup = BeautifulSoup(response, 'html.parser')
        first_links = set()
        url_list = url.split('/')
        issue_prefix = "https://" + '/'.join(url_list[2:5]) + "/issues/"
        pr_prefix = "https://" + '/'.join(url_list[2:5]) + "/pull/"
        for link in soup.find_all('a'):
            if link.get('href'):
                first_links.add(link.get('href').strip())
        issue_pr_links = [None, None]
        for first_link in first_links:
            if issue_prefix in first_link:
                issue_pr_links[0] = first_link
            if pr_prefix in first_link:
                issue_pr_links[1] = first_link
        if issue_pr_links[0] == None and issue_pr_links[1] == None:
            return None
        else:
            return issue_pr_links
    except Exception as e:
        print(e)
        return None


def find_issue_link(url, access_token):
    # url - commit url
    # return issue link in the commit message
    try:
        headers = {'Authorization': 'token ' + access_token}
        req = Request(url, headers=headers)
        response = urlopen(req).read()
        soup = BeautifulSoup(response, 'html.parser')
        first_links = set()
        url_list = url.split('/')
        issue_prefix = "https://" + '/'.join(url_list[2:5]) + "/issues/"
        for link in soup.find_all('a'):
            if link.get('href'):
                first_links.add(link.get('href').strip())
        for first_link in first_links:
            if issue_prefix in first_link:
                return first_link
        return None
    except Exception as e:
        print(e)
        return None



def find_pr_link(url, access_token):
    # return pr link in the commit message
    try:
        headers = {'Authorization': 'token ' + access_token}
        req = Request(url, headers=headers)
        response = urlopen(req).read()
        soup = BeautifulSoup(response, 'html.parser')
        first_links = set()
        url_list = url.split('/')
        pr_prefix = "https://" + '/'.join(url_list[2:5]) + "/pull/"
        for link in soup.find_all('a'):
            if link.get('href'):
                first_links.add(link.get('href').strip())
        for first_link in first_links:
            if pr_prefix in first_link:
                return first_link
        return None
    except Exception as e:
        print(e)
        return None

def get_issue_content(access_token, repo_sig, issue_num):
    g = Github(access_token)
    repo = g.get_repo(repo_sig)
    issue = repo.get_issue(number=issue_num)
    issue_content = issue.title
    issue_content = issue_content.replace('\r\n',' <enter> ').replace('\n\n',' <enter> ').replace('\n',' ').replace('\t',' <tab> ').replace('\r',' <enter> ')
    return issue_content

def get_pr_content(access_token, repo_sig, pr_num):
    g = Github(access_token)
    repo = g.get_repo(repo_sig)
    pr = repo.get_pull(pr_num)
    pr_content = pr.title
    pr_content = pr_content.replace('\r\n',' <enter> ').replace('\n\n',' <enter> ').replace('\n',' ').replace('\t',' <tab> ').replace('\r',' <enter> ')
    return pr_content

cur_dataset = pd.read_csv(csv_file, encoding="Latin-1")

issue_contents = []
pr_contents = []
for i in tqdm(range(0, cur_dataset.shape[0])):
    cur_line = cur_dataset.iloc[i, :].values
    commit_hash = str(cur_line[0]).strip()
    commit_url = "https://github.com/" + project_org + "/" + project_name + "/commit/" + commit_hash
    url_list = commit_url.split('/')
    repo_sig = url_list[3] + '/' + url_list[4]
    commit_issue_pr_links = find_pr_issue_link(commit_url, auth_token_1)
    if commit_issue_pr_links:

        g = Github(auth_token_2)
        repo = g.get_repo(repo_sig)

        if commit_issue_pr_links[0]: # issue
            try:
                issue_num = int(commit_issue_pr_links[0].split('/')[-1])
            except ValueError:
                p = re.compile("\d+")
                matched = p.search(commit_issue_pr_links[0].split('/')[-1])
                if not matched:
                    issue_contents.append("")
                    continue
                issue_num = int(matched.group(0))
            issue = repo.get_issue(number=issue_num)
            issue_content = issue.title
            issue_content = issue_content.replace('\r\n', ' <enter> ').replace('\n\n', ' <enter> ').replace('\n', ' ').replace('\t', ' <tab> ').replace('\r', ' <enter> ')
            issue_contents.append(issue_content)
        else:
            issue_contents.append("")

        if commit_issue_pr_links[1]: # pr
            try:
                pr_num = int(commit_issue_pr_links[1].split('/')[-1])
            except ValueError:
                p = re.compile("\d+")
                matched = p.search(commit_issue_pr_links[1].split('/')[-1])
                if not matched:
                    pr_contents.append("")
                    continue
                pr_num = int(matched.group(0))
            pr = repo.get_pull(pr_num)
            pr_content = pr.title
            pr_content = pr_content.replace('\r\n', ' <enter> ').replace('\n\n', ' <enter> ').replace('\n', ' ').replace('\t',' <tab> ').replace('\r', ' <enter> ')
            pr_contents.append(pr_content)
        else:
            pr_contents.append("")

    else:
        issue_contents.append("")
        pr_contents.append("")

issue_contents_col = pd.DataFrame(issue_contents, columns = ['Issue_content'])
pr_contents_col = pd.DataFrame(pr_contents, columns = ['PR_content'])

result = pd.concat([cur_dataset, issue_contents_col], axis=1)
result = pd.concat([result, pr_contents_col], axis=1)
file_name = csv_file.split('/')[-1].split('.')[0]
csv_output = "~/Withmeta/CrawledResults/crawled_results_" + file_name + ".csv"

result.to_csv(csv_output, index=False)
