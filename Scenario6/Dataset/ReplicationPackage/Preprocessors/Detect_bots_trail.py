from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner
import subprocess
import sys
import os
import csv
from pathlib import Path

project_name = sys.argv[1]

# Adding Timeout
import signal

class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)


# Prepapring Author - Commit Message Map for Generating Data for BIM
pauthdict = {}

get_all_authors_cmd = 'cd ~/ApacheProjects/' + str(project_name) + " ; " + "git log --pretty=\"%ce\" | sort | uniq > ~/Filelevel_analysis/bots/all_commiters_" + str(project_name) + ".txt"
os.system(get_all_authors_cmd)
commiters_file_path = "~/Filelevel_analysis/bots/all_commiters_" + str(project_name) + ".txt"
with open(Path(commiters_file_path), "r", encoding="Latin-1") as commiters_file:
    for commiter in commiters_file:
        commiter = commiter.strip()
        get_author_commit_hashes = 'cd ~/ApacheProjects/' + str(project_name) + " ; " + "git log --author=\"" + str(commiter) + "\" --pretty=format:\"%H\" > ~/Filelevel_analysis/bots/author_commit_hashes_"+ str(project_name) +".txt"
        os.system(get_author_commit_hashes)
        commiter_hashes_file_path = "~/Filelevel_analysis/bots/author_commit_hashes_"+ str(project_name) +".txt"
        with open(Path(commiter_hashes_file_path), "r", encoding="Latin-1") as commiters_hashes_file:
            for commit_id in commiters_hashes_file:
                commit_id = commit_id.strip()
                if commit_id == "9f7cd6fe027bbac8d9665da8c09975b347e01768":
                    continue
                commit_message_cmd = 'cd ~/ApacheProjects/' + str(
                    project_name) + " ; " + "git log --format=%B -n 1 " + str(commit_id)
                commit_message = subprocess.run(commit_message_cmd, stdout=subprocess.PIPE, text=True,shell=True).stdout
                if commiter not in pauthdict:
                    pauthdict[commiter] = [commit_message]
                else:
                    pauthdict[commiter].append(commit_message)

# with gzip.open('/da4_data/play/botDetection/paper_a2c.gz', 'rt', encoding='iso-8859-15') as f:
#     for line in f:
#         line = line.strip()
#         parts = line.split(';')
#         pauthdict[parts[0]] = {'commits': parts[1:], 'message': []}
#
# pcc = {}
# with gzip.open('/da4_data/play/botDetection/paper_cnt.gz', 'rt', encoding='iso-8859-15') as f:
#     for line in f:
#         line = line.strip()
#         parts = line.split(';')
#         pcc[parts[0]] = ';'.join(parts[3:])
#
# for key in pauthdict.keys():
#     commits = pauthdict[key]['commits']
#     for com in commits:
#         try:
#             pauthdict[key]['message'].append(pcc[com])
#         except:
#             continue

# Generating Data for BIM
from collections import defaultdict

bin_threshold = [40]
id_threshold = 0.5  # 50 percent
max_bot_bin = 500
# nbhumans = defaultdict(list)
# nbbots = defaultdict(list)

fw = open('~/Filelevel_analysis/bots/bots_detection_results'+ str(project_name) +'.csv', 'w')
fw_writer = csv.writer(fw)
fw_writer.writerow(["Author Email", "No. of Commits", "No. of Bins", "Ratio"])

# get a dict, {author: [msgs...] ....}
for threshold in bin_threshold:
    for key in pauthdict.keys():
        author, msgs = key, pauthdict[key] # author: commit messages
        print(author, len(msgs))

        if len(msgs) == 1: # human
            fw_writer.writerow([author, str(len(msgs)), str(1), str(1)])
            continue
        elif len(msgs) > 100000: # bot
            fw_writer.writerow([author, str(len(msgs)), str(1), str(0)])
            continue
        bins = {}
        bratio = 0
        i = 0
        try:
            with timeout(seconds=60):
                for commit in msgs: # for each commit message
                    i += 1
                    if len(bins) == 0:
                        bins[0] = [(commit, 100)]
                    elif len(commit) >= 200:
                        bins[len(bins)] = [(commit, 100)]
                        continue
                    else:
                        '''
                        # Create sequences to be aligned.
                        b = Sequence('what a beautiful day'.split())
                        a = Sequence('what a disappointingly bad day'.split())
                        '''
                        a = Sequence(commit.split())
                        added = False
                        brflag = False
                        for key in bins:
                            b = Sequence(bins[key][0][0].split())  # first eleman of the tuple in the list
                            # Create a vocabulary and encode the sequences.
                            v = Vocabulary()
                            try:
                                aEncoded = v.encodeSequence(a)
                                bEncoded = v.encodeSequence(b)

                                # Create a scoring and align the sequences using global aligner.
                                scoring = SimpleScoring(2, -1)
                                aligner = GlobalSequenceAligner(scoring, -2)
                                score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

                                # Iterate over optimal alignments and print them.
                                pi_max = 0
                                score_ = 0
                                for encoded in encodeds:
                                    alignment = v.decodeSequenceAlignment(encoded)
                                    score_ = alignment.score
                                    percentIdentity = alignment.percentIdentity()
                                    if percentIdentity > pi_max: pi_max = percentIdentity

                                if pi_max > threshold:
                                    #                         print (pi_max)
                                    bins[key].append((commit, percentIdentity))  # add b and similarity
                                    added = True
                                    break
                            except KeyboardInterrupt:
                                print('KeyboardInterrupt')
                                break
                            except:
                                brflag = True
                                break
                        if brflag:
                            bins = {}
                            break
                        if added == False: # new group
                            bins[len(bins)] = [(commit, 100)]
                        if len(bins) > max_bot_bin:
                            bratio = 1
                            break

        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            break
        except TimeoutError:
            print('Timeout')
            fw_writer.writerow([author, str(i), str(len(bins.keys())), str(ratio)])
            continue
        except Exception as e:
            print(e)
            break

        num_commits = len(msgs)
        ratio = max(len(bins.keys()) / num_commits, bratio)
        fw_writer.writerow([author, str(num_commits), str(len(bins.keys())), str(ratio)])

fw.close()
