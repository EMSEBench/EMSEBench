import os
from collections import Counter

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from imblearn.over_sampling import RandomOverSampler
from sklearn.model_selection import KFold
from torch.nn import functional as F
from torch.utils.data import TensorDataset, DataLoader
from transformers import BertTokenizer, BertModel
import sys

np.random.seed(0)
torch.manual_seed(0)
USE_CUDA = torch.cuda.is_available()
if USE_CUDA:
    torch.cuda.manual_seed(0)

hidden_dim = int(sys.argv[1].strip())
lr = float(sys.argv[2].strip())
dropout = float(sys.argv[3].strip())
n_layers = int(sys.argv[4].strip())


class ModelConfig:
    batch_size = 25
    output_size = 2 # fixed
    hidden_dim = hidden_dim # tune
    n_layers = n_layers # tune
    lr = lr # tune
    bidirectional = True
    drop_prob = dropout
    # training params
    epochs = 10
    # batch_size=50
    print_every = 10
    use_cuda = USE_CUDA
    bert_path = 'bert-base-uncased'
    save_path = 'HT_GRU'
    sampleRate = 2


class bert_lstm(nn.Module):
    def __init__(self, bertpath, hidden_dim, output_size, n_layers, bidirectional=True, drop_prob=0.5):
        super(bert_lstm, self).__init__()

        self.output_size = output_size
        self.n_layers = n_layers
        self.hidden_dim = hidden_dim
        self.bidirectional = bidirectional
        self.bert = BertModel.from_pretrained(bertpath)
        for param in self.bert.parameters():
            param.requires_grad = True

        # GRU layers
        self.gru = nn.GRU(768, hidden_dim, n_layers, batch_first=True, bidirectional=bidirectional)

        # dropout layer
        self.dropout = nn.Dropout(drop_prob)

        # linear and sigmoid layers
        if bidirectional:
            self.fc = nn.Linear(hidden_dim * 2, output_size)
        else:
            self.fc = nn.Linear(hidden_dim, output_size)

        # self.sig = nn.Sigmoid()

    def forward(self, x, hidden):
        x = self.bert(x)[0]
        lstm_out, hidden_last = self.gru(x, hidden)

        if self.bidirectional:
            hidden_last_L = hidden_last[-2]
            hidden_last_R = hidden_last[-1]
            hidden_last_out = torch.cat([hidden_last_L, hidden_last_R], dim=-1)
        else:
            hidden_last_out = hidden_last[-1]
        out = self.dropout(hidden_last_out)
        out = self.fc(out)
        return out

    def init_hidden(self, batch_size):
        return torch.zeros((4, batch_size, self.hidden_dim)).cuda()



def train_model(config, data_train, predic, CV_num):
    net = bert_lstm(config.bert_path,
                    config.hidden_dim,
                    config.output_size,
                    config.n_layers,
                    config.bidirectional,
                    config.drop_prob
                    )
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(net.parameters(), lr=config.lr)
    if (config.use_cuda):
        net.cuda()
    net.train()
    for e in range(config.epochs):
        # initialize hidden state
        h = net.init_hidden(config.batch_size)
        counter = 0
        # batch loop
        for inputs, labels in data_train:
            counter += 1
            if (config.use_cuda):
                inputs, labels = inputs.cuda(), labels.cuda()
            if hasattr(torch.cuda, 'empty_cache'):
                torch.cuda.empty_cache()
            net.zero_grad()
            output = net(inputs, h)
            loss = criterion(output.squeeze(), labels.long())
            loss.backward()
            optimizer.step()

            if hasattr(torch.cuda, 'empty_cache'):
                torch.cuda.empty_cache()

            # loss stats
            if counter % config.print_every == 0:
                net.eval()
                # with torch.no_grad():
                #     val_h = net.init_hidden(config.batch_size)
                #     val_losses = []

                net.train()
                # print("Epoch: {}/{}, ".format(e + 1, config.epochs),
                #       "Step: {}, ".format(counter),
                #       "Loss: {:.6f}, ".format(loss.item()))
    torch.save(net.state_dict(), config.save_path + predic + '_' + str(CV_num) + '.pth')


def test_model(config, data_test, predic, CV_num):
    net = bert_lstm(config.bert_path,
                    config.hidden_dim,
                    config.output_size,
                    config.n_layers,
                    config.bidirectional,
                    config.drop_prob
                    )
    net.load_state_dict(torch.load(config.save_path + predic + '_' + str(CV_num) + '.pth'))
    if (config.use_cuda):
        net.cuda()
    net.train()
    criterion = nn.CrossEntropyLoss()
    test_losses = []

    net.eval()

    classnum = 2
    res = []
    predict_num = torch.zeros((1, classnum))
    # init hidden state
    h = net.init_hidden(config.batch_size)
    net.eval()
    # iterate over test data
    for inputs, labels in data_test:
        if (USE_CUDA):
            inputs, labels = inputs.cuda(), labels.cuda()
        output = net(inputs, h)

        test_loss = criterion(output.squeeze(), labels.long())
        test_losses.append(test_loss.item())
        _, pred = torch.max(output, 1)
        res.append(pred.cpu().numpy().tolist())
        pre_mask = torch.zeros(output.size()).scatter_(1, pred.cpu().view(-1, 1), 1.)
    # print('predict_num', " ".join('%s' % id for id in predict_num))
    res = np.array(res).reshape(1, -1).tolist()
    return res[0]


def myDataProcess(dataFile):
    df = pd.read_csv(str(dataFile), encoding='Latin-1')

    labeledDF = df[df.label.notnull()]
    labeledDF["Concatenated_Messages"].apply(lambda x: x.replace('<enter>', '$enter').replace('<tab>', '$tab'). \
                                    replace('<url>', '$url').replace('<version>', '$version') \
                                    .replace('<pr_link>', '$pull request>').replace('<issue_link >',
                                                                                    '$issue') \
                                    .replace('<otherCommit_link>', '$other commit').replace("<method_name>",
                                                                                            "$method") \
                                    .replace("<file_name>", "$file").replace("<iden>", "$token")) # Concatenated_Messages

    whyLabels = labeledDF['label'].apply(
        lambda x: 1 if x == 0 else (0 if x == 1.0 else (1 if x == 2.0 else (0 if x == 3.0 else 1))))
    whatLabels = labeledDF['label'].apply(
        lambda x: 1 if x == 0 else (0 if x == 1.0 else (0 if x == 2.0 else (1 if x == 3.0 else 0))))
    Labels = labeledDF['label'].apply(
        lambda x: 1 if x == 0 else (0 if x == 1.0 else (0 if x == 2.0 else (0 if x == 3.0 else 1)))) # good
    print("load data successfully!")
    # ifAllTextFile = labeledDF["if_all_text_file"]
    # ifAllCodeFile = labeledDF["if_all_code_file"]
    # changeLines = labeledDF["change_lines"]
    # developerExpertise = labeledDF["developer_expertise"]
    # commitDatePos = labeledDF["commit_date_position"]
    messages = list(labeledDF['Concatenated_Messages'].array)

    return messages, np.array(whyLabels), np.array(whatLabels), np.array(Labels)


if __name__ == '__main__':
    #os.system("/home/tyc/srun-linux")
    os.environ["CUDA_VISIBLE_DEVICES"] = "1"

    model_config = ModelConfig() # the model's configuration (hyperparameters)
    text, whyLabels, whatLabels, Labels = myDataProcess(
        "../ClassifierTraining/new_Dataset_2.csv")
    result_comments = text
    tokenizer = BertTokenizer.from_pretrained(model_config.bert_path)

    result_comments_id = tokenizer(result_comments,
                                   padding=True,
                                   truncation=True,
                                   max_length=200,
                                   return_tensors='pt')
    X = result_comments_id['input_ids']
    y = torch.from_numpy(whyLabels).float()
    yWhat = torch.from_numpy(whatLabels).float()
    yAll = torch.from_numpy(Labels).float()

    fold = KFold(n_splits=10, random_state=6666, shuffle=True)

    PRECISION = np.array([0.0, 0.0])
    RECALl = np.array([0.0, 0.0])
    F1 = np.array([0.0, 0.0])
    ACC = 0.0
    fold_num = 1
    WeightedPRECISION = 0.0
    WeightedRECALl = 0.0
    WeightedF1 = 0.0
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    tp_i_why = 0
    fp_i_why = 0
    tn_i_why = 0
    fn_i_why = 0

    tp_i_what = 0
    fp_i_what = 0
    tn_i_what = 0
    fn_i_what = 0
    cur_CV = 1
    for train_index, test_index in fold.split(X, y):
        cur_CV += 1
        X_train, X_test, y_train, y_test = \
            X[train_index], X[test_index], y[train_index], y[test_index]

        print("train_label: %s" % str(sorted(Counter(y_train).items())))
        yWhat_train, yWhat_test = \
            yWhat[train_index], yWhat[test_index]

        yAll_train, yAll_test = \
            yAll[train_index], yAll[test_index]

        # why training

        XWhy_train, y_train = X_train, y_train # no imba

        # posNum = np.sum(whyLabels == 1)
        # negNum = (int)(posNum / model_config.sampleRate)
        # XWhy_train, y_train = RandomOverSampler(sampling_strategy={1: posNum, 0: negNum},
        #                                         random_state=666).fit_resample(
        #     X_train, y_train)
        # print("train_label: %s" % str(sorted(Counter(y_train).items())))
        # # XWhy_train = X_train
        # XWhy_train = torch.from_numpy(XWhy_train)
        # y_train = torch.from_numpy(y_train)

        train_data = TensorDataset(XWhy_train, y_train)
        test_data = TensorDataset(X_test, y_test)
        print(len(XWhy_train))
        print(len(y_train))
        print(len(X_test))

        train_loader = DataLoader(train_data,
                                  shuffle=True,
                                  batch_size=model_config.batch_size,
                                  drop_last=True)
        test_loader = DataLoader(test_data,
                                 shuffle=False,
                                 batch_size=model_config.batch_size,
                                 drop_last=True)
        if (USE_CUDA):
            print('Run on GPU.')
        else:
            print('No GPU available, run on CPU.')
        train_model(model_config, train_loader, "predWhy", cur_CV)

        predWhy = test_model(model_config, test_loader, "predWhy", cur_CV)

        # what training

        # XWhat_train, yWhat_train = X_train, yWhat_train # no imba

        #with imba
        posNum = np.sum(whatLabels == 1)
        negNum = (int)(posNum / 1.5)
        XWhat_train, yWhat_train = RandomOverSampler(sampling_strategy={1: posNum, 0: negNum},
                                                     random_state=666).fit_resample(
            X_train, yWhat_train)
        print("train_label: %s" % str(sorted(Counter(yWhat_train).items())))
        # XWhat_train = X_train
        XWhat_train = torch.from_numpy(XWhat_train)
        yWhat_train = torch.from_numpy(yWhat_train)


        train_data = TensorDataset(XWhat_train, yWhat_train)
        test_data = TensorDataset(X_test, yWhat_test)
        print(len(XWhat_train))
        print(len(yWhat_train))
        print(len(X_test))

        train_loader = DataLoader(train_data,
                                  shuffle=True,
                                  batch_size=model_config.batch_size,
                                  drop_last=True)
        test_loader = DataLoader(test_data,
                                 shuffle=False,
                                 batch_size=model_config.batch_size,
                                 drop_last=True)
        if (USE_CUDA):
            print('Run on GPU.')
        else:
            print('No GPU available, run on CPU.')
        train_model(model_config, train_loader, "predWhat", cur_CV)

        # Good performance evaluation
        predWhat = test_model(model_config, test_loader, "predWhat", cur_CV)
        print(len(predWhat))
        print(len(predWhy))
        print(len(yAll_test))
        for i in range(0, len(predWhy)):
            why, what, tar = predWhy[i], predWhat[i], yAll_test[i]
            if (why + what) == 2 and tar == 1:
                tp += 1
            elif (why + what) == 2 and tar == 0:
                fp += 1
            elif (why + what) != 2 and tar == 1:
                fn += 1
            elif (why + what) != 2 and tar == 0:
                tn += 1

        precision = 0 if tp + fp == 0 else tp / (tp + fp)
        NegativePrecision = 0 if tn + fn == 0 else tn / (tn + fn)
        recall = 0 if tp + fn == 0 else tp / (tp + fn)
        NegativeRecall = 0 if tn + fp == 0 else tn / (tn + fp)
        F1 = 0 if (precision + recall) == 0 else (2 * precision * recall) / (precision + recall)
        NegativeF1 = 0 if (NegativePrecision + NegativeRecall) == 0 else (2 * NegativeRecall * NegativePrecision) / (
                NegativePrecision + NegativeRecall)
        accuracy = (tp + tn) / (tp + tn + fp + fn)

        print(tp, fp, tn, fn)
        print('Total Accuracy', accuracy)
        print('Total Precision', [NegativePrecision, precision])
        print('Total Recall', [NegativeRecall, recall])
        print('Total F1', [NegativeF1, F1])

        # Why performance evaluation
        for i in range(0, len(predWhy)):
            why, tar = predWhy[i], y_test[i]
            if why == 1 and tar == 1:
                tp_i_why += 1
            elif why == 1 and tar == 0:
                fp_i_why += 1
            elif why != 1 and tar == 1:
                fn_i_why += 1
            elif why != 1 and tar == 0:
                tn_i_why += 1

        precision = 0 if tp_i_why + fp_i_why == 0 else tp_i_why / (tp_i_why + fp_i_why)
        NegativePrecision = 0 if tn_i_why + fn_i_why == 0 else tn_i_why / (tn_i_why + fn_i_why)
        recall = 0 if tp_i_why + fn_i_why == 0 else tp_i_why / (tp_i_why + fn_i_why)
        NegativeRecall = 0 if tn_i_why + fp_i_why == 0 else tn_i_why / (tn_i_why + fp_i_why)
        F1 = 0 if (precision + recall) == 0 else (2 * precision * recall) / (precision + recall)
        NegativeF1 = 0 if (NegativePrecision + NegativeRecall) == 0 else (2 * NegativeRecall * NegativePrecision) / (
                NegativePrecision + NegativeRecall)
        accuracy = (tp_i_why + tn_i_why) / (tp_i_why + tn_i_why + fp_i_why + fn_i_why)

        print(tp_i_why, fp_i_why, tn_i_why, fn_i_why)
        print('[Why] Total Accuracy of ', accuracy)
        print('[Why] Total Precision of ', [NegativePrecision, precision])
        print('[Why] Total Recall of ', [NegativeRecall, recall])
        print('[Why] Total F1 of ', [NegativeF1, F1])

        # their model what
        for i in range(0, len(predWhat)):
            what, tar = predWhat[i], yWhat_test[i]
            if what == 1 and tar == 1:
                tp_i_what += 1
            elif what == 1 and tar == 0:
                fp_i_what += 1
            elif what != 1 and tar == 1:
                fn_i_what += 1
            elif what != 1 and tar == 0:
                tn_i_what += 1

        precision = 0 if tp_i_what + fp_i_what == 0 else tp_i_what / (tp_i_what + fp_i_what)
        NegativePrecision = 0 if tn_i_what + fn_i_what == 0 else tn_i_what / (tn_i_what + fn_i_what)
        recall = 0 if tp_i_what + fn_i_what == 0 else tp_i_what / (tp_i_what + fn_i_what)
        NegativeRecall = 0 if tn_i_what + fp_i_what == 0 else tn_i_what / (tn_i_what + fp_i_what)
        F1 = 0 if (precision + recall) == 0 else (2 * precision * recall) / (precision + recall)
        NegativeF1 = 0 if (NegativePrecision + NegativeRecall) == 0 else (2 * NegativeRecall * NegativePrecision) / (
                NegativePrecision + NegativeRecall)
        accuracy = (tp_i_what + tn_i_what) / (tp_i_what + tn_i_what + fp_i_what + fn_i_what)

        print(tp_i_what, fp_i_what, tn_i_what, fn_i_what)
        print('[What] Total Accuracy ', accuracy)
        print('[What] Total Precision of ', [NegativePrecision, precision])
        print('[What] Total Recall of ', [NegativeRecall, recall])
        print('[What] Total F1 of ', [NegativeF1, F1])
