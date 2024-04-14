from itertools import combinations
from math import comb
import streamlit as st
import numpy as np
from calcul import get_champions_df, get_all_traits, get_best_teams


TFT_SET_NUMBER = 11


@st.cache_data
def convert_df(df):
    """
    Cache the conversion of dataframe to prevent computation on every rerun
    """
    return df.to_csv().encode('utf-8')


@st.cache_data
def champions():
    """
    Cache champions data
    """
    return get_champions_df(TFT_SET_NUMBER)


@st.cache_data
def traits():
    """
    Cache traits data
    """
    return get_all_traits(TFT_SET_NUMBER)


def main():
    """
    Script for main interface
    Use of different filters :
    * cost of champions
    * team size
    * minimum of synergies unlocked
    * minimum of a ratio of synergies unlocked and locked.
    * maximum number of teams for optimization.
    """
    df_champions = champions()
    st.title('TFT Best Synergies')
    with st.sidebar:
        st.subheader('Champion Cost')
        cost_1_col, cost_2_col, cost_3_col, cost_4_col, cost_5_col = st.columns(5)
        with cost_1_col:
            cost_1 = st.checkbox('1')
        with cost_2_col:
            cost_2 = st.checkbox('2')
        with cost_3_col:
            cost_3 = st.checkbox('3')
        with cost_4_col:
            cost_4 = st.checkbox('4')
        with cost_5_col:
            cost_5 = st.checkbox('5')
        team_size = st.select_slider('Team size', range(4, 10))
        min_synergies = st.select_slider('Minimum of unlock synergies', range(1, 9))
        min_ratio = st.select_slider('Minimum ratio', [round(item, 2) for item in list(np.linspace(0, 1, 11))])
        max_team = st.select_slider('Max team', range(20, 120, 20), value=100)
    costs = [index for index, cost_bool in enumerate([cost_1, cost_2, cost_3, cost_4, cost_5], 1) if cost_bool]
    df_champions = df_champions.loc[df_champions['Cost'].isin(costs)]
    champion_names = df_champions['Name'].tolist()
    champions_filter = st.multiselect(f'{", ".join(map(str, costs))} cost Champions',
                                      champion_names,
                                      max_selections=team_size
                                      )
    for champion in champions_filter:
        champion_names.remove(champion)
    generate_button = st.button('Generate')
    if generate_button:
        teams = combinations(champion_names, team_size - len(champions_filter))
        teams = map(lambda x: x + tuple(champions_filter), teams)
        # Get number of teams tested without iterate on team_combinations
        number_teams_tested = comb(len(champion_names), team_size - len(champions_filter))
        st.write(f'Testing {number_teams_tested} teams.')
        df_best_teams = get_best_teams(teams, number_teams_tested, min_synergies, min_ratio, max_team, TFT_SET_NUMBER)
        if df_best_teams:
            st.dataframe(df_best_teams)
            best_teams_csv = convert_df(df_best_teams)
            st.download_button(
                label="Download data as CSV",
                data=best_teams_csv,
                file_name='best_teams.csv',
                mime='text/csv',
            )
        else:
            st.write("Aucune équipe correspondant aux critères n'a été trouvée.")


if __name__ == '__main__':
    main()
