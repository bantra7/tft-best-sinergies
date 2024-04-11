import json
from bisect import bisect
from collections import Counter
import pandas as pd


def get_champions_df():
    """
    Récupération des données des champions sous format dataframe
    :return:
    """
    champions_df = pd.read_csv("data/champions-11.csv")
    return champions_df


def get_all_traits():
    """
    Récupération des données des classes sous format json
    :return:
    """
    with open('data/traits-11.json', 'r') as f:
        traits = json.load(f)
    return traits


def get_best_teams(teams, min_synergies, min_ratio, max_team):
    """

    Args:
        teams:
        traits:
        min_synergies:
        min_ratio:
        max_team:

    Returns:

    """
    best_teams = []
    traits = get_all_traits()
    for team in teams:
        team_score = 0
        team_ratio = 0
        team_synergies_count = 0
        team_synergies = []
        df_champions = get_champions_df()
        df_champions = df_champions.loc[df_champions['Name'].isin(team)]
        origins = Counter([item for row in df_champions['Origin'].tolist() for item in row.split(' ')])
        for origin_name, origin_count in origins.items():
            team_score += bisect(traits['origins'][origin_name], origin_count)
            if bisect(traits['origins'][origin_name], origin_count):
                team_synergies_count += 1
                team_synergies.append(origin_name)
        classes = Counter([item for row in df_champions['Class'].tolist() for item in row.split(' ')])
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
        # TODO création d'un dataframe, sort par le score et récupération des max_team premieres lignes
    df_best_teams = pd.json_normalize(best_teams)
    # df_best_teams = df_best_teams.sort_values('Score', ignore_index=True)
    # df_best_teams = df_best_teams.truncate(before=0, after=max_team-1)
    # Retourner le dataframe
    return df_best_teams
