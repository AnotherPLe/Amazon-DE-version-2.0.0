import requests
import json
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import logging

# URL của API
url = "https://tiki.vn/api/personalish/v1/blocks/listings?limit=40&include=advertisement&aggregations=2&version=home-persionalized&trackity_id=298f8108-8ed4-62f7-6bc4-961d3bf691ce&category=8322&page=1&urlKey=nha-sach-tiki"

# Các headers cần thiết
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
}

# Hàm lấy dữ liệu từ API và lưu vào CSV
def fetch_data_and_save_to_csv():
    try:
        # Gửi yêu cầu GET đến API
        response = requests.get(url, headers=headers)

        # Kiểm tra trạng thái phản hồi
        if response.status_code == 200:
            # Dữ liệu không được nén, trực tiếp sử dụng dữ liệu phản hồi
            json_data = response.text

            # Chuyển đổi dữ liệu JSON thành Python dictionary
            data = json.loads(json_data)

            # Log dữ liệu trả về để kiểm tra cấu trúc
            logging.info(f"Response data: {json.dumps(data, indent=4)}")

            # Giả sử dữ liệu trả về có một trường 'data' chứa danh sách các sản phẩm
            products = data.get('data', [])

            # Nếu có dữ liệu sản phẩm, lưu vào CSV
            if products:
                # Chuyển đổi danh sách sản phẩm thành DataFrame của pandas
                df = pd.DataFrame(products)

                # Kiểm tra kích thước DataFrame
                logging.info(f"DataFrame shape: {df.shape}")

                # Lưu DataFrame vào file CSV
                output_file = "/opt/airflow/csv/src_output/tiki_data.csv"  # Thử lưu vào thư mục tạm
                df.to_csv(output_file, index=False, encoding='utf-8-sig')

                logging.info(f"Data saved to {output_file}")
            else:
                logging.warning("No products data found in the API response.")
        else:
            logging.error(f"API request failed with status code {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

# Đặt các tham số mặc định cho DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Khởi tạo DAG
with DAG(
    'tiki_api_to_csv_dag',
    description='Fetch data from Tiki API and save it to CSV',
    schedule_interval=None,  # Không lên lịch tự động
    start_date=datetime(2025, 4, 4),
    catchup=False,
    default_args=default_args
) as dag:

    # Tạo task cho việc lấy dữ liệu và lưu vào CSV
    fetch_task = PythonOperator(
        task_id='fetch_and_save_data',
        python_callable=fetch_data_and_save_to_csv,
        dag=dag
    )

    fetch_task
