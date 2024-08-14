import pandas as pd

import requests
from bs4 import BeautifulSoup
from sklearn import linear_model

AGE_CATEGORIES = False
COUNTRIES = False
CLUBS = True

# tournament_id = 62562  # Accession La Plagne 2024
# tournament_id = 62560  # Maitres La Plagne 2024
# tournament_id = 59431  # Open B 2023
# tournament_id = 59412  # Accession 2023

def get_tournaments(url, tournament_name):
    """
    get tournament_ids from url, each tournament has a row like this :

	<tr class=liste_clair>
	  <td align=right width=30>62190</td>
      <td align=left width=200>AGEN</td>
      <td align=center width=30>47</td>
      <td align=left><a href=FicheTournoi.aspx?Ref=62190 class=lien_texte>Championnat de France des Jeunes 2024 - U16</a></td>
      <td align=right width=60>14 avr.</td>
      <td align=center width=30>FFE</td>
      <td align=center width=20 visible=False>X</td>
      <td align=center width=20 visible=False></td>
	</tr>
    """
    page = requests.get(url)
    # parse content
    soup = BeautifulSoup(page.content, 'html.parser')
    # find all links
    links = soup.find_all('a')
    tournaments = []
    for row in soup.find_all('tr', class_=['liste_clair', 'liste_fonce']):
        cells = row.find_all('td')
        if len(cells) > 3 and tournament_name in cells[3].get_text():
            tournament_id = cells[0].get_text(strip=True)
            tournaments.append(tournament_id)
    return tournaments

url = 'http://www.echecs.asso.fr/ListeTournois.aspx?Action=TOURNOICOMITE&ComiteRef=47'  # tournois Agen
tournaments = get_tournaments(url, 'Championnat de France des Jeunes 2024')
print(len(tournaments), 'tournaments')

def build_dataframe(player_data):
    df = pd.DataFrame.from_dict(player_data, orient='index')
    df['Perf_minus_Elo'] = df['Perf'] - df['Elo']
    # print the whole dataframe
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #     print(df[['Elo', 'Perf', 'Perf_minus_Elo']])
    df['age_group'] = df['Cat.'].apply(lambda x: x[:3])
    df['gender'] = df['Cat.'].apply(lambda x: x[3:])
    dummy_columns = ['gender']

    if AGE_CATEGORIES:
        dummy_columns.append('age_group')
    if COUNTRIES:
        dummy_columns.append('Fede')
    if CLUBS:
        dummy_columns.append('Club')
    df = pd.get_dummies(df, columns=dummy_columns)
    return df


def parse_player_data(tournaments):
    player_data = {}
    for tournament_id in tournaments:
        url = f'http://echecs.asso.fr/Resultats.aspx?URL=Tournois/Id/{tournament_id}/{tournament_id}&Action=Cl'
        # download content of url
        page = requests.get(url)
        # parse content
        soup = BeautifulSoup(page.content, 'html.parser')

        """
        the results table looks like this : 
        <table width=800 cellpadding=2 cellspacing=0 style=border-collapse:collapse;>
         <tr class=papi_titre>
          <td colspan=12 align=center>Accession<br />Classement après la ronde 9</td>
         </tr>
         <tr class=papi_liste_t>
          <td class=papi_r>Pl</td>
          <td class=papi_r>&nbsp;</td>
          <td class=papi_l>Nom</td>
          <td class=papi_c>Elo</td>
          <td class=papi_c>Cat.</td>
          <td class=papi_c>Fede</td>
          <td class=papi_c>Ligue</td>
          <td class=papi_l>Club</td>
          <td class=papi_r>Pts</td>
          <td class=papi_r>Tr.</td>
          <td class=papi_r>Bu.</td>
          <td class=papi_r>Perf</td>
         </tr>
         <tr class=papi_liste_f>
          <td class=papi_r>1</td>
          <td class=papi_r>&nbsp;</td>
          <td class=papi_l><b>SETUMADHAV YELLUMAHA</b></td>
          <td class=papi_r>1941&nbsp;F</td>
          <td class=papi_c>CadM</td>
          <td class=papi_c><img border=0 src=flags/IND.GIF height=15px /></td>
          <td class=papi_c></td>
          <td class=papi_l></td>
          <td class=papi_r><b>8</b></td>
          <td class=papi_c>42&frac12;</td>
          <td class=papi_c>52</td>
          <td class=papi_c>2218</td>
         </tr>"""
        # this table contains the results of all matches between players durng the tournament, in the third <td> of each row
        for row in soup.find_all('tr', class_=['papi_liste_c', 'papi_liste_f']):
            cells = row.find_all('td')
            if len(cells) > 2:
                player_name = cells[2].get_text(strip=True)
                elo = int(cells[3].get_text(strip=True).split()[0])
                perf = int(cells[-1].get_text(strip=True))
                fede_img = cells[5].find('img')
                if fede_img:
                    fede = fede_img['src'].split('/')[-1].split('.')[0]
                else:
                    fede = cells[5].get_text(strip=True)
                if 1 <= elo <= 4999 and 1 <= perf <= 4999:
                    player_data[player_name] = {
                        'Pl': cells[0].get_text(strip=True),
                        'Elo': elo,
                        'Cat.': cells[4].get_text(strip=True),
                        'Fede': fede,
                        'Ligue': cells[6].get_text(strip=True),
                        'Club': cells[7].get_text(strip=True),
                        'Pts': cells[8].get_text(strip=True),
                        'Tr.': cells[9].get_text(strip=True),
                        'Bu.': cells[10].get_text(strip=True),
                        'Perf': perf
                    }
                else:
                    print(f"Skipped row due to out of range Elo or Perf: {row}")

            else:
                print(f"Skipped row: {row}")
    return player_data


player_data = parse_player_data(tournaments)

print(len(player_data), 'players')

df = build_dataframe(player_data)

# Define the target variable
y = df['Perf_minus_Elo']

# Define the feature variables
dropped_columns = ['Perf_minus_Elo', 'Pl', 'Cat.', 'Ligue', 'Pts', 'Tr.', 'Bu.', 'Perf', 'Elo']
if not AGE_CATEGORIES:
    dropped_columns.append('age_group')
if not COUNTRIES:
    dropped_columns.append('Fede')
if not CLUBS:
    dropped_columns.append('Club')

X = df.drop(columns=dropped_columns)
# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#     print(X)
# Fit a linear regression model to the training data
model = linear_model.Ridge(alpha=.5)

model.fit(X, y)

# Print the coefficients to quantify the impact of each dummy variable
coefficients = pd.DataFrame(model.coef_, X.columns, columns=['Coefficient'])
# Define the order of age groups
# Extract the age group from the index of the coefficients DataFrame
coefficients['age_group'] = coefficients.index.str.split('_').str[-1]

# Define the order of age groups
age_group_order = ['Pou', 'Pup', 'Ben', 'Min', 'Cad', 'Jun', 'Sen', 'Sep', 'Vet']

# Sort the coefficients DataFrame by the age group order
coefficients['age_group'] = pd.Categorical(coefficients['age_group'], categories=age_group_order, ordered=True)
coefficients = coefficients.sort_values(by='age_group')

# Drop the temporary 'age_group' column
coefficients = coefficients.drop(columns=['age_group']).round(1)
coefficients['count'] = X.sum()

# add a column with player count for each category
min_player_count = 5
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(coefficients[coefficients['count'] >= min_player_count])