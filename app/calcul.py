"""
Module fournissant les méthodes de calcul sur les équipes TFT
"""
import json
from bisect import bisect
from collections import Counter
import pandas as pd
import streamlit as st


def get_champions_df(tft_set_number: int):
    """
    Récupération des données des champions sous format dataframe
    :return:
    """
    champions_df = pd.read_csv(f'app/data/champions-{tft_set_number}.csv')
    return champions_df


def get_all_traits(tft_set_number: int):
    """
    Récupération des données des classes sous format json
    :return:
    """
    with open(f'app/data/traits-{tft_set_number}.json', 'r', encoding="utf-8") as f:
        traits = json.load(f)
    return traits


def get_best_teams(teams, number_teams_tested, min_synergies, min_ratio, max_team, tft_set_number):
    """

    Args:
        teams: all teams tested
        number_teams_tested: length for creating streamlit progressbar
        min_synergies: minimum of synergies unlock
        min_ratio: minimum of the ratio of lock and unlock synergies
        max_team: number of rows of the best teams dataframe
        tft_set_number: number of the TFT set used

    Returns: Dataframe

    """
    best_teams = []
    traits = get_all_traits(tft_set_number)
    i = 0
    progress_text = "Operation in progress. Testing all teams."
    my_bar = st.progress(0, text=progress_text)
    for team in teams:
        percent_complete = round(i * 100 / number_teams_tested)
        my_bar.progress(percent_complete, text=progress_text)
        i += 1
        team_score = 0
        team_synergies_count = 0
        team_synergies = []
        df_champions = get_champions_df(tft_set_number)
        df_champions = df_champions.loc[df_champions['Name'].isin(team)]
        origins = Counter([item for row in df_champions['Origins'].tolist() for item in row.split('/')])
        for origin_name, origin_count in origins.items():
            team_score += bisect(traits['origins'][origin_name], origin_count)
            if bisect(traits['origins'][origin_name], origin_count):
                team_synergies_count += 1
                team_synergies.append(origin_name)
        classes = Counter([item for row in df_champions['Classes'].tolist() for item in row.split('/')])
        for class_name, class_count in classes.items():
            team_score += bisect(traits['classes'][class_name], class_count)
            if bisect(traits['classes'][class_name], class_count):
                team_synergies_count += 1
                team_synergies.append(class_name)
        team_ratio = round(team_synergies_count / len(df_champions.index), 2)
        if team_synergies_count > min_synergies and team_ratio > min_ratio:
            best_teams.append(
                {
                    'Team': df_champions['Name'].tolist(),
                    'Score': team_score,
                    'Ratio': team_ratio,
                    'Synergies': team_synergies,
                }
            )
    my_bar.empty()
    if best_teams:
        df_best_teams = pd.json_normalize(best_teams)
        df_best_teams = df_best_teams.sort_values('Score', ascending=False, ignore_index=True)
        df_best_teams = df_best_teams.truncate(before=0, after=max_team-1)
    else:
        df_best_teams = None
    return df_best_teams
