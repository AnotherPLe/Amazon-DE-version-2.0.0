import requests

# URL của một sản phẩm trên Amazon, ví dụ một trang sản phẩm bất kỳ
url = 'https://www.amazon.com/HP-Magenta-Yellow-Cartridges-3JB41AN/dp/B07SZKCGFJ/ref=sr_1_8?dib=eyJ2IjoiMSJ9.MNaz8F8PlFI7KLmYKDrLOaKkLKzDibvEGNUMjT1Z7Pf7I4DdigZyyHIdhNl5fzA1JMFEQHIfJqUEqDYlW3srsbYrow1y1I2fULy0iAQz8CDrIuCkTz-P1-Em0P8_CB3VP7yAF2pBNJd_wGBp1QsS4KnrcIvAk7ADVUcwOkb39-Exo8HAnoHlpnB1rEHTuqe8epMuqm7YmxNuLuhcjTpojr-qLkCo0WQ7jdIsu9AEpeK6JDsBPXoIA200ogr4J62088XAvTGCdeiNRi5G861HHM7Tje92u8UAZ1jDM6LerkE.xUofLe_DIxrU1e5UmCm5InUoIZILe2rZSObFpgzNtno&dib_tag=se&qid=1744126908&s=computers-intl-ship&sr=1-8'  # Thay thế với URL thực tế của sản phẩm

# Gửi yêu cầu GET đến URL
response = requests.get(url)

# In ra status code của yêu cầu
print(response.status_code)  # 200 là thành công, 403 là bị chặn, v.v.

# In ra phần đầu của HTML nhận được
print(response.text[:1000])  # In ra 1000 ký tự đầu của HTML
