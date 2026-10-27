# v0.80 — Propriétés d’imprimante

## Interface

La fenêtre de propriétés possède un en-tête avec l’icône native et le nom de la file, des états de configuration textuels, puis les onglets Général, Port et Maintenance. Les réglages de file ne sont pas présentés comme une preuve de connectivité.

Les propriétés générales sont disposées en tableau de caractéristiques, les actions associées regroupées. Définir par défaut et Installer le pilote sont désactivés lorsque leur résultat est déjà obtenu. La maintenance sépare la réserve de papier des commandes du spouleur commun au poste. Les champs non applicables à PDF restent désactivés.

Les onglets exposent les rôles tablist/tab/tabpanel, leurs relations, la sélection et le parcours clavier par flèches, Début et Fin. L’onglet reste sélectionné lors d’une actualisation ; les champs non enregistrés ne sont pas des brouillons persistants.

## Comportement et limites

Aucun nouveau service ni contrôle réseau. Les opérations utilisent les mêmes routes et autorisations. Une fenêtre de propriétés reste attachée à sa file, indépendamment de la sélection dans la fenêtre principale.

Ce reste une simulation : le spouleur ne gère pas un processus Windows, le pilote n’est pas un véritable paquet et l’impression ne sort aucun document physique. Le panneau Port conserve un champ de configuration, pertinent pour cette tâche. La fenêtre Imprimer et les retours d’erreur des commandes restent à améliorer.

## Vérifications

- Test dédié : icône dans l’en-tête, onglets clavier et relations ARIA, absence de requête lors de la navigation, modification appliquée à la bonne file après changement de sélection, maintien de l’onglet et restrictions PDF.
- 40 suites JavaScript passent.
- Les 19 tests du cœur et 8 ateliers ont passé lors de la validation v0.79 ; ces fichiers Python ne changent pas en v0.80. Ils ne sont pas relancés pour cette passe UI. Les tests web Python ne sont pas relancés.
- Aucun rendu navigateur graphique vérifié dans cet environnement.

## Recette dans Chrome

1. Ouvrir les propriétés d’une imprimante réseau et d’une file PDF.
2. Vérifier icône, lisibilité, largeur réduite, boutons et défilement dans la fenêtre.
3. Parcourir les onglets avec Tab puis flèches, Début et Fin ; le focus doit suivre la sélection.
4. Modifier le port de la première file après avoir sélectionné une autre imprimante dans la liste : la modification doit concerner uniquement la première.
5. Vérifier que papier et port réseau sont indisponibles pour PDF et que les contrôles de maintenance fonctionnent comme avant.
