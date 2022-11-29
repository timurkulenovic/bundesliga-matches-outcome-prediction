from bs4 import BeautifulSoup as bS
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

s = requests.Session()
BASE_URL = "https://www.betexplorer.com"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}


def selenium_driver(url):
    driver_location = "./chromedriver"

    chrome_options = Options()
    # If you comment the following line, a browser will show ...
    chrome_options.add_argument("--headless")

    # Adding a specific user agent
    chrome_options.add_argument("user-agent=data-science-project")

    driver = webdriver.Chrome(driver_location)
    driver.get(url)

    # Timeout needed for Web page to render (read more about it)
    time.sleep(1)

    return driver


def get_odds(driver):
    all_odds = []
    rnd = 0
    site = bS(driver.page_source, 'html.parser')
    rows = site.find("table", {"class": "table-main h-mb15 js-tablebanner-t js-tablebanner-ntb"}).find_all("tr")
    for row in rows:

        ths = row.find_all("th")
        if len(ths) > 0:
            rnd = int(ths[0].text.split(".")[0])
        elif rnd > 5:

            if not row.find("td", {"class": "h-text-left"}):
                continue

            home, away = row.find("td", {"class": "h-text-left"}).text.split(" - ")

            result = row.find("td", {"class": "h-text-center"}).text.split(":")
            home_goals, away_goals = int(result[0]), int(result[1])

            href = row.find("td", {"class": "h-text-left"}).find("a").get("href")
            driver.get("https://www.betexplorer.com/" + href)
            time.sleep(2)
            match = bS(driver.page_source, 'html.parser')
            pinnacle = match.find("table", {"class": "table-main h-mb15 sortable"}).find("tr", {"data-bid": 16})
            odds = []
            for odd in pinnacle.find_all("td", {"class": "table-main__detail-odds"}):
                odds.append(float(odd.text))
            all_odds.append([rnd, home, away, home_goals, away_goals, *odds])

    return all_odds


def create_df(matches_rows):
    df = pd.DataFrame(matches_rows, columns=['Round', 'Home', 'Away', 'HGoals', 'AGoals', "OddsH", "OddsD", "OddsA"])

    df.to_csv("data/odds_2017_2018.csv")


if __name__ == "__main__":

    start_url = "https://www.betexplorer.com/soccer/germany/bundesliga-2017-2018/results/"
    drvr = selenium_driver(start_url)
    odds_data = get_odds(drvr)
    create_df(odds_data)
    drvr.close()
