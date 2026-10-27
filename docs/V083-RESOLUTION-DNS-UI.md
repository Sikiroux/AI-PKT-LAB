# v0.83 — Résolution DNS

L’écran affiche la requête réellement exécutée (nom, type, poste source), un résultat textuel et des réponses tabulaires. La couleur complète le texte sans le remplacer. Les détails JSON sont repliés dans une section technique.

La saisie et le dernier résultat sont conservés pendant l’ouverture de la console, y compris après une actualisation ou un changement de section. Un ancien résultat est explicitement décrit comme résultat du dernier test ; les TTL ne sont pas un compte à rebours. Modifier la saisie ne change pas la requête affichée avec le résultat précédent.

Aucun test automatique. Résoudre est désactivé si le nom est vide ; les contrôles sont désactivés pendant la requête pour éviter les doublons. Une erreur de transport remplace le résultat précédent par « Test non confirmé ». Le cache non renseigné n’est pas présenté comme une interrogation réellement effectuée sur le serveur.

Un vidage de cache confirmé retire le résultat et invite à relancer un test. Un refus conserve le résultat précédent et affiche le code. Ce bouton ne vide que le cache de la source indiquée ; il n’accorde aucun droit supplémentaire.

## Validation et limites

Test dédié : absence de résolution automatique, requête figée, conservation après actualisation, état inconnu, erreur, double clic, nom vide et vidage refusé/confirmé. 43 suites JavaScript passent après correction d’une erreur de syntaxe dans le nouveau test.

Aucune règle Python, route ou autorisation modifiée. Derniers résultats cœur et ateliers : 19/19 et 8/8 en v0.79, non relancés pour cette passe UI. Tests web Python non relancés. Résolution réussie ne signifie pas accès au fichier réussi.

## Recette Chrome restante

Vérifier lisibilité et défilement dans une fenêtre étroite. Lancer une requête, modifier le nom sans résoudre : l’ancien résultat doit conserver son nom d’origine. Changer de section et revenir. Tester une réponse en cache, un échec et une observation inconnue. Vérifier les contrôles pendant la requête et le message après vidage du cache. Aucun rendu graphique n’a été vérifié dans cet environnement.
