from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeDriverManager
from bs4 import BeautifulSoup
import csv
import time
from fake_useragent import UserAgent

# Setup fake user agent
ua = UserAgent()
user_agent = ua.random

# Setup Selenium WebDriver with fake user agent for Microsoft Edge using EdgeDriverManager
edge_options = Options()
edge_options.add_argument(f"user-agent={user_agent}")

# Use EdgeDriverManager to install the Edge WebDriver
service = EdgeService(EdgeDriverManager().install())

# Create the WebDriver instance using the service and options
driver = webdriver.Edge(service=service, options=edge_options)

# Open the URL
url = "https://www.amazon.com/PerkHomy-Natural-Wrapping-Gardening-Knitting/dp/B0BCK98LLG/ref=sr_1_4?dib=eyJ2IjoiMSJ9.lqV4Fcnz2wuZNjGn5xTpmXQIvu0BFCYF3Fv0O48uFGirrjWcJvMBNBIjXS4zd34Y2qRVEvu64GxClNp-byxr_ng5Lm9iGXV3R8NLWH5jd4p54FlErXFpFHRrZ9rVwbR1ZxjezP45mRYIA-TPP_i4Ag7zN2isb1Ti2leKRVWrcl4rew2WQZwUddjj65cD-AMwD-M50QncWH8rNFhObx5_KO8lYY5_QMa5vssY_QaoImtOKGyr5N8uUDlQDcZjSHpRwOB9BAHkhbFesuP6ocA1o3RtmlDiU700qW5e88QRtZs.X-iDefFc4xpcFq81mPkPywNkQKNLNPbfKkqtf3rTPdw&dib_tag=se&qid=1744139337&s=automotive-intl-ship&sr=1-4&th=1"
driver.get(url)

# Wait for the page to load
time.sleep(3)

# Get the page source and parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Find the elements containing the rating percentages
ratings_data = soup.find_all('a', {'class': '_cr-ratings-histogram_style_histogram-row-container__Vh7Di'})

# Create a dictionary to store the rating percentages
rating_percentages = {}

# Extract percentage values for each star rating
for rating in ratings_data:
    label = rating.get('aria-label')
    if label:
        # Extract the star rating and percentage
        if "5 stars" in label:
            rating_percentages['5-star'] = label.split('(')[1].split(')')[0].strip()
        elif "4 stars" in label:
            rating_percentages['4-star'] = label.split('(')[1].split(')')[0].strip()
        elif "3 stars" in label:
            rating_percentages['3-star'] = label.split('(')[1].split(')')[0].strip()
        elif "2 stars" in label:
            rating_percentages['2-star'] = label.split('(')[1].split(')')[0].strip()
        elif "1 star" in label:
            rating_percentages['1-star'] = label.split('(')[1].split(')')[0].strip()

# Save the data to a CSV file
header = ['Star Rating', 'Percentage']
rows = [(key, value) for key, value in rating_percentages.items()]

with open('review_percentages.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(rows)

# Close the driver
driver.quit()

print("CSV file with review percentages saved successfully.")
