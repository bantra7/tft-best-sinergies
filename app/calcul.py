import json
from bisect import bisect

def get_all_champions():
    with open('app/data/champions-8.json', 'r') as f:
        champions = json.load(f)
    return champions


def get_champions_with_cost(champions, costs):
    return [champion for champion in champions if champion['Cost'] in costs]


def get_all_synergies():
    with open('app/data/synergies-8.json', 'r') as f:
        synergies = json.load(f)
    return synergies


def get_synergies_for_team(team):
    synergies = {
        'names': [],
        'unlock': {},
        'carrys': 0,
        'tanks': 0,
    }
    for champion in team:
        try:
            # Ajout Origine champion
            champion_origins = champion['Origin'].split('/')
            champion_classes = champion['Class'].split('/')
            for champion_origin in champion_origins:
                if synergies['unlock'].get(champion_origin):
                    synergies['unlock'][champion_origin] += 1
                else:
                    synergies['names'].append(champion_origin)
                    synergies['unlock'][champion_origin] = 1
            # Ajout Classes champion
            for champion_class in champion_classes:
                    if synergies['unlock'].get(champion_class):
                        synergies['unlock'][champion_class] += 1
                    else:
                        synergies['names'].append(champion_class)
                        synergies['unlock'][champion_class] = 1
            # Modification du tag carry
            synergies['carrys'] += int(champion['Carry'])
            # Modification du tag carry
            synergies['tanks'] += int(champion['Tank'])
        except Exception as e:
            print(champion)
    return synergies


def get_paliers_for_synergie_team(synergies, synergies_team):
    return {x['Name']: list(map(int, x['Paliers'].split('/'))) for x in synergies if x['Name'] in synergies_team}


def get_stats(team_synergies, paliers):
    synergies = team_synergies['unlock']
    i_unlock = 0
    score = 0
    ratio = 0
    synergies_unlock = []
    for synergie_name, synergie_number in synergies.items():
        if synergie_name:
            synergie_paliers = paliers[synergie_name]
            if synergie_number in synergie_paliers or synergie_number >= synergie_paliers[0]:
                # print(f'Synergie {synergie_name} ajoutée.')
                i_unlock += 1
                synergies_unlock.append(synergie_name)
            score += bisect(synergie_paliers, synergie_number)
    ratio = round(i_unlock/len(team_synergies['names']), 2)
    return synergies_unlock, i_unlock, score, ratio


def get_best_synergies(team_combinations, synergies, min_synergies, min_ratio, champion_constraint):
    best_sinergies = []
    for team in team_combinations:
        team_comp = '/'.join([champion['Champion'] for champion in team])
        team_synergies = get_synergies_for_team(team)
        paliers = get_paliers_for_synergie_team(synergies, team_synergies['names'])
        synergies_unlock_names, nbre_unlock_synergies, score, ratio = get_stats(team_synergies, paliers)
        # if nbre_unlock_synergies >= seuil_nbre and team_synergies['carrys'] >= nbre_carry and team_synergies['tanks'] >= nbre_tank and score >= seuil_score:
        if nbre_unlock_synergies >= min_synergies and ratio >= min_ratio and champion_constraint in team_comp:
            best_sinergies.append(
                { 
                  'TEAM': team_comp,
                  'NBRE_SYNERGIES': nbre_unlock_synergies,
                  'SCORE': score,
                  'RATIO': ratio,
                  'CARRYS': team_synergies['carrys'],
                  'TANKS' : team_synergies['tanks'],
                  'SYNERGIES_UNLOCK' : synergies_unlock_names,
                  'SYNERGIES_LEFT': team_synergies['names']
                }
            )
    return best_sinergies