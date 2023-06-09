# -*- coding: utf-8 -*-
"""Untitled3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AXVd59cZ2Nt4lDAe8g8yTbwcxXfkx2x9
"""

import tarfile
import os
import urllib

down_path = "http://spamassassin.apache.org/old/publiccorpus/"
ham_url = down_path + "20030228_easy_ham.tar.bz2"
spam_url = down_path + "20030228_spam.tar.bz2"
spam_path = os.path.join("datasets", "spam")

def fetch_spam_data(spam_url=spam_url, spam_path=spam_path):
    if not os.path.isdir(spam_path):
        os.makedirs(spam_path)
    for filename, url in (("ham.tar.bz2", ham_url), ("spam.tar.bz2", spam_url)):
        path = os.path.join(spam_path, filename)
        if not os.path.isfile(path):
            urllib.request.urlretrieve(url, path)
        tar_bz2_file = tarfile.open(path)
        tar_bz2_file.extractall(path=spam_path)
        tar_bz2_file.close()

fetch_spam_data()

ham_directory = os.path.join(spam_path, "easy_ham")
spam_directory = os.path.join(spam_path, "spam")
ham_filenames = [name for name in sorted(os.listdir(ham_directory)) if len(name) > 20]
spam_filenames = [name for name in sorted(os.listdir(spam_directory)) if len(name) > 20]

print(len(ham_filenames))
print(len(spam_filenames))

import email
import email.policy

def get_mails(is_spam, file, spam_path=spam_path):
    if is_spam:
        directory = "spam"
    else:
        directory = "easy_ham"
    with open(os.path.join(spam_path, directory, file), "rb") as f:
              return email.parser.BytesParser(policy=email.policy.default).parse(f)
ham_emails = [get_mails(is_spam=False, file=name) for name in ham_filenames]
spam_emails = [get_mails(is_spam=True, file=name) for name in spam_filenames]

print(ham_emails[42].get_content().strip())

print(spam_emails[42].get_content().strip())

def email_structure(email):
    if isinstance(email, str):
        return email
    payload = email.get_payload()
    if isinstance(payload, list):
        return "multipart({})".format(", ".join([
            email_structure(sub_email)
            for sub_email in payload
        ]))
    else:
        return email.get_content_type()
    
from collections import Counter

def structure_count(emails):
    structures = Counter()
    for email in emails:
        structure = email_structure(email)
        structures[structure] += 1
    return structures

structure_count(ham_emails).most_common()

for header, value in spam_emails[42].items():
    print(header,"-->",value)

spam_emails[42]["Subject"]

import numpy as np
from sklearn.model_selection import train_test_split

X = np.array(ham_emails + spam_emails)
y = np.array([0] * len(ham_emails) + [1] * len(spam_emails))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

import re 
from html import unescape

def htmlTOtext(html):
    text = re.sub('<head.*?>.*?</head>', '', html, flags=re.M | re.S | re.I)
    text = re.sub('<a\s.*?>', ' HYPERLINK ', text, flags=re.M | re.S | re.I)
    text = re.sub('<.*?>', '', text, flags=re.M | re.S)
    text = re.sub(r'(\s*\n)+', '\n', text, flags=re.M | re.S)
    return unescape(text)

htmlSPAM = []
for email in X_train[y_train==1]:
    if email_structure(email) == "text/html":
        htmlSPAM.append(email)
sampleSPAM = htmlSPAM[5]
print(sampleSPAM.get_content().strip()[:1000], "...")

print(htmlTOtext(sampleSPAM.get_content())[:1000], "...")

def emailTOtext(email):
    html = None
    for part in email.walk():
        ctype = part.get_content_type()
        if not ctype in ("text/plain", "text/html"):
            continue
        try:
            content = part.get_content()
        except: # in case of encoding issues
            content = str(part.get_payload())
        if ctype == "text/plain":
            return content
        else:
            html = content
    if html:
        return htmlTOtext(html)

print(emailTOtext(sampleSPAM)[:100], "...")

import nltk
stemmer = nltk.PorterStemmer()
for word in ("Computations", "Computation", "Computing", "Computed", "Compute", "Compulsive","Technology","Convulated"):
        print(word, "-->", stemmer.stem(word))



import urlextract
urlextractor = urlextract.URLExtract()
#try
print(urlextractor.find_urls("My personal website is talktosharmadhav.netlify.com and I like to surf wikipedia.com and keep my code on www.github.com/pseudocodenerd I just watched this https://www.youtube.com/watch?v=_7QRpuhz-90"))

from sklearn.base import BaseEstimator, TransformerMixin

class dopeTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, strip_headers=True, remove_punctuation=True,
                 replace_urls=True, replace_numbers=True, stemming=True):
        self.strip_headers = strip_headers
        
        self.remove_punctuation = remove_punctuation
        self.replace_urls = replace_urls
        self.replace_numbers = replace_numbers
        self.stemming = stemming
        
    def transform(self, X, y=None):
        X_transformed = []
        for email in X:
            text = emailTOtext(email)
            
            if self.replace_numbers:
                text = re.sub(r'\d+(?:\.\d*(?:[eE]\d+))?', 'NUMBER', str(text))#regexIStough!!
            if self.remove_punctuation:
                text = re.sub(r'\W+', ' ', text, flags=re.M)
            if self.replace_urls and urlextractor is not None:
                urls = list(set(urlextractor.find_urls(text)))
                urls.sort(key=lambda url: len(url), reverse=True)
                for url in urls:
                    text = text.replace(url, " URL ")
            word_counts = Counter(text.split())
            if self.stemming and stemmer is not None:
                stemmed_word_counts = Counter()
                for word, count in word_counts.items():
                    stemmed_word = stemmer.stem(word)
                    stemmed_word_counts[stemmed_word] += count
                word_counts = stemmed_word_counts
            X_transformed.append(word_counts)
        return np.array(X_transformed)  
    
    def fit(self, X, y=None):
        return self

sampleX = X_train[:2]
sampleXwordcount = dopeTransformer().fit_transform(sampleX)
print(sampleXwordcount)

from scipy.sparse import csr_matrix

class dopeVectorTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, vocab_size =1000):
        self.vocab_size = vocab_size
            
    def fit(self, X, y=None):#builds the vocabulary (an ordered list of the most common words)
        countT = Counter()
        for word_count in X:
            for word, count in word_count.items():
                countT[word]+=min(count, 10)
        mostCommon = countT.most_common()[:self.vocab_size]
        self.mostCommon = mostCommon
        self.vocab = {word: index + 1 for index, (word, count) in enumerate(mostCommon)}
        return self
    
    def transform(self, X, y=None):
        R=[]; C=[]; Data=[]
        for r, word_count in enumerate(X):
            for word, count in word_count.items():
                R.append(r)
                C.append(self.vocab.get(word,0))
                Data.append(count)
        return csr_matrix((Data, (R, C)), shape=(len(X), self.vocab_size + 1))

sampleVectorX = dopeVectorTransformer(vocab_size=5)
sampleVectors = sampleVectorX.fit_transform(sampleXwordcount)
print(sampleVectors)
sampleVectors.toarray()
print(sampleVectorX.vocab)

from sklearn.pipeline import Pipeline

pre_processing = Pipeline([("email_to_word_count", dopeTransformer()),
                          ("wordcount_to_vector", dopeVectorTransformer()),
                          ])
X_final = pre_processing.fit_transform(X_train)

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

model = LogisticRegression(random_state=42)
score = cross_val_score(model, X_final, y_train, cv=3, verbose=3)
score.mean()