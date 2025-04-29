#!/usr/bin/env python
# coding: utf-8

# In[203]:


import pandas as pd
import csv


# #### Quy trình tiền xử lý
# 1. Tiền xử lý file danh sách sản phẩm
# 
#     a. Merge tất cả danh sách folder
#     
#     b. Cân chỉnh cột discount: giá trị ban đầu đang lẫn cả $ và %
#     
#     thêm cột Coupon discount type:
#      
#     + nếu giá trị trong ô Coupon discount là một %, thêm vào Coupon discount type là percentage voucher discount discount
#     + còn nếu giá trị trong ô Coupon discount đang là một giá trị tiền cụ thể, thêm vào Coupon discount_type là value discount voucher
#     + còn nếu trong ô Coupon discount không có giá trị, ghi giá trị 0, thêm vào Coupon discount_type là No discount voucher
# 
#     sau đó xóa bỏ ký tự % hoặc $ trong ô Coupon discount
#     
#     c. tách asin từ URL
# 
#     d. Đồng nhất ngày giao, tính toán cụ thể số ngày
# 
#     + nếu ngày trong khoảng thì chia trung bình 
# 
# 2. Tiền xử lý file chi tiết từng sản phẩm
# 
#     a. Chỉnh sửa giá trị cột Dimension: 
# 
#     + tính giá trị thể tích dựa vào value trong dimension và thêm cột thể tích (chuyển từ inches về cm3), loại bỏ ký tự thừa
#     + chuyển giá trị sau dấu; về item weight, đồng nhất đơn vị trong item weight (là ounces), loại bỏ ký tự thừa
#     + Thêm cột:
#         - khoảng phân loại cho giá trị item weight
#         - khoảng giá tiền
#         - Thêm cột châu lục
#     + Xóa cột không dùng: Item Model Number
#     + Fill-up cột color: có màu cụ thể thì sẽ giữ nguyên, còn nếu đang none thì sẽ fill là: Multicolor
#     + Định dạng lại các cột 
#         - giá tiền
#         - thời gian
# 
# 3. Merger file chi tiết sản phẩm và file danh sách sản phẩm theo ASIN rồi remove duplicate
# 
# 4. Đẩy vào datawarehouse

# # 1. Xử lý file danh sách sản phẩm

# # 2. Xử lý file chi tiết sản phẩm

# In[204]:


df_prt2 = pd.read_csv('D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Data\\output_data_3 copy.csv',on_bad_lines='warn')


# In[206]:


# Loại bỏ dấu xuống dòng trong cột mô tả (nếu cột mô tả là 'Description')
df_prt2['Description'] = df_prt2['Description'].str.replace('\n', ' ').str.replace('\r', ' ')

# Hoặc áp dụng cho toàn bộ dataframe để loại bỏ tất cả các dấu ngắt dòng trong mọi cột
df_prt2 = df_prt2.applymap(lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x)


# In[208]:


df_part1 = pd.read_csv('D:\\LNTP ở HUST\\Học tập\\Năm 4\\20242\\ĐATN\\Data_overview\\merged_data_part1.csv')


# In[210]:


df_final = pd.merge(df_part1, df_prt2, on='ASIN', how='inner')


# In[214]:


for col in df_final.columns:
    null_count = df_final[col].isnull().sum()
    print(f"Số null trong cột '{col}' : {null_count}")


# In[215]:


df_final = df_final.drop_duplicates('ASIN')


# In[219]:


import re
# Hàm trích xuất Main Ranking Value từ chuỗi
def extract_main_ranking_value(text):
    if pd.isna(text):
        return None
    
    # Loại bỏ đoạn trong dấu ngoặc tròn, ví dụ: (See Top 100...)
    cleaned = re.sub(r'\(.*?\)', '', str(text))
    
    # Tìm giá trị đầu tiên sau dấu "#" và trước "in"
    match = re.search(r'#([\d,]+)\s+in', cleaned)
    if match:
        return int(match.group(1).replace(',', ''))  # chuyển sang số nguyên
    return None

# Áp dụng vào DataFrame
df_final['Main Ranking Value'] = df_final['Best_Sellers_Rank'].apply(extract_main_ranking_value)


# In[ ]:


import re

import numpy as np

# Thay thế chuỗi 'NaN' bằng giá trị NaN thực sự
df_final['Dimension'] = df_final['Dimension'].replace('NaN', np.nan)

# Hàm trích xuất trọng lượng từ chuỗi Dimension và chuyển đổi sang ounces
def extract_weight(dim_str):
    if pd.isna(dim_str) or ";" not in dim_str:
        return np.nan
    
    # Trích xuất phần văn bản sau dấu chấm phẩy chứa thông tin trọng lượng
    weight_part = dim_str.split(";")[1].strip()
    
    # Trích xuất giá trị số
    weight_value = re.search(r'(\d+\.?\d*)', weight_part)
    if weight_value:
        weight_value = float(weight_value.group(1))
        
        # Chuyển đổi sang ounces nếu cần
        if "pound" in weight_part.lower() or "lb" in weight_part.lower():
            weight_ounces = weight_value * 16  # 1 pound = 16 ounces
        else:  # Đã là ounces
            weight_ounces = weight_value
            
        return weight_ounces
    
    return np.nan

# Hàm làm sạch chuỗi Dimension
def clean_dimension(dim_str):
    if pd.isna(dim_str):
        return np.nan
    
    # Trích xuất phần Dimension (trước dấu chấm phẩy nếu có)
    if ";" in dim_str:
        dim_str = dim_str.split(";")[0]
    
    # Trích xuất các số từ chuỗi
    numbers = re.findall(r'(\d+\.?\d*)', dim_str)
    
    # Kiểm tra xem có đủ kích thước để làm việc không
    if len(numbers) < 2:
        return np.nan
    
    # Định dạng dựa trên số lượng kích thước có sẵn
    if len(numbers) >= 3:
        return f"{numbers[0]} x {numbers[1]} x {numbers[2]} inches"
    elif len(numbers) == 2:
        return f"{numbers[0]} x {numbers[1]} inches"
    else:
        return np.nan

# Hàm tính thể tích
def calculate_volume(dim_str):
    if pd.isna(dim_str):
        return np.nan
    
    # Trích xuất các số từ chuỗi
    numbers = re.findall(r'(\d+\.?\d*)', dim_str)
    
    # Chuyển đổi sang số thực
    numbers = [float(num) for num in numbers]
    
    # Tính thể tích dựa trên kích thước có sẵn
    if len(numbers) >= 3:
        # Nếu có ít nhất 3 số, giả định chúng là chiều dài, rộng, cao
        volume_inches = numbers[0] * numbers[1] * numbers[2]
    elif len(numbers) == 2:
        # Nếu chỉ có 2 kích thước, giả định đó là vật phẳng với chiều cao không đáng kể (0.1 inch)
        volume_inches = numbers[0] * numbers[1] * 0.1
    else:
        return np.nan
    
    # Chuyển đổi từ inch³ sang cm³ (1 inch³ = 16.387064 cm³)
    volume_cm3 = volume_inches * 16.387064
    
    # Làm tròn đến 2 chữ số thập phân
    return round(volume_cm3, 2)

# Trích xuất thông tin trọng lượng trước và chuẩn hóa sang ounces
df_final['Item_Weight'] = df_final['Dimension'].apply(extract_weight)

# Làm sạch cột Dimension và tính thể tích
df_final['clean_dimension'] = df_final['Dimension'].apply(clean_dimension)
df_final['volume_cm3'] = df_final['Dimension'].apply(calculate_volume)

# Thay thế cột Dimension gốc bằng phiên bản đã làm sạch
df_final['Dimension'] = df_final['clean_dimension']
df_final = df_final.drop(columns=['clean_dimension'])

# Làm tròn cột Item_Weight đến 2 chữ số thập phân
df_final['Item_Weight'] = df_final['Item_Weight'].apply(lambda x: round(x, 2) if not pd.isna(x) else np.nan)


# In[222]:


def extract_delivery_days(row):
    text = str(row['Day Delivered']).strip()
    
    # Trường hợp chỉ có số nguyên (giữ nguyên)
    if re.fullmatch(r'\d+', text):
        return int(text)

    # Trường hợp "NN ngày (ngày giao ...)"
    match_ngay = re.match(r'(\d+)\s+ngày', text)
    if match_ngay:
        return int(match_ngay.group(1))
    
    # Trường hợp "ngày giao chính xác: Apr 25" → tính ngày thực
    match_chinhxac = re.search(r'ngày giao chính xác: ([A-Za-z]+ \d{1,2})', text)
    if match_chinhxac:
        try:
            exact_date = pd.to_datetime(match_chinhxac.group(1) + ' 2025', format='%b %d %Y')
            if pd.notnull(row['Date Add']):
                return (exact_date - row['Date Add']).days
        except:
            return None
    
    return None  # fallback nếu không khớp gì

# Áp dụng:
df_final['Day Delivered'] =df_final.apply(extract_delivery_days, axis=1)
df_final['Day Delivered'] = pd.to_numeric(df_final['Day Delivered'], errors='coerce').fillna(0).astype(int)



# In[224]:


#Chuẩn hóa cột
df_final['Price_y'] = df_final['Price_y'].str.replace('$', '')
df_final['Price_x'] = df_final['Price_x'].str.replace('$', '')
df_final['Amazon_Global_Shipping'] = df_final['Amazon_Global_Shipping'].str.replace('$', '')
df_final['Estimated_Import_Charges'] = df_final['Estimated_Import_Charges'].str.replace('$', '')
df_final['5-star'] = df_final['5-star'].str.replace('%','')
df_final['4-star'] = df_final['4-star'].str.replace('%','')
df_final['3-star'] = df_final['3-star'].str.replace('%','')
df_final['2-star'] = df_final['2-star'].str.replace('%','')
df_final['1-star'] = df_final['1-star'].str.replace('%','')


# In[225]:


#Chỉnh sửa tên một số nước
df_final['Country_of_Origin'] = df_final['Country_of_Origin'].str.replace('Korea, Republic of', 'Korea')
df_final['Country_of_Origin'] = df_final['Country_of_Origin'].str.replace('USA', 'United States')


# In[226]:


df_final['Store'] = df_final['Store'].replace({'Brand: ': '', 'Store': ''}, regex=True)
df_final['Store'] = df_final['Store'].str.strip()              # bỏ khoảng trắng đầu/cuối
df_final['Store'] = df_final['Store'].str.replace(r'\s+', ' ', regex=True)  # thay nhiều khoảng trắng bằng 1


# In[228]:


#chỉnh sửa định dạng
df_final['Review'] = pd.to_numeric(df_final['Review'], errors='coerce')


# In[229]:


# Từ điển các quốc gia và châu lục
continent_dict = {
    'Afghanistan': 'Asia',
    'Albania': 'Europe',
    'Algeria': 'Africa',
    'Andorra': 'Europe',
    'Angola': 'Africa',
    'Antigua and Barbuda': 'North America',
    'Argentina': 'South America',
    'Armenia': 'Asia',
    'Australia': 'Oceania',
    'Austria': 'Europe',
    'Azerbaijan': 'Asia',
    'American Samoa': 'Oceania',
    'Bahamas': 'North America',
    'Bahrain': 'Asia',
    'Bangladesh': 'Asia',
    'Barbados': 'North America',
    'Belarus': 'Europe',
    'Belgium': 'Europe',
    'Belize': 'North America',
    'Benin': 'Africa',
    'Bhutan': 'Asia',
    'Bolivia': 'South America',
    'Bosnia and Herzegovina': 'Europe',
    'Botswana': 'Africa',
    'Brazil': 'South America',
    'Brunei': 'Asia',
    'Bulgaria': 'Europe',
    'Burkina Faso': 'Africa',
    'Burundi': 'Africa',
    'Cabo Verde': 'Africa',
    'Cambodia': 'Asia',
    'Cameroon': 'Africa',
    'Canada': 'North America',
    'Central African Republic': 'Africa',
    'Chad': 'Africa',
    'Chile': 'South America',
    'China': 'Asia',
    'Colombia': 'South America',
    'Comoros': 'Africa',
    'Congo, Democratic Republic of the': 'Africa',
    'Congo, Republic of the': 'Africa',
    'Costa Rica': 'North America',
    'Croatia': 'Europe',
    'Cuba': 'North America',
    'Cyprus': 'Asia',
    'Czech Republic': 'Europe',
    'Denmark': 'Europe',
    'Djibouti': 'Africa',
    'Dominica': 'North America',
    'Dominican Republic': 'North America',
    'Ecuador': 'South America',
    'Egypt': 'Africa',
    'El Salvador': 'North America',
    'Equatorial Guinea': 'Africa',
    'Eritrea': 'Africa',
    'Estonia': 'Europe',
    'Eswatini': 'Africa',
    'Ethiopia': 'Africa',
    'Fiji': 'Oceania',
    'Finland': 'Europe',
    'France': 'Europe',
    'Gabon': 'Africa',
    'Gambia': 'Africa',
    'Georgia': 'Asia',
    'Germany': 'Europe',
    'Ghana': 'Africa',
    'Greece': 'Europe',
    'Grenada': 'North America',
    'Guatemala': 'North America',
    'Guinea': 'Africa',
    'Guinea-Bissau': 'Africa',
    'Guyana': 'South America',
    'Haiti': 'North America',
    'Honduras': 'North America',
    'Hungary': 'Europe',
    'Hong Kong': 'Asia',
    'Iceland': 'Europe',
    'India': 'Asia',
    'Indonesia': 'Asia',
    'Iran': 'Asia',
    'Iraq': 'Asia',
    'Ireland': 'Europe',
    'Israel': 'Asia',
    'Italy': 'Europe',
    'Jamaica': 'North America',
    'Japan': 'Asia',
    'Jordan': 'Asia',
    'Kazakhstan': 'Asia',
    'Kenya': 'Africa',
    'Kiribati': 'Oceania',
    'Korea, North': 'Asia',
    'Korea, South': 'Asia',
    'Korea':'Asia',
    'Kosovo': 'Europe',
    'Kuwait': 'Asia',
    'Kyrgyzstan': 'Asia',
    'Laos': 'Asia',
    'Latvia': 'Europe',
    'Lebanon': 'Asia',
    'Lesotho': 'Africa',
    'Liberia': 'Africa',
    'Libya': 'Africa',
    'Liechtenstein': 'Europe',
    'Lithuania': 'Europe',
    'Luxembourg': 'Europe',
    'Madagascar': 'Africa',
    'Malawi': 'Africa',
    'Malaysia': 'Asia',
    'Maldives': 'Asia',
    'Mali': 'Africa',
    'Malta': 'Europe',
    'Marshall Islands': 'Oceania',
    'Mauritania': 'Africa',
    'Mauritius': 'Africa',
    'Mexico': 'North America',
    'Micronesia': 'Oceania',
    'Moldova': 'Europe',
    'Monaco': 'Europe',
    'Mongolia': 'Asia',
    'Montenegro': 'Europe',
    'Morocco': 'Africa',
    'Mozambique': 'Africa',
    'Myanmar': 'Asia',
    'Namibia': 'Africa',
    'Nauru': 'Oceania',
    'Nepal': 'Asia',
    'Netherlands': 'Europe',
    'New Zealand': 'Oceania',
    'Nicaragua': 'North America',
    'Niger': 'Africa',
    'Nigeria': 'Africa',
    'North Macedonia': 'Europe',
    'Norway': 'Europe',
    'Oman': 'Asia',
    'Pakistan': 'Asia',
    'Palau': 'Oceania',
    'Palestine': 'Asia',
    'Panama': 'North America',
    'Papua New Guinea': 'Oceania',
    'Paraguay': 'South America',
    'Peru': 'South America',
    'Philippines': 'Asia',
    'Poland': 'Europe',
    'Portugal': 'Europe',
    'Qatar': 'Asia',
    'Romania': 'Europe',
    'Russia': 'Europe',
    'Rwanda': 'Africa',
    'Saint Kitts and Nevis': 'North America',
    'Saint Lucia': 'North America',
    'Saint Vincent and the Grenadines': 'North America',
    'Samoa': 'Oceania',
    'San Marino': 'Europe',
    'Sao Tome and Principe': 'Africa',
    'Saudi Arabia': 'Asia',
    'Senegal': 'Africa',
    'Serbia': 'Europe',
    'Seychelles': 'Africa',
    'Sierra Leone': 'Africa',
    'Singapore': 'Asia',
    'Slovakia': 'Europe',
    'Slovenia': 'Europe',
    'Solomon Islands': 'Oceania',
    'Somalia': 'Africa',
    'South Africa': 'Africa',
    'South Sudan': 'Africa',
    'Spain': 'Europe',
    'Sri Lanka': 'Asia',
    'Sudan': 'Africa',
    'Suriname': 'South America',
    'Sweden': 'Europe',
    'Switzerland': 'Europe',
    'Syria': 'Asia',
    'Taiwan': 'Asia',
    'Tajikistan': 'Asia',
    'Tanzania': 'Africa',
    'Thailand': 'Asia',
    'Timor-Leste': 'Asia',
    'Togo': 'Africa',
    'Tonga': 'Oceania',
    'Trinidad and Tobago': 'North America',
    'Tunisia': 'Africa',
    'Turkey': 'Asia',
    'Turkmenistan': 'Asia',
    'Tuvalu': 'Oceania',
    'Uganda': 'Africa',
    'Ukraine': 'Europe',
    'United Arab Emirates': 'Asia',
    'United Kingdom': 'Europe',
    'United States': 'North America',
    'Uruguay': 'South America',
    'Uzbekistan': 'Asia',
    'Vanuatu': 'Oceania',
    'Vatican City': 'Europe',
    'Venezuela': 'South America',
    'Vietnam': 'Asia',
    'Yemen': 'Asia',
    'Zambia': 'Africa',
    'Zimbabwe': 'Africa'
}

# Thêm cột châu lục vào DataFrame
df_final['Continent'] = df_final['Country_of_Origin'].map(continent_dict)


# In[230]:


# Định nghĩa các khoảng khối lượng (theo ounces)
bins = [0, 16, 320, 800, 2400, float('inf')]

# Định nghĩa nhãn cho các khoảng khối lượng
labels = ['Small standard-size', 'Large standard-size', 'Large bulky', 'Extra-large', 'Extra-large 150+ lb']

# Thêm cột ProductSizeTier vào DataFrame df_final
df_final['ProductSizeTier'] = pd.cut(df_final['Item_Weight'], bins=bins, labels=labels, right=False)

# Định nghĩa các category cho cột ProductSizeTier
categories = pd.CategoricalDtype(categories=labels, ordered=True)

# Chuyển đổi cột ProductSizeTier sang dạng categorical với các category đã được định nghĩa
df_final['ProductSizeTier'] = df_final['ProductSizeTier'].astype(categories)

# Thêm giá trị "Undefined" vào cột ProductSizeTier nếu không có giá trị cụ thể
df_final['ProductSizeTier'] = df_final['ProductSizeTier'].cat.add_categories(['Undefined']).fillna('Undefined')


# In[231]:


import pandas as pd

# Chuyển cột Price_x sang kiểu số, nếu có lỗi sẽ chuyển thành NaN
df_final['Price_x'] = pd.to_numeric(df_final['Price_x'], errors='coerce')

# Bạn có thể xóa các dòng có giá trị NaN trong cột 'Price_x' nếu cần
# df_final = df_final.dropna(subset=['Price_x'])

# Định nghĩa các bin và nhãn
bins = [0, 10, 50, 150, 500, float('inf')]
labels = ['Very Low Income', 'Low Income', 'Lower-Middle Income', 'Upper-Middle Income', 'High Income']

# Thêm cột PriceGroup vào dataframe dựa trên các bin và nhãn
df_final['PriceGroup'] = pd.cut(df_final['Price_x'], bins=bins, labels=labels, right=False)


# In[232]:


import pandas as pd
import datetime

# Hàm để chuyển đổi chuỗi ngày tháng sang định dạng ngày tháng
def convert_to_date(date_value):
    # Kiểm tra nếu là None, NaN hoặc không phải chuỗi
    if pd.isna(date_value) or not isinstance(date_value, str):
        return None
    
    try:
        # Chuyển đổi chuỗi thành định dạng ngày tháng
        date_object = datetime.datetime.strptime(date_value, '%B %d, %Y').date()
        return date_object
    except ValueError:
        # Thử các định dạng khác nếu định dạng đầu tiên không phù hợp
        try:
            date_object = datetime.datetime.strptime(date_value, '%b %d, %Y').date()
            return date_object
        except ValueError:
            try:
                date_object = datetime.datetime.strptime(date_value, '%m/%d/%Y').date()
                return date_object
            except ValueError:
                return None

# Đảm bảo chỉ chuyển đổi các giá trị chuỗi
df_final['Date_First_Available'] = df_final['Date_First_Available'].apply(convert_to_date)
# Chuyển đổi cột thành kiểu datetime với `errors='coerce'` để thay thế các giá trị không hợp lệ bằng NaT
df_final['Date_First_Available'] = pd.to_datetime(df_final['Date_First_Available'], errors='coerce')


# In[234]:


df_final.rename(columns={'Price_y': 'PriceDetail'}, inplace=True)


# In[235]:


df_final['Color'] = df_final['Color'].fillna('Tone Free')


# In[237]:


df_final.drop(columns={'PriceDetail','Item_Model_Number'})


# In[240]:


df_final.to_csv("stg_amz.csv")


# In[246]:


def save_olap_csv(df_final, output_dir='./csv_output'):
    import os
    os.makedirs(output_dir, exist_ok=True)
    df_final = df_final.dropna(subset= 'ASIN')
    # dim_product
    dim_product = df_final[['ASIN', 'Product Name', 'Image URL', 'Color','Description']].drop_duplicates().rename(columns={
        'Product Name': 'Product_Name',
        'Image URL': 'Image_URL'
    })
    dim_product.to_csv(f'{output_dir}/dim_product.csv', index=False)

    # dim_ratings
    dim_ratings = df_final[['ASIN', 'Rating', 'Review', '5-star', '4-star', '3-star', '2-star', '1-star']].drop_duplicates().rename(columns={
        'Rating': 'Overall_Rating',
        'Review': 'Review_Count',
        '5-star': '5Star',
        '4-star': '4Star',
        '3-star': '3Star',
        '2-star': '2Star',
        '1-star': '1Star'
    })
    dim_ratings.to_csv(f'{output_dir}/dim_ratings.csv', index=False)

    # dim_measurements
    dim_measurements = df_final[['ASIN', 'Item_Weight', 'volume_cm3','ProductSizeTier']].drop_duplicates().rename(columns={
        'Item_Weight': 'Weight',
        'volume_cm3': 'Volumn'
    })
    dim_measurements.to_csv(f'{output_dir}/dim_measurements.csv', index=False)

    # dim_category
    dim_category = df_final[['Sub Department']].drop_duplicates().rename(columns={'Sub Department': 'Category'})
    dim_category['CategoryID'] = range(1, len(dim_category) + 1)
    dim_category.to_csv(f'{output_dir}/dim_category.csv', index=False)

    # dim_date
    dim_date = df_final[['Date_First_Available']].drop_duplicates().rename(columns={'Date_First_Available': 'Date'})
    # Loại bỏ các dòng có giá trị NaT (NaN trong datetime)
    dim_date = dim_date.dropna(subset=['Date'])
    # Thêm cột year, quarter, month, day
    dim_date['year'] = dim_date['Date'].dt.year.astype(int)  # Sửa lỗi tại đây
    dim_date['quarter'] = dim_date['Date'].dt.quarter.astype(int)
    dim_date['month'] = dim_date['Date'].dt.month.astype(int)
    dim_date['day'] = dim_date['Date'].dt.day.astype(int)
    dim_date['dateId'] = range(1, len(dim_date) + 1)
    dim_date.to_csv(f'{output_dir}/dim_date.csv', index=False)

    # dim_geolocation
    dim_geolocation = df_final[['Country_of_Origin', 'Continent']].drop_duplicates().rename(columns={
        'Country_of_Origin': 'CountryOfOrigin'
    })
    dim_geolocation = dim_geolocation.dropna(subset=['CountryOfOrigin'])
    dim_geolocation['locationID'] = range(1, len(dim_geolocation) + 1)
    dim_geolocation.to_csv(f'{output_dir}/dim_geolocation.csv', index=False)

    # dim_manufacturer
    dim_manufacturer = df_final[['Manufacturer']].drop_duplicates()
    dim_manufacturer = dim_manufacturer.dropna(subset=['Manufacturer'])
    dim_manufacturer['manufacturerID'] = range(1, len(dim_manufacturer) + 1)
    dim_manufacturer.to_csv(f'{output_dir}/dim_manufacturer.csv', index=False)

    # dim_brand
    dim_brand = df_final[['Store']].drop_duplicates().rename(columns={'Store': 'Brand'})
    dim_brand = dim_brand.dropna(subset='Brand')
    dim_brand['brandID'] = range(1, len(dim_brand) + 1)
    dim_brand.to_csv(f'{output_dir}/dim_brand.csv', index=False)

    # dim_product_category
    category_map = dict(zip(dim_category['Category'], dim_category['CategoryID']))
    dim_product_category = df_final[['ASIN', 'Sub Department']].drop_duplicates()
    dim_product_category['CategoryID'] = dim_product_category['Sub Department'].map(category_map)
    dim_product_category = dim_product_category[['ASIN', 'CategoryID']].dropna().astype({'CategoryID': 'int'})
    dim_product_category.to_csv(f'{output_dir}/dim_product_category.csv', index=False)

    # mapping
    date_map = dict(zip(dim_date['Date'], dim_date['dateId']))
    location_map = dict(zip(df_final['Country_of_Origin'], dim_geolocation['locationID']))
    manufacturer_map = dict(zip(dim_manufacturer['Manufacturer'], dim_manufacturer['manufacturerID']))
    brand_map = dict(zip(dim_brand['Brand'], dim_brand['brandID']))

    # fact_product_overview
    fact_product_overview = df_final[['ASIN', 'Sub Department', 'Country_of_Origin', 'Continent', 'Store', 'Manufacturer', 'Date_First_Available']].copy()
    fact_product_overview['CategoryID'] = fact_product_overview['Sub Department'].map(category_map)
    fact_product_overview['dateId'] = fact_product_overview['Date_First_Available'].map(date_map)
    fact_product_overview['locationID'] = (fact_product_overview['Country_of_Origin']).map(location_map)
    fact_product_overview['brandID'] = fact_product_overview['Store'].map(brand_map)
    fact_product_overview['manufacturerID'] = fact_product_overview['Manufacturer'].map(manufacturer_map)
    fact_product_overview = fact_product_overview[['ASIN', 'locationID', 'CategoryID', 'brandID', 'manufacturerID', 'dateId']]
    fact_product_overview.to_csv(f'{output_dir}/fact_product_overview.csv', index=False)


    # fact_sale
    fact_sale = df_final[['ASIN', 'Price_x', 'Sub Department', 'Country_of_Origin', 'Continent', 'Store', 'Manufacturer', 'Date_First_Available']].copy()
    fact_sale['discount_percentage'] = 0.0
    fact_sale['price_before_discount'] = fact_sale['Price_x']
    fact_sale['price'] = fact_sale['Price_x']
    fact_sale['CategoryID'] = fact_sale['Sub Department'].map(category_map)
    fact_sale['dateId'] = fact_sale['Date_First_Available'].map(date_map)
    fact_sale['locationID'] = (fact_sale['Country_of_Origin'] + '_' + fact_sale['Continent']).map(location_map)
    fact_sale['brandID'] = fact_sale['Store'].map(brand_map)
    fact_sale['manufacturerID'] = fact_sale['Manufacturer'].map(manufacturer_map)
    fact_sale = fact_sale[['ASIN', 'price_before_discount', 'discount_percentage', 'price', 'locationID', 'CategoryID', 'brandID', 'dateId', 'manufacturerID']]
    fact_sale.to_csv(f'{output_dir}/fact_sale.csv', index=False)

    # fact_customer_experience
    fact_customer_experience = df_final[['ASIN', 'Date_First_Available', 'Sub Department', 'Main Ranking Value', 'Price_x','Amazon_Global_Shipping', 'Estimated_Import_Charges','PriceGroup','Day Delivered']].copy()
    fact_customer_experience['dateId'] = fact_customer_experience['Date_First_Available'].map(date_map)
    fact_customer_experience['price'] = fact_customer_experience['Price_x']
    fact_customer_experience['CategoryID'] = fact_customer_experience['Sub Department'].map(category_map)
    fact_customer_experience['delivery_time_days'] = fact_customer_experience['Day Delivered']
    fact_customer_experience = fact_customer_experience.rename(columns={
        'Main Ranking Value': 'MainRankingValue',
        'Amazon_Global_Shipping': 'AmazonGlobal_Shipping',
        'Estimated_Import_Charges': 'Estimated_Import_Charge'
    })
    fact_customer_experience = fact_customer_experience[['ASIN', 'dateId', 'CategoryID', 'MainRankingValue', 'dateId','AmazonGlobal_Shipping', 'Estimated_Import_Charge','PriceGroup']]
    fact_customer_experience.to_csv(f'{output_dir}/fact_customer_experience.csv', index=False)

    print(f"✅ Saved all dimension + fact tables into CSV at: {output_dir}")
save_olap_csv(df_final)

