from itertools import pairwise

import pandas as pd
import requests
from bs4 import BeautifulSoup as bs

TFTTACTICS_URL = 'https://tftactics.gg'

CHAMPIONS = []

def main():
    r_champions = requests.get('https://tftactics.gg/champions/')
    soup_champions = bs(r_champions.content, "lxml")
    champions_list = soup_champions.find("div", {"class": "characters-list"})
    for champion in champions_list.children:
        champion_dict = {'Name': champion.text,
                         'Classes': [],
                         'Origins': []}
        # Récupération du nom
        r_champion = requests.get(f'{TFTTACTICS_URL}{champion["href"]}')
        soup_champion = bs(r_champion.content, "lxml")
        champion_stats = soup_champion.find("ul", {"class": "stats-list"})
        for champion_stat in champion_stats.children:
            # Récupération de tout les stats
            champion_stat_name, champion_stat_value = champion_stat.text.split(':')
            champion_dict[champion_stat_name] = champion_stat_value.strip()
        champion_traits = soup_champion.find_all("div", {"class": "ability-description-name"})
        for champion_trait in champion_traits:
            for champion_trait_data in pairwise(champion_trait.children):
                if champion_trait_data[1].text == 'Class':
                    champion_dict['Classes'].append(champion_trait_data[0].text)
                elif champion_trait_data[1].text == 'Origin':
                    champion_dict['Origins'].append(champion_trait_data[0].text)
        print(champion_dict)
        CHAMPIONS.append(champion_dict)
    df_champions = pd.json_normalize(CHAMPIONS)
    df_champions.to_csv('out.csv', index=False)


if __name__ == '__main__':
    main()
