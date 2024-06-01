import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

stop_words = set(stopwords.words('english'))

input_csv = "../Filelevel_all/FL_1000.csv"

cur_dataset = pd.read_csv(input_csv, encoding="Latin-1")

volumes = []

for i in range(0, cur_dataset.shape[0]):
    cur_line = cur_dataset.iloc[i, :].values
    new_message1 = str(cur_line[1]).strip()
    new_message1_tokens = word_tokenize(new_message1)
    filtered_sentence = [w for w in new_message1_tokens if not w.lower() in stop_words]
    volumes.append(len(filtered_sentence))

volumes_col = pd.DataFrame(volumes, columns = ['Volume'])

result = pd.concat([cur_dataset, volumes_col], axis=1)
result.to_csv("../Filelevel_all/FL_1000.csv", index=False)
