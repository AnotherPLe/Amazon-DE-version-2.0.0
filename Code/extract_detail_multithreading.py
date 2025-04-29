from concurrent.futures import ThreadPoolExecutor
import csv
import datetime
import threading
import mysql.connector
import logging
import math
import os
from pathlib import Path
import random
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent

ua = UserAgent()
user_agents = ua.random

def create_connection():
    # Thay đổi thông tin kết nối theo cơ sở dữ liệu của bạn
    connection = mysql.connector.connect(
        host="localhost",
        user="root",  # Tên người dùng
        password="phuocle11001203",  # Mật khẩu của bạn
        database="stg_datn"  # Tên cơ sở dữ liệu
    )
    return connection

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

# 📌 Làm sạch dữ liệu văn bản
def clean_text(text):
    return re.sub(r'[\u200e]', '', text)

# 📌 Hàm trích xuất đánh giá sao
def extract_review_percentages(soup):
    ratings_data = soup.find_all('a', {'class': '_cr-ratings-histogram_style_histogram-row-container__Vh7Di'})
    rating_percentages = {}

    for rating in ratings_data:
        label = rating.get('aria-label')
        if label:
            try:
                # Trích xuất phần trăm trực tiếp từ chuỗi
                if "5 stars" in label:
                    rating_percentages['5-star'] = label.split(' ')[0]
                elif "4 stars" in label:
                    rating_percentages['4-star'] = label.split(' ')[0]
                elif "3 stars" in label:
                    rating_percentages['3-star'] = label.split(' ')[0]
                elif "2 stars" in label:
                    rating_percentages['2-star'] = label.split(' ')[0]
                elif "1 star" in label:
                    rating_percentages['1-star'] = label.split(' ')[0]
            except IndexError:
                # Handle any unexpected errors
                print(f"Error extracting data for label: {label}")
    
    return rating_percentages

# 📌 Hàm trích xuất mô tả sản phẩm
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
    description = extract_description(soup)
    rating_percentages = extract_review_percentages(soup)

    dimension = asinid = datefirstavailable = manufactures = country = sellerrank = color = modelnumber = weight = price = priceamzship = eic = shipping_days = 'None'

    divs3 = divs2I.find_all('span', class_='a-text-bold')
    for div in divs3:
        if 'Package Dimensions' in div.text.strip() or 'Dimensions' in div.text.strip():
            div4 = div.find_next_sibling('span')
            dimension = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Item model number' in div.text.strip():
            div4 = div.find_next_sibling('span')
            modelnumber = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Date_First_Available' in div.text.strip():
            div4 = div.find_next_sibling('span')
            datefirstavailable = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Manufacturer' in div.text.strip():
            div4 = div.find_next_sibling('span')
            manufactures = clean_text(div4.text.strip() if div4 else 'None')
        elif 'ASIN' in div.text.strip():
            div4 = div.find_next_sibling('span')
            asinid = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Country_of_Origin' in div.text.strip():
            div4 = div.find_next_sibling('span')
            country = clean_text(div4.text.strip() if div4 else 'None')
        elif 'Best_Sellers_Rank' in div.text.strip():
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
                    elif 'Amazon_Global_Shipping' in key_text:
                        priceamzship = value_text
                    elif 'Estimated_Import_Charges' in key_text:
                        eic = value_text

        logging.info(f"Successfully extracted shipping details: Price={price}, Shipping={priceamzship}, Import={eic}")
    except Exception as e:
        logging.warning(f"Could not extract shipping details: {str(e)}")
        price = priceamzship = eic = 'None'


    shop_name = extract_store_name(soup)
    
    return {
        "Dimension": dimension,
        "ASIN": asinid,
        "Date_First_Available": datefirstavailable,
        "Manufacturer": manufactures,
        "Store": shop_name,
        "Country_of_Origin": country,
        "Best_Sellers_Rank": sellerrank,
        "Color": color,
        "Item_Model_Number": modelnumber,
        "Item_Weight": weight,
        "Price": price,
        "Amazon_Global_Shipping": priceamzship,
        "Estimated_Import_Charges": eic,
        "Description" : description,
        "5-star": rating_percentages.get('5-star', '0%'),
        "4-star": rating_percentages.get('4-star', '0%'),
        "3-star": rating_percentages.get('3-star', '0%'),
        "2-star": rating_percentages.get('2-star', '0%'),
        "1-star": rating_percentages.get('1-star', '0%')

    }

def detailproduct_table(soup, divs2,driver):
        # Trích xuất link ảnh
    shop_name = extract_store_name(soup)
    description = extract_description(soup)
    rating_percentages = extract_review_percentages(soup)
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
        if 'Date_First_Available' in div.text.strip():
            divs6 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            datefirstavailable = clean_text(divs6.text.strip() if divs6 else 'None')
        if 'Country_of_Origin' in div.text.strip():
            divs8 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            country = clean_text(divs8.text.strip() if divs8 else 'None')
        if 'Best_Sellers_Rank' in div.text.strip():
            divs9 = div.find_next_sibling('td')
            sellerrank = clean_text(divs9.text.strip() if divs9 else 'None')
        if 'Color' in div.text.strip():
            divs10 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            color = clean_text(divs10.text.strip() if divs10 else 'Not Given')
        if 'Item model number' in div.text.strip():
            divs11 = div.find_next_sibling('td', class_='a-size-base prodDetAttrValue')
            modelnumber = clean_text(divs11.text.strip() if divs11 else 'Not Given')
        if 'Item_Weight' in div.text.strip():
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
                        elif 'Amazon_Global_Shipping' in key_text:
                            priceamzship = value_text
                        elif 'Estimated_Import_Charges' in key_text:
                            eic = value_text
            
            logging.info(f"Successfully extracted shipping details: Price={price}, Shipping={priceamzship}, Import={eic}")
        
        except Exception as e:
            logging.warning(f"Could not extract shipping details: {str(e)}")
            price = priceamzship = eic = 'None'
            


    
    return {
        "Dimension": dimension,
        "ASIN": asinid,
        "Date_First_Available": datefirstavailable,
        "Manufacturer": manufactures,
        "Store": shop_name,
        "Country_of_Origin": country,
        "Best_Sellers_Rank": sellerrank,
        "Color": color,
        "Item_Model_Number": modelnumber,
        "Item_Weight": weight,
        "Price": price,
        "Amazon_Global_Shipping": priceamzship,
        "Estimated_Import_Charges": eic,
        "Description" : description,
        "5-star": rating_percentages.get('5-star', '0%'),
        "4-star": rating_percentages.get('4-star', '0%'),
        "3-star": rating_percentages.get('3-star', '0%'),
        "2-star": rating_percentages.get('2-star', '0%'),
        "1-star": rating_percentages.get('1-star', '0%')

    }

# 📌 Hàm lưu kết quả vào file CSV đầu ra
# 📌 Hàm lưu kết quả vào file CSV với tên do bạn tự chỉ định
def save_result_to_csv(data, output_file="output_data.csv"):
    fieldnames = ["Dimension", "ASIN", "Date_First_Available", "Manufacturer", "Store", "Country_of_Origin", 
                  "Best_Sellers_Rank", "Color", "Item_Model_Number", "Item_Weight", "Price", 
                  "Amazon_Global_Shipping", "Estimated_Import_Charges", "Description", "5-star", "4-star", 
                  "3-star", "2-star", "1-star"]

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

# def save_result_to_mysql(data, lock=None):
#     # Đảm bảo rằng chỉ một luồng có thể ghi vào MySQL tại một thời điểm
#     if lock:
#         lock.acquire()
    
#     try:
#         connection = create_connection()
#         cursor = connection.cursor()

#         # Câu lệnh SQL để chèn dữ liệu vào bảng
#         insert_query = """
#         INSERT INTO detail_product_data (Dimension, ASIN, Date_First_Available, Manufacturer, Store, Country_of_Origin, 
#         Best_Sellers_Rank, Color, Item_Model_Number, Item_Weight, Price, AmazonGlobal_Shipping, Estimated_Import_Charges, 
#         Description, `5-star`, `4-star`, `3-star`, `2-star`, `1-star`)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """

#         values = (
#             data["Dimension"], 
#             data["ASIN"], 
#             data["Date_First_Available"], 
#             data["Manufacturer"], 
#             data["Store"], 
#             data["Country_of_Origin"], 
#             data["Best_Sellers_Rank"], 
#             data["Color"], 
#             data["Item_Model_Number"], 
#             data["Item_Weight"], 
#             data["Price"], 
#             data["Amazon_Global_Shipping"], 
#             data["Estimated_Import_Charges"], 
#             data["Description"],
#             data["5-star"], 
#             data["4-star"], 
#             data["3-star"], 
#             data["2-star"], 
#             data["1-star"]
#         )

#         # Thực thi câu lệnh chèn dữ liệu
#         cursor.execute(insert_query, values)

#         # Commit để lưu thay đổi vào cơ sở dữ liệu
#         connection.commit()

#         # Đóng kết nối
#         cursor.close()
#         connection.close()

#         logging.info(f"Data inserted into MySQL: {data['ASIN']}")
#     finally:
#         if lock:
#             lock.release()  # Thả lock để cho phép luồng khác ghi vào MySQL


# Hàm crawl thông tin sản phẩm
def crawl_product(url, user_agents):
    driver = create_driver(user_agents)
    data = {}
    driver.get(url)
    # Kiểm tra User-Agent từ trình duyệt thật
    user_agent_check = driver.execute_script("return navigator.userAgent;")
    print(f"🔍 Thread {os.getpid()} is using User-Agent: {user_agent_check}")

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        divs2 = soup.find('div', id='prodDetails')
        divs2I = soup.find('div', id='detailBulletsWrapper_feature_div')

        if divs2:
            data = detailproduct_table(soup, divs2, driver)
        elif divs2I:
            data = detailproduct_bucket(soup, divs2I, driver)

        print(f"✅ Crawled: {url}")
        print(data)
        # Sau khi thu thập dữ liệu, ngay lập tức lưu vào MySQL
        save_result_to_csv(data)  # Lưu dữ liệu vào MySQL
    finally:
        driver.quit()

    return data

# Hàm thêm độ trễ ngẫu nhiên trước khi crawl
def crawl_product_with_delay(url, user_agents):
    delay = random.uniform(1, 5)  # Độ trễ ngẫu nhiên từ 1 đến 5 giây
    print(f"⏳ Process {os.getpid()} waiting {delay:.2f}s before crawling {url}")
    time.sleep(delay)  # Chờ trước khi bắt đầu crawl
    return crawl_product(url, user_agents)  # Gọi hàm crawl chính

# 📌 Hàm xử lý crawling với một file CSV duy nhất
def crawl_file(file_path, user_agents, start_idx, num_urls_per_file=100, lock=None):
    # Đọc dữ liệu từ file CSV
    df = pd.read_csv(file_path)
    urls = df['Link'].tolist()

    # Lấy các URL cần crawl
    urls_to_crawl = urls[start_idx:start_idx+num_urls_per_file]
    results = []

    # Dùng lock để đồng bộ các luồng
    if lock:
        lock.acquire()  # Đảm bảo chỉ một luồng có thể xử lý file tại một thời điểm
        try:
            print(f"📂 Đang crawl file: {file_path}")  # In ra tên file đang được crawl

            for url in urls_to_crawl:
                result = crawl_product_with_delay(url, user_agents)
                results.append(result)

                # Lưu kết quả vào file CSV đầu ra
                save_result_to_csv(result, file_path.replace("part1", "part2"))

            print(f"✅ Finished processing file: {file_path} from index {start_idx}")

        finally:
            lock.release()  # Thả lock để luồng khác có thể xử lý

# 📌 Hàm xử lý crawling với nhiều luồng song song
def multi_crawl(file_path, user_agents, num_threads, num_urls_per_file=100):
    lock = threading.Lock()  # Khởi tạo lock để đồng bộ các luồng

    # Sử dụng ThreadPoolExecutor để chạy nhiều luồng song song
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []

        # Chia nhỏ URL trong file thành từng phần (100 URL mỗi lần)
        total_urls = len(pd.read_csv(file_path)['Link'].tolist())
        for start_idx in range(0, total_urls, num_urls_per_file):
            futures.append(executor.submit(crawl_file, file_path, user_agents[start_idx % len(user_agents)], start_idx, num_urls_per_file, lock))

        # Chờ hoàn thành tất cả các tác vụ
        for future in futures:
            future.result()

    print("🏁 All crawling tasks completed!")

# 📌 Chạy chương trình chính
if __name__ == "__main__":
    #input_directory = "D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Code\\part1_20250409"  # Đường dẫn đến thư mục chứa các file CSV
    input_file = "D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Code\\part1_20250409\\part1_data_Automotive_Oils & Fluids_20250409.csv"  # Đường dẫn đến file CSV duy nhất

    num_threads = 3  # Số lượng luồng song song
    print(f"📌 Đang crawl từ các file CSV trong thư mục {input_file} với {num_threads} luồng song song...")

    # Bắt đầu crawl    
    multi_crawl(input_file, user_agents ,num_threads)


    print("✅ Hoàn thành crawling!")