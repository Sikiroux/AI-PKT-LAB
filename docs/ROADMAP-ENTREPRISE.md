# Roadmap actuelle — entreprise persistante

État livré : v0.62.2, correctif des barres de titre et rapprochement visuel de la maquette après la première passe du bureau et de l’annuaire. Les numéros futurs sont prévisionnels. Les anciennes correspondances 0.44–0.52 sont remplacées par ce tableau ; les guides de version conservent l’historique exact.

## Livré

| Bloc | Portée réelle |
|---|---|
| Réseau et services | Pont Packet Tracer, AD, fichiers, DNS, impression, FTP et déploiement simulés. Contrôle discret via Packet Tracer ouvert, pas moteur indépendant sans interface. |
| Entreprise v0.50 | 30 employés et six services dans les nouvelles entreprises, postes câblés, incidents avant signalement, incidents simultanés et impact métier. Les anciennes sauvegardes gardent leur effectif. |
| Tickets v0.49–0.52 | Liste, écran partagé facultatif, suivis, tâches, priorité, propositions de solution, distinction Résolu/Clos et réouverture. Confirmation du demandeur déclarative. |
| Parc et accessoires | Stock, préparation liée à l’atelier, remise/restitution, accessoires et incidents locaux. La remise ne remplace pas encore un poste connecté dans PT. |
| Bureaux v0.53–0.57 | Documentation recherchable, Explorateur/Annuaire, imprimantes/FTP, DNS et propriétés du poste ; formulaires séparés des listes pour les blocs refondus. |
| Services et interfaces v0.59 | Lecture des cinq états de service, journal existant limité à 100 événements, outils associés, fenêtres de quotas/capacité et raccordement/VPN, trois vues du parc. [Recette et limites](V059-SERVICES-ET-CONSOLES.md). |
| Entreprise et arrivées v0.62 | Politiques seed persistées, mail interne et licences administrés, demandes d’arrivée dans Tickets, première connexion de formation, contrôles des moteurs AD/mail/stock. Pas de SMTP réel, ni nouveau PC connecté. [Recette](V062-ARRIVEES-ET-SERVICES.md). |

Les interfaces sont partielles. Le journal de session n’est pas un Observateur d’événements Windows complet. Les moteurs ne reproduisent pas toutes les fonctions des services réels. Recette visuelle Windows/PT9 requise avant de déclarer l’ergonomie validée.

## Suite, par priorité

| Version envisagée | Objectif | Critère de sortie |
|---|---|---|
| 0.62.x | Recette et hotfixes | Blocages, ciblage, sauvegardes, scroll et preuves réseau corrigés avec reproduction et test ciblé. |
| 0.63 | Vie d’entreprise | Mobilités/départs, horaires, demandes et impacts métier ; architectures réseau réellement plus diverses. |
| 0.64 | Conversations | Dialogue scénarisé enrichi, modèle local facultatif ; le client ne décrit que ce qu’il sait. |
| 0.65 | Bilan pédagogique | Compétences, explications et portfolio d’interventions exportable. |

À approfondir transversalement : interfaces des permissions et comptes FTP, détails par article du parc, diagnostics par service, événements structurés par équipement, type de démarrage/dépendances de service, supervision/salle serveurs avec métriques reliées à la simulation. La livraison 0.59 amorce ces outils ; elle ne clôt pas ces objectifs.

## Principes

- La seed crée l’état initial ; l’historique sauvegardé gouverne ensuite la session. Même seed et version de génération : même état initial.
- Personne, compte et appareil ont des identifiants stables. Affectation et emplacement sont séparés du nom technique.
- Le moteur produit les symptômes et vérifie les résultats. Un LLM ne répare pas le réseau, n’accorde pas de droits et ne valide pas un ticket.
- Une preuve inconnue n’est pas un échec observé ; un ping ne prouve ni SMB, ni FTP, ni l’identité.
- Les employés modélisés, appareils représentés et éléments administratifs doivent être distingués.
- Tests automatisés et recette réelle PT restent distincts. Suites requises avant commit, sauvegarde avant migration.

Différés : appareil définitivement HS, Packet Tracer entièrement sans interface, appels IA et terminal IOS web complet.

À prolonger après v0.62 : boîte personnelle depuis le bureau client avec identité authentifiée, incidents mail procéduraux, quotas éditables, demandes de plusieurs groupes dans l’interface, validation du responsable, achats/extension du stock et raccordement PT du poste remis. Le changement de mot de passe d’arrivée est un essai depuis la console du technicien, pas une nouvelle session Windows.


## Correctif prioritaire v0.62.3

Livré dans le générateur : disposition compacte des 30 postes en deux groupes correspondant aux switches réels, icônes SVG natives dans les barres de titre. Recette PT9 à effectuer avant de qualifier le placement de validé. Les réseaux déjà sauvegardés restent inchangés. La roadmap 0.63–0.65 reste en place.
