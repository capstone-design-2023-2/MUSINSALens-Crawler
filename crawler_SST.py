import requests
from bs4 import BeautifulSoup
import os
import re
import pandas as pd
from urllib.parse import urljoin

page_number = 1

# 상품 정보를 담을 리스트 생성
product_list = []

# 이미지를 저장할 디렉토리 생성
image_dir = 'short_sleeve_top_product_images'
os.makedirs(image_dir, exist_ok=True)

while page_number < 11:
    
    # 웹페이지의 URL 설정
    url = f'https://www.musinsa.com/ranking/best?period=now&age=ALL&mainCategory=001&subCategory=001001&leafCategory=&price=&golf=false&kids=false&newProduct=false&exclusive=false&discount=false&soldOut=false&page={page_number}&viewType=small&priceMin=&priceMax='

    # 해당 URL로 요청을 보내서 HTML을 가져옴
    response = requests.get(url)
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(response.text, 'html.parser')

    # 원하는 요소를 찾아서 크롤링
    products = soup.find_all('li', class_='li_box')
    for product in products:
        # 이미지 URL 가져오기
        # image_url = product.find('img')['data-original']
    
        # 제품 URL 가져오기
        product_url_element = product.find('div',class_='list_img')
        product_url = product_url_element.find('a')['href']

        # 제품명 가져오기
        product_name_element = product.find('p', class_='list_info')

        # <strong> 태그 제외
        strong_tag = product_name_element.find('strong', class_='txt_reserve')
        if strong_tag:
            strong_tag.extract()
        
        product_name = product_name_element.text.strip()

        # 가격 가져오기
        price_element = product.find('p', class_='price')
    
        # <del> 태그 내의 가격 가져오기
        discount_price_element = price_element.find('del') if price_element else None
        discount_price = discount_price_element.text.strip() if discount_price_element else ''
    
        # <del> 태그 제거
        del_tag = price_element.find('del')
        if del_tag:
            del_tag.extract()
    
        price = price_element.text.strip()
    
        # 브랜드명 가져오기
        brand_element = product.find('p', class_='item_title')

        brand = brand_element.text.strip()

        # 상품 이름에서 사용할 수 없는 문자 제거
        product_name = re.sub(r'[\/:*?"<>|]', '', product_name)

        # 상품 정보를 딕셔너리로 저장
        product_info = {
            # '이미지 URL': image_url,
            '제품 URL' : product_url,
            '브랜드명' : brand,
            '제품명': product_name,
            '가격': price,
            '할인되기 전 가격': discount_price
        }

        product_list.append(product_info)
    page_number += 1
    
# 이미지 다운로드 및 정보 저장
for idx, product_info in enumerate(product_list):
    
    product_url = product_info['제품 URL']
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    product_response = requests.get(product_url, headers=headers)
    product_soup = BeautifulSoup(product_response.text, 'html.parser')
    
    #카테고리
    item_categorie_big = 'top'
    item_categorie_small = 'short_sleeve_top'
    
    #좋아요 갯수
    #like_count_element = product_soup.find('span', class_='prd_like_cnt')
    #like_count = like_count_element.find('span', {'name': 'count'}).text.strip() if like_count_element else ''
    
    #리뷰 갯수
    #review_count_element = product_soup.find('span', class_='prd-score__review-count')
    #review_count = review_count_element.find('span', {'name': 'count'}).text.strip() if like_count_element else ''
    
    
    product_image = product_soup.find('img', class_='plus_cursor')
    product_image_url = urljoin(product_url, product_image['src'])
            
    image_data = requests.get(product_image_url).content
    image_filename = os.path.join(image_dir, f'{product_info["제품명"]}.jpg')
    with open(image_filename, 'wb') as image_file:
        image_file.write(image_data)
    
    product_info['이미지 URL'] = product_image_url
    product_info['이미지 저장 경로'] = image_filename
    product_info['카테고리(대)'] = item_categorie_big
    product_info['카테고리(중)'] = item_categorie_small
    #product_info['좋아요 갯수'] = like_count
    #product_info['리뷰 갯수'] = review_count

# 데이터프레임 생성
df = pd.DataFrame(product_list)

# 엑셀 파일로 저장
excel_filename = 'short_sleeve_top_product_info.xlsx'
df.to_excel(excel_filename, index=False)

# 결과 출력
print(f'Data saved to {excel_filename}')

