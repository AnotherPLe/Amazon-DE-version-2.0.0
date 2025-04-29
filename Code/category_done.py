from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time

# Cấu hình ChromeOptions để tối ưu trình duyệt
chrome_options = Options()
chrome_options.add_argument("--headless")  # Chạy ẩn trình duyệt
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

# Khởi tạo trình duyệt
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.amazon.com/ref=nav_logo")
time.sleep(20)

# Mở menu hamburger
try:
    menu_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "nav-hamburger-menu"))
    )
    menu_button.click()
    time.sleep(20)
except Exception as e:
    print("Không tìm thấy menu:", e)
    driver.quit()

# Click vào "See All" để mở rộng danh mục nếu có
try:
    see_all = driver.find_element(By.XPATH, '//a[@class="hmenu-item hmenu-compressed-btn"]')
    see_all.click()
    time.sleep(20)
except:
    print("Không tìm thấy nút See All hoặc không cần click")

# Lấy danh mục trong "Shop by Department"
departments = driver.find_elements(By.CSS_SELECTOR, 'ul.hmenu-compress-section li a.hmenu-item[data-menu-id]')

data = []

for dept in departments:
    try:
        department_name = dept.text.strip()
        department_url = dept.get_attribute("href")
        department_menu_id = dept.get_attribute("data-menu-id")

        # Bỏ qua nếu department không có menu-id hoặc bị lỗi
        if not department_name or not department_menu_id:
            continue

        # Click vào danh mục để mở sub-department
        ActionChains(driver).move_to_element(dept).click().perform()
        time.sleep(2)  # Chờ hiệu ứng transition load xong

        # Chờ sub-menu xuất hiện
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'ul.hmenu[data-menu-id="{department_menu_id}"]'))
        )

        # Lấy HTML sau khi chuyển trang
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Lấy danh sách sub-department trong menu mới
        sub_departments = soup.select(f'ul.hmenu[data-menu-id="{department_menu_id}"] li a.hmenu-item')

        if sub_departments:
            for sub in sub_departments:
                sub_name = sub.text.strip()
                sub_url = sub.get("href", "")

                if sub_url and not sub_url.startswith("http"):
                    sub_url = f"https://www.amazon.com{sub_url}"

                # Bỏ qua nếu sub-category bị lỗi
                if sub_name and sub_url != "https://www.amazon.com/":
                    data.append([department_name, sub_name, sub_url])
        else:
            data.append([department_name, "", department_url])

        # Quay lại trang chính để click vào danh mục tiếp theo
        driver.back()
        time.sleep(20)  # Chờ load lại menu chính

    except Exception as e:
        print(f"Lỗi khi xử lý danh mục {department_name}: {e}")
        continue

# Lưu vào CSV
with open('amazon_categories_2.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Department', 'Sub Department', 'URL'])
    writer.writerows(data)

print("Lưu xong file amazon_categories_2.csv!")

# Đóng trình duyệt
driver.quit()
