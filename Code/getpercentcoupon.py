import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


ua = UserAgent()
fake = ua.random
# Thiết lập User-Agent giả
chrome_options = Options()
chrome_options.add_argument(f"user-agent={fake}")

# Cấu hình Selenium WebDriver với options
driver = webdriver.Chrome(options=chrome_options)  # Hoặc WebDriver khác nếu bạn sử dụng

# Mở trang chứa thông tin coupon
driver.get('https://www.amazon.com/s?i=automotive-intl-ship&bbn=2562090011&rh=n%3A2562090011%2Cn%3A15690151%2Cn%3A2230642011&s=date-desc-rank&page=3&xpid=8b89lQVk6Vi9J&qid=1743092460&ref=sr_pg_3')

# Lấy mã HTML của trang
html_content = driver.page_source

# Sử dụng BeautifulSoup để phân tích mã HTML
soup = BeautifulSoup(html_content, 'html.parser')
time.sleep(20)
def get_coupon(soup):
    # Tìm phần tử chứa thông tin coupon (trong trường hợp này, class="s-coupon-unclipped")
    coupon_text = soup.find('span', class_='s-coupon-unclipped').text.strip()

    # Trích xuất phần trăm từ chuỗi coupon
    if coupon_text:
        coupon_percentage = coupon_text.split()[1] 
    else: 
        coupon_percentage = 0 # Giả sử cấu trúc luôn là "Save XX%" 

    # In ra kết quả
    print(f"Coupon: {coupon_percentage}")

    return coupon_percentage

coupon = get_coupon(soup)
# Đóng trình duyệt sau khi xong
driver.quit()
