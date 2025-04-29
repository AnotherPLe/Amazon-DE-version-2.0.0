from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Đường dẫn đến ChromeDriver

# Thiết lập Chrome Options để sử dụng trình duyệt mà không mở cửa sổ (headless)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Sử dụng chế độ không giao diện người dùng (headless)
chrome_options.add_argument("--disable-gpu")  # Tắt GPU (nếu có)
chrome_options.add_argument("--no-sandbox")

# Khởi tạo trình duyệt Chrome với các options trên
driver = webdriver.Chrome(options=chrome_options)

# URL của sản phẩm Amazon
url = 'https://www.amazon.com/WEST-HORSE-Microfiber-Drying-Towel/dp/B0DX7FSF7Q/ref=sr_1_1?dib=eyJ2IjoiMSJ9.EPPfd5glwbV6n0QhzM27ozQLzyoEJbcYMyT4pDu8aw1dSqqbtmbSS9ICQC3GYGjglmBQtF8E6AOPwLab72pojWCaEvutg7mWzEgPdVBfmc6RtfPOJt9TvcXvNaUNnhc6lUpK6KlpISqORl9syx2hS1YW4aZaH7vfxKH--I3-QgAzLx5Pz3TIeMA-IvVxUlDbeBjdVeNxZHbercU5sQUTf-CwCXl93aqEeS3xDiq_IRieLg7HzNgb21epF95O2MoJHZqpivrUBugqZeACRFguhjFRV0_jnRZtaeJ9ocjjbc2dXxHWnuCFEBFDHTMFnM2TfKWxrlQ6h1lb2vE-Opu2jHp0S783PLXppLOWa5zx8h0.Rys-LkHP2SVLDSfTS0s3Acv7jjKPqBGzZDyzVMQaGx8&dib_tag=se&qid=1742633167&s=automotive-intl-ship&sr=1-1'

# Mở URL sản phẩm trong trình duyệt
driver.get(url)

# Đợi một chút để trang web tải xong
time.sleep(5)  # Điều chỉnh thời gian chờ nếu cần

# Lấy nội dung HTML sau khi trang được tải hoàn chỉnh
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Tìm thẻ chứa mô tả sản phẩm
feature_bullets = soup.find('div', id='feature-bullets')

# Lấy tất cả các mục trong danh sách <ul>
if feature_bullets:
    items = feature_bullets.find_all('li', class_='a-spacing-mini')

    # In các mục mô tả sản phẩm
    for item in items:
        description = item.get_text(strip=True)
        print(description)
else:
    print("Không tìm thấy phần mô tả sản phẩm.")

# Đóng trình duyệt sau khi hoàn thành
driver.quit()
