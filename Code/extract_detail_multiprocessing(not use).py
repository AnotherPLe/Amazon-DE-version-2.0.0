import csv
import datetime
import logging
import math
import os
import random
import re
import time
import pandas as pd
import multiprocessing
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent
from selenium.webdriver.common.proxy import Proxy, ProxyType


# 📌 Tạo User-Agent ngẫu nhiên
ua = UserAgent()
user_agents = ua.random

# 📌 Tạo trình duyệt Selenium với cấu hình tối ưu
def create_driver(user_agents):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Chạy không hiển thị giao diện
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={user_agents}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(options=chrome_options)
    
# 📌 Hàm tính số ngày giao hàng
def calculate_shipping_days(estimated_delivery_date_str, crawl_date_str):
    try:
        estimated_delivery_date = datetime.datetime.strptime(estimated_delivery_date_str, '%A, %B %d')
        crawl_date = datetime.datetime.strptime(crawl_date_str, '%A, %B %d')
        return (estimated_delivery_date - crawl_date).days
    except ValueError:
        return 'N/A'

# 📌 Làm sạch dữ liệu văn bản
def clean_text(text):
    return re.sub(r'[\u200e]', '', text)

# 📌 Hàm trích xuất link ảnh
def extract_image_link(soup):
    image_tag = soup.find('img', id='landingImage')
    return image_tag['src'] if image_tag and 'src' in image_tag.attrs else 'No Image'

# 📌 Hàm trích xuất tên cửa hàng
def extract_store_name(soup):
    divsshop = soup.find('a', class_='a-link-normal', id='bylineInfo')
    return divsshop.get_text().replace("Visit the ", "") if divsshop else "None"

# 📌 Hàm xử lý dữ liệu sản phẩm từ `detailproduct_bucket`
def detailproduct_bucket(soup, divs2I,driver):
    # Trích xuất link ảnh
    image_url = extract_image_link(soup)

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


    estimated_delivery_date_tag = soup.find('span', class_='a-text-bold')
    estimated_delivery_date = clean_text(estimated_delivery_date_tag.text.strip() if estimated_delivery_date_tag else 'N/A')
    crawl_date = datetime.datetime.now().strftime('%A, %B %d')
    shipping_days = calculate_shipping_days(estimated_delivery_date, crawl_date)
    shop_name = extract_store_name(soup)
    
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
        "Day Delivered": str(shipping_days),
        "Image URL": image_url
    }

def detailproduct_table(soup, divs2,driver):
        # Trích xuất link ảnh
    image_url = extract_image_link(soup)
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

    estimated_delivery_date_tag = soup.find('span', class_='a-text-bold')
    estimated_delivery_date = clean_text(estimated_delivery_date_tag.text.strip() if estimated_delivery_date_tag else 'N/A')
    crawl_date = datetime.datetime.now().strftime('%A, %B %d')
    shipping_days = calculate_shipping_days(estimated_delivery_date, crawl_date)

    
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
        "Day Delivered": str(shipping_days),
        "Image URL": image_url

    }


# 📌 Hàm lưu kết quả vào file CSV (Ghi ngay sau mỗi lần crawl xong)
def save_result_to_csv(data, output_file):
    fieldnames = ["Dimension", "ASIN", "Date First Available", "Manufacturer","Store", "Country of Origin", 
              "Best Sellers Rank", "Color", "Item Model Number", "Item Weight", "Price", 
              "AmazonGlobal Shipping", "Estimated Import Charges", "Day Delivered", "Image URL"]
    
    file_exists = os.path.exists(output_file)

    with open(output_file, 'a', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if not file_exists:
            csv_writer.writeheader()
        csv_writer.writerow(data)
        csv_file.flush()

# 📌 Hàm crawl dữ liệu từ một URL
def crawl_product(url):
    driver = create_driver(user_agents)
    data = {}
    driver.get(url)
        # 🛠️ Kiểm tra User-Agent từ trình duyệt thật
    user_agent_check = driver.execute_script("return navigator.userAgent;")

    # 🛠️ In thông tin process và User-Agent
    print(f"🔍 Process {os.getpid()} is using User-Agent: {user_agent_check}")

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        divs2 = soup.find('div', id='prodDetails')
        divs2I = soup.find('div', id='detailBulletsWrapper_feature_div')

        if divs2:
            data= detailproduct_table(soup, divs2,driver)
        elif divs2I:
            data= detailproduct_bucket(soup, divs2I,driver)

        print(f"✅ Crawled: {url}")
        print(data)
    finally:
        driver.quit()

    return data

def crawl_product_with_delay(url):
    """Hàm thêm độ trễ ngẫu nhiên trước khi crawl"""
    delay = random.uniform(1, 5)  # 🛠️ Độ trễ ngẫu nhiên từ 1 đến 5 giây
    print(f"⏳ Process {multiprocessing.current_process().pid} waiting {delay:.2f}s before crawling {url}")
    time.sleep(delay)  # Chờ trước khi bắt đầu crawl
    return crawl_product(url)  # Gọi hàm crawl chính

def multi_crawl(urls, output_file, num_processes):
    """Chạy crawling với các process song song có độ trễ ngẫu nhiên"""
    with multiprocessing.Pool(processes=num_processes) as pool:
        for result in pool.imap_unordered(crawl_product_with_delay, urls):
            save_result_to_csv(result, output_file)
            time.sleep(random.uniform(1, 3))  # 🛠️ Độ trễ ngẫu nhiên giữa các lần ghi dữ liệu

    print("🏁 All crawling tasks completed!")
    
# 📌 Chạy chương trình chính
if __name__ == "__main__":
    input_file = "D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Data_overview\\merged_part1_with_asin.csv"
    output_file = "output_1.csv"

    df = pd.read_csv(input_file)
    urls = df['Link'].tolist()
    num_processes = 2  
    print(f"📌 Đang crawl {len(urls)} sản phẩm với {num_processes} tiến trình song song...")

    
    multi_crawl(urls, output_file, num_processes)

    print("✅ Hoàn thành crawling!")
