import os
import re
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import mysql.connector

PAGE_NUMBER_LIMIT = 2
BASE_URL = 'https://www.musinsa.com/ranking/best?period=now&age=ALL&golf=false&kids=false&newProduct=false&exclusive=false&discount=false&soldOut=false&page=1&viewType=small&mainCategory=001&subCategory='
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
IMAGE_DIR = 'images'

with open('config.json') as config_file:
    config_data = json.load(config_file)

DB_CONFIG = {
    'host': config_data['database']['host'],
    'port': config_data['database']['port'],
    'user': config_data['database']['user'],
    'password': config_data['database']['password'],
    'database': config_data['database']['database']
}

def map_subcategory_to_category(sub_category):
    category_mapping = {
        '001001': 'short_sleeve_top',
        '001006': 'long_sleeve_top',
        '001004': 'long_sleeve_top',
        '001010': 'long_sleeve_top',
        '001005': 'long_sleeve_top',
        '001002': 'long_sleeve_top',
        '002021': 'vest',
        '001011' : 'sling',
        '002022': 'long_sleeve_outwear',
        '002001': 'long_sleeve_outwear',
        '002002': 'long_sleeve_outwear',
        '002025': 'long_sleeve_outwear',
        '002017': 'long_sleeve_outwear',
        '002003': 'long_sleeve_outwear',
        '002020': 'long_sleeve_outwear',
        '002019': 'long_sleeve_outwear',
        '002023': 'long_sleeve_outwear',
        '002018': 'long_sleeve_outwear',
        '002004': 'long_sleeve_outwear',
        '002008': 'long_sleeve_outwear',
        '002007': 'long_sleeve_outwear',
        '002024': 'long_sleeve_outwear',
        '002009': 'long_sleeve_outwear',
        '002013': 'long_sleeve_outwear',
        '002012': 'long_sleeve_outwear',
        '002014': 'long_sleeve_outwear',
        '002006': 'long_sleeve_outwear',
        '003009': 'shorts',
        '003002': 'trousers',
        '003007': 'trousers',
        '003008': 'trousers',
        '003004': 'trousers',
        '003011': 'trousers',
        '022001': 'skirt',
        '022002': 'skirt',
        '022003': 'skirt',
        '020006': 'short_sleeve_dress',
        '020007': 'short_sleeve_dress',
        '020008': 'short_sleeve_dress'

    }
    return category_mapping.get(sub_category, 'other')

def map_subcategory_to_main_category(sub_category):
    main_category_mapping = {
        '001001': '001', # short_sleeve_top
        '001006': '001', # long_sleeve_top
        '001004': '001',
        '001010': '001',
        '001005': '001',
        '001002': '001',
        '002021': '002', # vest
        '001011': '001', # sling
        '002022': '002', # long sleeve outwear
        '002001': '002',
        '002002': '002',
        '002025': '002',
        '002017': '002',
        '002003': '002',
        '002020': '002',
        '002019': '002',
        '002023': '002',
        '002018': '002',
        '002004': '002',
        '002008': '002',
        '002007': '002',
        '002024': '002',
        '002009': '002',
        '002013': '002',
        '002012': '002',
        '002014': '002',
        '002006': '002',
        '003009': '003', # shors
        '003002': '003', # troussers
        '003007': '003',
        '003008': '003',
        '003004': '003',
        '003011': '003',
        '022001': '022', # skirt
        '022002': '022',
        '022003': '022',
        '020006': '022', # short_sleeve_dress
        '020007': '022',
        '020008': '022'
    }
    return main_category_mapping.get(sub_category, 'other')

def get_product_info(product, sub_category):
    product_url_element = product.find('div', class_='list_img')
    product_url = product_url_element.find('a')['href']

    product_name_element = product.find('p', class_='list_info')
    strong_tag = product_name_element.find('strong', class_='txt_reserve')
    if strong_tag:
        strong_tag.extract()
    product_name = re.sub(r'[\/:*?"<>|]', '', product_name_element.text.strip())

    price_element = product.find('p', class_='price')
    discount_price_element = price_element.find('del') if price_element else None
    discount_price = discount_price_element.text.strip() if discount_price_element else ''      # 할인 전 가격
    

    del_tag = price_element.find('del')
    if del_tag:
        del_tag.extract()

    price = price_element.text.strip()

    brand_element = product.find('p', class_='item_title')
    brand = brand_element.text.strip()

    category = map_subcategory_to_category(sub_category)
    main_category = map_subcategory_to_main_category(sub_category)

    product_info = {
        'product_url': product_url,
        'brand': brand,
        'name': product_name,
        'price': price,
        'discount_price': discount_price,
        'sub_category': sub_category,
        'category': category,
        'main_category': main_category,
    }

    return product_info

def download_and_save_image(product_info):
    product_url = product_info['product_url']

    pattern = re.compile(r'/goods/(\d+)')
    match = re.search(pattern, product_url)
    code = match.group(1) if match else None

    headers = {'User-Agent': USER_AGENT}

    product_response = requests.get(product_url, headers=headers)
    product_soup = BeautifulSoup(product_response.text, 'html.parser')

    product_image = product_soup.find('img', class_='plus_cursor')
    product_image_url = urljoin(product_url, product_image['src'])

    category_folder = os.path.join(IMAGE_DIR, product_info['category'])
    os.makedirs(category_folder, exist_ok=True)

    image_data = requests.get(product_image_url).content
    image_filename = os.path.join(category_folder, f'{code}.jpg')
    with open(image_filename, 'wb') as image_file:
        image_file.write(image_data)

    product_info['image_url'] = product_image_url
    product_info['image_path'] = image_filename
    product_info['code'] = code
    #print(product_info)

def insert_data_to_database(product_list):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("===start insert===")
    data = [(product_info['image_url'],
             product_info['product_url'],
             product_info['brand'],
             product_info['name'],
             product_info['price'],
             product_info['discount_price'],
             product_info['category'],
             product_info['sub_category'],
             product_info['code'],
             product_info['image_path']             
             )
            for product_info in product_list]
    #print(data)
    cursor.executemany("""
        INSERT INTO product
        (
            image_url,
            info_url,
            brand,
            name,
            price,
            original_price,          
            category,
            sub_category,
            code,
            image_path
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data)

    conn.commit()
    cursor.close()
    conn.close()

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sub_categories = [
                    # '001001', # short_sleeve_top
                    # '001006', '001004', '001010', '001005', '001002', # long_sleeve_top
                    # '002021', # vest
                    # '001011', # sling
                    # '002022','002001','002002','002025','002017','002003','002020','002019','002023','002018','002004','002008','002007','002024','002009','002013','002012','002014','002006' # long_sleeve_outwear
                    '003009' # shorts
                    # '003002','003007','003008','003004','003011', # trousers
                    # '022001','022002','022003', # skirt
                    # '020006','020007','020008' # short_sleeve_dress
                    ]

    for sub_category in sub_categories:
        page_number = 1
        product_list = []

        while page_number < PAGE_NUMBER_LIMIT:
            url = f'{BASE_URL}{sub_category}&page={page_number}'
            

            main_category = map_subcategory_to_main_category(sub_category)
            url = url.replace('mainCategory=001', f'mainCategory={main_category}')
            print(url)
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.find_all('li', class_='li_box')

            for product in products:
                product_info = get_product_info(product, sub_category)
                product_list.append(product_info)

            page_number += 1

        for product_info in product_list:
            download_and_save_image(product_info)

        insert_data_to_database(product_list)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
