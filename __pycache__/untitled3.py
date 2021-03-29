import re
import time
from datetime import datetime
import dateutil.parser
import json
import requests
import pandas
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from collections import Counter

reviews_list = ['My cracked phone that the is cracked the','I am assuming cracked cracked that the ask']
review_list_joined = [output_word for review_text in reviews_list for output_word in review_text.split(' ')]
review_list_counts = Counter(review_list_joined)

z = review_list_counts.items()
z = sorted(z, key=lambda z: z[1], reverse=True)


for key in z:
    print(key[0],':',key[1])