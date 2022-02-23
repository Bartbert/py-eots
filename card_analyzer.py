import pandas as pd
import enums
from bs4 import BeautifulSoup
import mechanize
import http.cookiejar as cj


def load_card_data(player: enums.Player):
    file_name = 'data/allied_deck.csv' if player == enums.Player.ALLIES else 'data/japan_deck.csv'

    return pd.read_csv(file_name)


def retrieve_discards(user_name, pw, game_name):
    jar = cj.CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(jar)
    br.open('http://acts.warhorsesim.com/login.asp')
    br.select_form(nr=0)
    br.form['alias'] = user_name
    br.form['password'] = pw
    br.submit()

    for link in br.links():
        if link.url == 'myGames.asp?moduleID=19':
            print(link)
            br.follow_link(link)
            break

    for link in br.links():
        if link.text == game_name:
            print(link)
            br.follow_link(link)
            break

    for link in br.links():
        if link.url == 'discardsAll.asp':
            print(link)
            br.follow_link(link)
            break

    soup = BeautifulSoup(br.response().read(), 'html.parser')
    card_list = []

    table_list = soup.find_all('table', border='0', cellpadding='3', width='100%')

    for i in range(len(table_list)):
        table = table_list[i]

        for x in table.find_all('td', class_='textcenter', width='10%'):
            card = {'player_id': i, 'card_id': int(x.text)}
            card_list.append(card)

    return card_list


class CardAnalyzer:
    def __init__(self):
        self.allied_card_data = load_card_data(enums.Player.ALLIES)
        self.japan_card_data = load_card_data(enums.Player.JAPAN)

    def analyze_card_deck(self, user_name, pw, game_name, deck_type: enums.DeckType):

        discard_list = retrieve_discards(user_name, pw, game_name)

        result_allies = self.analyze_allies_card_deck(deck_type, discard_list)

        result_japan = self.analyze_japan_card_deck(deck_type, discard_list)

        return [result_allies, result_japan]

    def analyze_allies_card_deck(self, deck_type: enums.DeckType, discard_list):
        deck_df = self.allied_card_data

        if deck_type == enums.DeckType.SOUTH_PACIFIC:
            deck_df = deck_df.loc[deck_df['south_pacific'] == 'Y']

        discard_ids = []
        for card in discard_list:
            if card.get('player_id') == 1:
                discard_ids.append(card.get('card_id'))

        deck_df = deck_df.loc[~deck_df['card_id'].isin(discard_ids)]

        deck_attributes = self.deck_attribute_counts(deck_df)

        return deck_attributes

    def analyze_japan_card_deck(self, deck_type: enums.DeckType, discard_list):
        deck_df = self.japan_card_data

        if deck_type == enums.DeckType.SOUTH_PACIFIC:
            deck_df = deck_df.loc[deck_df['south_pacific'] == 'Y']

        discard_ids = []
        for card in discard_list:
            if card.get('player_id') == 0:
                discard_ids.append(card.get('card_id'))

        deck_df = deck_df.loc[~deck_df['card_id'].isin(discard_ids)]

        deck_attributes = self.deck_attribute_counts(deck_df)

        return deck_attributes

    def deck_attribute_counts(self, deck_df: pd.DataFrame):
        result = []

        item = {'attribute': '1 OP', 'count': len(deck_df.loc[deck_df['ops_value'] == 1])}
        result.append(item)

        item = {'attribute': '2 OP', 'count': len(deck_df.loc[deck_df['ops_value'] == 2])}
        result.append(item)

        item = {'attribute': '3 OP', 'count': len(deck_df.loc[deck_df['ops_value'] == 3])}
        result.append(item)

        item = {'attribute': 'Card Draw', 'count': len(deck_df.loc[deck_df['draw_card'] == 'Y'])}
        result.append(item)

        item = {'attribute': 'PW', 'count': len(deck_df.loc[deck_df['pw_change'] > 0])}
        result.append(item)

        item = {'attribute': 'ISR Ender', 'count': len(deck_df.loc[deck_df['isr_end'] == 'Y'])}
        result.append(item)

        item = {'attribute': 'ISR Starter', 'count': len(deck_df.loc[deck_df['isr_start'] == 'Y'])}
        result.append(item)

        item = {'attribute': 'Intel Change', 'count': len(deck_df.loc[~deck_df['intel_status'].isna()])}
        result.append(item)

        item = {'attribute': 'Logistics 4+', 'count': len(deck_df.loc[deck_df['logistics_value'] > 3])}
        result.append(item)

        item = {'attribute': 'WIE', 'count': len(deck_df.loc[~deck_df['wie_level'].isna()])}
        result.append(item)

        item = {'attribute': 'Sub', 'count': len(deck_df.loc[deck_df['sub'] > 0])}
        result.append(item)

        item = {'attribute': 'Weather', 'count': len(deck_df.loc[deck_df['weather'] == 'Y'])}
        result.append(item)

        item = {'attribute': 'Kamikaze', 'count': len(deck_df.loc[deck_df['kamikaze'] == 'Y'])}
        result.append(item)

        return result
