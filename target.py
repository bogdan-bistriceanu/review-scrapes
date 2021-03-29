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

#set to True if you want a csv generated at the aggregate/multibrand level
aggregate_csv_enabled = True

#set to True if you want a csv generate at the brand level
brand_csv_enabled = True

#set to True if you want a csv generate at the product level
product_csv_enabled = True

#where we are pulling the data from
marketplace_name = 'target.com'

scrape_params = {
	'honest_kids_juice': {
        'scrape_ids': ['13783652']
	}
}

def dataset():
    data = {
    	'ace_review_id': ["ReviewID"],
    	'review_rating': ["Numeric"],
    	'review_title': ["Review"],
    	'review_text': ["Review"],
    	'clean_review_text': ["Ignore"],
    	'review_time': ["Date"],
    	'review_length': ["Numeric"],
    	'feedback_positive': ["Numeric"],
    	'feedback_negative': ["Numeric"],
    	'product_brand': ["Ignore"],
    	'product_scrape_id': ["Ignore"],
    	'author_nickname': ["Ignore"]
    }
    return data

def get_clean_text(text):
    re_1 = "\.{1,}" #match multiple periods in a row
    re_2 = "(\’|\')" #match apostrophes
    re_3 = "\%" #match percent % characters
    re_4 = "[^a-zA-Z0-9\s\#\’\']" #match all non alphanumeric, space, pound #
    re_5 = "\s{2,}" #match multiple spaces in a row
    
    review_text = text.lower()
    review_text = re.sub(re_1, " ", review_text)
    review_text = re.sub(re_2, "", review_text)
    review_text = re.sub(re_3, " percent", review_text)
    review_text = re.sub(re_4, " ", review_text)
    review_text = re.sub(re_5, " ", review_text)
    
    return review_text

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)

def get_lemmatized_text(text):
    lemmatizer = WordNetLemmatizer() 
  
    review_text = get_clean_text(text)
    review_text_tokens = nltk.word_tokenize(review_text)

    clean_output = ' '.join([lemmatizer.lemmatize(w, get_wordnet_pos(w)) for w in review_text_tokens])
    
    return clean_output

def validate_csv(data):
    is_valid = True
    
    for item in data:
        if len(data[item]) == 1:
            is_valid = False

    return is_valid

def create_csv(filename, data):
    file_name = filename + '_review_data_' + datetime.today().strftime('%Y_%m_%d') + '.csv'
    data_frame = pandas.DataFrame(data)
    if validate_csv(data):
        data_frame.to_csv(file_name.lower(), encoding='utf-8-sig', index=False)
        print(f"Finished writing {file_name}")

def append_data(key, value):
    aggregate_csv[key].append(value)
    brand_csv[key].append(value)
    product_csv[key].append(value)

def process_review(review, current_id):
    #we store some information which will describe our rows
    append_data('ace_review_id', str(current_id)+'_'+str(scrape_brand)+'_'+str(scrape_id))
    append_data('product_brand', scrape_brand)
    append_data('product_scrape_id', scrape_id)
    
    #we check if the rating exists, and if it does we retrieve the value
    if review.get('Rating'):
        append_data('review_rating', review.get('Rating'))
    else:
        append_data('review_rating','')
        
    #we check if the title exists, and if it does we retrieve the value
    if review.get('title'):
        append_data('review_title', review.get('title').encode('UTF-8').decode('UTF-8'))
    else:
        append_data('review_title','')
    
    #we check if the review text exists, and if it does we retrieve the value
    if review.get('text'):
        append_data('review_text', review.get('text').encode('UTF-8').decode('UTF-8'))
    else:
        append_data('review_text','')
        
    #we check if the review text exists, and if it does we retrieve the value, clean it, and lemmatize it
    if review.get('text'):
        append_data('clean_review_text', get_lemmatized_text(review.get('text').encode('UTF-8').decode('UTF-8')))
    else:
        append_data('clean_review_text','')
    
    #we check if the review date text exists, and if it does we retrieve the value
    if review.get('submitted_at'):
        append_data('review_time', review.get('submitted_at'))
    else:
        append_data('review_time','')

    #we check if the review text exists, and if it does we calculate the length
    if review.get('text'):
        append_data('review_length', len(review.get('text').encode('UTF-8').decode('UTF-8')))
    else:
        append_data('review_length','')        

    #we check if feedback positive exists, and if it does we retrieve the value
    if review.get('feedback').get('helpful'):
        append_data('feedback_positive', review.get('feedback').get('helpful'))
    else:
        append_data('feedback_positive','0')
   
    #we check if feedback negative exists, and if it does we retrieve the value
    if review.get('feedback').get('unhelpful'):
        append_data('feedback_negative', review.get('feedback').get('unhelpful'))
    else:
        append_data('feedback_negative','0')           

    #we check if author nickname exists, and if it does we retrieve the value
    if review.get('author').get('nickname'):
        append_data('author_nickname', review.get('author').get('nickname'))
    else:
        append_data('author_nickname','')

aggregate_csv = dataset()

for brand in scrape_params:
    
    brand_csv = dataset()
    
    scrape_brand = brand
    
    if scrape_params.get(brand).get('scrape_ids'):
        scrape_ids = scrape_params.get(brand).get('scrape_ids')
    
    for scrape_id in scrape_ids:
        
        if len(scrape_id) > 0:
            
            product_csv = dataset()
            
            scrape_url = 'https://r2d2.target.com/ggc/reviews/v1/reviews'
            url_params = {
                'reviewType': 'PRODUCT',
                'key': 'c6b68aaef0eac4df4931aae70500b7056531cb37',
                'reviewedId': scrape_id,
                'sortBy': 'most_recent',
                'page': '0',
                'size': '100',
                'hasOnlyPhotos': 'false',
                'ratingFilter': '',
                'verifiedOnly': 'false'
            }
            
            inital_api_call = requests.get(scrape_url, url_params)
            inital_api_call_data=inital_api_call.json()
            
            print(inital_api_call.url)
            print(inital_api_call_data)
            
            total_reviews = inital_api_call_data.get('total_results')
            print(f"Total available reviews: {total_reviews}")
            
            if total_reviews < 100:
                scraping_iterations = 1
            else:
                scraping_iterations = divmod(total_reviews, 100)[0] + 1
            print(f"Total scraping iterations: {scraping_iterations}")
            
            current_iteration = 0
            current_page = 0
            current_id = 0
            
            while current_iteration < scraping_iterations:
                
                scrape_iteration = requests.get(scrape_url, url_params)
                scrape_iteration_data = scrape_iteration.json()
                
                print(scrape_iteration.url)
                #print(scrape_iteration.data)        
                
                scrape_review_data = scrape_iteration_data.get('results')
                
                #print(scrape_review_data)
                
                #we iterate over the current batch of reviews
                for review in scrape_review_data:
                    
                    #we call our processing function to retrieve and store data
                    process_review(review,current_id)
                    
                    #we iterate our review id counter
                    current_id += 1
            
                current_iteration += 1
                current_page += 1
                url_params['page'] = current_page


            if product_csv_enabled:
                create_csv(brand + '_' + scrape_id, product_csv)

    if brand_csv_enabled:
        create_csv(brand, brand_csv)      

if aggregate_csv_enabled:
    create_csv(marketplace_name, aggregate_csv)