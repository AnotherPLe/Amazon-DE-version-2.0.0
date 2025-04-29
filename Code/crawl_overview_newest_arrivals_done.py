import datetime
import os
import re
import time
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
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
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
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
            'Coupon Discount':[],
            'Rating': [],
            'Review': [],
            'Link': [],
            'Image URL': [],
            'Day Delivered':[],
            'Date Added': []
        }
        self.setup_driver()

    def setup_driver(self):
        """Cấu hình Chrome WebDriver"""
        user_agent = self.ua.random
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("--disable-extensions")  # Tắt tiện ích mở rộng
        chrome_options.add_argument("--headless")
        
        # ✅ Cú pháp đúng cho Selenium 4.x
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
            num_day_delivered = self._get_calculate_shipping_days(item)
            self.product_data['Day Delivered'].append(num_day_delivered)
            self.product_data['Date Added'].append(current_date)
            coupon = self.extract_coupon(soup,item)
            self.product_data['Coupon Discount'].append(coupon)
            new_items += 1
        return new_items
    def extract_coupon(self, soup, item):
            # Tìm phần tử chứa thông tin coupon (trong trường hợp này, class="s-coupon-unclipped")
            coupon_element = item.find('span', class_='s-coupon-unclipped')

            if coupon_element:
                # Nếu có coupon, trích xuất văn bản
                coupon_text = coupon_element.text.strip()
                
                # Kiểm tra nếu coupon là phần trăm hay giá trị tiền tệ và trả về toàn bộ giá trị coupon
                if '%' in coupon_text:  # Coupon là phần trăm
                    return coupon_text.split()[1]  # Giả sử cấu trúc luôn là "Save XX%"
                elif '$' in coupon_text:  # Coupon là giá trị tiền tệ
                    return coupon_text.split()[1]  # Giả sử cấu trúc luôn là "Save $XX.XX"
            else:
                # Nếu không có coupon, trả về 0
                return 0
            
    def extract_image_link(self, soup, item):
        """Trích xuất URL của hình ảnh từ sản phẩm"""
        image_tag = item.find('img', class_='s-image')  # Cập nhật class để tìm thẻ img đúng
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
            crawl_date = datetime.datetime.today()

            # Tìm tất cả span có chữ "Delivery"
            delivery_spans = item.find_all('span', string=re.compile(r"Delivery"))
            for span in delivery_spans:
                text = span.get_text(strip=True)
                # VD: "Delivery Wed, May 14"
                match = re.search(r"Delivery\s+(?:\w+,)?\s*([A-Za-z]+)\s+(\d{1,2})", text)
                if match:
                    month = match.group(1)
                    day = int(match.group(2))
                    try:
                        month_num = datetime.datetime.strptime(month, '%b').month
                    except:
                        month_num = datetime.datetime.strptime(month, '%B').month
                    delivery_date = datetime.datetime(crawl_date.year, month_num, day)
                    return f"{(delivery_date - crawl_date).days} ngày (giao {month} {day})"

            return ''  # Không tìm thấy span chứa ngày giao
        except Exception as e:
            logging.warning(f"Lỗi tính ngày giao hàng: {e}")
            return ''



    def save_to_csv(self, department, sub_department):
        """Lưu dữ liệu vào CSV với timestamp"""
        df = pd.DataFrame(self.product_data)
        output_dir = Path('D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Code\\Prt1')
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
            page = 1
            while True:
                start_time = time.time()
                self.driver.get(url)
                WebDriverWait(self.driver,5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot")))
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                layout = self.detect_layout(soup)
                new_items = self.extract_product_info(soup, layout, department, sub_department)
                
                # Lưu dữ liệu sau mỗi trang
                self.save_to_csv(department, sub_department)
                elapsed_time = time.time() - start_time
                
                logging.info(f"Page {page} for {department}/{sub_department} : Crawled {new_items} items in {elapsed_time:.2f} seconds")
                
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
