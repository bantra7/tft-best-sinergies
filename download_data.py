import json
from itertools import pairwise

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.wait import WebDriverWait

TFT_TACTICS_URL = "https://tftactics.gg"
TFT_SET_NUMBER = 13


def get_page_source(url: str):
    page_source = None
    driver = webdriver.Chrome()  # Or webdriver.Firefox() based on your browser
    driver.get(url)
    try:
        # Step 1: Locate and click the Consent button for cookies
        wait = WebDriverWait(driver, 10)  # Adjust the timeout as necessary
        consent_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'fc-button')))
        consent_button.click()
        print("Consent button clicked!")

        # Step 2: Locate and click the dropdown toggle button
        toggle_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'dropdown-toggle')))
        toggle_button.click()
        print("Dropdown toggle button clicked!")

        # Step 3: Wait for the "Set 13" button to become clickable after toggling
        set_13_button = wait.until(EC.element_to_be_clickable((By.XPATH, f'//button[@set="{TFT_SET_NUMBER}"]')))
        set_13_button.click()
        print(f"Set {TFT_SET_NUMBER} button clicked!")
        # Step 4: Get the page source after interactions
        page_source = driver.page_source

    except Exception as e:
        print(f"An error occurred: {e}")
    # Optionally, wait to see the effect, then close the driver
    finally:
        driver.quit()
    return page_source


def main():
    champions = []
    traits_dict = {
        'classes': {},
        'origins': {}
    }
    champions_page_source = get_page_source(f'{TFT_TACTICS_URL}/champions/')
    if champions_page_source:
        soup_champions = BeautifulSoup(champions_page_source, 'html.parser')
        champions_list = soup_champions.find("div", {"class": "characters-list"})
        for champion in champions_list.children:
            print(f"Adding new champion : {champion.text}")
            champion_dict = {'Name': champion.text,
                             'Classes': [],
                             'Origins': [],
                             'Cost': 0
                             }
            r_champion = requests.get(f'{TFT_TACTICS_URL}{champion["href"]}')
            soup_champion = BeautifulSoup(r_champion.content, "lxml")
            # Récupération des traits du champion
            champion_traits = soup_champion.find_all("div", {"class": "ability-description-name"})
            for champion_stats in soup_champion.find("ul", {"class": "stats-list"}).children:
                if 'Cost' in champion_stats.text:
                    champion_dict['Cost'] = int(champion_stats.text.split(' ')[-1])
            for champion_trait in champion_traits:
                for champion_trait_data in pairwise(champion_trait.children):
                    if champion_trait_data[1].text == 'Class':
                        champion_dict['Classes'].append(champion_trait_data[0].text)
                    elif champion_trait_data[1].text == 'Origin':
                        champion_dict['Origins'].append(champion_trait_data[0].text)
            champion_dict['Classes'] = '/'.join(champion_dict['Classes'])
            champion_dict['Origins'] = '/'.join(champion_dict['Origins'])
            champions.append(champion_dict)
    classes_page_source = get_page_source(f'{TFT_TACTICS_URL}/db/classes/')
    if classes_page_source:
        soup_classes = BeautifulSoup(classes_page_source, 'html.parser')
        classes_list = [class_data.text for class_data in soup_classes.find_all("div", {"class": "d-none d-md-block"})]
        classes_bonus_numbers = [tuple(int(classes_bonus_number.text) for classes_bonus_number in
                                       class_bonus_data.find_all("div", {"class": "table-bonus-count"})) for
                                 class_bonus_data in
                                 soup_classes.find_all("div", {"class": "table-bonus-list"})]
        classes_list = list({(classes_list[i], classes_bonus_numbers[i]) for i in range(0, len(classes_list))})
        traits_dict['classes'] = {class_tuple[0]: list(class_tuple[1]) for class_tuple in classes_list}
    origins_page_source = get_page_source(f'{TFT_TACTICS_URL}/db/origins/')
    if origins_page_source:
        soup_origins = BeautifulSoup(origins_page_source, "lxml")
        origins_list = [origin_data.text for origin_data in
                        soup_origins.find_all("div", {"class": "d-none d-md-block"})]
        origins_bonus_numbers = [tuple(int(origins_bonus_number.text) for origins_bonus_number in
                                       origin_bonus_data.find_all("div", {"class": "table-bonus-count"})) for
                                 origin_bonus_data in
                                 soup_origins.find_all("div", {"class": "table-bonus-list"})]
        origins_list = list({(origins_list[i], origins_bonus_numbers[i]) for i in range(0, len(origins_list))})
        traits_dict['origins'] = {origin_tuple[0]: list(origin_tuple[1]) for origin_tuple in origins_list}
    # Save Data
    df_champions = pd.json_normalize(champions)
    df_champions.to_csv(f'app/data/champions-{TFT_SET_NUMBER}.csv', index=False)
    with open(f'app/data/traits-{TFT_SET_NUMBER}.json', 'w', encoding="utf-8") as f:
        json.dump(traits_dict, f, indent=2)


if __name__ == '__main__':
    main()
