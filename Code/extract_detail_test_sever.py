import csv
import datetime
import logging
import os
from pathlib import Path
import re
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
import mysql.connector

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
    
def detailproduct_bucket(soup, divs2I):
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

def detailproduct_table(soup, divs2):
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

def save_result_to_csv(data, output_file):
    fieldnames = ["Dimension", "ASIN", "Date_First_Available", "Manufacturer", "Store", "Country_of_Origin", 
                  "Best_Sellers_Rank", "Color", "Item_Model_Number", "Item_Weight", "Price", 
                  "Amazon_Global_Shipping", "Estimated_Import_Charges", ""]

    # Tạo thư mục nếu chưa có
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_path.exists()

    with open(output_path, 'a', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if not file_exists:
            csv_writer.writeheader()

        csv_writer.writerow(data)
        csv_file.flush()    

url_list = pd.read_csv(f'\\tsclient\D\LNTP ở HUST\Học tập\Năm 4\20242\ĐATN\Data_overview\merged_data_part1.csv')
# # Kết nối MySQL
# conn = mysql.connector.connect(
#     host='localhost',
#     user='root',  # Thay thế bằng user của bạn
#     password='phuocle11001203',  # Thay thế bằng password của bạn
#     database='stg_datn'  # Tên database
# )
# cursor = conn.cursor()

# # Tạo bảng nếu chưa có
# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS detail_product_data (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         Dimension VARCHAR(255),
#         ASIN VARCHAR(255),
#         Date_First_Available VARCHAR(255),
#         Manufacturer VARCHAR(255),
#         Store VARCHAR(255),
#         Country_of_Origin VARCHAR(255),
#         Best_Sellers_Rank TEXT,
#         Color VARCHAR(255),
#         Item_Model_Number VARCHAR(255),
#         Item_Weight VARCHAR(255),
#         Price VARCHAR(255),
#         Amazon_Global_Shipping VARCHAR(255),
#         Estimated_Import_Charges VARCHAR(255),
#         Product_Description TEXT
#     )
# """)

count = 0
for urldetail in url_list['Link']:
    count += 1
    driver = create_driver(user_agents)
    
    print(f"Lần lấy thông tin thứ: {count} với User-Agent: {user_agents}")

    driver.get(urldetail)
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        divs2 = soup.find('div', id='prodDetails')
        divs2I = soup.find('div', id='detailBulletsWrapper_feature_div')

        if divs2I:
            result = detailproduct_bucket(soup, divs2I)
        elif divs2:
            result = detailproduct_table(soup,divs2)
        if result:
            print(result)
            save_result_to_csv(result,"part2.csv")
        #     sql = """
        #     INSERT INTO detail_product_data (
        #         Dimension, ASIN, Date_First_Available, Manufacturer, Store,
        #         Country_of_Origin, Best_Sellers_Rank, Color, Item_Model_Number,
        #         Item_Weight, Price, Amazon_Global_Shipping, Estimated_Import_Charges, Product_Description
        #     ) 
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        # """
        #     values = [result[field] if field != 'Description' else '\n'.join(result[field]) for field in result]
        #     cursor.execute(sql, values)
        #     conn.commit()



    except Exception as e:
        logging.info(f"Lỗi khi mở URL {urldetail}: {str(e)}")
    
    driver.quit()
    time.sleep(3)

# cursor.close()
# conn.close()
print("Đã lưu toàn bộ dữ liệu vào MySQL.")