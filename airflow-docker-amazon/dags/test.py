import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import logging
import re

# Hàm crawl dữ liệu đã có sẵn
def scrape_department(url):
    logging.info(f"Scraping data from: {url}")
    scraper = AmazonScraper()
    department = "Your_Department"  # Thay thế với thông tin thực tế
    sub_department = "Your_Sub_Department"  # Thay thế với thông tin thực tế
    scraper.scrape(url, department, sub_department)

# Đọc URL từ CSV
def read_urls_from_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        if 'URL' not in df.columns:
            raise ValueError("CSV file must contain 'URL' column")
        return df['URL'].tolist()  # Trả về danh sách các URL
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        return []

# Đặt các tham số mặc định cho DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Đọc URL từ file CSV
csv_file = '/opt/airflow/csv/src_input/amazon_categories_full copy.csv.csv'
urls = read_urls_from_csv(csv_file)

# Khởi tạo DAG
with DAG(
    'scrape_amazon_dag_test',
    description='Crawl data from Amazon using URLs from CSV',
    schedule_interval=None,
    start_date=datetime(2025, 4, 5),
    catchup=False,
    default_args=default_args
) as dag:

    # Tạo các task cho từng URL trong danh sách từ file CSV
    for index, url in enumerate(urls):
        sanitized_url_name = re.sub(r'[^a-zA-Z0-9_-]', '_', url)  # Làm sạch tên URL để đặt tên task hợp lệ
        task = PythonOperator(
            task_id=f"scrape_task_{sanitized_url_name}_{index}",
            python_callable=scrape_department,
            op_args=[url],  # Truyền URL làm tham số vào hàm scrape_department
            dag=dag,
        )
        task
