import requests
import bs4
import os
import re
import unicodedata
import pandas as pd
import nltk
import numpy as np



def get_urls():
    
    url = ('https://www.newegg.com/p/pl?N=100007709%20601361654%20601359415')
    response = requests.get(url)
    html = response.text
    soup = bs4.BeautifulSoup(html, features="lxml")
    
    regex = r'\/(\d+)'
    subject = soup.find('span', {'class': 'list-tool-pagination-text'}).text

    num_pages = int(re.findall(regex, subject)[0])
    
    urls = [('https://www.newegg.com/p/pl?N=100007709%20601361654%20601359415&page=' + str(x)) for x in list(range(1,num_pages+1))]
    
    return urls

urls = get_urls()

def get_newegg_gpu(urls):
    
    rows = []

    for url in urls:

        response = requests.get(url)
        html = response.text
        soup = bs4.BeautifulSoup(html, features="lxml")

        items = soup.find_all('div', {'class': 'item-cell'})

        for item in items:

            item_title = item.find('a', {'class':'item-title'}).text

            old_price = item.find('li', {'class': 'price-was'}).text

            if old_price == '':
                old_price = '0'
            else:
                old_price = old_price

            current_price = item.find('li', {'class': 'price-current'}).text

            if current_price == '':
                current_price = '0'
            else:
                current_price = current_price
            
            in_stock = item.find('p', {'class': 'item-promo'})
            
            if in_stock is None:
                in_stock = 'available'
            elif in_stock.text == 'OUT OF STOCK':
                in_stock = 'out of stock'
            else:
                in_stock = "sale?"

            row = []
            row.append(item_title)
            row.append(old_price)
            row.append(current_price)
            row.append(in_stock)
            rows.append(row)

        df = pd.DataFrame(columns=['item_title', 'old_price', 'current_price', 'in_stock'], data = rows)
        
    return df


def clean_gpu_data(df):
    df.old_price = df.old_price.str.replace('$', '').str.replace(',', '')
    df['current_price'] = df.current_price.str.split(pat='\xa0', expand=True)
    df.current_price = df.current_price.str.replace('$', '').str.replace(',', '')
    df.current_price = df.current_price.astype(float, errors = 'ignore')
    return df


def check_availibility():
    
    df = clean_gpu_data(get_newegg_gpu(urls))
    
    df = df[df.in_stock == 'available'].sort_values('current_price')
    
    return df