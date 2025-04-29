import os
import pandas as pd
import re

# Thư mục chứa các file CSV
folder_path = "Code\\Prt1"  # 🔹 Thay đổi đường dẫn này
folder_output = "Data_overview"

# Danh sách tất cả các file CSV trong thư mục
csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

# Kiểm tra nếu không có file CSV nào
if not csv_files:
    print("❌ Không tìm thấy file CSV nào trong thư mục!")
else:
    # Đọc và gộp tất cả các file CSV, kiểm tra header
    df_list = []
    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path)
        
        # Kiểm tra header và chuẩn hóa nếu cần
        if df.columns.str.contains("Link").any():  # Kiểm tra nếu có cột "Link"
            df_list.append(df)
        else:
            print(f"⚠️ Cảnh báo: File '{file}' không có cột 'Link' và sẽ bị bỏ qua!")
    
    # Gộp tất cả DataFrame thành một
    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True)
        
        # Hàm để trích xuất ASIN từ link
        def extract_asin(url):
            if isinstance(url, str):  # Kiểm tra nếu url là chuỗi
                match = re.search(r"/dp/([A-Za-z0-9]{10})", url)
                if match:
                    return match.group(1)
            return None  # Trả về None nếu không tìm thấy ASIN hoặc url không phải là chuỗi
        
        # Giả sử cột chứa link Amazon là 'Link', bạn có thể thay tên cột nếu cần
        merged_df['ASIN'] = merged_df['Link'].apply(extract_asin)
        
        # Lưu file CSV mới
        output_file = os.path.join(folder_output, "merged_data_part1_op.csv")
        merged_df.to_csv(output_file, index=False)
        print(f"✅ Đã gộp {len(csv_files)} file CSV vào '{output_file}' và thêm cột ASIN thành công!")
    else:
        print("❌ Không có file CSV hợp lệ để gộp.")
