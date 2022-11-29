from bs4 import BeautifulSoup as bS
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

s = requests.Session()
BASE_URL = "https://uk.soccerway.com"
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


def get_matches_urls(driver):
    m_urls = {}
    for season in [f"{year}/{year+1}" for year in range(2020, 2021)]:
        m_urls[season] = {}
        driver.find_element_by_xpath(f"//select[@id='season_id_selector']/option[text()='{season}']").click()
        time.sleep(2)

        for rnd in range(5, 6):
            if rnd == 14:
                rnd = f'{rnd} *'
            m_urls[season][rnd] = []
            driver.find_element_by_xpath(
                f"//select[@id='page_competition_1_block_competition_matches_summary_10_page_dropdown']/option[text()='{rnd}']").click()
            time.sleep(1.5)
            matches_parsed = bS(driver.page_source, 'html.parser')
            table = matches_parsed.find("table", {"class": "matches"})

            for row in table.find_all("tr", {"class": "match"}):
                href = row.find("td", {"class": "score-time"}).find("a").get("href")
                m_urls[season][rnd].append(href)
            print(season, rnd, m_urls[season][rnd][0])

    return m_urls


def get_possessions(chart):
    possessions = []
    possession_chart = chart.find("div", {"id": "page_chart_1_chart_statsplus_1_chart_possession_1-wrapper"})
    for pie in possession_chart.find_all("div", {"class": "highcharts-pie"}):
        poss = pie.find("div", {"class": "highcharts-data-labels"}).find("span").find("div").text
        possessions.append(int(poss))
    possessions.reverse()
    possession_home, possession_away = possessions
    return possession_home, possession_away


def get_data_from_table(rows, index):
    return rows[index].find("td", {"class": "left"}).text, rows[index].find("td", {"class": "right"}).text


def scrape_matches_data(driver, urls):
    matches_rows = []
    temp = open('temp.txt', 'a')
    for season in urls:
        for rnd in urls[season]:
            print(season, rnd)
            i = 0
            while i < len(urls[season][rnd]):
                href = urls[season][rnd][i]
                print(href)
                driver.get(f"{BASE_URL}{href}")
                time.sleep(1.5)
                match_parsed = bS(driver.page_source, 'html.parser')

                match_info = match_parsed.find("div", {"id": "page_match_1_block_match_info_5"})

                if match_info is None:
                    print("Has to be repeated")
                    continue

                home_team = match_info.find("div", {"class": "container left"}).find("a", {"class": "team-title"}).text
                away_team = match_info.find("div", {"class": "container right"}).find("a", {"class": "team-title"}).text
                date = match_info.find("div", {"class": "details"}).find("a").text
                ko_time = match_info.find("div", {"class": "details"}).find_all("span")[6].text.strip()

                lineups = match_parsed.find("div", {"class": "combined-lineups-container"})
                home_lineups = lineups.find("div", {"class": "container left"}).find("table").find_all("tr")[1:12]
                away_lineups = lineups.find("div", {"class": "container right"}).find("table").find_all("tr")[1:12]

                home_players = "/".join([home_player.find("a").text for home_player in home_lineups])
                away_players = "/".join([away_player.find("a").text for away_player in away_lineups])

                match_id = href.split("/")[-2]

                driver.get(f"{BASE_URL}/charts/statsplus/{match_id}/")
                time.sleep(2)

                chart_parsed = bS(driver.page_source, 'html.parser')

                table_rows = chart_parsed.find("table").find_all("tr")

                print(table_rows)

                goals_home, goals_away = get_data_from_table(table_rows, 1)
                corners_home, corners_away = get_data_from_table(table_rows, 3)
                shots_on_target_home, shots_on_target_away = get_data_from_table(table_rows, 5)
                shots_wide_home, shots_wide_away = get_data_from_table(table_rows, 7)
                fouls_home, fouls_away = get_data_from_table(table_rows, 9)
                offsides_home, offsides_away = get_data_from_table(table_rows, 11)
                possession_home, possession_away = get_possessions(chart_parsed)

                new_row = [season, rnd, home_team, away_team, date, ko_time, home_players,
                           away_players, goals_home, goals_away, corners_home,
                           corners_away, shots_on_target_home, shots_on_target_away,
                           shots_wide_home, shots_wide_away, fouls_home, fouls_away,
                           offsides_home, offsides_away, possession_home, possession_away]

                matches_rows.append(new_row)

                temp.write(','.join([str(el) for el in new_row]) + "\n")

                i += 1

    return matches_rows


def create_df(matches_rows):
    df = pd.DataFrame(matches_rows, columns=['Season', 'Round', 'HomeTeam', 'AwayTeam', 'Date', 'Hour', 'HomeTeamPlayers', 'AwayTeamPlayers',
                                             'GoalsHome', 'GoalsAway', 'CornersHome', 'CornersAway', "ShotsTargetHome", 'ShotsTargetAway',
                                             'ShotsWideHome', 'ShotsWideAway', 'FoulsHome', 'FoulsAway', 'OffsidesHome', 'OffsidesAway',
                                             'HomeTeamPossession', 'AwayTeamPossession'])

    df.to_csv("data/matches_soccerway_2021.csv")


if __name__ == "__main__":

    start_url = "https://uk.soccerway.com/national/germany/bundesliga/20192020/regular-season/r53499/"
    drvr = selenium_driver(start_url)
    matches_urls = get_matches_urls(drvr)
    matches = scrape_matches_data(drvr, matches_urls)
    create_df(matches)
    drvr.close()
