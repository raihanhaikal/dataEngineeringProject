"""
Data didapatkan dari twitter melalui Kafka Streaming dan telah di sesuaikan dengan skema MySQL. Data diambil dari tweet yang mengandung kata "Indihome"
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re

indihome = pd.read_csv('/content/dump.csv')
indihome.head()

indihome = indihome.drop(columns=['index', 'user_id', 'timestamp'])
indihome

indihome['text'] =  [re.sub(r"b'|b\'|b\"|\\[a-z][0-9][a-z]|\\[a-z][a-z][0-9]|\\n|\\\\[x][0-9][0-9]\\|\'|x[a-z][a-z]|x[0-9][0-9]", 
                           "", str(j)) for j in indihome['text']]
indihome.head()

"""# Text Preprocessing

**Text PreProcessing**


---

Case Folding
"""

# gunakan fungsi Series.str.lower() pada Pandas
indihome['text'] = indihome['text'].str.lower()


print('Case Folding Result : \n')
print(indihome['text'].head(5))

"""Tokenization"""

import string 
import re #regex library

# import word_tokenize & FreqDist from NLTK
from nltk.tokenize import word_tokenize 
from nltk.probability import FreqDist
import nltk
nltk.download('punkt')
nltk.download('stopwords')

# ------ Tokenizing ---------

def remove_tweet_special(text):
    # remove tab, new line, ans back slice
    text = text.replace('\\t'," ").replace('\\n'," ").replace('\\u'," ").replace('\\',"")
    # remove non ASCII (emoticon, chinese word, .etc)
    text = text.encode('ascii', 'replace').decode('ascii')
    # remove mention, link, hashtag
    text = ' '.join(re.sub("([@#][A-Za-z0-9]+)|(\w+:\/\/\S+)"," ", text).split())
    # remove incomplete URL
    return text.replace("http://", " ").replace("https://", " ")
                
indihome['text'] = indihome['text'].apply(remove_tweet_special)

#remove number
def remove_number(text):
    return  re.sub(r"\d+", "", text)

indihome['text'] = indihome['text'].apply(remove_number)

#remove punctuation
def remove_punctuation(text):
    return text.translate(str.maketrans("","",string.punctuation))

indihome['text'] = indihome['text'].apply(remove_punctuation)

#remove whitespace leading & trailing
def remove_whitespace_LT(text):
    return text.strip()

indihome['text'] = indihome['text'].apply(remove_whitespace_LT)

#remove multiple whitespace into single whitespace
def remove_whitespace_multiple(text):
    return re.sub('\s+',' ',text)

indihome['text'] = indihome['text'].apply(remove_whitespace_multiple)

# remove single char
def remove_singl_char(text):
    return re.sub(r"\b[a-zA-Z]\b", "", text)

indihome['text'] = indihome['text'].apply(remove_singl_char)

def word_tokenize_wrapper(text):
    return word_tokenize(text)

indihome['token_text'] = indihome['text'].apply(word_tokenize_wrapper)

print('Tokenizing Result : \n') 
print(indihome.head())

# NLTK calc frequency distribution
def freqDist_wrapper(text):
    return FreqDist(text)

indihome['token_text_freq'] = indihome['token_text'].apply(freqDist_wrapper)

print('Frequency Tokens : \n') 
print(indihome['token_text_freq'].head().apply(lambda x : x.most_common()))

"""Filtering"""

from nltk.corpus import stopwords

# ----------------------- get stopword from NLTK stopword -------------------------------
# get stopword indonesia
list_stopwords = stopwords.words('indonesian')
# ---------------------------- manualy add stopword  ------------------------------------
# append additional stopword
list_stopwords.extend(["yg", "dg", "rt", "dgn", "ny", "d", 'klo', 
                       'kalo', 'amp', 'biar', 'bikin', 'bilang', 
                       'gak', 'gk', 'ga', 'krn', 'nya', 'nih', 'sih', 
                       'si', 'tau', 'tdk', 'tuh', 'utk', 'ya', 
                       'jd', 'jgn', 'sdh', 'aja', 'n', 't', 
                       'nyg', 'hehe', 'pen', 'u', 'nan', 'loh', 'rt',
                       '&amp', 'yah'])

def stopwords_removal(words):
    return [word for word in words if word not in list_stopwords]

indihome['token_text_SR'] = indihome['token_text'].apply(stopwords_removal) 


print(indihome['token_text_SR'].head())

"""Stemmer"""

!pip install Sastrawi
!pip install swifter

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import swifter

# create stemmer
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# stemmed
def stemmed_wrapper(term):
    return stemmer.stem(term)

term_dict = {}

for document in indihome['token_text_SR']:
    for term in document:
        if term not in term_dict:
            term_dict[term] = ' '
            
print(len(term_dict))
print("------------------------")

for term in term_dict:
    term_dict[term] = stemmed_wrapper(term)
    print(term,":" ,term_dict[term])
    
print(term_dict)
print("------------------------")


# apply stemmed term to dataframe
def get_stemmed_term(document):
    return [term_dict[term] for term in document]

indihome['tweet_tokens_stemmed'] = indihome['token_text_SR'].swifter.apply(get_stemmed_term)
print(indihome['tweet_tokens_stemmed'])

indihome.to_csv("Text_Preprocessing.csv")

"""# Clustering"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from sklearn.cluster import KMeans 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
from sklearn.metrics import pairwise_distances

import nltk
import string

import matplotlib.pyplot as plt
# %matplotlib inline
plt.style.use('fivethirtyeight')


# email module has some useful functions
import os, sys, email,re

df = pd.read_csv('/content/Text_Preprocessing.csv',nrows = 35000)
df

from sklearn.feature_extraction.text import TfidfVectorizer
data = df['tweet_tokens_stemmed']


tf_idf_vectorizor = TfidfVectorizer(#stop_words = 'english',#tokenizer = tokenize_and_stem,
                             max_features = 20000)
tf_idf = tf_idf_vectorizor.fit_transform(data)
tf_idf_norm = normalize(tf_idf)
tf_idf_array = tf_idf_norm.toarray()

pd.DataFrame(tf_idf_array, columns=tf_idf_vectorizor.get_feature_names()).head()

from sklearn.cluster import KMeans
sklearn_pca = PCA(n_components = 2)
Y_sklearn = sklearn_pca.fit_transform(tf_idf_array)

number_clusters = range(1, 10)

kmeans = [KMeans(n_clusters=i, max_iter = 600) for i in number_clusters]
kmeans

score = [kmeans[i].fit(Y_sklearn).score(Y_sklearn) for i in range(len(kmeans))]
score

plt.plot(number_clusters, score)
plt.xlabel('Number of Clusters')
plt.ylabel('Score')
plt.title('Elbow Method')
plt.show()

from sklearn.cluster import KMeans
sklearn_pca = PCA(n_components = 2)
Y_sklearn = sklearn_pca.fit_transform(tf_idf_array)
kmeans = KMeans(n_clusters=5, max_iter=600, algorithm = 'auto')
fitted = kmeans.fit(Y_sklearn)
prediction = kmeans.predict(Y_sklearn)
plt.scatter(Y_sklearn[:, 0], Y_sklearn[:, 1], c=prediction, s=50, cmap='viridis')

centers = fitted.cluster_centers_
plt.scatter(centers[:, 0], centers[:, 1],c='black', s=200, alpha=0.6)

def get_top_features_cluster(tf_idf_array, prediction, n_feats):
    labels = np.unique(prediction)
    dfs = []
    for label in labels:
        id_temp = np.where(prediction==label) # indices for each cluster
        x_means = np.mean(tf_idf_array[id_temp], axis = 0) # returns average score across cluster
        sorted_means = np.argsort(x_means)[::-1][:n_feats] # indices with top 20 scores
        features = tf_idf_vectorizor.get_feature_names()
        best_features = [(features[i], x_means[i]) for i in sorted_means]
        df = pd.DataFrame(best_features, columns = ['features', 'score'])
        dfs.append(df)
    return dfs
dfs = get_top_features_cluster(tf_idf_array, prediction, 15)

import seaborn as sns
plt.figure(figsize=(8,6))
ax = sns.barplot(x = 'score' , y = 'features', orient = 'h' , data = dfs[0][:15])
ax.set_title('Cluster 1')

plt.figure(figsize=(8,6))
ax = sns.barplot(x = 'score' , y = 'features', orient = 'h' , data = dfs[1][:15])
ax.set_title('Cluster 2')

plt.figure(figsize=(8,6))
ax = sns.barplot(x = 'score' , y = 'features', orient = 'h' , data = dfs[2][:15])
ax.set_title('Cluster 3')

plt.figure(figsize=(8,6))
ax = sns.barplot(x = 'score' , y = 'features', orient = 'h' , data = dfs[3][:15])
ax.set_title('Cluster 4')

plt.figure(figsize=(8,6))
ax = sns.barplot(x = 'score' , y = 'features', orient = 'h' , data = dfs[4][:15])
ax.set_title('Cluster 5')
