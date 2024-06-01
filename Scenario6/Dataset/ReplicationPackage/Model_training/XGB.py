from xgboost import XGBClassifier
import numpy as np
import pandas as pd
from transformers import BertTokenizer, BertModel
from sklearn.pipeline import make_pipeline
from sklearn import preprocessing
from sklearn.model_selection import cross_validate
from skopt import BayesSearchCV
from sklearn.model_selection import KFold
import pickle
import warnings
import torch

def warn(*args, **kwargs):
    pass

warnings.warn = warn

def myDataProcess(dataFile):
    df = pd.read_csv(str(dataFile), encoding='Latin-1')

    labeledDF = df[df.label.notnull()]
    labeledDF["Concatenated_Messages"].apply(lambda x: x.replace('<enter>', '$enter').replace('<tab>', '$tab'). \
                                    replace('<url>', '$url').replace('<version>', '$version') \
                                    .replace('<pr_link>', '$pull request>').replace('<issue_link >',
                                                                                    '$issue') \
                                    .replace('<otherCommit_link>', '$other commit').replace("<method_name>",
                                                                                            "$method") \
                                    .replace("<file_name>", "$file").replace("<iden>", "$token")) #Concatenated_Messages

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
    #sim_scores = list(labeledDF['Similar_scores_fixed'].array)

    return messages, whyLabels, whatLabels, Labels#, sim_scores

texts, whyLabels, whatLabels, Labels  = myDataProcess("./new_Dataset_2.csv")

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
tokenized_texts = tokenizer(texts,padding=True,truncation=True,max_length=100,return_tensors='pt')
BERT_model = BertModel.from_pretrained("bert-base-uncased")

embedded_CLS_texts = BERT_model(input_ids=tokenized_texts['input_ids'],attention_mask=tokenized_texts['attention_mask'],return_dict=False)[1]
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
print(embedded_CLS_texts.shape)
embedded_CLS_texts_list = embedded_CLS_texts.detach().numpy()
#embedded_CLS_texts_list = torch.from_numpy(embedded_CLS_texts_list)
#for i in range(len(sim_scores)):
#    if sim_scores[i] == "0":
#        embedded_CLS_texts_list[i].append(np.nan)
#    else:
#        embedded_CLS_texts_list[i].append(float(sim_scores[i])) # add sim score as another feature

random_grid = {
        'gamma': [0,0.1,0.2,0.4,0.5,0.8,1, 1.6,2,3.2,5,6.4,12.8,25.6],
        'colsample_bytree': [0.6, 0.8, 1.0],
        'max_depth': [3, 4, 5,6,7,8,9,10,11,12],
        'learning_rate': [0.01, 0.03, 0.06, 0.1, 0.15, 0.2, 0.25, 0.3],
        'n_estimators': [50,65,80,100,130,150],
        'booster': ['gbtree', 'gblinear'],
        'tree_method': ['exact', 'approx', 'hist'],
        'reg_alpha': [0,0.1,0.2,0.4,0.8,1.6,3.2,6.4,12.8,25.6],
        'reg_lambda': [0,0.1,0.2,0.4,0.8,1.6,3.2,6.4,12.8,25.6],
        'subsample': [0.5, 0.6, 0.7, 0.8, 0.9, 1]
        }
scoring = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
fold = KFold(n_splits=10, random_state=6666, shuffle=True)


clf_why = XGBClassifier()
grid_model_why = BayesSearchCV(estimator=clf_why,
                    search_spaces=random_grid,
                    cv=fold, n_iter = 50, scoring='roc_auc', refit='roc_auc'
                    , error_score='raise')
grid_model_why.fit(embedded_CLS_texts_list, whyLabels)
print(grid_model_why.best_score_)

clf_what = XGBClassifier()
grid_model_what = BayesSearchCV(estimator=clf_what,
                    search_spaces=random_grid,
                    cv=fold, n_iter = 50, scoring='roc_auc', refit='roc_auc'
                    , error_score='raise')
grid_model_what.fit(embedded_CLS_texts_list, whatLabels)
print(grid_model_what.best_score_)

clf_good = XGBClassifier()
grid_model_good = BayesSearchCV(estimator=clf_good,
                    search_spaces=random_grid,
                    cv=fold, n_iter = 50, scoring='roc_auc', refit='roc_auc'
                    , error_score='raise')
grid_model_good.fit(embedded_CLS_texts_list, Labels)
print(grid_model_good.best_score_)

clf_A_why = XGBClassifier(gamma=grid_model_why.best_params_['gamma'],
subsample=grid_model_why.best_params_['subsample'],
colsample_bytree=grid_model_why.best_params_['colsample_bytree'],
learning_rate=grid_model_why.best_params_['learning_rate'],
n_estimators=grid_model_why.best_params_['n_estimators'],
booster=grid_model_why.best_params_['booster'],
max_depth=grid_model_why.best_params_['max_depth'],
tree_method=grid_model_why.best_params_['tree_method'],
reg_alpha=grid_model_why.best_params_['reg_alpha'],
reg_lambda=grid_model_why.best_params_['reg_lambda']
                                                                           )
scores_why = cross_validate(clf_A_why, embedded_CLS_texts_list, whyLabels, cv=fold, scoring=scoring, error_score='raise', return_estimator=True)
with open('XGB200_why_1.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][0],f)
with open('XGB200_why_2.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][1],f)
with open('XGB200_why_3.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][2],f)
with open('XGB200_why_4.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][3],f)
with open('XGB200_why_5.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][4],f)
with open('XGB200_why_6.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][5],f)
with open('XGB200_why_7.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][6],f)
with open('XGB200_why_8.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][7],f)
with open('XGB200_why_9.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][8],f)
with open('XGB200_why_10.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][9],f)

clf_A_what =  XGBClassifier(gamma=grid_model_what.best_params_['gamma'],
subsample=grid_model_what.best_params_['subsample'],
colsample_bytree=grid_model_what.best_params_['colsample_bytree'],
learning_rate=grid_model_what.best_params_['learning_rate'],
n_estimators=grid_model_what.best_params_['n_estimators'],
booster=grid_model_what.best_params_['booster'],
max_depth=grid_model_what.best_params_['max_depth'],
tree_method=grid_model_what.best_params_['tree_method'],
reg_alpha=grid_model_what.best_params_['reg_alpha'],
reg_lambda=grid_model_what.best_params_['reg_lambda']
                                                                           )
scores_what = cross_validate(clf_A_what, embedded_CLS_texts_list, whatLabels, cv=fold, scoring=scoring, error_score='raise', return_estimator=True)
with open('XGB200_what_1.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][0],f)
with open('XGB200_what_2.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][1],f)
with open('XGB200_what_3.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][2],f)
with open('XGB200_what_4.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][3],f)
with open('XGB200_what_5.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][4],f)
with open('XGB200_what_6.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][5],f)
with open('XGB200_what_7.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][6],f)
with open('XGB200_what_8.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][7],f)
with open('XGB200_what_9.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][8],f)
with open('XGB200_what_10.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][9],f)

clf_A_good = XGBClassifier(gamma=grid_model_good.best_params_['gamma'],
subsample=grid_model_good.best_params_['subsample'],
colsample_bytree=grid_model_good.best_params_['colsample_bytree'],
learning_rate=grid_model_good.best_params_['learning_rate'],
n_estimators=grid_model_good.best_params_['n_estimators'],
booster=grid_model_good.best_params_['booster'],
max_depth=grid_model_good.best_params_['max_depth'],
tree_method=grid_model_good.best_params_['tree_method'],
reg_alpha=grid_model_good.best_params_['reg_alpha'],
reg_lambda=grid_model_good.best_params_['reg_lambda']
                                                                           )
scores_good = cross_validate(clf_A_good, embedded_CLS_texts_list, Labels, cv=fold, scoring=scoring, error_score='raise', return_estimator=True)
with open('XGB200_good_1.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][0],f)
with open('XGB200_good_2.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][1],f)
with open('XGB200_good_3.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][2],f)
with open('XGB200_good_4.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][3],f)
with open('XGB200_good_5.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][4],f)
with open('XGB200_good_6.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][5],f)
with open('XGB200_good_7.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][6],f)
with open('XGB200_good_8.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][7],f)
with open('XGB200_good_9.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][8],f)
with open('XGB200_good_10.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][9],f)

print("Why AUC: ", sum(scores_why['test_roc_auc']) / 10)
print("What AUC: ", sum(scores_what['test_roc_auc']) / 10)
print("Good AUC: ", sum(scores_good['test_roc_auc']) / 10)
print("Why F1: ", sum(scores_why['test_f1']) / 10)
print("What F1: ", sum(scores_what['test_f1']) / 10)
print("Good F1: ", sum(scores_good['test_f1']) / 10)
print("Why accuracy: ", sum(scores_why['test_accuracy']) / 10)
print("What accuracy: ", sum(scores_what['test_accuracy']) / 10)
print("Good accuracy: ", sum(scores_good['test_accuracy']) / 10)
print("Why precision: ", sum(scores_why['test_precision']) / 10)
print("What precision: ", sum(scores_what['test_precision']) / 10)
print("Good precision: ", sum(scores_good['test_precision']) / 10)
print("Why recall: ", sum(scores_why['test_recall']) / 10)
print("What recall: ", sum(scores_what['test_recall']) / 10)
print("Good recall: ", sum(scores_good['test_recall']) / 10)

print("Why scores: ", scores_why)
print("What scores: ", scores_what)
print("Good scores: ", scores_good)
