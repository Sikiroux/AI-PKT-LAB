# Contrat du modèle d’entreprise — après les audits v0.62.5

Statut : spécification de la prochaine refonte, pas fonctionnalités livrées.
Base logicielle : v0.62.7. Ce document fixe les règles pour les blocs 0.63–0.69.

## 1. Résultat attendu

Une entreprise possède des employés, des appareils, des services et des activités. Un événement modifie une ressource ; ses dépendances déterminent les activités affectées. Un employé rencontre un symptôme lorsqu’il utilise cette ressource, puis le signale. Le ticket conserve ce signalement et accompagne l’intervention. Prendre en charge un incident ne crée pas sa panne.

Le générateur de labs reste disponible. Ses scénarios ne deviennent utilisables dans l’entreprise persistante qu’après adaptation et recette : sélection d’une cible existante, effet observable, réparation possible et contrôle des éléments initialement sains.

## 2. Trois informations différentes

| Couche | Contenu | Utilisation |
|---|---|---|
| État de référence | Configurations PT, états des moteurs simulés, historique des mutations | Calcul des effets et validation ; causes cachées réservées au moteur |
| Observation | Contrôle daté, appareil source, cible, résultat, méthode et portée | Ce que le technicien a réellement vérifié |
| Connaissance du client | Symptômes rencontrés, moment, message, essais, observations de collègues | Description et réponses du client |

Un contrôle absent ou périmé ne crée pas un incident réseau. Une absence de signalement ne signifie pas que tout fonctionne. Un succès ICMP n’est pas une preuve SMB, FTP, DNS applicatif, d’identité ou d’affichage.

## 3. Identités et relations

Réutiliser le référentiel existant au lieu de créer un second annuaire parallèle.

| Objet | Identité stable | Relations |
|---|---|---|
| Entreprise | environment_id | Périmètre de toutes les autres identités |
| Employé | employee_id | Compte, service métier, horaires, activité, affectations |
| Compte | account_id | Employé ; droits et sessions distincts de l’appareil |
| Appareil | asset_id et serial PT si représenté | Emplacement, ports, affectation, périphériques |
| Ressource | resource_id | Partage précis, imprimante/file, dépôt FTP, service, application ou fichier local |
| Affectation | assignment_id | Employé–appareil avec début et fin ; historique conservé |
| Incident | incident_id | Événement, ressources affectées, signalements et preuves |
| Signalement | report_id | Demandeur, appareil utilisé, ressource, symptôme et date |
| Ticket | ticket_id | Signalements liés, traitement, solution et confirmation |

Un nom ou prénom n’est jamais une clé de jointure. Le nom technique du PC ne change pas lors d’un changement d’utilisateur. La demande désigne le poste utilisé au moment du problème ; une affectation ultérieure ne réécrit pas cette histoire. Un remplacement physique crée un nouvel appareil et conserve l’ancien ; le rôle « client » ne constitue pas son identité. La migration doit réconcilier le référentiel actuel fondé en partie sur les rôles avec les articles du stock, sans écraser leur historique.

## 4. Source de vérité

| Domaine | Référence | Règle d’intégration |
|---|---|---|
| Câble, port, VLAN, trunk, routage, IP, DHCP, DNS configuré sur un poste PT | Packet Tracer | Mutation réelle prise en charge et réparation depuis PT ; aucun état web contradictoire |
| Réponse réseau actuelle | Observation PT datée | Pas de disponibilité inventée depuis la seule configuration |
| AD, droits de partage, fichiers simulés, mail/licences, état applicatif | Moteur web correspondant | Opération existante, contrôle métier, révision et persistance |
| Écran, souris et clavier simulés | Moteur périphériques | État matériel séparé de la connectivité du PC |
| Affectation et emplacement | Référentiel du parc | Ne constituent ni une autorisation ni une preuve réseau |
| Expérience utilisateur | Activité et observations connues du client | Ne dévoile jamais les champs internes de cause |

Pour un paramètre présent dans PT et dans un adaptateur, l’adaptateur doit refléter l’observation de PT. Une différence doit être signalée comme telle ; elle ne doit pas produire deux valeurs prétendument vraies. Exemple prioritaire : DNS du poste dans PT et DNS affiché dans la console simulée.

## 5. Dépendances : exigences propres à chaque action

Il ne suffit pas d’associer chaque personne à une liste de services globalement requis.

| Action utilisateur | Dépendances minimales | Ce qu’elle ne prouve pas |
|---|---|---|
| Lire un fichier local | Poste et stockage simulés, application adaptée | Disponibilité du réseau ou d’AD |
| Lire un partage par son nom | Résolution adaptée, chemin réseau, service fichiers, identité/session selon politique, deux couches de droits | Impression ou accès FTP |
| Se connecter à un compte du domaine | Réseau et service d’annuaire selon mode de connexion ; règles du compte | Droits sur tous les partages |
| Utiliser une session déjà ouverte | État de la session et exigences de l’action | Contact permanent avec AD pour chaque clic |
| Imprimer sur une imprimante réseau | Document, file/spouleur applicables, chemin réseau, imprimante | Tous les autres services accessibles |
| Utiliser une imprimante locale/PDF | Dépendances locales de cette file | Connectivité vers l’imprimante réseau |
| Déposer un document via FTP | Liaison, service, compte FTP, droits, canaux nécessaires | Authenticité d’une session AD |
| Travailler sur écran externe | Sortie vidéo et périphérique sélectionné, alimentation, entrée, liaison | Que le PC soit inaccessible au réseau |
| Prendre la main à distance | Liaison technicien–cible, service distant et autorisation technique | Droits de l’utilisateur sur ses documents |

Une panne AD ne doit pas fermer arbitrairement toutes les sessions déjà ouvertes. Une nouvelle authentification et un accès à une ressource protégée ont leurs propres règles. Une fonction non modélisée reste une limite documentée, sans simuler une fausse règle Windows.

## 6. Horloges et reproduction

Deux horloges distinctes sont obligatoires :

- Temps réel : âge des preuves PT, délais du pont, sessions techniques et jetons de sécurité.
- Temps d’entreprise : horaires, activité, événements planifiés, délai avant découverte et signalement.

L’accélération du temps d’entreprise ne renouvelle pas une preuve ICMP et n’étend pas une session authentifiée. La pause empêche de nouveaux événements métier ; les contrôles explicites restent disponibles. Le fast-forward PT est une action explicite distincte, globale à PT, et ne constitue pas l’horloge de l’entreprise.

Une expiration pédagogique de mot de passe est un événement planifié : sa réalisation passe par les règles existantes du moteur AD, avec une date cohérente pour ce moteur. Ne pas réinterpréter silencieusement ses timestamps lors d’une migration.

Conserver : seed initiale, version du générateur, version du modèle, compteurs des flux aléatoires séparés, horloge métier, événements, décisions d’injection et résultats. Même seed signifie même état initial, pas même session après des interventions différentes. La reproduction d’un incident nécessite la sauvegarde ou le journal de décisions, et les observations PT ne sont pas déterministes par déclaration.

## 7. Cycle d’un incident

| Étape | Déclencheur | État enregistré |
|---|---|---|
| Planifié | Tirage admissible ou événement programmé | Cible stable, préconditions, date métier, décision enregistrée |
| Mutation en attente | Préconditions vérifiées | Demande identifiée vers le moteur ou le pont |
| Réalisé | Mutation confirmée | Changement exact, date, révision ou confirmation PT |
| Effets recalculés | Changement de ressource | Activités possibles, dégradées ou bloquées |
| Découvert | Employé tente une action dépendante | Symptôme réellement rencontré, message et ressource |
| Signalé | Délai de signalement écoulé | Nouveau signalement ou rattachement à un incident existant |
| Pris en charge | Action du technicien | Affectation du ticket ; aucune injection |
| Rétabli techniquement | Contrôles pertinents positifs et récents | Preuves liées à la cible, action et solution proposées |
| Résolu | Solution soumise | Confirmation attendue du demandeur |
| Clos | Retest client positif et acceptation selon politique | Résultat métier, auteur et date |
| Réouvert | Retest négatif ou réapparition documentée | Nouvelle observation, même historique conservé |

Les demandes de service, comme une arrivée d’employé, restent des demandes : elles n’exigent pas de panne préalable. Un exercice de lab déclenché volontairement reste identifié comme exercice, distinct d’un événement d’entreprise.

Ne pas relancer aveuglément une mutation PT après une réponse perdue : état « résultat non confirmé », observation puis réconciliation. Aucun ticket ne prétend qu’une panne précise a été injectée sans confirmation. L’opération et son identifiant doivent pouvoir être repris après sauvegarde sans seconde injection.

## 8. Activités et priorité

Chaque activité définit ses ressources requises, ses alternatives et les tâches réalisables hors réseau. Calculer l’impact depuis ces dépendances et les employés présents, sans gonfler l’effectif à trente par défaut.

Une perte du partage bloque la tâche qui exige ce partage ; elle ne bloque pas automatiquement le mail ou les fichiers locaux. Une alternative valide peut rendre une activité dégradée plutôt que bloquée. Le client peut travailler ailleurs tout en attendant l’intervention.

Conserver la matrice impact/urgence existante. L’impact calculé est une proposition documentée ; le technicien garde une classification justifiée. Les délais de traitement sont distingués du délai de découverte et du temps de réparation. Les pauses d’un ticket en attente suivent la politique de délai définie, pas une règle implicite commune à tous les chronomètres.

## 9. Signalements, doublons et incidents communs

La clé de regroupement utilise environnement, événement/cause commune confirmée par le moteur et ressource affectée. Le même texte ou la même famille « fichiers » ne suffit pas.

- Un nouvel essai sur la même ressource pour le même incident enrichit le signalement existant.
- Plusieurs personnes affectées par le même trunk produisent un incident commun et des signalements liés.
- Deux problèmes distincts d’un employé restent possibles ; la cadence évite toutefois les séries artificielles sur la même personne.
- Si une panne commune explique une indisponibilité, ne pas injecter parallèlement une panne applicative identique juste pour fabriquer un second ticket.
- Un incident silencieux peut exister avant sa découverte. Les pannes ne disparaissent pas parce que personne ne les a acceptées.

Ne pas appeler systématiquement ce regroupement un objet « Problème » GLPI : un problème au sens de l’outil et un incident parent sont des objets différents. Le simulateur conserve son modèle interne, présenté honnêtement.

## 10. Dialogue client

Le dossier de connaissance contient : activité tentée, ressource, appareil, premier échec, dernière réussite connue, message affiché, essais avec résultats, observations directes et propos rapportés de collègues.

Questions pertinentes selon la famille : « Quel dossier et depuis quelle application ? », « Est-il sur ton PC ou sur le partage ? », « Quel message apparaît ? », « Cela fonctionnait à quelle heure ? », « Ton écran affiche-t-il son menu ? », « Après cet essai, que vois-tu ? ».

Une réponse peut être « Je ne sais pas ». « Avant mon signalement » n’est pas une chronologie exploitable. Les réponses évoluent après un essai ou un événement et restent cohérentes avec l’historique. La vue du technicien sur les contrôles est séparée des paroles du client.

Un éventuel LLM reformule uniquement un dossier de faits filtrés. Il ne lit pas la cause cachée, ne modifie aucun moteur et ne valide pas un ticket. Ce contrat ne nécessite pas de LLM pour fonctionner.

## 11. Trois scénarios de référence

### A. Retour du courant et écran noir

Préconditions : poste câblé sain, écran externe avec politique de remise sous tension manuelle explicitement modélisée, employé affecté au poste. Les appareils définitivement HS restent hors de ce premier scénario.

| Temps métier | Événement ou action | Conséquence observable |
|---|---|---|
| 14:10 | Coupure de courant simulée du site | Activités concernées suspendues ; journal événementiel |
| 14:25 | Courant rétabli | Ressources PT contrôlées ; pas de succès présumé avant preuve |
| 14:27 | Poste disponible, écran externe resté éteint | Le réseau peut répondre alors que l’affichage local manque |
| 14:31 | L’employé revient et tente de travailler | « Mon écran reste noir alors que mes collègues ont repris. » |
| 14:33 | Signalement | Ticket ciblant le poste et son écran, activité empêchée |
| Intervention | Identification écran/PC, alimentation, entrée et câble ; observation du menu écran | Hypothèses distinguées ; un ping positif ne conclut pas « écran en panne » |
| Retest | Écran rallumé, contenu visible, application métier utilisable | Rétablissement constaté puis confirmation client |

La coupure est un événement métier tant que l’alimentation réelle des appareils PT n’est pas prise en charge et validée. Elle ne doit pas être présentée comme coupure réseau réellement injectée. Ne jamais éteindre un appareil PT impossible à rallumer depuis son interface. Une variante réseau associée doit utiliser uniquement une mutation validée et être identifiée séparément.

### B. VLAN absent d’un trunk

Préconditions : architecture V2 saine, VLAN utilisateurs concerné explicitement défini, trunk et chemins connus, employés dépendants de ressources distantes. Les correspondances port–VLAN proviennent de PT.

| Temps métier | Événement ou action | Conséquence observable |
|---|---|---|
| 09:05 | Modification confirmée de la liste des VLAN autorisés sur un trunk | VLAN ciblé non transporté sur cette liaison ; les autres restent sains |
| 09:08 | Première tentative d’accès au partage | Échec réseau pour les postes dont le chemin traverse la liaison |
| 09:10 | Premier signalement | Nom du partage et erreur décrits, cause trunk non dévoilée |
| 09:12 | Autre employé rencontre le même problème | Signalement lié au même incident ; impact recalculé |
| Intervention | Comparer postes affectés/sains, ports access, VLAN et trunks | La panne se répare depuis PT ; pas de seconde panne AD ou fichiers injectée |
| Retest | VLAN restauré, contrôles ciblés et accès au partage rétablis | Tests métier et préservation des VLAN initialement sains |

L’accès par IP et l’accès par nom constituent deux essais distincts. Un cache DNS positif ne restaure pas un chemin réseau coupé. Une session ouverte peut rester ouverte sans pouvoir accéder à ses ressources.

### C. Mot de passe expiré et nouvelle connexion

Préconditions : compte actif, expiration pédagogique planifiée, réseau et annuaire disponibles, utilisateur identifié. Cette cause est distincte d’un compte désactivé ou verrouillé.

| Temps métier | Événement ou action | Conséquence observable |
|---|---|---|
| 08:30 | Expiration appliquée et persistée dans AD simulé | Politique de connexion exigeant un changement ; pas de coupure réseau |
| 08:34 | L’utilisateur ouvre une nouvelle session | Message de changement de mot de passe selon le moteur |
| 08:36 | Signalement | Message exact et poste utilisés, pas « compte indisponible » générique |
| Intervention | Vérification d’identité selon procédure ; distinguer expiration, verrouillage et désactivation | Procédure appropriée, pas d’attribution de droits supplémentaires |
| Retest | Changement conforme puis authentification avec le nouveau secret de formation | Ancien secret refusé, session correcte, accès limité aux droits existants |

Une session déjà ouverte ne devient pas automatiquement déconnectée à l’expiration. La simulation doit documenter les limites de son modèle de session, pas inventer une révocation Windows immédiate.

## 12. Architecture réseau V2 à construire

Pour trente employés : zones physiques compactes, switches d’accès selon capacité et emplacement, réseau serveur, VLAN utilisateurs/sensible/serveurs/invités/administration selon politique. Le VLAN n’est pas nécessairement un service métier et un switch n’est pas nécessairement réservé à un service.

Choisir le routage inter-VLAN après recette du matériel disponible : routeur avec sous-interfaces ou commutateur L3. Vérifier le nombre et la vitesse des ports pour tous les uplinks ; éviter de promettre quatre trunks Gigabit sur un matériel qui n’en offre que deux. DHCP pour les postes et adresses stables pour l’infrastructure selon le scénario. Une variante Wi-Fi exige une recette propre pour les modèles AP/WLC et leurs fonctions réellement disponibles.

Le générateur et l’entreprise utilisent un plan de placement commun : dimensions des icônes et libellés, centre de connexion, groupes compacts, marges et chemins des câbles. Le cadre 0–3900 est une enveloppe maximale indicative, pas une obligation d’étaler chaque petit réseau sur toute la surface. Les anciennes sauvegardes ne sont pas déplacées automatiquement.

## 13. Migration et intégration

1. Ajouter le schéma versionné et les journaux sans modifier les sauvegardes existantes.
2. Sauvegarder avant migration ; transformer les liens connus via identifiants stables, signaler les liens ambigus.
3. Migrer les incidents ouverts en conservant symptômes, affectation, événements et preuves datées. Ne pas les réinjecter.
4. Introduire un coordinateur unique ; réutiliser les moteurs AD/fichiers/DNS/périphériques et les adaptateurs.
5. Geler progressivement les anciens chemins après parité vérifiée ; ne pas les supprimer avant recette.
6. Réduire les doubles états et interrogations répétées des pages sans casser les opérations existantes.

Le schéma minimal ajoute clock, resources, activities, events, reports, incident_links et un journal de mutations avec revision et operation_id. Les credentials, états des services et preuves existantes restent dans leurs moteurs de référence. Une entrée du journal décrit une mutation ; elle n’est pas une seconde copie éditable de l’état. Les fonctions de synchronisation du référentiel ne doivent plus recréer les affectations initiales au détriment des remises, retours ou changements de poste enregistrés.

## 14. Critères d’acceptation du futur moteur

- Une panne confirmée existe avant le signalement ; prendre en charge ne mute rien.
- Un événement échoué ou non confirmé ne génère pas une fausse panne réussie.
- Aucun état réseau web ne contredit silencieusement le paramètre observé dans PT.
- Les symptômes désignent une ressource locale ou distante et une action précise.
- Une panne commune regroupe les signalements sans effacer leurs demandeurs.
- L’impact suit les activités dépendantes ; les autres restent possibles.
- Les réponses client proviennent exclusivement de son dossier de connaissance.
- Une sauvegarde/reprise ne double ni mutation ni signalement.
- L’accélération métier ne prolonge pas les preuves réelles.
- La clôture utilise preuve technique pertinente et confirmation métier selon politique.
- Les tests initiaux non concernés restent positifs après réparation.
- Les trois scénarios ci-dessus sont reproductibles et documentés, avec recette PT séparée pour les mutations réseau.

## 15. Ordre de livraison

0.63 : topologie V2, adaptateurs et placement ; état sain validé avant incidents.
0.64 : coordinateur événements/activités/signalements, premières mutations réseau et migration.
0.65 : dossier de connaissance et dialogue contextuel, retest client.
0.66 : cohérence des services, paramètres communs et dépendances par action.
0.67 : fiche ticket, textes, priorité et cycle de traitement.
0.68 : design system et applications restantes.
0.69 : aides contextualisées, bilan et portfolio.

Ce cadrage remplace les anciennes correspondances de versions ; les fonctionnalités non livrées restent indiquées comme telles.

## Références de fonctionnement

- GLPI, cycle de vie d’un ticket : https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketlifecycle
- GLPI, matrice du cycle de vie : https://glpi-user-documentation.readthedocs.io/fr/master/modules/assistance/lifecyclematrix.html
- Cisco, routage inter-VLAN via routeur : https://www.cisco.com/c/en/us/support/docs/lan-switching/inter-vlan-routing/14976-50.html
- Cisco, routage inter-VLAN sur Catalyst : https://www.cisco.com/c/fr_ca/support/docs/lan-switching/inter-vlan-routing/41260-189.html

Ces sources décrivent les produits réels. Elles ne certifient pas l’implémentation ni toutes les fonctions des appareils Packet Tracer. Les décisions d’architecture ci-dessus sont les choix du simulateur issus des deux audits.
