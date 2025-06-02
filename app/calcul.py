"""
This module provides functions for calculating and determining the best
Teamfight Tactics (TFT) team compositions based on champion synergies.
It reads champion and trait data, processes team combinations,
and scores them based on unlocked synergies.
"""
import json
from bisect import bisect
from collections import Counter
from typing import List, Dict, Any, Optional, Iterable

import pandas as pd
import streamlit as st


def get_champions_df(tft_set_number: int) -> Optional[pd.DataFrame]:
    """
    Retrieves champion data as a Pandas DataFrame for a specific TFT set.

    Args:
        tft_set_number: The TFT set number (e.g., 10, 11) to load data for.

    Returns:
        A Pandas DataFrame containing champion data (Name, Classes, Origins, Cost),
        or None if the data file is not found.
    """
    file_path: str = f'app/data/champions-{tft_set_number}.csv'
    try:
        champions_df: pd.DataFrame = pd.read_csv(file_path)
        return champions_df
    except FileNotFoundError:
        st.error(f"Error: Champions data file not found at {file_path}")
        return None
    except pd.errors.EmptyDataError:
        st.error(f"Error: Champions data file is empty at {file_path}")
        return None
    except pd.errors.ParserError:
        st.error(f"Error: Could not parse champions data file at {file_path}")
        return None
    except Exception as e: # General fallback for other unexpected errors
        st.error(f"An unexpected error occurred while reading champions data: {e}")
        return None


def get_all_traits(
        tft_set_number: int) -> Optional[Dict[str, Dict[str, List[int]]]]:
    """
    Retrieves trait data (classes and origins) from a JSON file for a specific TFT set.

    Args:
        tft_set_number: The TFT set number (e.g., 10, 11) to load data for.

    Returns:
        A dictionary containing trait data, structured as
        {'classes': {'ClassName': [bonus_thresholds]},
         'origins': {'OriginName': [bonus_thresholds]}},
        or None if the data file is not found.
    """
    file_path: str = f'app/data/traits-{tft_set_number}.json'
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            traits: Dict[str, Dict[str, List[int]]] = json.load(f)
        return traits
    except FileNotFoundError:
        st.error(f"Error: Traits data file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from traits data file at {file_path}")
        return None
    except Exception as e: # General fallback for other unexpected errors
        st.error(f"An unexpected error occurred while reading traits data: {e}")
        return None


def get_best_teams(teams: Iterable[List[str]], number_teams_tested: int,
                   min_synergies: int, min_ratio: float,
                   max_team_display_count: int,
                   tft_set_number: int) -> Optional[pd.DataFrame]:
    """
    Analyzes a list of potential TFT teams and returns a DataFrame of the best ones
    based on synergy scores and specified criteria.

    Args:
        teams (Iterable[List[str]]): An iterable of teams, where each team is a list of champion names.
        number_teams_tested (int): The total number of teams being tested (for Streamlit progress bar).
        min_synergies (int): The minimum number of unlocked synergies a team must have.
        min_ratio (float): The minimum ratio of unlocked synergies to team size.
        max_team_display_count (int): The maximum number of top teams to return in the DataFrame.
        tft_set_number (int): The TFT set number for which to calculate team compositions.

    Returns:
        A Pandas DataFrame containing the best teams sorted by score, including their
        team composition, score, synergy ratio, and list of synergies.
        Returns None if no teams meet the criteria or if input data is missing.
    """
    best_teams_data: List[Dict[str, Any]] = []

    all_traits_data: Optional[Dict[str, Dict[
        str, List[int]]]] = get_all_traits(tft_set_number)
    all_champions_df: Optional[pd.DataFrame] = get_champions_df(tft_set_number)

    if all_traits_data is None or all_champions_df is None:
        st.error(
            "Cannot calculate best teams due to missing champion or trait data."
        )
        return None

    progress_text: str = "Operation in progress. Testing all teams."
    my_bar = st.progress(0, text=progress_text)

    for i, team_champion_names in enumerate(teams):
        percent_complete: int = round((i + 1) * 100 / number_teams_tested)
        my_bar.progress(percent_complete,
                        text=f"{progress_text} ({i+1}/{number_teams_tested})")

        team_score: int = 0
        team_synergies_count: int = 0
        unlocked_synergies: List[str] = []

        # Filter the main champions DataFrame for the current team
        current_team_df: pd.DataFrame = all_champions_df[
            all_champions_df['Name'].isin(team_champion_names)]

        if current_team_df.empty:
            continue

        # Calculate Origins synergies
        team_origins_flat: List[str] = [
            item
            for sublist in current_team_df['Origins'].dropna().str.split('/')
            for item in sublist if item
        ]
        origin_counts: Counter = Counter(team_origins_flat)

        for origin_name, count in origin_counts.items():
            if origin_name in all_traits_data['origins']:
                synergy_level: int = bisect(
                    all_traits_data['origins'][origin_name], count)
                team_score += synergy_level
                if synergy_level > 0:
                    team_synergies_count += 1
                    unlocked_synergies.append(origin_name)
            else:
                st.warning(
                    f"Origin '{origin_name}' found in champion data but not in traits data. Skipping."
                )

        # Calculate Classes synergies
        team_classes_flat: List[str] = [
            item
            for sublist in current_team_df['Classes'].dropna().str.split('/')
            for item in sublist if item
        ]
        class_counts: Counter = Counter(team_classes_flat)

        for class_name, count in class_counts.items():
            if class_name in all_traits_data['classes']:
                synergy_level: int = bisect(
                    all_traits_data['classes'][class_name], count)
                team_score += synergy_level
                if synergy_level > 0:
                    team_synergies_count += 1
                    unlocked_synergies.append(class_name)
            else:
                st.warning(
                    f"Class '{class_name}' found in champion data but not in traits data. Skipping."
                )

        team_size: int = len(current_team_df.index)
        if team_size == 0:  # Should not happen if current_team_df is not empty, but as a safeguard
            team_ratio = 0.0
        else:
            team_ratio: float = round(team_synergies_count / team_size, 2)

        if team_synergies_count >= min_synergies and team_ratio >= min_ratio:
            best_teams_data.append({
                'Team': current_team_df['Name'].tolist(),
                'Score': team_score,
                'Ratio': team_ratio,
                'Synergies': unlocked_synergies,
            })

    my_bar.empty()

    if not best_teams_data:
        st.info("No teams found matching the specified criteria.")
        return None

    df_best_teams: pd.DataFrame = pd.json_normalize(best_teams_data)
    df_best_teams = df_best_teams.sort_values('Score',
                                              ascending=False,
                                              ignore_index=True)
    df_best_teams = df_best_teams.head(
        max_team_display_count)  # More idiomatic pandas

    return df_best_teams
