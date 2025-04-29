import requests
from bs4 import BeautifulSoup

# URL của trang cần lấy dữ liệu
url = "https://www.amazon.com/Helmet-Protection-Professional-installation-Microphone/dp/B0DHW3ZFBB/ref=sr_1_3571?dib=eyJ2IjoiMSJ9.RCJ2cnZSsbrfNyte9OlGFSmHFVnwJ-vyRSoZdtO_vg8nm09-6SSThhxajnJcTUBdXYLMk7tD-y-W3m-68apm_XHQe6PCAi22wHzPstgRe7--8tEere6x5GJTwrSHlBWIpCRs-PNXUweM4w3QWNku9besnI3PXf-bSwzv_b4I6dBAKeLPjZvR-cf1EUu2EEPEDwQTr3vsw--A-35tldpPaHkBRI-HAZeCVua15aNT45vzBhp_msf7_DvYPqOPoMgHduL1lPLFXqpyPNNlUsCcE_3U8RVHqkK3aQzCgzDdxQ3zxnJI3QFT7ZkzJYiKG6xcsmw6mR4UtJYI7unD8V_MmHNu_ZDratLTt1ZS4GBChrc.Veom7pfdApU7VYbP-Xx7kIbQkHc3ShUsVTnjmdXz9ng&dib_tag=se&qid=1742637105&s=automotive-intl-ship&sr=1-3571&xpid=X_07fvANhKxEM"  # Thay thế bằng URL thực tế của bạn

# Gửi yêu cầu GET đến URL
response = requests.get(url)

# Kiểm tra nếu yêu cầu thành công
if response.status_code == 200:
    # Phân tích HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    print (soup)
    # Tìm bảng có class 'a-lineitem' hoặc các thẻ chứa giá trị bạn cần
    table = soup.find('table', class_='a-lineitem')
    if table:
        # Lặp qua các dòng trong bảng và trích xuất thông tin
        for row in table.find_all('tr'):
            td_key = row.find('td', class_='a-span9 a-text-left')
            td_value = row.find('td', class_='a-span2 a-text-right')

            if td_key and td_value:
                key_text = td_key.get_text(strip=True)
                value_text = td_value.get_text(strip=True)

                # In ra các giá trị tìm được
                print(f"{key_text}: {value_text}")
    else:
        print("Không tìm thấy bảng giá.")
else:
    print("Không thể lấy dữ liệu từ URL. Mã lỗi:", response.status_code)
