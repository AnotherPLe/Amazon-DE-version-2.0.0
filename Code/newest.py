import pandas as pd

# Đọc file CSV
file_path = 'Code\\amazon_categories_full.csv'  # Thay thế bằng đường dẫn tới file của bạn
df = pd.read_csv(file_path)

# Hàm thêm tham số &s=date-desc-rank vào giữa URL trước và sau &ref
def add_sort_param(url):
    # Kiểm tra xem URL có chứa '&ref' không
    if '&ref' in url:
        # Tìm vị trí của '&ref' trong URL
        ref_index = url.index('&ref')
        # Thêm tham số '&s=date-desc-rank' ngay trước '&ref'
        url = url[:ref_index] + '&s=date-desc-rank' + url[ref_index:]
    else:
        # Nếu không có '&ref', chỉ thêm tham số vào cuối URL
        url += '&s=date-desc-rank'
    return url

# Áp dụng hàm trên vào cột Link
df['URL'] = df['URL'].apply(add_sort_param)

# Lưu lại file CSV mới
output_path = 'urls_with_newest_arrivals_categories.csv'  # Đường dẫn lưu file mới
df.to_csv(output_path, index=False)

print(f'File đã được lưu tại: {output_path}')
