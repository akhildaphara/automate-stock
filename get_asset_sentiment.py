# -*- coding: utf-8 -*-
"""get_asset_sentiment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/akhildaphara/automate-stock/blob/main/get_asset_sentiment.ipynb

1. Dependencies
"""

from transformers import PegasusTokenizer, PegasusForConditionalGeneration
from bs4 import BeautifulSoup
import requests

"""2. Initiate the model"""

model_name = "human-centered-summarization/financial-summarization-pegasus"
tokenizer = PegasusTokenizer.from_pretrained(model_name)
model = PegasusForConditionalGeneration.from_pretrained(model_name)

"""3. Define Tickers

"""

monitored_tickers = ['TSLA', "DOGE", "AAPL"]

"""4. Search for stock news using Google and Yahoo"""

def search_for_stock_news_url(ticker):
  search_url = "https://www.google.com/search?q=yahoo+finance+{}&tbm=nws".format(ticker)
  r= requests.get(search_url)
  soup = BeautifulSoup(r.text, "html.parser")
  atags = soup.findAll('a')
  hrefs = [link['href'] for link in atags]
  return hrefs

print('Searching for stock news for: ', monitored_tickers)  
raw_url = {ticker:search_for_stock_news_url(ticker) for ticker in monitored_tickers}

"""5. Clean raw urls"""

import re

exclude_list = ["google.com/"]
def strip_unwanted_urls(urls, exclude_list):
  val = []
  for url in urls:
    if "https://" in url and not any(exclude_word in url for exclude_word in exclude_list):
      res = re.findall(r'https?://\S+', url)[0].split('&')[0]
      val.append(res)
  return list(set(val))

print('Cleaning URLs.')  
cleaned_urls = {ticker:strip_unwanted_urls(raw_url[ticker], exclude_list) for ticker in monitored_tickers}

"""6. Get Articles from URLs"""

def scrape_and_process_urls(urls):
  articles = []
  for url in urls:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    paragraphs = soup.findAll('p')
    text = [paragraph.text for paragraph in paragraphs]
    words = " ".join(text).split(" ")[:350]
    article = " ".join(words)
    articles.append(article)
  return articles

print('Scraping news links.')
url_articles = {ticker:scrape_and_process_urls(cleaned_urls[ticker]) for ticker in monitored_tickers}

"""7. Summarize all the articles"""

def summarize_articles(articles):
  summaries = []
  for article in articles:
    input_ids = tokenizer.encode(article, return_tensors="pt", truncation=True)
    output = model.generate(input_ids,max_length=50, num_beams=5, early_stopping=True)
    summary = tokenizer.decode(output[0],skip_special_tokens=True)
    summaries.append(summary)
  return summaries

print("Getting summaries of links.")
url_summaries = {ticker:summarize_articles(url_articles[ticker]) for ticker in monitored_tickers}

"""8. Sentiment Analysis"""

from transformers import pipeline
sentiment = pipeline("sentiment-analysis")

print('Analysing and scoring the summaries.')
scores = {ticker: sentiment(url_summaries[ticker]) for ticker in monitored_tickers}

"""9. Exporting as CSV"""

def create_output_array(tickers, summaries, scores, urls):
  output = []
  for ticker in tickers:
    for i in range(len(summaries[ticker])):
      data = [
              ticker,
              summaries[ticker][i],
              scores[ticker][i]['label'],
              scores[ticker][i]['score'],
              urls[ticker][i]
              ]
      output.append(data)
  return output

print('Exporting results.')
final_output = create_output_array(monitored_tickers, url_summaries, scores, cleaned_urls)
final_output.insert(0,['Ticker', 'Summary', 'Label','Score','Url'])

import csv
with open('assetSummaries.csv', mode='w',newline='') as f:
  csv_writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
  csv_writer.writerows(final_output)
print("Data saved as 'assetSummaries.csv' file!")