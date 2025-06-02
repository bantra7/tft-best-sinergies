"""
Streamlit web application for finding the best Teamfight Tactics (TFT)
team compositions based on champion synergies.
Users can filter champions by cost, define team size, and set criteria
for synergy strength to discover optimal teams.
"""
import itertools
import math
import os
import re
from typing import List, Dict, Optional, Tuple, Iterator

import numpy as np
import pandas as pd
import streamlit as st

from calcul import get_champions_df, get_all_traits, get_best_teams

DATA_PATH = "app/data"


def get_available_set_numbers(data_path: str = DATA_PATH) -> List[int]:
    """
    Scans the data directory for champion data files and extracts available set numbers.
    Files are expected to be named like 'champions-SET_NUMBER.csv'.

    Args:
        data_path (str): The path to the directory containing data files.

    Returns:
        List[int]: A sorted list of unique TFT set numbers found, in descending order (newest first).
    """
    set_numbers: set[int] = set()
    try:
        for filename in os.listdir(data_path):
            match = re.match(r"champions-(\d+)\.csv", filename)
            if match:
                set_numbers.add(int(match.group(1)))
    except FileNotFoundError:
        st.error(
            f"Data directory not found at {data_path}. Please ensure data is downloaded.")
        return []
    except OSError as e:
        st.error(f"OS error scanning for available set numbers in {data_path}: {e}")
        return []
    except Exception as e: # General fallback for other unexpected errors
        st.error(f"An unexpected error occurred while scanning for set numbers: {e}")
        return []
    return sorted(list(set_numbers), reverse=True)


@st.cache_data
def convert_df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Converts a Pandas DataFrame to CSV format and encodes it to UTF-8 bytes.
    This function is cached to prevent re-computation on every rerun.

    Args:
        df (pd.DataFrame): The DataFrame to convert.

    Returns:
        bytes: The CSV data as UTF-8 encoded bytes.
    """
    return df.to_csv().encode('utf-8')


@st.cache_data
def load_champions_data(tft_set_number: int) -> Optional[pd.DataFrame]:
    """
    Loads champion data for a specific TFT set.
    This function is cached.

    Args:
        tft_set_number (int): The TFT set number.

    Returns:
        Optional[pd.DataFrame]: DataFrame with champion data, or None if loading fails.
    """
    return get_champions_df(tft_set_number)


@st.cache_data
def load_traits_data(
        tft_set_number: int) -> Optional[Dict[str, Dict[str, List[int]]]]:
    """
    Loads trait data for a specific TFT set.
    This function is cached.

    Args:
        tft_set_number (int): The TFT set number.

    Returns:
        Optional[Dict[str, Dict[str, List[int]]]]: Dictionary with trait data, or None if loading fails.
    """
    return get_all_traits(tft_set_number)


def main() -> None:
    """
    Main function to run the Streamlit application interface.
    It allows users to set various filters such as champion cost, team size,
    minimum synergies, synergy ratio, and the maximum number of teams to display.
    Based on these filters, it calculates and displays the best team compositions.
    """
    st.set_page_config(page_title="TFT Best Synergies", layout="wide")
    st.title('TFT Best Synergies')

    available_sets: List[int] = get_available_set_numbers()
    if not available_sets:
        st.error(
            "No TFT set data found. Please run the `download_data.py` script first."
        )
        return

    # --- Sidebar for User Inputs ---
    with st.sidebar:
        st.header("Filters")

        selected_tft_set: int = available_sets[0]  # Default to latest
        if len(available_sets) > 1:
            selected_tft_set = st.selectbox(
                "Select TFT Set:",
                options=available_sets,
                index=0,
                help="Choose the TFT set for which to find team compositions.")

        st.subheader('Champion Cost')
        cost_columns: List[st.delta_generator.DeltaGenerator] = st.columns(5)
        selected_costs_bool: List[bool] = []
        for i, col in enumerate(cost_columns):
            with col:
                selected_costs_bool.append(st.checkbox(str(i + 1), value=True))

        team_size: int = st.select_slider('Team Size',
                                          options=list(range(3, 11)),
                                          value=7)
        min_synergies: int = st.select_slider('Min Unlocked Synergies',
                                              options=list(range(1, 10)),
                                              value=3)
        min_ratio_options: List[float] = [
            round(item, 2) for item in np.linspace(0, 1, 11)
        ]
        min_ratio: float = st.select_slider(
            'Min Synergy Ratio (Unlocked/Team Size)',
            options=min_ratio_options,
            value=0.3)
        max_team_display: int = st.select_slider('Max Teams to Display',
                                                 options=list(
                                                     range(10, 101, 10)),
                                                 value=50)

    # --- Load Data based on selected set ---
    df_champions: Optional[pd.DataFrame] = load_champions_data(
        selected_tft_set)
    # traits_data is loaded by get_best_teams inside calcul.py, so no need to load it here explicitly
    # unless it's needed directly in main.py for other purposes.

    if df_champions is None:
        st.error(
            f"Could not load champion data for Set {selected_tft_set}. Please check data files."
        )
        return

    # --- Filter Champions based on selected costs ---
    actual_costs_selected: List[int] = [
        i + 1 for i, checked in enumerate(selected_costs_bool) if checked
    ]
    if not actual_costs_selected:
        st.warning("Please select at least one champion cost.")
        return

    filtered_df_champions: pd.DataFrame = df_champions[
        df_champions['Cost'].isin(actual_costs_selected)]
    available_champion_names: List[str] = sorted(
        filtered_df_champions['Name'].unique().tolist())

    st.subheader("Team Configuration")
    # --- Champion Multiselect ---
    pre_selected_champions: List[str] = st.multiselect(
        f'Pre-select Champions (Set {selected_tft_set}) - (Max {team_size})',
        options=available_champion_names,
        default=[],
        max_selections=team_size,
        help="Optionally pre-select champions for your team.")

    # --- Generate Button and Team Calculation ---
    if st.button('Generate Optimal Teams', type="primary"):
        remaining_champion_names: List[str] = [
            name for name in available_champion_names
            if name not in pre_selected_champions
        ]

        num_champions_to_select: int = team_size - len(pre_selected_champions)

        if num_champions_to_select < 0:
            st.error("Number of pre-selected champions exceeds team size.")
            return
        if num_champions_to_select == 0 and not pre_selected_champions:
            st.warning("Please select some champions or increase team size.")
            return
        if num_champions_to_select > len(remaining_champion_names):
            st.warning(
                f"Not enough available champions ({len(remaining_champion_names)}) to form a team of size {team_size} "
                f"with the current cost filters after pre-selecting {len(pre_selected_champions)}. "
                "Try adjusting filters or pre-selected champions."
            ) # Wrapped long warning line
            return

        # Prepare team combinations iterator
        team_combinations_iter: Iterator[Tuple[str, ...]]
        if num_champions_to_select > 0:
            team_combinations_iter = itertools.combinations(
                remaining_champion_names, num_champions_to_select)
            # Combine with pre-selected champions
            team_combinations_iter = map(
                lambda x: tuple(sorted(x + tuple(pre_selected_champions))),
                team_combinations_iter)
        elif pre_selected_champions:  # Only pre-selected champions form the team
            team_combinations_iter = iter(
                [tuple(sorted(pre_selected_champions))])
        else:  # No champions to form a team
            st.warning(
                "No champions available to form teams. Adjust your filters.")
            return

        # Calculate the number of teams to be tested
        # This can be computationally expensive for large numbers, handle potential OverflowError
        try:
            if num_champions_to_select > 0:
                num_teams_to_test: int = math.comb(
                    len(remaining_champion_names), num_champions_to_select)
            elif pre_selected_champions:
                num_teams_to_test = 1
            else:
                num_teams_to_test = 0
        except (ValueError, OverflowError) as e:  #ValueError if k > n
            st.error(
                f"Could not calculate the number of team combinations: {e}. "
                "Try reducing team size or available champions."
            ) # Wrapped long error line
            return

        if num_teams_to_test == 0 and not pre_selected_champions:
            st.info(
                "No team combinations to test with the current selections.")
            return

        st.info(f'Testing {num_teams_to_test} potential team combinations...')

        df_best_teams: Optional[pd.DataFrame] = get_best_teams(
            teams=team_combinations_iter,
            number_teams_tested=num_teams_to_test,
            min_synergies=min_synergies,
            min_ratio=min_ratio,
            max_team_display_count=max_team_display,
            tft_set_number=selected_tft_set)

        if df_best_teams is not None and not df_best_teams.empty:
            st.success(
                f"Top {len(df_best_teams)} teams found for Set {selected_tft_set}:"
            )
            st.dataframe(df_best_teams)
            best_teams_csv_bytes: bytes = convert_df_to_csv_bytes(
                df_best_teams)
            st.download_button(
                label="Download Best Teams as CSV",
                data=best_teams_csv_bytes,
                file_name=f'best_tft_teams_set_{selected_tft_set}.csv',
                mime='text/csv',
            )
        else:
            st.info(
                "No teams matching your criteria were found. Try adjusting the filters."
            )


if __name__ == '__main__':
    main()
