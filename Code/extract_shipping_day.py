from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import datetime
import re

# Cấu hình Chrome
ua = UserAgent()
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument(f"user_agent = {}")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

# Mở URL Amazon
url = "https://www.amazon.com/s?i=specialty-aps&bbn=16225009011&rh=n%3A%252116225009011%2Cn%3A541966&ref=nav_em__nav_desktop_sa_intl_computers_and_accessories_0_2_6_6"
driver.get(url)

# Đợi cho tới khi sản phẩm được load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot")))

# Parse HTML bằng BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Lấy danh sách sản phẩm
products = soup.find_all("div", {"data-component-type": "s-search-result"})

# Crawl từng sản phẩm
for product in products:
    # Tiêu đề sản phẩm
    title_tag = product.find("h2")
    title = title_tag.get_text(strip=True) if title_tag else "Không có tiêu đề"

    # Tìm div chứa ngày giao hàng
    delivery_div = product.find('div', {'data-cy': 'delivery-recipe'})
    delivery_day = "Không có thông tin giao hàng"

    # Tìm tất cả span có chữ "Delivery"
    delivery_spans = product.find_all('span', string=re.compile(r"Delivery"))
    for span in delivery_spans:
        text = span.get_text(strip=True)
        print("🔍 span:", text)  # Debug

        match = re.search(r"([A-Za-z]+),?\s*([A-Za-z]+)\s+(\d{1,2})", text)
        if match:
            month = match.group(2)
            day = int(match.group(3))
            try:
                month_num = datetime.datetime.strptime(month, '%b').month
            except:
                month_num = datetime.datetime.strptime(month, '%B').month
            today = datetime.datetime.today()
            delivery_date = datetime.datetime(today.year, month_num, day)
            delivery_day = f"{(delivery_date - today).days} ngày (giao {month} {day})"
            break


    print(f"📦 {title}\n   🚚 {delivery_day}\n")

driver.quit()
