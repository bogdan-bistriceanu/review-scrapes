import time
import math
import re
import dateutil.parser
import json
import requests
import pandas
import numpy
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime

#set to True if you want a csv generated at the aggregate/multibrand level
marketplace_csv_enabled = True

#set to True if you want a csv generate at the brand level
brand_csv_enabled = True

#set to True if you want a csv generate at the product level
product_csv_enabled = True

scrape_params = {
	'base_url':'https://www.walmart.com/reviews/product/',
	'marketplace':'walmart',
	'scrape_brands':{
		'honest_kids_juice':{
			'scrape_ids': ['438874464','30999596','909530024','118929607']
		},
		'smart_water':{
			'scrape_ids': ['444036544','15580511','708013533']
		},
		'simply':{
			'scrape_ids': ['35042672','35042667','405494243','959033640','775073344']
		}
	}
}
def get_clean_text(text):
    re_0 = "(\t|\n|\r)" #match tabs, newlines, carriage returns
    re_1 = "\.{1,}" #match multiple periods in a row
    re_2 = "(\’|\')" #match apostrophes
    re_3 = "\%" #match percent % characters
    re_4 = "[^a-zA-Z0-9\s\#\’\']" #match all non alphanumeric, space, pound #
    re_5 = "\s{2,}" #match multiple spaces in a row
    
    review_text = text.lower()
    review_text = re.sub(re_0, " ", review_text)
    review_text = re.sub(re_1, " ", review_text)
    review_text = re.sub(re_2, "", review_text)
    review_text = re.sub(re_3, " percent", review_text)
    review_text = re.sub(re_4, " ", review_text)
    review_text = re.sub(re_5, " ", review_text)
    
    return review_text
    
    return review_text

def get_clean_number(number):
    re_1 = "\D"

    clean_number = re.sub(re_1,"",number)

    return clean_number

def get_clean_date(date):
	re_1 = "(\t|\n|\r)"
	re_2 = "Verified purchase"
	clean_date = re.sub(re_1, "", date)
	clean_date = re.sub(re_2, "", date)
	clean_date = clean_date.strip()
	clean_date = datetime.strptime(clean_date, '%B %d, %Y')
	clean_date = clean_date.strftime('%m/%d/%y')
	return clean_date

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

def review_dataset():
	data = {
		'ace_review_id': ["ReviewID"],
		'review_rating': ["Numeric"],
		'review_title': ["Review"],
		'review_text': ["Review"],
		'clean_review_text': ["Ignore"],
		'review_time': ["Date"],
		'review_length': ["Numeric"],
		'feedback_positive': ["Numeric"],
		'product_name': ["Ignore"],
		'product_brand': ["Ignore"],
		'product_scrape_id': ["Ignore"],
		'author_nickname': ["Ignore"],
		'marketplace': ["Ignore"]
	}
	return data

def append_data(key, value):
	product_csv[key].append(value)
	brand_csv[key].append(value)
	marketplace_csv[key].append(value)

def create_csv(filename, data):
	file_path = "C:\\Users\\Bogdan\\Desktop\\APS\\Coke\\walmart\\"
	file_name = filename + '_review_data_' + datetime.today().strftime('%Y_%m_%d') + '.csv'
	data_frame = pandas.DataFrame(data)
	data_frame['review_rating'].replace('', numpy.nan, inplace=True)
	data_frame['clean_review_text'].replace('', numpy.nan, inplace=True)
	data_frame.dropna(subset=['review_rating'], inplace=True)
	data_frame.dropna(subset=['clean_review_text'], inplace=True)
	data_frame.drop_duplicates(subset=['clean_review_text'], inplace=True)
	data_frame.to_csv(file_path+file_name.lower(), encoding='utf-8-sig', index=False)
	print(f"Finished writing {file_name}")

def process_review(review):
	append_data('ace_review_id', 'review_' + str(review_number))

	try:
		append_data('review_rating',review.find_element(By.CSS_SELECTOR, "div.review-heading span.average-rating span.seo-avg-rating").get_attribute("innerText").split('.')[0])
	except NoSuchElementException:
		append_data('review_rating', '')

	try:
		append_data('review_title',review.find_element(By.CSS_SELECTOR, "h3.review-title").get_attribute("innerText").strip().encode('UTF-8').decode('UTF-8'))
	except NoSuchElementException:
		append_data('review_title','')

	try:
		append_data('review_text',get_clean_text(review.find_element(By.CSS_SELECTOR, "div.review-text").get_attribute("innerText").strip().encode('UTF-8').decode('UTF-8')))
	except NoSuchElementException:
		append_data('review_text','')

	try:
		append_data('clean_review_text', get_lemmatized_text(review.find_element(By.CSS_SELECTOR, "div.review-text").get_attribute("innerText").strip().encode('UTF-8').decode('UTF-8')))
	except NoSuchElementException:
		append_data('clean_review_text','')

	try:
		append_data('review_time',get_clean_date(review.find_element(By.CSS_SELECTOR, "div.review-date").get_attribute("innerText").strip()))
	except NoSuchElementException:
		append_data('review_time','')

	try:
		append_data('review_length', len(get_lemmatized_text(review.find_element(By.CSS_SELECTOR, "div.review-text").get_attribute("innerText").strip().encode('UTF-8').decode('UTF-8'))))
	except NoSuchElementException:
		append_data('review_length','')

	try:
		append_data('author_nickname', review.find_element(By.CSS_SELECTOR, "span.review-footer-userNickname").get_attribute("innerText").strip())
	except NoSuchElementException:
		append_data('author_nickname','')

	try:
		append_data('feedback_positive', review.find_element(By.CSS_SELECTOR, "div.ReviewHelpfulness button.yes-vote span.yes-no-count").get_attribute("innerText").strip())
	except NoSuchElementException:
		append_data('feedback_positive', 0)

	append_data('product_name', product_name)
	append_data('product_brand', product_brand)
	append_data('product_scrape_id', scrape_id)
	append_data('marketplace', scrape_params['marketplace'])

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_driver = webdriver.Chrome(options=chrome_options)

marketplace_csv = review_dataset()

for brand in scrape_params['scrape_brands']:

	brand_csv = review_dataset()

	scrape_brand = brand

	if scrape_params['scrape_brands'].get(brand).get('scrape_ids'):
		scrape_ids = scrape_params['scrape_brands'].get(brand).get('scrape_ids')

	for scrape_id in scrape_ids:

		product_csv = review_dataset()

		chrome_driver.get(scrape_params['base_url'] + scrape_id);

		total_reviews = chrome_driver.execute_script("return __WML_REDUX_INITIAL_STATE__.reviews[__WML_REDUX_INITIAL_STATE__.product.selected.product].totalReviewCount")
		print(f"Total reviews: {total_reviews}")

		total_review_pages = math.ceil(total_reviews / 20)
		print(f"Total review pages: {total_review_pages}")

		product_name = chrome_driver.find_element(By.CSS_SELECTOR, "h2.prod-ProductTitle").get_attribute("innerText").strip()
		product_brand = brand

		page_number = 1
		review_number = 1

		while page_number <= total_review_pages:
			scrape_url = scrape_params['base_url'] + scrape_id + '/?page=' + str(page_number)
			print(f"Processing: {scrape_url}")
			chrome_driver.get(scrape_url);
			review_list = chrome_driver.find_elements(By.CSS_SELECTOR, "div.customer-review-body")
			for review in review_list:
				process_review(review)
				review_number += 1
			page_number += 1
		
		if product_csv_enabled:
			create_csv(scrape_params['marketplace'] + '_' + brand + '_' + scrape_id, product_csv)
	if brand_csv_enabled:
		create_csv(scrape_params['marketplace'] + '_' + brand, brand_csv)
if marketplace_csv_enabled:
	create_csv(scrape_params['marketplace'], marketplace_csv)

chrome_driver.quit()