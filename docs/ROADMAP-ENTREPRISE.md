# Roadmap actuelle — entreprise persistante

État livré : v0.78. Les correctifs issus des audits ont commencé : catalogue, observations et surveillance bornée. Le comportement réel dans Packet Tracer 9 reste à valider. Les blocs suivants nécessitent le cadrage du modèle commun avant toute extension du moteur d'entreprise.

## UI/UX en cours

v0.78 : client FTP en navigation local/distant, recherches, sélection explicite, transferts et distinction session/transport/service. Tests sur DOM simulé ; recette visuelle requise. [Détails](V078-CLIENT-FTP-UI.md).

v0.77 : fiche ticket en quatre vues, demande isolée, actions accessibles, résultat attendu mis en avant et impact repliable. Tests JavaScript verts ; recette visuelle Chrome encore à faire. [Détails](V077-FICHE-TICKET-UI.md).

À poursuivre : applications du bureau, états de connexion compréhensibles et finitions communes. La refonte complète UI/UX n’est pas considérée terminée.

## Stabilité en cours

v0.76 : téléchargement FTP nommé, trace de réussite par poste/environnement et contrôle de la copie locale ; service seul insuffisant. Impression d’un document et transferts de tous les utilisateurs d’une panne partagée restent à approfondir. [Recette et limites](V076-TRANSFERT-FTP.md).

v0.75 : résolution du nom et lecture du document contrôlées séparément pour les tickets DNS simultanés ; retest client cohérent. FTP et impression restent à approfondir. [Recette et limites](V075-DNS-ET-DOCUMENTS.md).

v0.74 : validation AD liée à une authentification du demandeur sur son poste ; libellés des autres contrôles précisés. À approfondir ensuite : validation du transfert FTP, de l’ouverture de document après résolution DNS et de l’impression demandée. [Portée et recette](V074-CONFIRMATION-SESSION-AD.md).

v0.73 : demandeur historique conservé, vérification liée au compte du signalement, distinction liaison/IP dans le dialogue des incidents simultanés. [Recette et limites](V073-IDENTITE-DU-SIGNALEMENT.md).

v0.72 : contrôles indépendants des appareils manquants ; mauvais fichier toujours refusé et mutations strictes. [Recette PT9](V072-CONTROLES-INDEPENDANTS.md).

v0.71 : mobilité/VPN du technicien séparés de la connexion Windows des employés ; invalidation des preuves de tous les bureaux. [Recette PT9](V071-TRANSPORT-ET-SESSIONS.md).

v0.70 : priorité temporaire aux bureaux visibles dans la surveillance du parc, avec équité conservée. Recette PT9 nécessaire ; ce correctif ne clôt pas le bloc stabilité ni la cohérence complète des incidents. [Détails](V070-SURVEILLANCE-BUREAU.md).

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

## Avancement depuis les audits

- v0.62.8 : placement commun entreprises/ateliers de services, à contrôler visuellement dans PT9.
- v0.63 : cinq VLAN et routage générés pour les nouvelles grandes entreprises ; recette réelle en attente. Pools DHCP prêts, postes encore statiques ; suivi des baux et Wi-Fi non livrés.
- v0.63.1 : mutation locale et signalement récupérable dans la même sauvegarde ; premières formulations et chronologie corrigées. Les mutations PT transactionnelles restent à faire.

- v0.64 : première découverte différée des pannes locales périodiques ; réévaluation avant signalement et suppression des demandes devenues inutiles. Horloge métier, activités détaillées et événements physiques restent à développer.

- v0.65 : dialogue contextualisé des incidents simultanés, questions par famille, ressource et essais datés. Dialogue libre/LLM, scénarios historiques et salariés autonomes restent hors de ce bloc.

- v0.66 : preuves réseau communes et ciblées, sessions utilisateur liées au compte/poste, VPN préservé lors des observations inconnues. Bloc ciblé ; recette réelle et cohérence des autres dépendances restent nécessaires.

- v0.67–0.68 : ressources et retests explicites dans les nouveaux tickets, contexte repliable, tokens communs, bibliothèque documentaire et inspecteur des comptes FTP. Livraison ciblée ; refonte des autres consoles et recette visuelle encore nécessaires.

- v0.69 : indices contextualisés et suivis, corrections volontaires de tous les incidents actuels, bilan des contrôles et aides, export HTML. Corrections des scénarios actifs AD/fichiers/DNS/multi-services ; autres variantes et évaluation approfondie des compétences restent à développer.

## Suite issue des deux audits

Contrat de référence : [Modèle d’entreprise](MODELE-ENTREPRISE.md). Spécification préparée sur la v0.62.7 ; la majorité des fonctions décrites reste à implémenter.

| Version envisagée | Objectif | Critère de sortie |
|---|---|---|
| 0.63 | Réseau V2 et placement commun labs/entreprise | État sain vérifié dans PT, VLAN/routage/DHCP et variante Wi-Fi selon matériel validé. |
| 0.64 | Événements, activités et signalements | Panne confirmée avant découverte, impacts réels, regroupement et reprise sans double injection. |
| 0.65 | Dialogue contextualisé | Chronologie, ressource précise, essais et retest ; aucune connaissance de cause cachée. |
| 0.66 | Cohérence des services | Une source de vérité pour chaque paramètre et des dépendances propres à chaque action. |
| 0.67 | Tickets et textes | Symptômes compréhensibles, fiche simplifiée, priorité existante conservée, confirmation utile. |
| 0.68 | Design system et applications | États et composants cohérents, scroll/focus et applications encore dominées par les formulaires revus. |
| 0.69 | Consolidation pédagogique | Aides contextualisées, bilan justifié et export d’interventions. |

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

Livré dans le générateur : disposition compacte des 30 postes en deux groupes correspondant aux switches réels, icônes SVG natives dans les barres de titre. Recette PT9 à effectuer avant de qualifier le placement de validé. Les réseaux déjà sauvegardés restent inchangés. Ces anciens numéros sont remplacés par le tableau issu des audits ci-dessus.


## Affinage UI v0.79

Files d’impression : recherche locale, filtres, compteurs, conservation lors de l’actualisation, libellé du mode hors connexion corrigé. Rendu navigateur à vérifier ; propriétés et explication des codes techniques restent à améliorer.


## Affinage UI v0.80

Propriétés d’imprimante : identité visuelle, états explicites, onglets accessibles, actions générales et maintenance regroupées. Rendu Chrome à vérifier. Fenêtre Imprimer et messages des commandes encore à améliorer.


## Affinage UI v0.81

Boîte Imprimer : résumé, états vides, protection double envoi et distinction accepté/imprimé. Rendu Chrome à vérifier. Les erreurs des autres commandes d’administration et la cohérence visuelle des autres applications restent à traiter.
