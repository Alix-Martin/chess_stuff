import requests
from bs4 import BeautifulSoup

def main():
    url = 'http://www.echecs.asso.fr/TournoiInscriptions.aspx?Id=63393'  # Open B
    url = 'http://www.echecs.asso.fr/TournoiInscriptions.aspx?Id=63389'  # Accession

    # download content of url
    page = requests.get(url)
    # parse content
    soup = BeautifulSoup(page.content, 'html.parser')
    # find all tables
    tables = soup.find_all('table')
    """
    the player list looks like this : 
    <div class="page-mid">
    <table border=0 cellspacing=0 cellpadding=4 width=100%>
      
        <tr class=liste_titre>
          <td align=center width=60>NrFFE</td>
          <td align=center width=10>T</td>
          <td align=left width=200>Nom et Prénom</td>
          <td align=center width=45>Elo</td>
          <td align=center width=45>Rapide</td>
          <td align=center width=45>Blitz</td>
          <td align=center width=40>Cat</td>
          <td align=center width=40>Fede</td>
          <td align=center width=30>Ok</td>
          <td align=left>Club</td>
        </tr>
      
        <tr class=liste_clair>
          <td align=center>N66007</td>
          <td align=center></td>
          <td align=left>ABIVEN Pierre-Louis</td>
          <td align=right>1956&nbsp;F</td>
          <td align=right>1990&nbsp;F</td>
          <td align=right>1802&nbsp;E</td>
          <td align=center>MinM</td>
          <td align=center><img src=flags/FRA.gif height=15px /></td>
          <td align=center>X</td>
          <td align=left>Nomad' Echecs</td>
        </tr>	
    """
    # find the table with the player list
    player_table = None
    for table in tables:
        if table.find('td', string='NrFFE'):
            player_table = table
            break

    if player_table is None:
        print('No player table found')
        return

    # find all rows in the player table
    rows = player_table.find_all('tr')
    # skip the first row
    ratings = dict()
    for row in rows[1:]:
        # find all cells in the row
        cells = row.find_all('td')
        # get the player name
        try:
            player_name = cells[2].get_text()
            # get the player rating
            player_rating = cells[3].get_text()
            ratings[player_name] = player_rating
        except IndexError:
            continue
    print(len(ratings), 'players')
    print()
    # build a list of players sorted by rating
    sorted_ratings = sorted(ratings.items(), key=lambda x: int(x[1].split('\xa0')[0]), reverse=True)
    n_pairings = int(len(ratings) // 2)
    for i in range(n_pairings):
        print(sorted_ratings[i][0], sorted_ratings[i][1], 'vs',
              sorted_ratings[i + n_pairings][0], sorted_ratings[i + n_pairings][1])

main()