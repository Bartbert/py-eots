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


def deck_attribute_counts(deck_df: pd.DataFrame):
    result = []

    item = {'attribute': '1 OP', 'count': len(deck_df.loc[deck_df['ops_value'] == 1]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': '2 OP', 'count': len(deck_df.loc[deck_df['ops_value'] == 2]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': '3 OP', 'count': len(deck_df.loc[deck_df['ops_value'] == 3]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'Card Draw', 'count': len(deck_df.loc[deck_df['draw_card'] == 'Y']), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'PW', 'count': len(deck_df.loc[deck_df['pw_change'] > 0]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'ISR Ender', 'count': len(deck_df.loc[deck_df['isr_end'] == 'Y']), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'ISR Starter', 'count': len(deck_df.loc[deck_df['isr_start'] == 'Y']), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'Intel Change', 'count': len(deck_df.loc[~deck_df['intel_status'].isna()]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'Logistics 4+', 'count': len(deck_df.loc[deck_df['logistics_value'] > 3]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'WIE', 'count': len(deck_df.loc[~deck_df['wie_level'].isna()]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'Sub', 'count': len(deck_df.loc[deck_df['sub'] > 0]), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'Weather', 'count': len(deck_df.loc[deck_df['weather'] == 'Y']), 'probability': 0.0}
    result.append(item)

    item = {'attribute': 'Kamikaze', 'count': len(deck_df.loc[deck_df['kamikaze'] == 'Y']), 'probability': 0.0}
    result.append(item)

    return result


def calculate_probability(deck_count: int, attribute_count: int, draw_count: int):
    if attribute_count == 0:
        return 0.0

    probability = 1.0
    for i in range(draw_count):
        probability *= (1 - (attribute_count / deck_count))
        deck_count -= 1

    return 1 - probability


class CardAnalyzer:
    def __init__(self):
        self.allied_card_data = load_card_data(enums.Player.ALLIES)
        self.japan_card_data = load_card_data(enums.Player.JAPAN)

    def analyze_card_deck(self, user_name, pw, game_name, deck_type: enums.DeckType,
                          allies_draw_count: int, japan_draw_count: int):

        discard_list = retrieve_discards(user_name, pw, game_name)

        result_allies = self.analyze_allies_card_deck(deck_type=deck_type,
                                                      draw_count=allies_draw_count, discard_list=discard_list)

        result_japan = self.analyze_japan_card_deck(deck_type=deck_type,
                                                    draw_count=japan_draw_count, discard_list=discard_list)

        return [result_allies, result_japan]

    def analyze_allies_card_deck(self, deck_type: enums.DeckType, draw_count: int, discard_list):
        deck_df = self.allied_card_data

        if deck_type == enums.DeckType.SOUTH_PACIFIC:
            deck_df = deck_df.loc[deck_df['south_pacific'] == 'Y']

        discard_ids = []
        for card in discard_list:
            if card.get('player_id') == 1:
                discard_ids.append(card.get('card_id'))

        deck_df = deck_df.loc[~deck_df['card_id'].isin(discard_ids)]

        deck_attributes = deck_attribute_counts(deck_df)

        for attribute in deck_attributes:
            probability = calculate_probability(deck_count=len(deck_df),
                                                attribute_count=attribute.get('count'), draw_count=draw_count)

            attribute.update({'probability': probability})

        result_df = pd.DataFrame(data=deck_attributes)
        result_df = result_df.loc[~result_df['attribute'].isin(['Weather', 'Kamikaze'])]

        return result_df

    def analyze_japan_card_deck(self, deck_type: enums.DeckType, draw_count: int, discard_list):
        deck_df = self.japan_card_data

        if deck_type == enums.DeckType.SOUTH_PACIFIC:
            deck_df = deck_df.loc[deck_df['south_pacific'] == 'Y']

        discard_ids = []
        for card in discard_list:
            if card.get('player_id') == 0:
                discard_ids.append(card.get('card_id'))

        deck_df = deck_df.loc[~deck_df['card_id'].isin(discard_ids)]

        deck_attributes = deck_attribute_counts(deck_df)

        for attribute in deck_attributes:
            probability = calculate_probability(deck_count=len(deck_df),
                                                attribute_count=attribute.get('count'), draw_count=draw_count)

            attribute.update({'probability': probability})

        result_df = pd.DataFrame(data=deck_attributes)

        return result_df
