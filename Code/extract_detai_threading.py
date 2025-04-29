import csv
import datetime
import logging
import os
import re
import threading
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent

ua = UserAgent()
user_agents = ua.random
def create_driver(user_agents):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={user_agents}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--disable-extensions")  # Tắt tiện ích mở rộng
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(options=chrome_options)


def clean_text(text):
    return re.sub(r'[\u200e]', '', text)

def extract_store_name(soup):
    divsshop = soup.find('a', class_='a-link-normal', id='bylineInfo')

    # Kiểm tra nếu tìm thấy thẻ, nếu không thì gán giá trị 'None'
    if divsshop:
        # Lấy văn bản và bỏ phần "Visit the"
        store = divsshop.get_text().replace("Visit the ", "")
    else:
        store = "None"
    return store

def extract_description(soup):
    # Tìm thẻ chứa mô tả sản phẩm
    feature_bullets = soup.find('ul', class_='a-unordered-list a-vertical a-spacing-mini')

    # Lấy tất cả các mục trong danh sách <ul>
    if feature_bullets:
        items = feature_bullets.find_all('li', class_='a-spacing-mini')
        descriptions = []
        for item in items:
            description = item.get_text(strip=True)  # Lấy văn bản trong từng thẻ <li>
            descriptions.append(description)
        
    else:
        return "Không tìm thấy phần mô tả sản phẩm."
    
    return descriptions
    
def detailproduct_bucket(soup, divs2I,driver):
    # Trích xuất link ảnh

    dimension = asinid = datefirstavailable = manufactures = country = sellerrank = color = modelnumber = weight = price = priceamzship = eic = shipping_days = 'None'

    divs3 = divs2I.find_all('span', class_='a-text-bold')
    for div in divs3:
        if 'Package Dimensions' in div.text.strip() or 'Dimensions' in div.text.strip():
            div4 = div.find_next_sibling('span')
            dimension = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Item model number' in div.text.strip():
            div4 = div.find_next_sibling('span')
            modelnumber = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Date First Available' in div.text.strip():
            div4 = div.find_next_sibling('span')
            datefirstavailable = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Manufacturer' in div.text.strip():
            div4 = div.find_next_sibling('span')
            manufactures = clean_text(div4.text.strip() if div4 else 'None')
        elif 'ASIN' in div.text.strip():
            div4 = div.find_next_sibling('span')
            asinid = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Country of Origin' in div.text.strip():
            div4 = div.find_next_sibling('span')
            country = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Best Sellers Rank' in div.text.strip():
            parent_tag = div.parent
            sellerrank = clean_text(parent_tag.get_text(strip=True))
        elif 'Color' in div.text.strip():
            div4 = div.find_next_sibling('span')
            color = clean_text(div4.text.strip() if div4 else 'Not Given')

    # Tìm và click vào nút "Details" để mở bảng shipping
    try:
        details_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.a-declarative [role='button']"))
        )
        driver.execute_script("arguments[0].click();", details_button)
        
        # Đợi cho bảng shipping hiện ra
        shipping_table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "a-lineitem"))
        )
        
        # Parse thông tin từ bảng mới
        table_html = shipping_table.get_attribute('outerHTML')
        table_soup = BeautifulSoup(table_html, 'html.parser')
        rows = table_soup.find_all('tr')
        
        price = priceamzship = eic = 'None'  # Khởi tạo giá trị mặc định

        for row in rows:
            td_key = row.find('td', class_='a-span9 a-text-left')
            td_value = row.find('td', class_='a-span2 a-text-right')
            
            if td_key and td_value:
                key_span = td_key.find('span', class_='a-size-base a-color-secondary')
                value_span = td_value.find('span', class_='a-size-base a-color-base')
                
                if key_span and value_span:
                    key_text = key_span.get_text(strip=True)
                    value_text = value_span.get_text(strip=True)
                    
                    # Trích xuất thông tin theo từng mục
                    if 'Price' in key_text:
                        price = value_text
                    elif 'AmazonGlobal Shipping' in key_text:
                        priceamzship = value_text
                    elif 'Estimated Import Charges' in key_text:
                        eic = value_text

        logging.info(f"Successfully extracted shipping details: Price={price}, Shipping={priceamzship}, Import={eic}")
    except Exception as e:
        logging.warning(f"Could not extract shipping details: {str(e)}")
        price = priceamzship = eic = 'None'

    shop_name = extract_store_name(soup)
    product_descriptions = extract_description(soup)
    
    return {
        "Dimension": dimension,
        "ASIN": asinid,
        "Date First Available": datefirstavailable,
        "Manufacturer": manufactures,
        "Store": shop_name,
        "Country of Origin": country,
        "Best Sellers Rank": sellerrank,
        "Color": color,
        "Item Model Number": modelnumber,
        "Item Weight": weight,
        "Price": price,
        "AmazonGlobal Shipping": priceamzship,
        "Estimated Import Charges": eic,
        "Description": product_descriptions,
    }

def detailproduct_table(soup, divs2,driver):
        # Trích xuất link ảnh
    shop_name = extract_store_name(soup)

    dimension = asinid = datefirstavailable = manufactures = country = sellerrank = color = modelnumber = weight = price = priceamzship = eic = shipping_days = 'None'

    divs3 = divs2.find_all('th', class_='a-color-secondary a-size-base prodDetSectionEntry')
    for div in divs3:
        if 'Manufacturer' in div.text.strip():
            divs7 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            manufactures = clean_text(divs7.text.strip() if divs7 else 'None')
        if 'Dimensions' in div.text.strip():
            divs4 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            dimension = clean_text(divs4.text.strip() if divs4 else 'None')
        if 'ASIN' in div.text.strip():
            divs5 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            asinid = clean_text(divs5.text.strip() if divs5 else 'None')
        if 'Date First Available' in div.text.strip():
            divs6 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            datefirstavailable = clean_text(divs6.text.strip() if divs6 else 'None')
        if 'Country of Origin' in div.text.strip():
            divs8 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            country = clean_text(divs8.text.strip() if divs8 else 'None')
        if 'Best Sellers Rank' in div.text.strip():
            divs9 = div.find_next_sibling('td')
            sellerrank = clean_text(divs9.text.strip() if divs9 else 'None')
        if 'Color' in div.text.strip():
            divs10 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            color = clean_text(divs10.text.strip() if divs10 else 'Not Given')
        if 'Item model number' in div.text.strip():
            divs11 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            modelnumber = clean_text(divs11.text.strip() if divs11 else 'Not Given')
        if 'Item Weight' in div.text.strip():
            divs12 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            weight = clean_text(divs12.text.strip() if divs12 else 'Not Given')

        # Thông tin giá shipping
        try:
            # Tìm và click vào nút Details
            details_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span.a-declarative [role='button']"))
            )
            driver.execute_script("arguments[0].click();", details_button)
            
            # Đợi cho bảng shipping hiện ra
            shipping_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "a-lineitem"))
            )
            
            # Parse thông tin từ bảng mới
            table_html = shipping_table.get_attribute('outerHTML')
            table_soup = BeautifulSoup(table_html, 'html.parser')
            rows = table_soup.find_all('tr')
            
            for row in rows:
                td_key = row.find('td', class_='a-span9 a-text-left')
                td_value = row.find('td', class_='a-span2 a-text-right')
                
                if td_key and td_value:
                    key_span = td_key.find('span', class_='a-size-base a-color-secondary')
                    value_span = td_value.find('span', class_='a-size-base a-color-base')
                    
                    if key_span and value_span:
                        key_text = key_span.get_text(strip=True)
                        value_text = value_span.get_text(strip=True)
                        
                        if 'Price' in key_text:
                            price = value_text
                        elif 'AmazonGlobal Shipping' in key_text:
                            priceamzship = value_text
                        elif 'Estimated Import Charges' in key_text:
                            eic = value_text
            
            logging.info(f"Successfully extracted shipping details: Price={price}, Shipping={priceamzship}, Import={eic}")
        
        except Exception as e:
            logging.warning(f"Could not extract shipping details: {str(e)}")
            price = priceamzship = eic = 'None'

    product_descriptions = extract_description(soup)
    
    return {
        "Dimension": dimension,
        "ASIN": asinid,
        "Date First Available": datefirstavailable,
        "Manufacturer": manufactures,
        "Store": shop_name,
        "Country of Origin": country,
        "Best Sellers Rank": sellerrank,
        "Color": color,
        "Item Model Number": modelnumber,
        "Item Weight": weight,
        "Price": price,
        "AmazonGlobal Shipping": priceamzship,
        "Estimated Import Charges": eic,
        "Description": product_descriptions,
        
        

    }

url_list = pd.read_csv(f'D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Data_overview\\merged_part1_with_asin.csv')

def process_url(urldetail, csv_writer, fieldnames):
    user_agents = ua.random
    driver = create_driver(user_agents)  # Khởi tạo driver mới với User-Agent mới
    driver.get(urldetail)
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        divs2 = soup.find('div', id='prodDetails')
        divs2I = soup.find('div', id='detailBulletsWrapper_feature_div')

        if divs2:
            result = detailproduct_table(soup, divs2)
            if result:
                row = [result.get(field, 'None') for field in fieldnames]
                csv_writer.writerow(row)
                csv_writer.flush()
        elif divs2I:
            result = detailproduct_bucket(soup, divs2I)
            if result:
                row = [result.get(field, 'None') for field in fieldnames]
                csv_writer.writerow(row)
                csv_writer.flush()

    except Exception as e:
        logging.info(f"Lỗi khi mở URL {urldetail}: {str(e)}")
    finally:
        driver.quit()

def crawl():
    url_list = pd.read_csv(f'D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Data_overview\\merged_part1_with_asin.csv')

    filename = "Data\\part2_dataDetail_automotive_test_2.csv"
    fieldnames = ["Dimension", "ASIN", "Date First Available", "Manufacturer", "Store", "Country of Origin", 
                  "Best Sellers Rank", "Color", "Item Model Number", "Item Weight", "Price", 
                  "AmazonGlobal Shipping", "Estimated Import Charges", "Description"]

    file_exists = os.path.exists(filename)

    with open(filename, 'a', newline="", encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        if not file_exists:
            csv_writer.writerow(fieldnames)

        # Tạo danh sách các threads
        threads = []
        for urldetail in url_list['Link']:
            thread = threading.Thread(target=process_url, args=(urldetail, csv_writer, fieldnames))
            threads.append(thread)
            thread.start()

        # Chờ tất cả các thread hoàn thành
        for thread in threads:
            thread.join()

    print(f"Completed scraping and saved to {filename}.")

crawl()