from itertools import pairwise
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd

TFT_TACTICS_URL = 'https://tftactics.gg'

TFT_SET_NUMBER = 11


def get_champions_data() -> list[dict]:
    """
    Récupération des données des champions de TFT
    Returns: dict
    """
    champions = []
    r_champions = requests.get(f'{TFT_TACTICS_URL}/champions/')
    soup_champions = BeautifulSoup(r_champions.content, "lxml")
    champions_list = soup_champions.find("div", {"class": "characters-list"})
    for champion in champions_list.children:
        champion_dict = {'Name': champion.text,
                         'Classes': [],
                         'Origins': []
                         }
        r_champion = requests.get(f'{TFT_TACTICS_URL}{champion["href"]}')
        soup_champion = BeautifulSoup(r_champion.content, "lxml")
        # Récupération des stats du champion
        champion_stats = soup_champion.find("ul", {"class": "stats-list"})
        for champion_stat in champion_stats.children:
            champion_stat_name, champion_stat_value = champion_stat.text.split(':')
            champion_dict[champion_stat_name] = champion_stat_value.strip()
        # Récupération des traits du champion
        champion_traits = soup_champion.find_all("div", {"class": "ability-description-name"})
        for champion_trait in champion_traits:
            for champion_trait_data in pairwise(champion_trait.children):
                if champion_trait_data[1].text == 'Class':
                    champion_dict['Classes'].append(champion_trait_data[0].text)
                elif champion_trait_data[1].text == 'Origin':
                    champion_dict['Origins'].append(champion_trait_data[0].text)
        champion_dict['Classes'] = '/'.join(champion_dict['Classes'])
        champion_dict['Origins'] = '/'.join(champion_dict['Origins'])
        champions.append(champion_dict)
    return champions


def get_traits_data() -> dict:
    """
    Récupération des données des synergies de TFT
    Returns: dict
    """
    traits_dict = {
        'classes': {},
        'origins': {}
    }
    r_classes = requests.get(f'{TFT_TACTICS_URL}/db/classes/')
    soup_classes = BeautifulSoup(r_classes.content, "lxml")
    classes_list = [class_data.text for class_data in soup_classes.find_all("div", {"class": "d-none d-md-block"})]
    classes_bonus_numbers = [tuple(int(classes_bonus_number.text) for classes_bonus_number in
                                   class_bonus_data.find_all("div", {"class": "table-bonus-count"})) for
                             class_bonus_data in
                             soup_classes.find_all("div", {"class": "table-bonus-list"})]
    classes_list = list(set([(classes_list[i], classes_bonus_numbers[i]) for i in range(0, len(classes_list))]))
    r_origins = requests.get(f'{TFT_TACTICS_URL}/db/origins/')
    soup_origins = BeautifulSoup(r_origins.content, "lxml")
    origins_list = [origin_data.text for origin_data in soup_origins.find_all("div", {"class": "d-none d-md-block"})]
    origins_bonus_numbers = [tuple(int(origins_bonus_number.text) for origins_bonus_number in
                                   origin_bonus_data.find_all("div", {"class": "table-bonus-count"})) for
                             origin_bonus_data in
                             soup_origins.find_all("div", {"class": "table-bonus-list"})]
    origins_list = list(set([(origins_list[i], origins_bonus_numbers[i]) for i in range(0, len(origins_list))]))
    traits_dict['classes'] = {class_tuple[0]: list(class_tuple[1]) for class_tuple in classes_list}
    traits_dict['origins'] = {origin_tuple[0]: list(origin_tuple[1]) for origin_tuple in origins_list}
    return traits_dict


def main():
    """Scrip principal"""
    # Champions
    champions_data = get_champions_data()
    df_champions = pd.json_normalize(champions_data)
    df_champions.to_csv(f'app/data/champions-{TFT_SET_NUMBER}.csv', index=False)
    # Traits
    traits = get_traits_data()
    with open(f'app/data/traits-{TFT_SET_NUMBER}.json', 'w') as f:
        json.dump(traits, f, indent=2)


if __name__ == '__main__':
    main()
