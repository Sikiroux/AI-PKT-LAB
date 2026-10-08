# v0.47.1 — Repérer l’intervention active

## Ce qui change

- Une synthèse indique le nombre de demandes à préparer et identifie le scénario actif.
- Le bouton **Revenir à l’intervention active** sélectionne le bon ticket et retire les filtres qui pourraient le masquer.
- La liste présente le scénario actif d’abord, puis les demandes à préparer dans leur ordre d’arrivée, puis les autres interventions et les tickets clos.
- Les badges distinguent **À préparer**, **Scénario actif** et **Intervention clôturée**, indépendamment du statut de traitement. Mettre un scénario en attente ne libère pas l’environnement pour une seconde panne.
- Les filtres **Demandes à préparer** et **Intervention active** permettent de séparer ces étapes.
- Le bouton de prise en charge d’une autre demande n’apparaît pas tant qu’un scénario est actif ; une explication le remplace. La protection serveur de v0.47 reste effective.
- Les paramètres Applications, Multi-services et Intervalle aléatoire apparaissent seulement lorsqu’ils servent au catalogue sélectionné. Le niveau reste disponible pour les variantes multi-services du catalogue Varié.
- Le compte à rebours des arrivées se rafraîchit sans reconstruire les formulaires ni effacer une note en cours de saisie. Il indique la prochaine **tentative**, car le plafond peut différer l’arrivée.
- Les messages de préparation et de contrôle précisent l’opération en cours, notamment les réparations d’accessoires sans ping.

La procédure **Comprendre la file des tickets** est aussi disponible dans l’application Documentation du bureau simulé. Elle ne dévoile aucune cause de panne.

## Comportements conservés

La seed, le catalogue, le rythme de génération et les sauvegardes ne changent pas. Plusieurs demandes peuvent attendre, mais un seul exercice est préparé à la fois. Les arrivées ne modifient pas les postes. Les sessions restent mises en pause au redémarrage du logiciel.

## Vérification manuelle

Dans une entreprise contenant plusieurs tickets, mettre le scénario actif en attente : il doit rester identifiable en tête et empêcher la préparation d’un autre scénario. Utiliser le bouton de retour après filtrage/recherche. Changer le catalogue et le type d’intervalle ; seuls les paramètres utiles doivent rester visibles. Écrire une note pendant plusieurs secondes : le compte à rebours ne doit pas interrompre la saisie.

Tests automatiques : règles de classement, filtres d’étapes via leurs helpers, retour à l’intervention, réglages conditionnels, compte à rebours et disparition du panneau après changement d’environnement. Rendu visuel final à tester dans ton navigateur ; les tests DOM ne remplacent pas cette vérification.
