import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations
from calcul import get_champions_df, get_all_traits, get_synergies_for_team, get_stats, \
    get_paliers_for_synergie_team, get_best_synergies
from math import comb


@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')


@st.cache_data
def champions():
    """
    Récupération en cache des champions
    :return:
    """
    return get_champions_df()


@st.cache_data
def synergies():
    """
    Récupération en cache des synergies
    :return:
    """
    return get_all_traits()


def main():
    """
    Script de l'interface principale
    :return:
    """
    df_champions = champions()
    st.title('TFT Best Synergies')
    with st.sidebar:
        # Filtres à sélectionner pour la récupération des meilleures compositions
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
        size = st.select_slider('Taille de l\'équipe', range(4, 10))
        min_synergies = st.select_slider('Minimum de synergies actives', range(1, 9))
        min_ratio = st.select_slider('Ratio minimum', [round(item, 2) for item in list(np.linspace(0, 1, 11))])
        # champions_names = [''] + [champion['Champion'] for champion in champions()]
        # champion_constraint = st.selectbox('Champion constraint', champions_names)

    generate_button = st.button('Generate')
    if generate_button:
        costs = [index for index, cost_bool in enumerate([cost_1, cost_2, cost_3, cost_4, cost_5], 1) if cost_bool]
        st.write(f'On regarde les costs {costs}.')
        st.write(f'On cherche une team de {size} champions.')
        df_champions = df_champions.loc[df_champions['Cost'].isin(costs)]
        team_combinations = combinations(df_champions, size)
        number_teams_tested = comb(len(df_champions), size)
        st.write(f'On va tester {number_teams_tested} teams.')
        best_sinergies = get_best_synergies(team_combinations, synergies(), min_synergies, min_ratio)
        st.write(
            f'Nombre de teams avec plus que {min_synergies} synergie(s) et un ratio minimum de {min_ratio}: {len(best_sinergies)}.')
        best_synergies_df = pd.DataFrame(best_sinergies)
        best_sinergies_csv = convert_df(best_synergies_df)
        result_button = st.button('See Results')
        st.download_button(
            label="Download data as CSV",
            data=best_sinergies_csv,
            file_name='best_sinergies.csv',
            mime='text/csv',
        )


if __name__ == '__main__':
    main()
