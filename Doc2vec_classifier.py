"""

Classify data based on word2vec.

Based on: https://towardsdatascience.com/multi-class-text-classification-with-doc2vec-logistic-regression-9da9947b43f4

Taks in a csv data set with the columns: headline_text and topic.

Extension: in future we may want to extend so that we can deal with multiple topic labels. 

"""

import pandas as pd
import numpy as np
from tqdm import tqdm
tqdm.pandas(desc="progress-bar")
from gensim.models import Doc2Vec
from sklearn import utils
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import gensim
from sklearn.linear_model import LogisticRegression
from gensim.models.doc2vec import TaggedDocument
import re
import seaborn as sns
import matplotlib.pyplot as plt
import multiprocessing
from bs4 import BeautifulSoup
import nltk
import pdb
nltk.download('punkt')
from nltk.corpus import stopwords


cores = multiprocessing.cpu_count()

def cleanText(text):
	text = BeautifulSoup(text, "lxml").text
	text = re.sub(r'\|\|\|', r' ', text) 
	text = re.sub(r'http\S+', r'<URL>', text)
	text = text.lower()
	text = text.replace('x', '')
	return text


def read_and_process(file_path) :	
	

	"""

	Converts the .csv file into a pandas
	dataframe ready for use by word2vec.
	
	Parameters
	------------
	
	file_path : str 
	
	Location of the .csv file containing the data
	
	
	Returns
	
	df : pandas dataframe
	
	Data from the csv put into a pandas dataframe
	
	"""


	df = pd.read_csv(file_path)
	df = df[['headline_text','Topic']]
	df = df[pd.notnull(df['headline_text'])]
	df.rename(columns = {'headline_text':'narrative'}, inplace = True)

	df.index = range(df.shape[0])
	df['narrative'].apply(lambda x: len(x.split(' '))).sum()
	
	df['narrative'] = df['narrative'].apply(cleanText)
	
	return df



def vec_for_learning(model, tagged_docs):
    sents = tagged_docs.values
    targets, regressors = zip(*[(doc.tags[0], model.infer_vector(doc.words, steps=20)) for doc in sents])
    return targets, regressors

def vec_for_learning(model, tagged_docs):
    sents = tagged_docs.values
    targets, regressors = zip(*[(doc.tags[0], model.infer_vector(doc.words, steps=20)) for doc in sents])
    return targets, regressors
    

def tokenize_text(text):
    tokens = []
    for sent in nltk.sent_tokenize(text):
        for word in nltk.word_tokenize(sent):
            if len(word) < 2:
                continue
            tokens.append(word.lower())
    return tokens

#Read in and process the data:
#file_path = 'headline_examples.csv' 
file_path = 'training_new_corpus/headlines_two_class.csv'
df = read_and_process(file_path)

#split the data:
train, test = train_test_split(df, test_size=0.3, random_state=42)

#Tag the data:
train_tagged = train.apply(lambda r: TaggedDocument(words=tokenize_text(r['narrative']), tags=[r.Topic]), axis=1)
test_tagged = test.apply(lambda r: TaggedDocument(words=tokenize_text(r['narrative']), tags=[r.Topic]), axis=1)


dimensions = 2
#Initialize and train the model: (mindlessly using parameters from the original source of the code)
model_dbow = Doc2Vec(dm=0, vector_size=dimensions, negative=5, hs=0, min_count=2, sample = 0, workers=cores)
model_dbow.build_vocab([x for x in tqdm(train_tagged.values)]) 


for epoch in range(30):
    model_dbow.train(utils.shuffle([x for x in tqdm(train_tagged.values)]), total_examples=len(train_tagged.values), epochs=1)
    model_dbow.alpha -= 0.002
    model_dbow.min_alpha = model_dbow.alpha
    

#Given the model we now return the vectors and labels:
y_train, X_train = vec_for_learning(model_dbow, train_tagged)
y_test, X_test = vec_for_learning(model_dbow, test_tagged)

Test_Positions = list( X_train )

def labeler(label) : 
	if label == "Climate Change" : 
		return "b"
	else :
		return "r"

Labels = [ labeler(k) for k in y_train ] 
plt.scatter( np.transpose(Test_Positions)[0] ,np.transpose(Test_Positions)[1] , c=Labels ) 
plt.savefig("D2V_in_2D_on_training_data")

#Plot the coordinates:
#pdb.set_trace()

print("TEST TAGGED")
print(test_tagged)

logreg = LogisticRegression(n_jobs=1, C=1e5)
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)


print('\n\nTesting accuracy %s' % accuracy_score(y_test, y_pred))
print('\n\nTesting F1 score: {}'.format(f1_score(y_test, y_pred, average='weighted')))

#convert pd to a numpy array:

TT = test_tagged.values

#pdb.set_trace()

for i in range(len(TT) ) : 
	WORDS = ' '.join(word for word in TT[i].words) 
	print("\nActual = {}  , Predicted = {} , Text = {} ".format(TT[i].tags,y_pred[i],WORDS) ) 
