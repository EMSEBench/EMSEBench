from sklearn.svm import SVC
import numpy as np
import pandas as pd
from transformers import BertTokenizer, BertModel
import imblearn
import sklearn
#from sklearn.pipeline import make_pipeline
from sklearn import preprocessing
from sklearn.model_selection import cross_validate
from sklearn.model_selection import GridSearchCV
#from imblearn.pipeline import make_pipeline
import warnings
import pickle
from imblearn.over_sampling import RandomOverSampler

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

texts, whyLabels, whatLabels, Labels = myDataProcess("../new_Dataset_2.csv")

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
tokenized_texts = tokenizer(texts,padding=True,truncation=True,max_length=150,return_tensors='pt')
BERT_model = BertModel.from_pretrained("bert-base-uncased")

embedded_CLS_texts = BERT_model(input_ids=tokenized_texts['input_ids'],attention_mask=tokenized_texts['attention_mask'],return_dict=False)[1]
embedded_CLS_texts_list = embedded_CLS_texts.detach().numpy()

# for i in range(len(sim_scores)):
#   embedded_CLS_texts_list[i].append(sim_scores[i]) # add sim score as another feature

p_grid = {'C': np.logspace(-4, 2, 10), 'gamma': ['scale','auto',1,0.1,0.01,0.001],'kernel': ['rbf', 'poly', 'sigmoid']}
scoring = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']


clf_why = SVC()
grid_model_why = GridSearchCV(clf_why,
                    param_grid=p_grid,
                    cv=10, scoring='roc_auc', refit='roc_auc'
                    , error_score='raise')
grid_model_why.fit(embedded_CLS_texts_list, whyLabels)
print(grid_model_why.best_score_)
print(grid_model_why.best_params_)

clf_what = SVC()
grid_model_what = GridSearchCV(clf_what,
                    param_grid=p_grid,
                    cv=10, scoring='roc_auc', refit='roc_auc'
                    , error_score='raise')
grid_model_what.fit(embedded_CLS_texts_list, whatLabels)
print(grid_model_what.best_score_)
print(grid_model_what.best_params_)

clf_good = SVC()
grid_model_good = GridSearchCV(clf_good,
                    param_grid=p_grid,
                    cv=10, scoring='roc_auc', refit='roc_auc'
                    ,error_score='raise')
grid_model_good.fit(embedded_CLS_texts_list, Labels)
print(grid_model_good.best_score_)
print(grid_model_good.best_params_)

clf_A_why = SVC(C=grid_model_why.best_params_['C'],
                                                                            kernel=grid_model_why.best_params_['kernel'],
                                                                            gamma=grid_model_why.best_params_['gamma']
                                                                           )
scores_why = cross_validate(clf_A_why, embedded_CLS_texts_list, whyLabels, cv=10, scoring=scoring,  error_score='raise', return_estimator=True)

with open('SVM_why_fh_1.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][0],f)
with open('SVM_why_fh_2.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][1],f)
with open('SVM_why_fh_3.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][2],f)
with open('SVM_why_fh_4.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][3],f)
with open('SVM_why_fh_5.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][4],f)
with open('SVM_why_fh_6.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][5],f)
with open('SVM_why_fh_7.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][6],f)
with open('SVM_why_fh_8.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][7],f)
with open('SVM_why_fh_9.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][8],f)
with open('SVM_why_fh_10.pkl','wb') as f:
    pickle.dump(scores_why['estimator'][9],f)

clf_A_what = SVC(C=grid_model_what.best_params_['C'],
                                                                            kernel=grid_model_what.best_params_['kernel'],
                                                                            gamma=grid_model_what.best_params_['gamma']
                                                                           )
scores_what = cross_validate(clf_A_what, embedded_CLS_texts_list, whatLabels, cv=10, scoring=scoring,  error_score='raise', return_estimator=True)

with open('SVM_what_fh_1.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][0],f)
with open('SVM_what_fh_2.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][1],f)
with open('SVM_what_fh_3.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][2],f)
with open('SVM_what_fh_4.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][3],f)
with open('SVM_what_fh_5.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][4],f)
with open('SVM_what_fh_6.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][5],f)
with open('SVM_what_fh_7.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][6],f)
with open('SVM_what_fh_8.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][7],f)
with open('SVM_what_fh_9.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][8],f)
with open('SVM_what_fh_10.pkl','wb') as f:
    pickle.dump(scores_what['estimator'][9],f)

clf_A_good = SVC(C=grid_model_good.best_params_['C'],
                                                                            kernel=grid_model_good.best_params_['kernel'],
                                                                            gamma=grid_model_good.best_params_['gamma']
                                                                           )
scores_good = cross_validate(clf_A_good, embedded_CLS_texts_list, Labels, cv=10, scoring=scoring, error_score='raise', return_estimator=True)

with open('SVM_good_fh_1.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][0],f)
with open('SVM_good_fh_2.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][1],f)
with open('SVM_good_fh_3.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][2],f)
with open('SVM_good_fh_4.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][3],f)
with open('SVM_good_fh_5.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][4],f)
with open('SVM_good_fh_6.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][5],f)
with open('SVM_good_fh_7.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][6],f)
with open('SVM_good_fh_8.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][7],f)
with open('SVM_good_fh_9.pkl','wb') as f:
    pickle.dump(scores_good['estimator'][8],f)
with open('SVM_good_fh_10.pkl','wb') as f:
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
