import time
import csv
from calcul import get_all_champions, get_all_synergies, get_synergies_for_team, get_stats, get_paliers_for_synergie_team, get_champions_with_cost
from itertools import combinations
CHAMPIONS = {}
SYNERGIES = {}

def main():
    start = time.time()
    costs = ['1','2','3']
    n = 6
    nbre_carry = 2
    nbre_tank = 2
    seuil_nbre = 5
    seuil_score = 5
    seuil_ratio = 0.5
    SYNERGIES = get_all_synergies()
    CHAMPIONS = get_all_champions()
    champions = get_champions_with_cost(CHAMPIONS, costs)
    team_combinations = combinations(champions,n)
    best_sinergies = []
    i = 0
    for team in team_combinations:
        i+=1
        team_comp = '/'.join([champion['Champion'] for champion in team])
        team_synergies = get_synergies_for_team(team)
        paliers = get_paliers_for_synergie_team(SYNERGIES, team_synergies['names'])
        nbre_unlock_synergies, score, ratio = get_stats(team_synergies, paliers)
        # if nbre_unlock_synergies >= seuil_nbre and team_synergies['carrys'] >= nbre_carry and team_synergies['tanks'] >= nbre_tank and score >= seuil_score:
        if nbre_unlock_synergies >= seuil_nbre and ratio >= seuil_ratio:
            best_sinergies.append(
                { 
                  'TEAM': team_comp,
                  'NBRE_SYNERGIES': nbre_unlock_synergies,
                  'SCORE': score,
                  'RATIO': ratio,
                  'CARRYS': team_synergies['carrys'],
                  'TANKS' : team_synergies['tanks'],
                  'SYNERGIES': team_synergies['names']
                }
            )
    with open('best_sinergies.csv', 'w', newline='') as file_out:
        writer = csv.DictWriter(file_out, best_sinergies[0].keys(), delimiter=',', )
        writer.writeheader()
        for team_comp in best_sinergies:
            writer.writerow(team_comp)
    print(f'On regarde les costs {costs}.')
    print(f'On cherche une team de {n} champions.')
    print(f'Nombre de teams testées : {i}.')
    print(f'On veut au moins {seuil_nbre} carry(s) et {nbre_tank} tank(s).')
    print(f'Nombre de teams avec plus que {seuil_nbre} synergie(s) et un score minimum de {seuil_score} et un ratio minimum de {seuil_ratio}: {len(best_sinergies)}.')
    print(time.ctime(time.time() - start)[11:19])
        

if __name__ == '__main__':
    main()
