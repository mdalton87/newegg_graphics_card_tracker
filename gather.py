import requests
import bs4
import os
import re
import unicodedata
import pandas as pd
import nltk
import numpy as np


################################################################################################################

# NEWEGG Functions

################################################################################################################




def get_urls_newegg():
    
    url = ('https://www.newegg.com/p/pl?N=100007709%20601361654%20601359415')
    response = requests.get(url)
    html = response.text
    soup = bs4.BeautifulSoup(html, features="lxml")
    
    regex = r'\/(\d+)'
    subject = soup.find('span', {'class': 'list-tool-pagination-text'}).text

    num_pages = int(re.findall(regex, subject)[0])
    
    urls = [('https://www.newegg.com/p/pl?N=100007709%20601361654%20601359415&page=' + str(x)) for x in list(range(1,num_pages+1))]
    
    return urls

urls = get_urls_newegg()

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


def clean_gpu_data_newegg(df):
    df.old_price = df.old_price.str.replace('$', '').str.replace(',', '')
    df['current_price'] = df.current_price.str.split(pat='\xa0', expand=True)
    df.current_price = df.current_price.str.replace('$', '').str.replace(',', '')
    df.current_price = df.current_price.astype(float, errors = 'ignore')
    return df


def check_availibility_newwegg():
    
    df = clean_gpu_data_newegg(get_newegg_gpu(urls))
    
    df = df[df.in_stock == 'available'].sort_values('current_price')
    
    return df




################################################################################################################

# EBAY Functions

################################################################################################################


def get_urls_ebay():
    
    url = 'https://www.ebay.com/sch/i.html?_from=R40&_nkw=rtx+3060&_sacat=175673&rt=nc&Chipset%252FGPU%2520Model=NVIDIA%2520GeForce%2520RTX%25203060%2520Ti%7CNVIDIA%2520GeForce%2520RTX%25203060&_dcat=27386&_ipg=200'
    response = requests.get(url)
    html = response.text
    soup = bs4.BeautifulSoup(html)
    
    regex = r'(\d*\,\d+)'
    subject = soup.find('h1', {'class': 'srp-controls__count-heading'}).text

    string = ''
    for x in re.findall(regex, subject)[0]:
        if str.isdigit(x) == True:
            string = string + x  
            
    num_pages_ebay = int(string) // 200 + 1
    
    urls = [('https://www.ebay.com/sch/i.html?_from=R40&_nkw=rtx+3060&_sacat=175673&rt=nc&Chipset%252FGPU%2520Model=NVIDIA%2520GeForce%2520RTX%25203060%2520Ti%7CNVIDIA%2520GeForce%2520RTX%25203060&_dcat=27386&_ipg=200&_pgn=' + str(x)) for x in list(range(1, num_pages_ebay(url)+1))]
    
    return urls


    
def get_gpu_ebay(urls):
    
    rows = []
    
    for url in urls:

        response = requests.get(url)
        html = response.text
        soup = bs4.BeautifulSoup(html, features="lxml")

        items = soup.find_all('div', {'class': 's-item__info clearfix'})

        for item in items:

            title = item.find('h3', {'class': "s-item__title"}).text
            condition = item.find('span', {'class': 'SECONDARY_INFO'})
            current_price = item.find('span', {'class': 's-item__price'})
            total_bids = item.find('span', {'class': 's-item__bids s-item__bidCount'})
            bidding_time_left = item.find('span', {'class': 's-item__time-left',})
            shipping_cost = item.find('span', {'class': 's-item__shipping s-item__logisticsCost'})

            if condition is None:
                condition = np.nan
            else:
                condition = condition.text

            if current_price is None:
                current_price = np.nan
            else:
                current_price = current_price.text

            if total_bids is None:
                total_bids = np.nan
            else:
                total_bids = total_bids.text

            if bidding_time_left is None:
                bidding_time_left = np.nan
            else:
                bidding_time_left = bidding_time_left.text

            if shipping_cost is None:
                shipping_cost = np.nan
            else:
                shipping_cost = shipping_cost.text

            link = ''
            for x in item.find_all('a', {'_sp': 'p2351460.m1686.l7400'}):
                if x.has_attr('href'):
                    link = x.attrs['href']


            row = []
            row.append(title)
            row.append(condition)
            row.append(current_price)
            row.append(total_bids)
            row.append(bidding_time_left)
            row.append(shipping_cost)
            row.append(link)
            rows.append(row)

        df = pd.DataFrame(columns=['title', 'condition', 'current_price', 'total_bids', 'bidding_time_left', 'shipping_cost', 'url'], data = rows)

    return df


def clean_ebay_gpu(df):
    df = df.drop(index=0)
    df.current_price = df.current_price.str.replace('$', '').str.replace(',', '').astype(float)
    df.shipping_cost = df.shipping_cost.str.replace('+', '').str.replace('$', '').str.replace(' shipping', '').str.replace('Free', '0').astype(float)
    df.title = df.title.str.replace('New Listing', '').str.replace('IN HAND', '').str.replace('✔️', '').str.replace(' \*2 DAY SHIP\* ','')
    df.sort_values('current_price').reset_index()