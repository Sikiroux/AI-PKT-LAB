# v0.85 — Ouverture d’un poste depuis un ticket

## Incident observé

La capture fournie montre plusieurs HTTP 400 sur `/workspace/action`. Le bouton ouvrait `about:blank`, appelait la fonction générique de traitement puis fermait l’onglet à tout échec. Cette fonction englobait aussi l’actualisation des tickets : un échec de celle-ci pouvait être confondu avec un refus d’accès distant.

La capture ne contient pas la réponse JSON du serveur : le motif exact du 400 n’est pas établi.

## Correctif

Un parcours dédié ouvre un écran d’attente dans l’onglet réservé au clic. En cas de refus, l’onglet reste ouvert et affiche le message retourné par le serveur. La fiche ticket affiche aussi ce message. Les textes sont insérés avec textContent.

Après succès de la connexion, navigation vers le poste et l’entreprise capturés au clic. Une erreur ultérieure d’actualisation des tickets ne ferme plus cet onglet. Un changement d’entreprise empêche la navigation vers un autre contexte. Le blocage des fenêtres par le navigateur est annoncé sans lancer la demande. Pas de nouvelle tentative automatique ni de contournement des prérequis réseau.

## Validation et limites

Test dédié : message conservé lors du refus, popup bloquée sans requête, actualisation échouée après succès, double clic et changement d’entreprise. Les 45 suites JavaScript passent pour cette version. Aucun changement backend. Cœur et ateliers non relancés pour ce correctif navigateur (derniers résultats 19/19 et 8/8 en v0.79). Tests web Python non relancés.

Recette réelle Chrome/Packet Tracer à effectuer. Ce correctif supprime la fermeture silencieuse ; il ne prétend pas réparer le refus HTTP 400 dont la cause reste inconnue. Relever le message désormais affiché dans l’onglet pour diagnostiquer le prérequis en échec. Un contrôle réel de connexion peut toujours être nécessaire et peut prendre du temps.
