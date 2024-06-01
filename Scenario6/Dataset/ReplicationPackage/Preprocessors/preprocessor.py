import sys
import pandas as pd
import re
import subprocess
from allennlp.models.archival import load_archive
from allennlp.predictors import Predictor
import json
from urllib.request import Request
from urllib.request import urlopen
import csv
import time
from pathlib import Path
from os.path import exists
import os

current_project_commitid_csv = sys.argv[1]
project = sys.argv[2]
github_token = sys.argv[3]
orgnazition = sys.argv[4]
marker = sys.argv[5]

# Get all the commits for a specific project
# git log --all --remotes --pretty=format:%H > ../test_cmd.csv

def find_url(message):
    if 'git-svn-id: ' in message:
        # For git-svn-id links, handle them separately
        pattern = re.compile(
            r'git-svn-id:\s+(?:http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\s+(?:[a-z]|[0-9])+(?:-(?:[a-z]|[0-9])+){4})')
    else:
        pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(pattern, message)
    urls = sorted(list(set(urls)), reverse=True)
    for url in urls:
        message = message.replace(url, '<url>')
    return message

def custimizable_pr_issue_finder(message):
    if 'bug' in message or 'Bug' in message:
        # For git-svn-id links, handle them separately
        pattern = re.compile(
            r'[Bb]ug\s?#?[0-9]{1,}')
    else:
        pattern = re.compile(r'#\s?[0-9]{1,}') # including issue id and pr id
    bugids = re.findall(pattern, message)
    bugids = sorted(list(set(bugids)), reverse=True)
    for bugid in bugids:
        message = message.replace(bugid, '<issue_link>')
        # use this token for simplicity, it will be replaced by pr/issue link content later
    pattern = re.compile(r'DUBBO-[0-9]{1,7}')
    bugids = re.findall(pattern, message)
    bugids = sorted(list(set(bugids)), reverse=True)
    for bugid in bugids:
        message = message.replace(bugid, '<issue_link>')

    return message

def if_automated_message_patterns(message):
    index_1 = message.lower().find("merge branch")
    index_2 = message.lower().find("[maven-release-plugin]")
    index_3 = message.lower().find("cherry picked from commit")
    index_4 = message.lower().find("next development version")
    index_5 = message.lower().find("conflict")
    if index_1 >= 0 or index_2 >= 0 or index_3 >= 0 or index_4 >= 0 or index_5 >= 0:
        return True
    return False

def if_merge_conflict(message):
    index_5 = message.lower().find("conflict")
    if index_5 >= 0:
        return True
    return False

def find_version(message):
    pattern = re.compile(r'[vVr]?\d+(?:\.\w+)+(?:-(?:\w)*){1,2}')
    versions = pattern.findall(message)
    versions = sorted(list(set(versions)), reverse=True)
    for version in versions:
        message = message.replace(version, '<version>')

    pattern2 = re.compile(r'[vVr]?\d+(?:\.\w+)+')
    versions = pattern2.findall(message)
    # Remove duplicate pattern
    versions = sorted(list(set(versions)), reverse=True)
    for version in versions:
        message = message.replace(version, '<version>')
    return message

def find_rawCode(message):
    rawCodeSta = message.find('```')
    replaceIden = [] # all the index intervals that contain code snippets
    res = ''
    while rawCodeSta > 0:
        rawCodeEnd = message.find('```', rawCodeSta + 3, len(message))
        if rawCodeEnd != -1:
            replaceIden.append([rawCodeSta, rawCodeEnd + 3])
        else:
            break
        rawCodeSta = message.find('```', rawCodeEnd + 3, len(message))
    if len(replaceIden) > 0:
        end = 0
        for iden in replaceIden:
            res += message[end:iden[0]]
            end = iden[1]
        res += message[end:len(message)]
        return res  # return a message without code in it
    else:
        return message

def find_SignInfo(message):
    # Sign-off is a line at the end of the commit message
    # which certifies who is the author of the commit. Its main purpose
    # is to improve tracking of who did what, especially with patches.
    # It should contain the user real name if used for an open-source project.
    # https://stackoverflow.com/questions/1962094/what-is-the-sign-off-feature-in-git-for#:~:text=Sign%2Doff%20is%20a%20line,did%20what%2C%20especially%20with%20patches.&text=It%20should%20contain%20the%20user,for%20an%20open%2Dsource%20project.
    index = message.lower().find("signed-off-by")
    if index == -1:
        return message
    if index > 0 and (message[index - 1] == '"' or message[index - 1] == "'"):
        return message
    subMessage = message[index:]
    enterIndex = subMessage.find(">")
    message = message[0:index] + " " + message[index + enterIndex + 1:]
    return message # return a message without signoff info in it

def find_CoauthorInfo(message):
    # Sign-off is a line at the end of the commit message
    # which certifies who is the author of the commit. Its main purpose
    # is to improve tracking of who did what, especially with patches.
    # It should contain the user real name if used for an open-source project.
    # https://stackoverflow.com/questions/1962094/what-is-the-sign-off-feature-in-git-for#:~:text=Sign%2Doff%20is%20a%20line,did%20what%2C%20especially%20with%20patches.&text=It%20should%20contain%20the%20user,for%20an%20open%2Dsource%20project.
    index = message.lower().find("co-authored-by")
    if index == -1:
        return message
    if index > 0 and (message[index - 1] == '"' or message[index - 1] == "'"):
        return message
    subMessage = message[index:]
    enterIndex = subMessage.find(">")
    message = message[0:index] + " " + message[index + enterIndex + 1:]
    return message # return a message without co-author info in it

def find_ChangeId(message):
    # Sign-off is a line at the end of the commit message
    # which certifies who is the author of the commit. Its main purpose
    # is to improve tracking of who did what, especially with patches.
    # It should contain the user real name if used for an open-source project.
    # https://stackoverflow.com/questions/1962094/what-is-the-sign-off-feature-in-git-for#:~:text=Sign%2Doff%20is%20a%20line,did%20what%2C%20especially%20with%20patches.&text=It%20should%20contain%20the%20user,for%20an%20open%2Dsource%20project.
    index = message.lower().find("change-id")
    if index == -1:
        return message
    if index > 0 and (message[index - 1] == '"' or message[index - 1] == "'"):
        return message
    subMessage = message[index:]
    enterIndex = subMessage.find(">")
    message = message[0:index] + " " + message[index + enterIndex + 1:]
    return message # return a message without Change-Id info in it

def tokenize(identifier):
    # camel case splitting
    new_identifier = ""
    identifier = list(identifier)
    new_identifier += identifier[0]
    for i in range(1, len(identifier)):
        if str(identifier[i]).isupper() and (
                str(identifier[i - 1]).islower() or (i < len(identifier) - 1 and str(identifier[i + 1]).islower())):
            if not new_identifier.endswith(" "):
                new_identifier += " "
        new_identifier += identifier[i]
        if str(identifier[i]).isdigit() and i < len(identifier) - 1 and not str(identifier[i + 1]).isdigit():
            if not new_identifier.endswith(" "):
                new_identifier += " "
    return new_identifier.split(" ")

def split(path):
    # Split according to non-alphanumeric values and ignore the'< xxx > 'obtained by preprocessing
    new_sentence = ''
    for s in path:
        if not str(s).isalnum():
            if len(new_sentence) > 0 and not new_sentence.endswith(' '):
                new_sentence += ' '
            if s != ' ':
                new_sentence += s
                new_sentence += ' '
        else:
            new_sentence += s
    tokens = new_sentence.replace('< enter >', '<enter>').replace('< tab >', '<tab>'). \
        replace('< url >', '<url>').replace('< version >', '<version>') \
        .replace('< pr _ link >', '<pr_link>').replace('< issue _ link >', '<issue_link>') \
        .replace('< otherCommit_link >', '<otherCommit_link>').strip().split(' ')
    return tokens

def find_file_name2(sample):

    filePath = sample[2] # changed file name list
    messageOld = sample[1]
    message = messageOld.lower()
    replaceTokens = []
    otherMeanWords = ['version', 'test', 'assert', 'junit']
    specialWords = ['changelog', 'contributing', 'release', 'releasenote', 'readme', 'releasenotes']
    punctuations = [',', '.', '?', '!', ';', ':', '、']

    for file in filePath:
        filePathTokens = file.split('/')
        fileName = filePathTokens[-1]
        # Do not replace the file name if it ends with ".md"
        if fileName.endswith(".md"):
            continue
        # If you include the file name directly
        if fileName.lower() in message:
            index = message.find(fileName.lower())
            replaceTokens.append(messageOld[index:index + len(fileName)])
        if '.' in fileName:
            # Get the file name without suffix
            newFileName = fileName
            pattern = re.compile(r'(?:\d+(?:\.\w+)+)')
            versions = pattern.findall(newFileName)
            for version in versions:
                if version != newFileName:
                    newFileName = newFileName.replace(version, '')

            # Remove the extension and all lowercase, for'.' Begin or contain'.'
            # The file name only removes the extension e.g. ".Trivas.yml"-> ".Trivas"
            lastIndex = newFileName[1:].rfind('.')
            if lastIndex == -1:
                lastIndex = len(newFileName) - 1
            newFileName = newFileName[:lastIndex + 1]
            fileNameGreen = newFileName.lower()
            # If include a file name with the suffix removed
            if fileNameGreen in specialWords:
                continue
            elif fileNameGreen in otherMeanWords:
                index = 0
                while index != -1:
                    tempIndex = message[index + 1:len(message)].find(fileNameGreen)
                    if tempIndex == -1:
                        break
                    else:
                        index = index + 1 + tempIndex
                        if index != -1 and messageOld[index].isupper():
                            replaceTokens.append(messageOld[index:index + len(fileNameGreen)])
                            break
            # Msg contains a file name without an extension，e.g. AClass.java in 'xxx AClss/method() xxx'
            elif fileNameGreen in message:
                index = message.find(fileNameGreen)
                replaceTokens.append(messageOld[index:index + len(fileNameGreen)])
            else:
                fileNameTokens = tokenize(newFileName)
                if len(fileNameTokens) < 2:
                    continue
                if fileNameTokens[0].lower() in message:
                    camelSta = message.find(fileNameTokens[0].lower())
                    camelEnd = -1
                    tempMessag = message[camelSta:]
                    while camelSta >= 0 and len(tempMessag) > 0:
                        tempMessagTokens = tempMessag.split(' ')
                        find = True
                        if tempMessagTokens[0] == fileNameTokens[0].lower():
                            # Delete punctuation marks such as periods and commas. Other symbols cannot correspond to hump file names
                            for i in range(0, min(len(tempMessagTokens), len(fileNameTokens))):
                                if len(tempMessagTokens[i]) < 2:
                                    continue
                                if str(tempMessagTokens[i][-1]) in punctuations:
                                    tempMessagTokens[i] = tempMessagTokens[i][:-1]

                            for i in range(0, len(fileNameTokens)):
                                if i < len(tempMessagTokens) and tempMessagTokens[i] != fileNameTokens[i].lower():
                                    find = False
                                    break
                                elif i > len(tempMessagTokens):
                                    find = False
                                    break
                            if find:
                                lastTokenIndex = tempMessag.find(fileNameTokens[-1].lower())
                                camelEnd = len(tempMessag[:lastTokenIndex]) + len(fileNameTokens[-1]) + camelSta
                                if camelEnd < len(tempMessag) and tempMessag[camelEnd] in punctuations:
                                    camelEnd += 1
                                break
                        index = message[camelSta + 1:].find(fileNameTokens[0].lower())
                        if index == -1:
                            break
                        camelSta = camelSta + 1 + index
                        tempMessag = message[camelSta:]
                    if camelSta != -1 and camelEnd != -1:
                        replaceTokens.append(messageOld[camelSta:camelEnd])
    replaceTokens = list(set(replaceTokens))
    return replaceTokens

def cmp(elem):
    return elem[0]

def replace_file_name(sample):

    replaced_tokens = find_file_name2(sample)
    message = sample[1]

    # find out start and end index of replaced tokens
    locations = []
    # Token that starts with'@'is usually annotation and usually appears in patchs, so ignore it even if it is the same as the file name
    diffMeanPunctuations = ['@']
    for t in replaced_tokens:
        end = 0
        while end < len(message):
            start = str(message).find(t, end, len(message))
            if start == -1:
                break
            end = start + len(t)
            before = start > 0 and (
                    str(message[start - 1]).isalnum() or str(message[start - 1]) in diffMeanPunctuations)
            after = end < len(message) and str(message[end]).isalnum()
            if not before and not after:
                locations.append([start, end])

    # Merge intervals of mutually contained substituted token
    locations.sort(key=cmp)
    i = 0
    while i < len(locations) - 1:
        if locations[i][1] > locations[i + 1][0]:
            if locations[i][0] == locations[i + 1][0]:
                if locations[i][1] < locations[i + 1][1]:
                    locations.pop(i)
                elif locations[i][1] > locations[i + 1][1]:
                    locations.pop(i + 1)
            elif locations[i][0] < locations[i + 1][0] and locations[i][1] >= locations[i + 1][1]:
                locations.pop(i + 1)
        else:
            i += 1

    # '.' and '#'are used to indicate that a method/field is included in the class, or for the package path,
    # eg. AClass.getInt()、FrameworkMethod#producesType()、org.junit.runner.Description#getTestClass

    # Special symbol before file name
    backSymbols = ['.', '/']
    # Special symbol after file name
    forwardSymbols = ['.', '#']
    newLocations = []
    newMethodeName = []

    for location in locations:
        sta = location[0]
        end = location[1]
        ifMethod = False
        packagePath = ''
        if sta > 0 and str(message[sta - 1]) in backSymbols:
            newSta = sta - 1
            while newSta >= 0 and str(message[newSta]) != ' ':
                packagePath = str(message[newSta]) + packagePath
                newSta -= 1
            sta = newSta + 1

        if end < len(message) and str(message[end]) in forwardSymbols:
            newEnd = end + 1
            while newEnd < len(message) and str(message[newEnd]) != ' ':
                newEnd += 1
            end = newEnd
            ifMethod = True
        if ifMethod:
            newMethodeName.append([sta, end])
        newLocations.append([sta, end])

        if packagePath != '':
            index = 0
            while index >= 0:
                index = message.find(packagePath, index, len(message))
                if index == sta:
                    index = end
                elif index != -1:
                    indexEnd = index + len(packagePath)
                    while indexEnd < len(message) and str(message[indexEnd]) != " ":
                        indexEnd += 1
                    newLocations.append([index, indexEnd])
                    index += 1

    newLocations.sort(key=cmp)
    newMethodeName.sort(key=cmp)
    # replace tokens in message with <file_name>
    end = 0
    new_message = ""
    for location in newLocations:
        start = location[0]
        new_message += message[end:start]
        if location in newMethodeName:
            new_message += " <method_name> "
        else:
            new_message += " <file_name> "
        end = location[1]
    new_message += message[end:len(message)]

    return new_message

def allennlp_tag(message, predictor):
    result = predictor.predict(message)
    tokens = result['tokens']
    tags = result['pos_tags']

    indices = []
    for i in range(len(tokens)):
        s = str(tokens[i])
        if s.startswith('file_name>') or s.startswith('version>') or s.startswith('url>') \
                or s.startswith('enter>') or s.startswith('tab>') or s.startswith('iden>') or s.startswith(
            'method_name>') \
                or s.startswith('pr_link>') or s.startswith('issue_link>') or s.startswith('otherCommit_link>'):
            indices.append(i)
        elif s.endswith('<file_name') or s.endswith('<version') or s.endswith('<url') \
                or s.endswith('<enter') or s.endswith('<tab') or s.endswith('<iden') or s.endswith('<method_name') \
                or s.endswith('<pr_link') or s.endswith('<issue_link') or s.endswith('<otherCommit_link'):
            indices.append(i)

    new_tokens = []
    new_tags = []
    for i in range(len(tokens)):
        if i in indices:
            s = str(tokens[i])
            if s.startswith('file_name>'):
                s = s.replace('file_name>', '')
                new_tokens.append('file_name')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('method_name>'):
                s = s.replace('method_name>', '')
                new_tokens.append('method_name')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('version>'):
                s = s.replace('version>', '')
                new_tokens.append('version')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('url>'):
                s = s.replace('url>', '')
                new_tokens.append('url')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('enter>'):
                s = s.replace('enter>', '')
                new_tokens.append('enter')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('tab>'):
                s = s.replace('tab>', '')
                new_tokens.append('tab')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('iden>'):
                s = s.replace('iden>', '')
                new_tokens.append('iden')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('pr_link>'):
                s = s.replace('pr_link>', '')
                new_tokens.append('pr_link')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('issue_link>'):
                s = s.replace('issue_link>', '')
                new_tokens.append('issue_link')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.startswith('otherCommit_link>'):
                s = s.replace('otherCommit_link>', '')
                new_tokens.append('otherCommit_link')
                new_tags.append('XX')
                new_tokens.append('>')
                new_tags.append('XX')
                new_tokens.append(s)
                new_tags.append('XX')
            elif s.endswith('<file_name'):
                s = s.replace('<file_name', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('file_name')
                new_tags.append('XX')
            elif s.endswith('<method_name'):
                s = s.replace('<method_name', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('method_name')
                new_tags.append('XX')
            elif s.endswith('<version'):
                s = s.replace('<version', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('version')
                new_tags.append('XX')
            elif s.endswith('<url'):
                s = s.replace('<url', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('url')
                new_tags.append('XX')
            elif s.endswith('<enter'):
                s = s.replace('<enter', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('enter')
                new_tags.append('XX')
            elif s.endswith('<tab'):
                s = s.replace('<tab', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('tab')
                new_tags.append('XX')
            elif s.endswith('<iden'):
                s = s.replace('<iden', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('iden')
                new_tags.append('XX')
            elif s.endswith('<pr_link'):
                s = s.replace('<pr_link', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('pr_link')
                new_tags.append('XX')
            elif s.endswith('<issue_link'):
                s = s.replace('<issue_link', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('issue_link')
                new_tags.append('XX')
            elif s.endswith('<otherCommit_link'):
                s = s.replace('<otherCommit_link', '')
                new_tokens.append(s)
                new_tags.append('XX')
                new_tokens.append('<')
                new_tags.append('XX')
                new_tokens.append('otherCommit_link')
                new_tags.append('XX')
        else:
            new_tokens.append(tokens[i])
            new_tags.append(tags[i])
    tokens = new_tokens
    tags = new_tags
    length = len(tokens)

    new_tokens = []
    new_tags = []
    targets = ['file_name', 'version', 'url', 'enter', 'tab', 'iden', 'issue_link', 'pr_link', 'otherCommit_link',
               'method_name']
    i = 0
    while i < length:
        if i < length - 2 and tokens[i] == '<' and tokens[i + 1] in targets and tokens[i + 2] == '>':
            new_tokens.append(tokens[i] + tokens[i + 1] + tokens[i + 2])
            new_tags.append('XX')
            i += 3
        else:
            new_tokens.append(tokens[i])
            new_tags.append(tags[i])
            i += 1

    tokens = new_tokens
    tags = new_tags
    length = len(tokens)
    tokens = ' '.join(tokens)
    tags = ' '.join(tags)
    print('---------------------------------------')
    print(tokens)
    print(tags)
    # print(trees)
    return tokens, tags, length

def filter_tokens(length, tokens, tags):
    indices = []
    tokens = tokens.split(' ')
    tags = tags.split(' ')
    for i in range(1, length):
        if str(tokens[i]).startswith('@'): # Patches
            indices.append(i)
        elif str(tokens[i]).isalnum() and not str(tokens[i]).islower():
            if str(tags[i]).startswith("NN"):
                indices.append(i)
            else:
                before = i > 0 and str(tokens[i - 1]) == "'"
                after = i + 1 < len(tokens) and str(tokens[i + 1]) == "'"
                if before and after:
                    indices.append(i)

    return indices, tokens

def request(url, access_token):
    #url = url.replace('https://github.com/', 'https://api.github.com/repos/').replace('/commit/', '/commits/')
    # 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
    # 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
    # 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
    # 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
    # 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
    # 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
    try:
        headers = {'Authorization': 'token ' + access_token}
        req = Request(url, headers=headers)
        response = urlopen(req).read()
        commit = json.loads(response.decode())
        files = commit['files']
        return files
    except Exception as e:
        print(e)
        return None

def search_in_patches(url, indices, tokens):
    patches = []
    files = request(url, github_token)
    print(url, files)
    while files is None:
        files = request(url, github_token)
    for file in files:
        if 'patch' in file.keys():
            patch = file['patch']
            patches.append(patch)
    found_indices = []
    found_tokens = []
    for index in indices:
        for patch in patches:
            if str(patch).find(tokens[index]) > -1:
                if index > 0 and index < len(tokens) - 1 and str(tokens[index - 1]) == "'" and str(
                        tokens[index + 1]) == "'":
                    found_tokens.append("'" + str(tokens[index]) + "'")
                else:
                    found_tokens.append(tokens[index])
                found_indices.append(index)
                break

    return found_indices, list(set(found_tokens))

def get_unreplacable(message, replacement):
    unreplacable_indices = []
    start = 0
    index = str(message).find(replacement, start, len(message))
    while index > -1:
        start = index + len(replacement)
        for i in range(index, start):
            unreplacable_indices.append(i)
        index = str(message).find(replacement, start, len(message))
    return unreplacable_indices

def replace_tokens(message, tokens):
    unreplacable = []
    replacements = ['<file_name>', '<version>', '<url>', '<enter>', '<tab>', '<issue_link>', '<pr_link>',
                    '<otherCommit_link>', '<method_name>']
    for replacement in replacements:
        unreplacable += get_unreplacable(message, replacement)

    # find out start and end index of replaced tokens
    locations = []
    for t in tokens:
        end = 0
        while end < len(message):
            start = str(message).find(t, end, len(message))
            if start == -1:
                break
            end = start + len(t)
            before = start > 0 and str(message[start - 1]).isalnum()
            after = end < len(message) and str(message[end]).isalnum()
            if not before and not after:
                locations.append([start, end])

    locations.sort(key=cmp)
    i = 0
    while i < len(locations) - 1:
        if locations[i][1] > locations[i + 1][0]:
            if locations[i][0] == locations[i + 1][0]:
                if locations[i][1] < locations[i + 1][1]:
                    locations.pop(i)
                elif locations[i][1] > locations[i + 1][1]:
                    locations.pop(i + 1)
            elif locations[i][0] < locations[i + 1][0] and locations[i][1] >= locations[i + 1][1]:
                locations.pop(i + 1)
        else:
            i += 1

    # merge continuous replaced tokens
    new_locations = []
    i = 0
    start = -1
    while i < len(locations):
        if start < 0:
            start = locations[i][0]
        if i < len(locations) - 1 and locations[i + 1][0] - locations[i][1] < 2:
            i += 1
            continue
        else:
            end = locations[i][1]
            new_locations.append([start, end])
            start = -1
            i += 1

    # replace tokens in message with <file_name>
    end = 0
    new_message = ""
    for location in new_locations:
        start = location[0]
        new_message += message[end:start]
        new_message += "<iden>"
        end = location[1]
    new_message += message[end:len(message)]

    return new_message

def get_bots(bots_detection_results_csv):
    bots_set = set()
    with open(Path(bots_detection_results_csv), 'r') as detection_csv:
        reader = csv.reader(detection_csv)
        for row in reader:
            if float(row[3].strip()) < 0.5:
                bots_set.add(row[0].strip())
    return bots_set

# one project a time
# be sure to delete every bots_detection_results.csv for each project!!!
samples = []
# bot_detection_file = "~/GoodCommitMessage/Projects/bots_detection_results_" + str(project) + ".csv"
# if not exists(bot_detection_file):
#     pauthdict = get_pauthdict(project)
#     get_bots_detection_results(pauthdict, project)
# bot_commiters = get_bots(bot_detection_file)
# print("Check!!!")
# print("Bots: ", bot_commiters)

cur_dataset = pd.read_csv(current_project_commitid_csv, header=None)
for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    commit_id = cur_line[0]
    # project = cur_line[1]
    # bug_introducing = cur_line[1]
    print("Commit id: ", commit_id)
    if not commit_id.strip():
        continue
    # Actually, author
    # commit_commiter_cmd = 'cd ~/GoodCommitMessage/Projects/' + str(
    #     project) + " ; " + "git log --format=\"%ae\" " + str(commit_id) + "^!"
    # commit_commiter = subprocess.run(commit_commiter_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout.strip()
    # if commit_commiter in bot_commiters:
    #     new_commit_message = "bot commit message"
    commit_message_cmd = 'cd ~/GoodCommitMessage/Projects/' + str(
            project) + " ; " + "git log --format=%B -n 1 " + str(commit_id)
    new_commit_message = subprocess.run(commit_message_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout
    if not new_commit_message:
        new_commit_message = "commit not found"
    else:
        if len(new_commit_message) >= 2000:
            new_commit_message = new_commit_message[:2000]
        new_commit_message = new_commit_message.replace('\n\n',' <enter> ').replace('\n',' ').replace('\t',' <tab> ')
        # process it, and put the processed commit messages into a new column
        new_commit_message = find_url(new_commit_message)
        new_commit_message = find_version(new_commit_message)
        new_commit_message = find_rawCode(new_commit_message)
        new_commit_message = find_SignInfo(new_commit_message)
        new_commit_message = find_CoauthorInfo(new_commit_message)
        new_commit_message = find_ChangeId(new_commit_message)
        new_commit_message = custimizable_pr_issue_finder(new_commit_message)
    if not new_commit_message:
        new_commit_message = "empty log message"
    if if_merge_conflict(new_commit_message):
        new_commit_message = "merge conflict message"
    # if if_automated_message_patterns(new_commit_message):
    #     print("Cur New Message: ", new_commit_message)
    #     new_commit_message = "bot commit message"
    if new_commit_message[0] == " ":
        isUnuse = True
        for s in new_commit_message:
            if s.isalnum():
                isUnuse = False
                break
        if isUnuse:
            new_commit_message = "empty log message"

    file_names_cmd = 'cd ~/GoodCommitMessage/Projects/' + str(project).strip() + " ; " + "git diff-tree --no-commit-id --name-only -r " + str(commit_id).strip()
    changed_files = subprocess.run(file_names_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout
    changed_files = changed_files.replace('\n', ' ')
    changed_files_list = changed_files.split()
    if len(changed_files_list) >= 32:
        changed_files_list = changed_files_list[:32]

    samples.append([commit_id, new_commit_message, changed_files_list, project])

new_commit_messages = []
counter = 1
for sample in samples:
    print("Replace Files!! ", counter)
    counter += 1
    if len(sample[1]) > 0:
        new_commit_message = replace_file_name(sample)
        new_commit_messages.append([new_commit_message, sample[0], sample[3]])
    else:
        new_commit_messages.append([sample[1], sample[0], sample[3]])

# archive = load_archive('https://allennlp.s3.amazonaws.com/models/elmo-constituency-parser-2020.02.10.tar.gz')
# predictor = Predictor.from_archive(archive, 'constituency-parser')

predictor = Predictor.from_path(archive_path="https://allennlp.s3.amazonaws.com/models/elmo-constituency-parser-2020.02.10.tar.gz", predictor_name='constituency_parser')
# Failed: predictor = Predictor.from_path(archive_path="./elmo-constituency-parser-2018.03.14.tar.gz", predictor_name='constituency_parser')

new_commit_messages_infos = []
for new_commit_message, commit_id, project in new_commit_messages:
    print("Current tagging Commit ID: ", commit_id)
    tokens, tags, length = allennlp_tag(new_commit_message, predictor)
    new_commit_messages_infos.append([tokens.replace("'", "''"), length, tags.replace("'", "''"), new_commit_message, commit_id, project])

final_new_commit_messages = []
for new_commit_info in new_commit_messages_infos:
    new_commit_message = new_commit_info[3]
    length = new_commit_info[1]
    tokens = new_commit_info[0]
    tags = new_commit_info[2]
    commit_id = new_commit_info[4]
    project = new_commit_info[5]
    # Change the org!
    url = 'https://api.github.com/repos/' + orgnazition + "/" + str(project).strip() + "/commits/" + str(commit_id).strip()
    #print(url)
    if len(new_commit_message) > 0:
        indices, tokens = filter_tokens(length, tokens, tags)
        print("point1: ", url)
        if len(indices) > 0:
            print("point2: ", url)
            found_indices, found_tokens = search_in_patches(url, indices, tokens)
            if len(found_indices) > 0:
                new_commit_message = replace_tokens(new_commit_message, found_tokens)
    final_new_commit_messages.append(new_commit_message)

new_commit_message_col = pd.DataFrame(final_new_commit_messages, columns = ['new_message1'])
result = pd.concat([cur_dataset, new_commit_message_col], axis=1)
#print(result)
Preprocessed_csv = "~/GoodCommitMessage/Projects/Results/Apache/Preprocessing_all/Preprocessed_" + str(project) + marker + ".csv"
result.to_csv(Preprocessed_csv, index=False)
# os.remove(bot_detection_file)
#print(cur_dataset.shape[0])
#print(cur_dataset.iloc[1, :].values)
