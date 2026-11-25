# v0.97 — Console DNS : clavier et conservation des filtres

Dans la vue Enregistrements, Haut/Bas, Début et Fin déplacent la sélection et le focus sans reconstruire les lignes, résoudre un nom ni modifier la zone. Entrée et Alt+Entrée ouvrent les propriétés de l’entrée ciblée. Ctrl+F place le focus dans la recherche et F5 relit la console.

Le clic et le double-clic sont utilisables sur la ligne. Le bouton Propriétés reste désactivé si une recherche ou un filtre masque la sélection. La recherche porte sur le nom, le type et la valeur/cible ; un alias peut donc apparaître dans une recherche portant sur sa cible.

Recherche, filtre de type et identifiant sélectionné sont conservés dans le même onglet, par environnement et bureau. L’identifiant est contrôlé à la relecture de la zone : une entrée supprimée ou masquée n’est pas réactivée comme sélection.

Les propriétés ouvertes restent attachées à leur identifiant initial quand la sélection de la liste change. Les protections existantes contre les doubles envois, les entrées supprimées et l’indisponibilité de la console sont conservées.

## Validation

51 suites JavaScript passent. Le nouveau test couvre navigation locale, stabilité des lignes, propriétés sans résolution, sélection masquée, actualisation, réouverture des filtres et conservation de l’identifiant lors d’un enregistrement depuis les propriétés.

Le rendu et les interactions réelles dans Chrome restent à contrôler. Le périmètre reste celui du gestionnaire DNS simulé, avec une zone interne ; cette version n’ajoute pas la gestion complète des zones DNS de Windows Server.
