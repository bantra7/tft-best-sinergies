"""
This script downloads champion and trait data for Teamfight Tactics (TFT)
from tftactics.gg. It uses Selenium to interact with the website and
BeautifulSoup to parse the HTML content. The downloaded data is saved
locally as CSV and JSON files.
"""

import argparse
import json
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

TFT_TACTICS_URL = "https://tftactics.gg"


def get_page_source(url: str, tft_set_number: int) -> Optional[str]:
    """
    Fetches the page source of a given URL after performing specific Selenium actions.

    Args:
        url: The URL to fetch the page source from.
        tft_set_number: The TFT set number to select on the page.

    Returns:
        The page source as a string if successful, None otherwise.
    """
    page_source: Optional[str] = None
    driver = webdriver.Chrome()  # Or webdriver.Firefox() based on your browser
    try:
        driver.get(url)
        # Step 1: Locate and click the Consent button for cookies
        wait: WebDriverWait = WebDriverWait(
            driver, 10)  # Adjust the timeout as necessary
        consent_button: WebElement = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'fc-button')))
        consent_button.click()
        print("Consent button clicked!")

        # Step 2: Locate and click the dropdown toggle button
        toggle_button: WebElement = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'dropdown-toggle')))
        toggle_button.click()
        print("Dropdown toggle button clicked!")

        # Step 3: Wait for the specified set button to become clickable after toggling
        set_button_xpath: str = f'//button[@set="{tft_set_number}"]'
        set_button: WebElement = wait.until(
            EC.element_to_be_clickable((By.XPATH, set_button_xpath)))
        set_button.click()
        print(f"Set {tft_set_number} button clicked!")
        # Step 4: Get the page source after interactions
        page_source = driver.page_source

    except TimeoutException as e: # Specific import from selenium.common.exceptions
        print(f"TimeoutException occurred during Selenium page interactions: {e}")
    except WebDriverException as e:
        print(f"WebDriverException occurred during Selenium page interactions: {e}")
    except Exception as e: # General fallback for other unexpected errors
        print(f"An unexpected error occurred in get_page_source: {e}")
    finally:
        driver.quit()
    return page_source


def main(tft_set_number: int) -> None:
    """
    Main function to scrape champion and trait data for a specific TFT set.

    Args:
        tft_set_number: The TFT set number for which to download data.
    """
    champions: List[Dict[str, Any]] = []
    traits_data: Dict[str, Dict[str, List[int]]] = {
        'classes': {},
        'origins': {}
    }

    # Scrape Champions Data
    champions_url: str = f'{TFT_TACTICS_URL}/champions/'
    print(
        f"Fetching champions data from: {champions_url} for Set {tft_set_number}"
    )
    champions_page_html: Optional[str] = get_page_source(
        champions_url, tft_set_number)

    if champions_page_html:
        soup_champions: BeautifulSoup = BeautifulSoup(champions_page_html,
                                                      'html.parser')
        champions_list_container: Optional[Tag] = soup_champions.find(
            "div", {"class": "characters-list"})
        if champions_list_container:
            for champion_element in champions_list_container.children:
                if not isinstance(
                        champion_element,
                        Tag) or not champion_element.has_attr('href'):
                    continue

                champion_name: str = champion_element.text.strip()
                print(f"Processing champion: {champion_name}")
                champion_details: Dict[str, Any] = {
                    'Name': champion_name,
                    'Classes': [],
                    'Origins': [],
                    'Cost': 0
                }

                champion_page_url: str = f'{TFT_TACTICS_URL}{champion_element["href"]}'
                try:
                    champion_page_response: requests.Response = requests.get(
                        champion_page_url, timeout=10) # Added timeout
                    champion_page_response.raise_for_status()
                except requests.exceptions.Timeout:
                    print(f"Timeout while fetching page for champion {champion_name}: {champion_page_url}")
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching page for champion {champion_name} ({champion_page_url}): {e}")
                    continue

                soup_champion_page: BeautifulSoup = BeautifulSoup(
                    champion_page_response.content, "lxml")

                # Get champion cost
                stats_list: Optional[Tag] = soup_champion_page.find(
                    "ul", {"class": "stats-list"})
                if stats_list:
                    for stat_item in stats_list.children:
                        if isinstance(stat_item,
                                      Tag) and 'Cost' in stat_item.text:
                            try:
                                champion_details['Cost'] = int(
                                    stat_item.text.split(' ')[-1])
                                break
                            except (ValueError, IndexError) as e:
                                print(
                                    f"Could not parse cost for {champion_name}: {e}"
                                )
                else:
                    print(f"Could not find stats list for {champion_name}")

                # Get champion traits (classes and origins)
                trait_elements: List[Tag] = soup_champion_page.find_all(
                    "div", {"class": "ability-description-name"})
                for trait_element in trait_elements:
                    try:
                        trait_name_tag: Optional[Tag] = trait_element.find(
                            'span')
                        trait_type_tag: Optional[Tag] = trait_element.find(
                            'div')

                        if trait_name_tag and trait_type_tag:
                            trait_name: str = trait_name_tag.text.strip()
                            trait_type: str = trait_type_tag.text.strip()

                            if trait_type == 'Class':
                                champion_details['Classes'].append(trait_name)
                            elif trait_type == 'Origin':
                                champion_details['Origins'].append(trait_name)
                        else:
                            print(
                                f"Could not find trait name or type for an element in {champion_name}"
                            )
                    except AttributeError as e:
                        print(
                            f"Error parsing trait element for {champion_name}: {e}"
                        )

                champion_details['Classes'] = '/'.join(
                    champion_details['Classes'])
                champion_details['Origins'] = '/'.join(
                    champion_details['Origins'])
                champions.append(champion_details)
        else:
            print("Could not find champions list container on the page.")
    else:
        print("Failed to get champions page source.")

    # Scrape Classes Data
    classes_url: str = f'{TFT_TACTICS_URL}/db/classes/'
    print(
        f"Fetching classes data from: {classes_url} for Set {tft_set_number}")
    classes_page_html: Optional[str] = get_page_source(classes_url,
                                                       tft_set_number)
    if classes_page_html:
        soup_classes: BeautifulSoup = BeautifulSoup(classes_page_html,
                                                    'html.parser')
        raw_class_names: List[str] = []
        class_name_elements: List[Tag] = soup_classes.find_all(
            "div", {"class": "d-none d-md-block"})
        for elem in class_name_elements:
            if elem.text.strip():  # Ensure we don't add empty strings
                raw_class_names.append(elem.text.strip())

        class_bonus_elements: List[Tag] = soup_classes.find_all(
            "div", {"class": "table-bonus-list"})
        parsed_class_bonuses: List[Tuple[int, ...]] = []
        for bonus_list_element in class_bonus_elements:
            try:
                bonuses: Tuple[int, ...] = tuple(
                    int(count_element.text)
                    for count_element in bonus_list_element.find_all(
                        "div", {"class": "table-bonus-count"}))
                if bonuses:  # Ensure we don't add empty tuples if no bonus counts found
                    parsed_class_bonuses.append(bonuses)
            except (ValueError, AttributeError) as e:
                print(f"Error parsing class bonuses: {e}")
                parsed_class_bonuses.append(
                    tuple()
                )  # Add empty tuple on error to maintain length consistency if needed

        # Using a dictionary to ensure unique class names and associate with bonuses
        # Assuming the order and count of names and bonuses match
        unique_classes: Dict[str, List[int]] = {}
        for i in range(min(len(raw_class_names), len(parsed_class_bonuses))):
            class_name = raw_class_names[i]
            class_bonuses = list(parsed_class_bonuses[i])
            if class_name not in unique_classes:  # Keep first encountered if duplicates, though source data should be clean
                unique_classes[class_name] = class_bonuses
            else:  # If duplicates exist, this could indicate an issue with scraping or data source
                print(
                    f"Warning: Duplicate class name '{class_name}' found. Keeping first instance's bonuses."
                )

        traits_data['classes'] = unique_classes
    else:
        print("Failed to get classes page source.")

    # Scrape Origins Data
    origins_url: str = f'{TFT_TACTICS_URL}/db/origins/'
    print(
        f"Fetching origins data from: {origins_url} for Set {tft_set_number}")
    origins_page_html: Optional[str] = get_page_source(origins_url,
                                                       tft_set_number)
    if origins_page_html:
        soup_origins: BeautifulSoup = BeautifulSoup(
            origins_page_html, "lxml")  # lxml can be more robust
        raw_origin_names: List[str] = []
        origin_name_elements: List[Tag] = soup_origins.find_all(
            "div", {"class": "d-none d-md-block"})
        for elem in origin_name_elements:
            if elem.text.strip():
                raw_origin_names.append(elem.text.strip())

        origin_bonus_elements: List[Tag] = soup_origins.find_all(
            "div", {"class": "table-bonus-list"})
        parsed_origin_bonuses: List[Tuple[int, ...]] = []
        for bonus_list_element in origin_bonus_elements:
            try:
                bonuses: Tuple[int, ...] = tuple(
                    int(count_element.text)
                    for count_element in bonus_list_element.find_all(
                        "div", {"class": "table-bonus-count"}))
                if bonuses:
                    parsed_origin_bonuses.append(bonuses)
            except (ValueError, AttributeError) as e:
                print(f"Error parsing origin bonuses: {e}")
                parsed_origin_bonuses.append(tuple())

        unique_origins: Dict[str, List[int]] = {}
        for i in range(min(len(raw_origin_names), len(parsed_origin_bonuses))):
            origin_name = raw_origin_names[i]
            origin_bonuses = list(parsed_origin_bonuses[i])
            if origin_name not in unique_origins:
                unique_origins[origin_name] = origin_bonuses
            else:
                print(
                    f"Warning: Duplicate origin name '{origin_name}' found. Keeping first instance's bonuses."
                )

        traits_data['origins'] = unique_origins
    else:
        print("Failed to get origins page source.")

    # Save Data
    if champions:
        df_champions: pd.DataFrame = pd.json_normalize(champions)
        champions_csv_path: str = f'app/data/champions-{tft_set_number}.csv'
        df_champions.to_csv(champions_csv_path, index=False)
        print(f"Champions data saved to {champions_csv_path}")
    else:
        print("No champion data to save.")

    if traits_data['classes'] or traits_data['origins']:
        traits_json_path: str = f'app/data/traits-{tft_set_number}.json'
        with open(traits_json_path, 'w', encoding="utf-8") as f:
            json.dump(traits_data, f, indent=2)
        print(f"Traits data saved to {traits_json_path}")
    else:
        print("No traits data to save.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=(
            "Download TFT champion and trait data for a specific set. "
            "Example: python download_data.py --set_number 11"
        )
    ) # Wrapped help string further
    parser.add_argument(
        "--set_number",
        type=int,
        default=13, # Default to a recent set, user should verify
        help="The TFT set number to download data for (e.g., 11, 12, 13).")
    args = parser.parse_args()
    main(args.set_number)
