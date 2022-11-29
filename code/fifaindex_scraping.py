from bs4 import BeautifulSoup as bS
import requests
import pandas as pd

s = requests.Session()
BASE_URL = "https://www.fifaindex.com"


def get_basic_data(player_html):
    nat = player_html.find("td", {"data-title": "Nationality"}).find("a").get("title")
    ovr_span, pot_span = player_html.find("td", {"data-title": "OVR / POT"}).find_all("span")
    ovr, pot = int(ovr_span.text), int(pot_span.text)
    name = player_html.find("td", {"data-title": "Name"}).find("a").get("title")[:-8]
    positions = '/'.join([position.text for position in player_html.find("td", {"data-title": "Preferred Positions"}).find_all("a")])
    age = int(player_html.find("td", {"data-title": "Age"}).text)
    team = player_html.find("td", {"data-title": "Team"}).find("a").get("title")[:-8]

    return [name, nat, ovr, pot, positions, age, team]


def get_additional_data(profile):
    row = []

    first_card_body = profile.find("div", {"class": "col-lg-8"}).find("div", {"class": "card mb-5"}).find("div", {"class": "card-body"})
    for j, p in enumerate(first_card_body.find_all("p")):
        if j in [3, 4, 5, 10, 11, 13, 14]:
            continue
        if j in [0, 1]:
            row.append(int(p.find("span", {"class": "data-units-metric"}).text[:-3]))
        if j == 2:
            row.append(p.find("span").text)
        if j == 6:
            row.append(p.find("span").text.replace(" ", ""))
        if j in [7, 8]:
            row.append(len(p.find_all("i", {"class": "fas"})))
        if j in [9, 12]:
            row.append(int(p.find("span", {"class": "float-right"}).text[1:].replace(".", "")))

    other_cards = profile.find("div", {"class": "row grid"}).find_all("p")
    for p in other_cards:
        if p.text.startswith("Composure"):
            continue
        num = p.find("span", {"class": "float-right"})
        if num:
            row.append(int(num.text))

    return row


def scrape_data():
    players = []
    clubs = set()
    for fifa in range(21, 22):
        i = 1
        print(fifa)
        while True:
            print(i)

            url = f"{BASE_URL}/players/fifa{fifa}/{i}/?league=19&order=desc"
            page_html = s.get(url).text
            page_parsed = bS(page_html, 'html.parser')
            table = page_parsed.find("table", {"class": "table table-striped table-players"})

            if table is None:
                break

            for player in table.find("tbody").find_all("tr"):
                if not player.has_attr("data-playerid"):
                    continue

                player_data = [fifa] + get_basic_data(player)
                clubs.add(player.find("td", {"data-title": "Team"}).find("a").get("href"))

                profile_url = f'{BASE_URL}{player.find("td", {"data-title": "Name"}).find("a").get("href")}'
                profile_parsed = bS(s.get(profile_url).text, 'html.parser')

                player_data.extend(get_additional_data(profile_parsed))

                players.append(player_data)

            i += 1

    return players, clubs


def scrape_clubs(clubs):
    clubs_rows = []
    for club in clubs:
        club_row = [club.split("/")[-2][-2:]]
        club_url = f'{BASE_URL}{club}'
        club_parsed = bS(s.get(club_url).text, 'html.parser')

        pl = club_parsed.find("div", {"class": "pl-3"})
        club_row.append(pl.find("h1").text[:-8])
        stars = len(pl.find_all("i", {"class": "fas fa-star fa-lg"})) + 0.5 * len(pl.find_all("i", {"class": "fas fa-star-half-alt fa-lg"}))
        club_row.append(stars)

        main_card = club_parsed.find("div", {"class": "col-lg-8"}).find("div", {"class": "card mb-5"})
        for j, li in enumerate(main_card.find_all("li")[0:5]):
            if j == 4:
                club_row.append(li.find("span").text[1:].replace(".", ""))
            else:
                club_row.append(li.find("span").text)
        clubs_rows.append(club_row)

    return clubs_rows


def create_players_df(players):
    df = pd.DataFrame(players, columns=["FIFA", "Name", "Nationality", "OVR", "POT", "Positions", "Age", "Team",
                                        "Height", "Weight", "Foot", "WorkRate", "WeakFoot", "SkillMoves", "Value", "Wage",
                                        'Ball_Control', 'Dribbling', 'Marking', 'Slide_Tackle', 'Stand_Tackle', 'Aggression',
                                        'Reactions', 'Att._Position', 'Interceptions', 'Vision', 'Crossing',
                                        'Short_Pass', 'Long_Pass', 'Acceleration', 'Stamina', 'Strength', 'Balance', 'Sprint_Speed',
                                        'Agility', 'Jumping', 'Heading', 'Shot_Power', 'Finishing', 'Long_Shots', 'Curve', 'FK_Acc.',
                                        'Penalties', 'Volleys', 'GK_Positioning', 'GK_Diving', 'GK_Handlin', 'GK_Kicking', 'GK_Reflexes'])

    df.to_csv("data/players_fifa.csv")


def create_clubs_df(clubs):
    df = pd.DataFrame(clubs, columns=["Fifa", "Name", "Rating", "RivalTeam", "Attack", "Midfield", "Defence", "TransferBudget"])
    df.to_csv("data/clubs_fifa_2021.csv")


if __name__ == "__main__":

    players_data, clubs_list = scrape_data()
    clubs_data = scrape_clubs(clubs_list)

    create_players_df(players_data)
    create_clubs_df(clubs_data)
