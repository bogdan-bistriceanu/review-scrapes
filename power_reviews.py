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
marketplace_name = 'ulta.com'


scrape_params = {
	'morphe': {
        'scrape_ids': ['pimprod2022516','VP12690']
	},
    'test': {
        'scrape_ids': ['1']
	}
}

def get_clean_text(text):
    re_1 = "\.{1,}" #match multiple periods in a row
    re_2 = "\'" #match apostrophes
    re_3 = "\%" #match percent % characters
    re_4 = "[^a-zA-Z0-9\s\#]" #match all non alphanumeric, space, pound #
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
    if review.get('metrics').get('rating'):
        append_data('review_rating', review.get('metrics').get('rating'))
    else:
        append_data('review_rating','')
        
    #we check if the title exists, and if it does we retrieve the value
    if review.get('details').get('headline'):
        append_data('review_title', review.get('details').get('headline'))
    else:
        append_data('review_title','')
    
    #we check if the review text exists, and if it does we retrieve the value
    if review.get('details').get('comments'):
        append_data('review_text', review.get('details').get('comments').encode('UTF-8').decode('UTF-8'))
    else:
        append_data('review_text','')
        
    #we check if the review text exists, and if it does we retrieve the value, clean it, and lemmatize it
    if review.get('details').get('comments'):
        append_data('clean_review_text', get_lemmatized_text(review.get('details').get('comments').encode('UTF-8').decode('UTF-8')))
    else:
        append_data('clean_review_text','')
    
    #we check if the review date text exists, and if it does we retrieve the value
    if review.get('details').get('created_date'):
        append_data('review_time', review.get('details').get('created_date'))
    else:
        append_data('review_time','')

    #we check if the review text exists, and if it does we calculate the length
    if review.get('details').get('created_date'):
        append_data('review_length', len(review.get('details').get('comments').encode('UTF-8').decode('UTF-8')))
    else:
        append_data('review_length','')        

    #we check if feedback positive exists, and if it does we retrieve the value
    if review.get('metrics').get('helpful_votes'):
        append_data('feedback_positive', review.get('metrics').get('helpful_votes'))
    else:
        append_data('feedback_positive','')
   
    #we check if feedback negative exists, and if it does we retrieve the value
    if review.get('metrics').get('not_helpful_votes'):
        append_data('feedback_negative', review.get('metrics').get('helpful_votes'))
    else:
        append_data('feedback_negative','')           

    #we check if author nickname exists, and if it does we retrieve the value
    if review.get('details').get('nickname'):
        append_data('author_nickname', review.get('details').get('nickname'))
    else:
        append_data('author_nickname','')                
               
    #we check if staff reviewer status exists, and if it does we retrieve the value
    if review.get('badges').get('is_staff_reviewer'):
        append_data('is_staff_reviewer', review.get('badges').get('is_staff_reviewer'))
    else:
        append_data('is_staff_reviewer','')           

    #we check if verified buyer status exists, and if it does we retrieve the value
    if review.get('badges').get('is_verified_buyer'):
        append_data('is_verified_buyer', review.get('badges').get('is_verified_buyer'))
    else:
        append_data('is_verified_buyer','')
        
    #we check if author nickname exists, and if it does we retrieve the value
    if review.get('badges').get('is_verified_reviewer'):
        append_data('is_verified_reviewer', review.get('badges').get('is_verified_reviewer'))
    else:
        append_data('is_verified_reviewer','')

    #we check if would recommend exists, and if it does we retrieve the value
    if review.get('details').get('bottom_line'):
        append_data('would_recommend', review.get('details').get('bottom_line'))
    else:
        append_data('would_recommend','')
    
    #we check if location exists, and if it does we retrieve the value
    if review.get('details').get('location'):
        append_data('author_location', review.get('details').get('location'))
    else:
        append_data('author_location','')                           

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
    	'author_nickname': ["Ignore"],
        'is_staff_reviewer': ["Ignore"],
        'is_verified_buyer': ["Ignore"],
        'is_verified_reviewer': ["Ignore"],
        'would_recommend': ["Ignore"],
        'author_location': ["Ignore"]
    }
    return data 

aggregate_csv = dataset()

for brand in scrape_params:
    
    brand_csv = dataset()
    
    scrape_brand = brand
    
    if scrape_params.get(brand).get('scrape_ids'):
        scrape_ids = scrape_params.get(brand).get('scrape_ids')
    
    for scrape_id in scrape_ids:
        
        if len(scrape_id) > 0:
            
            product_csv = dataset()
            
            scrape_url = 'https://display.powerreviews.com/m/6406/l/en_US/product/' + scrape_id + '/reviews'
            url_params = {
                'apikey':'daa0f241-c242-4483-afb7-4449942d1a2b',
                'paging.from': 0,
                'paging.size': 25
            }
            
            inital_api_call = requests.get(scrape_url, url_params)
            inital_api_call_data=inital_api_call.json()
            
            #print(inital_api_call.url)
            #print(inital_api_call_data)
            
            total_reviews = inital_api_call_data.get('paging').get('total_results')
            print(f"Total available reviews: {total_reviews}")
            
            if total_reviews < 25:
                scraping_iterations = 1
            else:
                scraping_iterations = divmod(total_reviews, 25)[0] + 1
            print(f"Total scraping iterations: {scraping_iterations}")
            
            current_iteration = 0
            current_offset = 0
            current_id = 0
            
            while current_iteration < scraping_iterations:
                
                scrape_iteration = requests.get(scrape_url, url_params)
                scrape_iteration_data = scrape_iteration.json()
                
                print(scrape_iteration.url)
                #print(scrape_iteration.data)        
                
                scrape_review_data = scrape_iteration_data.get('results')[0].get('reviews')
                
                #print(scrape_review_data)
                
                #we iterate over the current batch of reviews
                for review in scrape_review_data:
                    
                    #we call our processing function to retrieve and store data
                    process_review(review,current_id)
                    
                    #we iterate our review id counter
                    current_id += 1
            
                current_iteration += 1
                current_offset += 25
                url_params['paging.from'] = current_offset


            if product_csv_enabled:
                create_csv(brand + '_' + scrape_id, product_csv)

    if brand_csv_enabled:
        create_csv(brand, brand_csv)      

if aggregate_csv_enabled:
    create_csv(marketplace_name, aggregate_csv)