from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
from fake_useragent import UserAgent

# Setup fake user agent
ua = UserAgent()
user_agent = ua.random

# Setup Selenium WebDriver with fake user agent for Google Chrome using ChromeDriverManager
chrome_options = Options()
chrome_options.add_argument(f"user-agent={user_agent}")

# Use ChromeDriverManager to install the Chrome WebDriver
service = ChromeService(ChromeDriverManager().install())

# Create the WebDriver instance using the service and options
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the URL
url = "https://www.amazon.com/PerkHomy-Natural-Wrapping-Gardening-Knitting/dp/B0BCK98LLG/ref=sr_1_4?dib=eyJ2IjoiMSJ9.lqV4Fcnz2wuZNjGn5xTpmXQIvu0BFCYF3Fv0O48uFGirrjWcJvMBNBIjXS4zd34Y2qRVEvu64GxClNp-byxr_ng5Lm9iGXV3R8NLWH5jd4p54FlErXFpFHRrZ9rVwbR1ZxjezP45mRYIA-TPP_i4Ag7zN2isb1Ti2leKRVWrcl4rew2WQZwUddjj65cD-AMwD-M50QncWH8rNFhObx5_KO8lYY5_QMa5vssY_QaoImtOKGyr5N8uUDlQDcZjSHpRwOB9BAHkhbFesuP6ocA1o3RtmlDiU700qW5e88QRtZs.X-iDefFc4xpcFq81mPkPywNkQKNLNPbfKkqtf3rTPdw&dib_tag=se&qid=1744139337&s=automotive-intl-ship&sr=1-4&th=1"
driver.get(url)

# Wait for the page to load
time.sleep(5)

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
        try:
            # Directly extract percentage value from the label string
            if "5 stars" in label:
                rating_percentages['5-star'] = label.split(' ')[0]
            elif "4 stars" in label:
                rating_percentages['4-star'] = label.split(' ')[0]
            elif "3 stars" in label:
                rating_percentages['3-star'] = label.split(' ')[0]
            elif "2 stars" in label:
                rating_percentages['2-star'] = label.split(' ')[0]
            elif "1 star" in label:
                rating_percentages['1-star'] = label.split(' ')[0]
        except IndexError:
            # Handle any unexpected errors
            print(f"Error extracting data for label: {label}")

# Check if all ratings are extracted
print(rating_percentages)

# Save the data to a CSV file with columns as 5-star, 4-star, 3-star, etc.
header = ['5-star', '4-star', '3-star', '2-star', '1-star']
rows = [[rating_percentages.get('5-star', '0%'),
         rating_percentages.get('4-star', '0%'),
         rating_percentages.get('3-star', '0%'),
         rating_percentages.get('2-star', '0%'),
         rating_percentages.get('1-star', '0%')]]

with open('review_percentages.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(rows)

# Close the driver
driver.quit()

print("CSV file with review percentages saved successfully.")
