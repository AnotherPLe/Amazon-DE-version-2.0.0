import os
import time
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Cấu hình logging
log_file = "amazon_scraper.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class AmazonScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.product_data = {
            'Department': [],
            'Sub Department': [],
            'Product Name': [],
            'Price': [],
            'Rating': [],
            'Review': [],
            'Link': [],
            'Date Added': []
        }
        self.setup_driver()

    def setup_driver(self):
        """Cấu hình Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={self.ua.random}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--enable-unsafe-swiftshade")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

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
            self.product_data['Date Added'].append(current_date)
            new_items += 1
        return new_items

    def _get_text(self, item, tag, class_name):
        element = item.find(tag, class_name)
        return element.text.strip() if element else None

    def _get_link(self, item):
        link = item.find('a', 'a-link-normal s-line-clamp-4 s-link-style a-text-normal')
        return f"https://www.amazon.com{link.get('href')}" if link else None

    def _get_rating(self, item):
        rate = item.find('span', 'a-icon-alt')
        return rate.text.split()[0] if rate else None

    def sort_by_newest(self, url):
        """Tự động chọn 'Sort by: Newest Arrivals'"""
        self.driver.get(url)
        try:
            sort_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "s-result-sort-select"))
            )
            sort_dropdown.click()
            newest_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//select[@id='s-result-sort-select']/option[@value='date-desc-rank']"))
            )
            newest_option.click()
            time.sleep(4)
            logging.info("Sorted by 'Newest Arrivals'")
            return self.driver.current_url
        except Exception as e:
            logging.warning(f"Could not sort by newest: {str(e)}. Using original URL.")
            return url

    def save_to_csv(self, department, sub_department):
        """Lưu dữ liệu vào CSV với timestamp"""
        df = pd.DataFrame(self.product_data)
        output_dir = Path('D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Code\\Part 1')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d")
        filename = output_dir / f'part1_data_{department}_{sub_department}_{timestamp}.csv'
        
        # Nếu file tồn tại, nối dữ liệu và loại trùng lặp
        if filename.exists():
            existing_df = pd.read_csv(filename)
            df = pd.concat([existing_df, df]).drop_duplicates(subset=['Link'])
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logging.info(f"Saved/Updated {len(df)} products to {filename}")

    def scrape(self, url, department, sub_department):
        """Thực hiện crawl dữ liệu đến trang cuối cùng và lưu realtime"""
        try:
            url = self.sort_by_newest(url)
            page = 1
            
            while True:
                start_time = time.time()
                self.driver.get(url)
                time.sleep(10)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                layout = self.detect_layout(soup)
                new_items = self.extract_product_info(soup, layout, department, sub_department)
                
                # Lưu dữ liệu sau mỗi trang
                self.save_to_csv(department, sub_department)
                elapsed_time = time.time() - start_time
                
                logging.info(f"Page {page} for {department}/{sub_department}: Crawled {new_items} items in {elapsed_time:.2f} seconds")
                
                # Kiểm tra nút Next
                next_link = soup.select_one('a.s-pagination-next')
                if not next_link:
                    logging.info(f"Reached the last page (Page {page}) for {department}/{sub_department}")
                    break
                
                url = f"https://www.amazon.com{next_link.get('href')}"
                page += 1
                logging.info(f"Moving to page {page} for {department}/{sub_department}")

        except Exception as e:
            logging.error(f"Error during scraping {url}: {str(e)}")
            self.save_to_csv(department, sub_department)  # Lưu dữ liệu trước khi thoát
        finally:
            self.driver.quit()

def main():
    # Đường dẫn tới file CSV
    csv_file = 'D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Code\\amazon_categories_full copy.csv'
    
    # Đọc file CSV
    try:
        df = pd.read_csv(csv_file)
        if not all(col in df.columns for col in ['Department', 'Sub Department', 'URL']):
            raise ValueError("CSV file must contain 'Department', 'Sub Department', and 'URL' columns")
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        return
    
    # Duyệt qua từng dòng trong CSV
    for index, row in df.iterrows():
        department = row['Department']
        sub_department = row['Sub Department']
        url = row['URL']
        
        logging.info(f"Processing {index + 1}/{len(df)}: {department}/{sub_department} - {url}")
        
        # Khởi tạo scraper và crawl
        scraper = AmazonScraper()
        scraper.scrape(url, department, sub_department)

if __name__ == "__main__":
    main()