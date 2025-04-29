import csv
import re
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import logging
import time
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Cấu hình logging


class AmazonScraper:

    def __init__(self):
        self.ua = UserAgent()
        self.product_data = {
            'Department': [],
            'Sub Department': [],
            'Product Name': [],
            'Price': [],
            'Coupon Discount': [],
            'Rating': [],
            'Review': [],
            'Link': [],
            'Image URL': [],
            'Day Delivered': [],
            'Date Added': []
        }
        self.setup_driver()

    def setup_driver(self):
        """Cấu hình Chrome WebDriver"""
        user_agent = self.ua.random
        logging.info(f"Using user-agent: {user_agent}")
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("--disable-extensions")  # Tắt tiện ích mở rộng
        chrome_options.add_argument("--headless")
        
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def detect_layout(self, soup):
        """Tự động phát hiện layout của trang"""
        layout_patterns = [
            {'type': 'row', 'container': ('div', 'a-section a-spacing-small a-spacing-top-small'), 'skip_first': True},
            {'type': 'tiles', 'container': ('div', 'sg-col-4-of-24 sg-col-4-of-12 s-result-item s-asin sg-col-4-of-16 sg-col s-widget-spacing-small sg-col-4-of-20'), 'skip_first': False},
            {'type': 'tiles_onepage', 'container': ('div', 'sg-col-4-of-24 sg-col-4-of-12 s-result-item s-asin sg-col-4-of-16 AdHolder sg-col s-widget-spacing-small sg-col-4-of-20'), 'skip_first': False}
        ]
        for pattern in layout_patterns:
            tag, class_name = pattern['container']
            if soup.find(tag, class_name):
                logging.info(f"Detected layout: {pattern['type']}")
                return pattern
        logging.warning("Could not detect layout, using default (tiles)")
        return layout_patterns[1]

    def extract_product_info(self, soup, layout, department, sub_department):
        """Trích xuất thông tin sản phẩm từ layout đã phát hiện"""
        tag, class_name = layout['container']
        items = soup.find_all(tag, class_name)
        current_date = time.strftime("%Y-%m-%d")
        
        start_idx = 1 if layout['skip_first'] else 0
        new_items = 0
        for item in items[start_idx:]:
            self.product_data['Department'].append(department)
            self.product_data['Sub Department'].append(sub_department)
            self.product_data['Product Name'].append(self._get_text(item, 'a', 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal') or 
                                                    self._get_text(item, 'h2', 'a-size-base-plus a-spacing-none a-color-base a-text-normal'))
            self.product_data['Link'].append(self._get_link(item))
            self.product_data['Price'].append(self._get_text(item, 'span', 'a-price-whole'))
            self.product_data['Rating'].append(self._get_rating(item))
            self.product_data['Review'].append(self._get_text(item, 'span', 'a-size-base s-underline-text'))
            image_url = self.extract_image_link(soup, item)
            self.product_data['Image URL'].append(image_url)
            self.product_data['Day Delivered'].append(self._get_calculate_shipping_days(item))
            self.product_data['Date Added'].append(current_date)
            coupon = self.extract_coupon(soup,item)
            self.product_data['Coupon Discount'].append(coupon)
            new_items += 1
        return new_items

    def extract_coupon(self, soup, item):
        coupon_element = item.find('span', class_='s-coupon-unclipped')

        if coupon_element:
            coupon_text = coupon_element.text.strip()
            if '%' in coupon_text:
                return coupon_text.split()[1]
            elif '$' in coupon_text:
                return coupon_text.split()[1]
        else:
            return 0

    def extract_image_link(self, soup, item):
        image_tag = item.find('img', class_='s-image')
        if image_tag and 'src' in image_tag.attrs:
            return image_tag['src']
        return 'No Image'

    def _get_text(self, item, tag, class_name):
        element = item.find(tag, class_name)
        return element.text.strip() if element else None

    def _get_link(self, item):
        link = item.find('a', 'a-link-normal')
        return f"https://www.amazon.com{link.get('href')}" if link else None

    def _get_rating(self, item):
        rate = item.find('span', 'a-icon-alt')
        return rate.text.split()[0] if rate else None

    def _get_calculate_shipping_days(self, item):
        try:
            delivery_div = item.find('div', {'data-cy': 'delivery-recipe'})
            if not delivery_div:
                return ''
            date_span = delivery_div.find('span', class_='a-color-base a-text-bold')
            if not date_span:
                return ''
            estimated_delivery_str = date_span.get_text(strip=True)
            if not estimated_delivery_str:
                return ''
            crawl_date = datetime.datetime.today()
            match_range = re.match(r"([A-Za-z]+) (\d{1,2}) - (\d{1,2})", estimated_delivery_str)
            if match_range:
                month = match_range.group(1)
                start_day = int(match_range.group(2))
                end_day = int(match_range.group(3))
                try:
                    month_num = datetime.datetime.strptime(month, '%b').month
                except:
                    month_num = datetime.datetime.strptime(month, '%B').month
                start_date = datetime.datetime(crawl_date.year, month_num, start_day)
                end_date = datetime.datetime(crawl_date.year, month_num, end_day)
                avg_timestamp = (start_date.timestamp() + end_date.timestamp()) / 2
                avg_delivery_date = datetime.datetime.fromtimestamp(avg_timestamp)
                return f"{(avg_delivery_date - crawl_date).days}"
            match_single = re.match(r"([A-Za-z]+) (\d{1,2})", estimated_delivery_str)
            if match_single:
                month = match_single.group(1)
                day = int(match_single.group(2))
                try:
                    month_num = datetime.datetime.strptime(month, '%b').month
                except:
                    month_num = datetime.datetime.strptime(month, '%B').month
                estimated_date = datetime.datetime(crawl_date.year, month_num, day)
                return f"{(estimated_date - crawl_date).days} ngày (ngày giao {month} {day})"
            match_full = re.search(r"\b([A-Za-z]+),?\s+([A-Za-z]+)\s+(\d{1,2})\b", estimated_delivery_str)
            if match_full:
                weekday = match_full.group(1)
                month = match_full.group(2)
                day = int(match_full.group(3))
                try:
                    month_num = datetime.datetime.strptime(month, '%b').month
                except:
                    month_num = datetime.datetime.strptime(month, '%B').month
                exact_date = datetime.datetime(crawl_date.year, month_num, day)
                return f"ngày giao chính xác: {month} {day}"
            return ''
        except Exception as e:
            return ''

    def save_to_csv(self, department, sub_department):
        df = pd.DataFrame(self.product_data)
        timestamp = time.strftime("%Y%m%d")
        output_dir = Path(f'/opt/airflow/csv/src_output/pt1_{timestamp}')
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = output_dir / f'part1_data_{department}_{sub_department}_{timestamp}.csv'
        if filename.exists():
            existing_df = pd.read_csv(filename)
            df = pd.concat([existing_df, df]).drop_duplicates(subset=['Link'])
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logging.info(f"Saved/Updated {len(df)} products to {filename}")

    def scrape(self, url, department, sub_department):
        try:
            page = 1
            while True:
                start_time = time.time()
                self.driver.get(url)
                WebDriverWait(self.driver,5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot")))

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                layout = self.detect_layout(soup)
                new_items = self.extract_product_info(soup, layout, department, sub_department)
                
                self.save_to_csv(department, sub_department )
                elapsed_time = time.time() - start_time
                logging.info(f"Page {page} for {department}/{sub_department} : Crawled {new_items} items in {elapsed_time:.2f} seconds")
                
                next_link = soup.select_one('a.s-pagination-next')
                if not next_link:
                    logging.info(f"Reached the last page (Page {page}) for {department}/{sub_department}")
                    break
                
                url = f"https://www.amazon.com{next_link.get('href')}"
                page += 1
                logging.info(f"Moving to page {page} for {department}/{sub_department}")

        except Exception as e:
            logging.error(f"Error during scraping {url}: {str(e)}")
            self.save_to_csv(department, sub_department)
        finally:
            self.driver.quit()

def scrape_department(department_info):
    department, sub_department, url = department_info
    logging.info(f"Processing: {department}/{sub_department} - {url}")
    scraper = AmazonScraper()
    scraper.scrape(url, department, sub_department)

# Đọc dữ liệu từ file CSV và kiểm tra cấu trúc
def scrape_data_from_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        if not all(col in df.columns for col in ['Department', 'Sub_Department', 'URL']):
            raise ValueError("CSV file must contain 'Department', 'Sub Department', and 'URL' columns")
        return df[['Department', 'Sub_Department', 'URL']].values.tolist()
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        return []

# Đặt các tham số mặc định cho DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Đọc dữ liệu từ file CSV
csv_file = '/opt/airflow/csv/src_input/amazon_categories_full copy.csv'

# Đọc dữ liệu từ file CSV
department_data = scrape_data_from_csv(csv_file)

# Khởi tạo DAG
with DAG(
    'scrape_amazon_dag',
    description='Crawl data from Amazon using URLs from CSV',
    schedule_interval=None,
    start_date=datetime(2025, 4, 4),
    catchup=False,
    default_args=default_args
) as dag:

    for index, department_info in enumerate(department_data):
        sanitized_sub_department = re.sub(r'[^a-zA-Z0-9_-]', '_', department_info[1])
        
        task = PythonOperator(
            task_id=f"process_{sanitized_sub_department}_{index}",
            python_callable=scrape_department,
            op_args=[department_info],  # Truyền department_info vào hàm
            dag=dag,
        )
        task
