# Roadmap prévisionnelle — entreprise persistante

Les numéros ci-dessous sont des objectifs, pas des promesses de fonctionnalités livrées. Les moteurs AD, fichiers, DNS, impression, FTP et déploiement existent déjà ; les prochaines étapes les rendent cohérents et plus fidèles dans l’interface. Une version intermédiaire peut remplacer plusieurs petits incréments.

## Livraison regroupée v0.43

- Correctifs après v0.41 : processus ICMP réellement disponible et icônes OS.js.
- Diagnostics : identité, preuves datées, prérequis distincts et export limité.
- Ticket épinglé facultatif et ouverture du bureau distant en grand.
- Pas de nouvelle migration de sauvegarde dans cette livraison.

## Livraison v0.44

Référentiel des personnes représentées, comptes, appareils et tickets ; identifiants logiques reproductibles et portée par environnement. Le personnel complet et l’historique de remplacement matériel restent à étendre. Voir [le contrat et les limites](V044-REFERENTIEL.md).

## Livraison v0.45

Console d’annuaire : utilisateurs, groupes, ordinateurs, OU, historique, stratégie et refus des modifications périmées. Messagerie et licences restent au bloc v0.47. Voir [le périmètre](V045-ANNUAIRE-CONSOLES.md).

## Livraison v0.46

Premier cycle de réserve/remise/restitution et consultation du parc commun. La préparation est déclarative ; le lien avec le déploiement visuel et le remplacement des postes connectés restent à développer. Voir [le périmètre](V046-PARC-STOCK.md).

## Livraison v0.46.1

L’atelier visuel est lié à un article du stock ; la remise exige son bilan réussi. La restitution démarre un nouveau cycle protégé contre les anciennes fenêtres. Le remplacement du poste connecté reste à réaliser. Voir [le périmètre](V0461-STOCK-DEPLOIEMENT.md).

## Livraison v0.46.2

Fiches des postes et six procédures intégrées au bureau. Le coffre d’accès locaux, les périphériques et leurs interventions sont les prochains blocs avant l’extension des services. Voir [le périmètre](V0462-FICHES-DOCUMENTATION.md).

## Suite envisagée

### Priorité revue après la recette v0.47.2

Avant mail et licences : fiabiliser la recette, puis retravailler les tickets et le placement. Les numéros ci-dessous sont des objectifs historiques à replanifier, pas un inventaire des versions livrées.

1. Tickets : liste filtrable, fiche structurée, suivi et solution ; contrôles pédagogiques séparés. La fiche épinglée actuelle reste en lecture seule.
2. Demandes contextualisées : auteur et bénéficiaire distincts, impact, service, échéance et résultat attendu. La documentation actuelle explique le simulateur ; la base de connaissances propre à l'entreprise reste à générer.
3. Nommage indépendant des personnes : nom technique stable, affectation et localisation séparées. Ne pas renommer les sauvegardes existantes automatiquement.
4. Placement compact par zone : branches lisibles, marge pour les libellés, limitation des croisements et variantes. Augmenter ensuite la taille et la diversité réelle des réseaux.

Ces étapes restent à implémenter ; elles ne sont pas livrées par le nettoyage.

| Version | Objectif | Critère de sortie |
|---|---|---|
| 0.44 | Référentiel procédural commun | Un employé, son compte, son matériel et ses tickets partagent des identifiants stables. Même seed et même version de génération : même état initial. |
| 0.45 | Affiner les applications d’administration | Affiner la console d’annuaire et les liens des fiches utilisateurs. Définir les références réelles et limites de fidélité. |
| 0.46 | Parc matériel et préparation | Premier cycle stock/remise/restitution livré ; association au déploiement visuel et remplacement réseau encore à faire. |
| 0.47 | Mail, licences et documents | Comptes mail et conventions, places disponibles, documents de remise et validation des résultats attendus. |
| 0.48 | Arrivée d’employé complète | Préparer compte, accès, mail, licences, poste, documents et livraison à partir d’une demande procédurale. |
| 0.49 | Événements d’entreprise | Arrivées, mobilités et départs produisent des demandes cohérentes ; incidents collectifs regroupés ; pause et fréquence réglables. |
| 0.50 | Conversations | Dialogue scénarisé fiable, puis modèle local facultatif. Le client décrit seulement ce qu’il sait ; la clôture dépend du moteur. |
| 0.51 | Supervision et salle serveurs | Observations PT et services simulés distingués ; métriques reliées à l’activité et aux incidents, sans valeurs décoratives présentées comme mesures. |
| 0.52 | Formation | Difficultés, procédures internes, aide facultative, bilan des interventions, parcours de départ et changement de service. |

## Principes

### Incrément v0.48.1

Noms indépendants des personnes et du préfixe de site pour les nouvelles entreprises ; placement logique par branche avec variantes déterministes. Compatibilité de présentation des anciennes sessions conservée. La diversité d'architecture, la taille des réseaux et les aménagements physiques restent à développer. Voir [le périmètre](V0481-NOMS-ET-PLACEMENT.md).

### Premier incrément d'interface v0.48

La file comparative et la recherche par demandeur/poste sont livrées ; la fiche complète s'affiche sous la file. Les règles de traitement restent inchangées. La refonte métier complète, le nommage et les topologies ne sont pas considérés comme terminés. Voir [le périmètre v0.48](V048-FILE-DES-TICKETS.md).

Le scénario décrit une entreprise complète avec ou sans personnel IT interne. Le portable du technicien est distinct du personnel de l’entreprise. Tous les employés n’ont pas nécessairement un appareil Packet Tracer dédié ; le périmètre modélisé doit être explicite.

La seed crée l’état initial, puis l’historique enregistré devient la vérité de la session. Une réparation, un nouvel employé ou une licence attribuée ne sont pas effacés par une régénération arbitraire. Les événements futurs utilisent leurs propres tirages reproductibles et leur ordre est sauvegardé.

Le moteur vérifie les résultats ; un LLM ne peut pas créer une réparation, accorder des droits ou valider un ticket. Les symptômes proviennent des états réels de la simulation.

Les demandes de service et changements planifiés complètent les incidents. La préparation d’un nouveau poste doit être associée à un employé et à un matériel identifié, pas seulement à une case « terminé ».

## Hotfixes

Corriger en priorité les blocages, erreurs de preuve, pertes de sauvegarde et fenêtres inutilisables. Chaque correction significative a une reproduction et un test ciblé. Sauvegarder avant migration. Exécuter les suites requises avant commit ; distinguer tests automatisés et validation réelle dans PT.

Différés : appareil définitivement HS, Packet Tracer complètement sans interface, appels IA, terminal IOS web complet. Le contrôle discret utilise Packet Tracer ouvert et son IPC : ce n’est pas un moteur PT headless indépendant.

## Complément v0.46.3

Équipement local livré pour les postes simulés : accessoires identifiés, branchement, entrée vidéo, aperçu local, remplacement, stock d’accessoires et historique. Les effets restent indépendants de RDP et du réseau. À poursuivre : coffre des accès locaux, demandes procédurales liées aux accessoires, puis mail/licences et parcours d’arrivée.

## Complément v0.46.4

Comptes et registre d’accès locaux de formation intégrés aux fiches et liés à la vue Ordinateurs de l’annuaire. Neuf incidents procéduraux d’accessoires externes proposés explicitement dans le catalogue Applications, avec clôture locale sans ping. Prochain bloc : mail et licences, puis documents de remise et arrivée d’employé complète. Une session locale avec un bureau sur place complet et les composants intégrés du portable restent à développer.

### Documentation : premier incrément v0.48.2

Répertoire factuel issu de l’environnement, nommage, domaine et serveur de fichiers accessibles dans Documentation. Le manuel reste disponible. Les politiques propres à chaque société, les procédures métier générées, les recherches contextuelles depuis un ticket et la gestion documentaire éditable restent à développer : ce premier incrément ne les remplace pas.
