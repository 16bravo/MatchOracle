from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import pandas as pd
from datetime import datetime
from dateutil import parser
import sys

def convert_date(date_str):
    try:
        dt = parser.parse(date_str)
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        return None

chrome_driver_path = '/usr/local/bin/chromedriver'
chrome_service = Service(chrome_driver_path)

chrome_options = Options()
options = [
    "--headless",
    "--disable-gpu",
    "--window-size=922,900",
    "--ignore-certificate-errors",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-dev-shm-usage"
]
for option in options:
    chrome_options.add_argument(option)

driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

url = 'https://www.eloratings.net/fixtures'

driver.get(url)
wait = WebDriverWait(driver, 10)
table_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'maintable')))
html_content = driver.page_source
driver.quit()
soup = BeautifulSoup(html_content, 'html.parser')
table = soup.find('div', class_='maintable')

date = []
team1 = []
team2 = []
tournament = []
country = []

for row in table.find_all('div', class_='slick-row'):
    date_text = row.find('div', class_='l0').get_text(separator='<br>').strip()
    date_text = date_text.replace("<br>", " ")
    date_obj = convert_date(date_text)
    date_obj = datetime.strptime(date_obj, "%d/%m/%Y")
    date.append(date_obj)

    match_text = row.find('div', class_='l1').get_text(separator='<br>').strip()
    match_list = match_text.split('<br>')
    team1.append(match_list[0])
    team2.append(match_list[1] if len(match_list) > 1 else '')

    tournament_text = row.find('div', class_='l2').get_text(separator='<br>').strip()
    tournament_text = tournament_text.replace("<br> & <br>", " and ")
    tournament_list = tournament_text.split('<br>')
    tournament.append(tournament_list[0])
    country.append(tournament_list[1] if len(tournament_list) > 1 else '')

df = pd.DataFrame({
    'date': date,
    'home_team': team1,
    'away_team': team2,
    'tournament': tournament,
    'country': country
})

# to replace with equivalence dataset

df['home_team'] = df['home_team'].str.replace(r'São Tomé & Príncipe', 'São Tomé and Príncipe')
df['home_team'] = df['home_team'].str.replace(r'Bosnia/Herzeg', 'Bosnia and Herzegovina')
df['home_team'] = df['home_team'].str.replace(r'Turks and Caicos', 'Turks and Caicos Islands')
df['home_team'] = df['home_team'].str.replace(r'Central African Rep', 'Central African Republic')
df['home_team'] = df['home_team'].str.replace(r'St Vincent/Gren', 'St Vincent & Grenadines')
df['home_team'] = df['home_team'].str.replace(r'Bosnia & Herzegovina', 'Bosnia and Herzegovina')

df['away_team'] = df['away_team'].str.replace(r'São Tomé & Príncipe', 'São Tomé and Príncipe')
df['away_team'] = df['away_team'].str.replace(r'Bosnia/Herzeg', 'Bosnia and Herzegovina')
df['away_team'] = df['away_team'].str.replace(r'Turks and Caicos', 'Turks and Caicos Islands')
df['away_team'] = df['away_team'].str.replace(r'Central African Rep', 'Central African Republic')
df['away_team'] = df['away_team'].str.replace(r'St Vincent/Gren', 'St Vincent & Grenadines')
df['away_team'] = df['away_team'].str.replace(r'Bosnia & Herzegovina', 'Bosnia and Herzegovina')

df['country'] = df['country'].str.replace(r'^(in the |in )', '', regex=True)
df['country'] = df['country'].str.replace(r'UAE', 'United Arab Emirates')
df['country'] = df['country'].str.replace(r'US Virgin Isl', 'US Virgin Islands')
df['country'] = df['country'].str.replace(r'Bosnia/Herzeg', 'Bosnia and Herzegovina')
df['country'] = df['country'].str.replace(r'Br Virgin Islands', 'British Virgin Islands')
df['country'] = df['country'].str.replace(r'Turks and Caicos', 'Turks and Caicos Islands')
df['country'] = df['country'].str.replace(r'The Gambia', 'Gambia')
df['country'] = df['country'].str.replace(r'Central African Rep', 'Central African Republic')
df['country'] = df['country'].str.replace(r'São Tomé/Príncipe', 'São Tomé and Príncipe')
df['country'] = df['country'].str.replace(r'Antigua & Barbuda', 'Antigua and Barbuda')
df['country'] = df['country'].str.replace(r'Trinidad & Tobago', 'Trinidad and Tobago')
df['country'] = df['country'].str.replace(r'St Vincent/Gren', 'St Vincent & Grenadines')

df['neutral'] = (df['home_team'] != df['country'])
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
df = df.sort_values(by='date')

df.to_csv('data/source/fixtures.csv', index=False)
