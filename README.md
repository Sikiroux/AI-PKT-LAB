# v0.71 — Sessions conservées lors des changements de transport

Déplacer le portable technicien ou déconnecter son VPN ne déconnecte plus le compte Windows de l’employé. Les anciennes preuves réseau sont invalidées sur tous les bureaux ; les actions restent suspendues jusqu’au rétablissement. [Détails et recette PT9](docs/V071-TRANSPORT-ET-SESSIONS.md).

# v0.70 — Surveillance du bureau consulté

Les bureaux visibles reçoivent une priorité temporaire dans la surveillance périodique du parc de 30 postes. Les onglets abandonnés ne conservent plus cette priorité. Aucune validation réseau implicite ni accélération périodique. [Portée, limites et recette PT9](docs/V070-SURVEILLANCE-BUREAU.md).

# v0.69 — Aides, réponses et bilan des interventions

Indices consultables et mémorisés, correction volontaire des incidents actuels, bilan factuel et export HTML imprimable. Consulter une correction ne répare rien et ne valide pas le ticket. [Détails, limites et recette](docs/V069-AIDES-ET-BILAN.md).

# v0.68 — Tickets clarifiés et applications harmonisées

Livraison groupée v0.67 + v0.68 : ressources et résultats attendus dans les nouveaux tickets, contexte moins répétitif, documentation en bibliothèque et gestion FTP par compte sélectionné. Le socle de sessions et preuves réseau v0.66 est conservé.

[Détails v0.67](docs/V067-TICKETS-ET-TEXTES.md) · [Détails et recette v0.68](docs/V068-SYSTEME-APPLICATIONS.md). Recette visuelle Windows/PT9 requise ; toutes les consoles ne sont pas encore refondues.

# v0.66 — Services et sessions cohérents

Les nouvelles sessions utilisateur restent ouvertes pendant l’utilisation du logiciel ; leur état ne dépend plus de l’expiration d’une preuve réseau. Les preuves ICMP des applications vérifient la même paire source/cible. Les observations inconnues ne détruisent plus le VPN, et ses preuves communes sont partagées entre bureaux. [Détails et recette Windows/PT9](docs/V066-SERVICES-SESSIONS.md).

Les actions réseau exigent toujours un contrôle récent. Le comportement réel et l’indisponibilité intermittente de l’annuaire restent à vérifier dans Packet Tracer.

# v0.65 — Dialogue client contextualisé

Les incidents des grandes entreprises proposent des questions adaptées au problème. Le demandeur précise le poste et la ressource, conserve son récit initial et décrit ses essais datés. Les retests ne réparent rien et distinguent connexion réseau, résolution DNS et accès aux fichiers. [Portée et limites](docs/V065-DIALOGUES-CLIENT.md).

Ce dialogue reste déterministe, sans LLM. Les anciens scénarios gardent leur moteur.

# v0.64 — Panne, découverte, signalement

Les arrivées périodiques des grandes entreprises séparent désormais la panne locale de sa découverte : une tentative d’activité a lieu 20 à 60 secondes plus tard. Le ticket apparaît si le problème persiste ; une réparation préalable évite un signalement devenu inutile. Sauvegarde et reprise préservent cette chronologie. [Portée et limites](docs/V064-ACTIVITES-SIGNALEMENTS.md).

Ce premier moteur de découverte ne simule pas encore une journée de travail complète. Les tickets initiaux et manuels restent immédiats.

# v0.63.1 — Signalements récupérables et symptômes précis

Pour les incidents simultanés des entreprises de trente employés, la mutation locale et son ticket récupérable sont sauvegardés ensemble. Une perte de la file de tickets ne laisse plus une mutation enregistrée sans signalement. Les demandes Documents distinguent partage réseau et application locale ; le dialogue indique une heure de constatation réelle plutôt qu’une formule générique. [Détails et limites](docs/V0631-SIGNALEMENTS.md).

Il s’agit du premier correctif de préparation de la v0.64, pas encore du moteur de vie d’entreprise ni d’un nouveau catalogue de pannes Packet Tracer.

# v0.63 — Réseau d’entreprise V2

Les nouvelles entreprises de trente employés ont cinq VLAN, des trunks 802.1Q et un routage inter-VLAN explicite. Les adresses des postes et les ports du portable technicien restent cohérents avec leur réseau. Pools DHCP et relais configurés ; les postes restent **statiques**, le suivi des baux dynamiques étant encore à développer. [Plan et recette PT9](docs/V063-RESEAU-V2.md).

Ce nouveau socle est **à tester dans Packet Tracer 9**. Les sauvegardes existantes et les petits sites ne sont pas migrés. La version ne rajoute ni Wi-Fi ni nouveaux incidents ; ces blocs restent au programme.

# v0.62.8 — Placement commun des entreprises et ateliers

Les trente postes sont disposés en blocs compacts autour de leur switch, avec une zone serveurs distincte. Les ateliers « services d’entreprise » emploient aussi ce placement dans les réseaux initial, de référence et tous les instantanés des PKA. Les anciens labs classiques conservent leur disposition. [Recette et limites](docs/V0628-PLACEMENT-COMMUN.md).

La segmentation VLAN/DHCP prévue pour la v0.63 reste à développer : cette livraison prépare uniquement la présentation logique.

# v0.62.7 — Surveillance réseau et continuité du bureau

La suite est cadrée dans le [contrat du modèle d’entreprise](docs/MODELE-ENTREPRISE.md) : dépendances, événements, signalements, connaissances du client et trois scénarios de référence. Il s’agit d’une spécification, pas de nouvelles fonctions déjà disponibles.

Surveillance bornée à un poste par passage pour les entreprises de trente employés, alternance entre sessions actives et reste du parc, contrôle explicite ciblé avec fast-forward. Une preuve périmée ou un pont indisponible conserve le bureau avec un bandeau ; les actions réseau restent soumises à une preuve récente. [Guide et recette](docs/V0627-SURVEILLANCE-RESEAU.md). Validation réelle dans Packet Tracer 9 à effectuer.

## v0.62.6 — Correctifs issus des audits

Catalogue des labs, dialogue réseau, preuve commune d'annuaire et journalisation corrigés. [Détails](docs/V0626-CORRECTIFS-AUDIT.md).

## v0.62.5 — Indices utiles et arrêt du logiciel

Les indices progressifs précisent les outils et les tests selon AD, DNS, fichiers, impression, FTP, accessoires ou arrivée d’un employé. Quitter enregistre les données puis arrête le serveur ; le lanceur Windows ne reste plus sur pause après un arrêt normal. [Guide et limites](docs/V0625-AIDES-ET-ARRET.md).

# v0.62.4 — Sessions et accès distant stabilisés

Cache d’entreprise conservé pendant les contrôles, sessions indépendantes entre employés, bureau distant conservé lors d’une interruption et raccourci Accès distant rétabli. La fenêtre de session masque la connexion quand le compte est authentifié. [Détails et recette](docs/V0624-SESSIONS-STABLES.md). Comportement réel avec PT9 à tester.

# v0.62.3 — Topologie compacte et icônes de fenêtre

Les nouvelles entreprises de 30 postes regroupent les clients autour de leur switch réel, avec une étendue réduite et des marges pour les libellés. Les icônes de titre utilisent directement les SVG du bureau. [Changements et recette PT9](docs/V0623-TOPOLOGIE-LISIBLE.md). Les sauvegardes existantes ne sont pas réagencées. Placement et rendu réel à tester dans Packet Tracer.

# v0.62.2 — Barre de titre alignée et bureau rapproché de la maquette

Correctif visuel des titres/contrôles OS.js et reprise du fond, de la grille centrée et de l’en-tête de la maquette. Voir [la recette du correctif](docs/V0622-ALIGNEMENT-FENETRES.md).

Première passe de la refonte du bureau inspirée de la maquette : barre des tâches intégrée, fenêtres harmonisées et annuaire avec liste structurée et résumé des propriétés réelles. Voir [les changements et la recette](docs/V0621-BUREAU-ANNUAIRE.md).

Politiques propres à l’entreprise, console Arrivées et services, échanges mail internes simulés, catalogue de licences et demandes liées au centre de tickets. Les contrôles relisent les moteurs AD, mail, licences et déploiement du stock. Voir [le guide et la recette](docs/V062-ARRIVEES-ET-SERVICES.md). Aucun SMTP externe ni ajout automatique de PC Packet Tracer. Rendu Windows/PT9 à vérifier.

# v0.59 — Chantier regroupé services et interfaces (0.58 + 0.59)

Console de services et journal de session issus des moteurs ; propriétés de quotas/capacité séparées ; raccordement et VPN dans des fenêtres dédiées ; parc connecté, réserve et historique séparés. Documentation intégrée et roadmap réorganisée. Voir [le périmètre et la recette](docs/V059-SERVICES-ET-CONSOLES.md). Rendu Windows/PT9 à vérifier.

# v0.57 — Paramètres du poste

Listes séparées des actions, propriétés du lecteur Z: et gestion des applications dans des fenêtres dédiées. Confirmation de désinstallation et suppression des données périmées après une lecture refusée. Voir [la recette](docs/V057-PARAMETRES-POSTE.md). Rendu Windows / Packet Tracer : à tester.

# v0.56 — Console DNS : zone et propriétés

Zone interne visible, liste recherchable et propriétés/création dans des fenêtres dédiées. Sélection séparée de l’ouverture, cibles stables et refus sur état indisponible. Voir [la recette](docs/V056-CONSOLE-DNS.md). Rendu Windows et Packet Tracer : à vérifier manuellement.

# v0.55 — Imprimantes et client FTP

Équipements, files d’attente et propriétés dans des fenêtres distinctes. Connexion FTP dédiée, listes locales/distantes, sélection stable et résultats des transferts. Les routes et moteurs existants sont conservés. Voir [la recette](docs/V055-IMPRIMANTES-FTP.md). Rendu Windows et contrôles Packet Tracer : recette manuelle à faire.

# v0.54 — Explorateur et Annuaire : navigation et propriétés

Sélection séparée de l’ouverture, éditeur de texte dans une fenêtre dédiée, menus contextuels, arborescence des OU et propriétés par onglets. Les moteurs et leurs vérifications restent inchangés. Voir [la recette et les limites](docs/V054-APPLICATIONS-BUREAU.md). Le rendu Windows / Packet Tracer 9 reste à tester.

# v0.53 — Documentation et cohérence des consignes

Recherche sans distinction d’accents, catégories, liste et lecture séparées, informations de l’entreprise distinguées des procédures. Correction du parcours des tickets simultanés et du coffre local dans l’aide. Voir [la recette](docs/V053-DOCUMENTATION.md). Rendu Windows à tester.

# v0.52 — Centre de tickets et bureaux (blocs 0.51 + 0.52)

Fil d’activité unifié, suivis publics / internes, tâches persistantes et qualification urgence × impact. Fenêtres harmonisées, barre des tâches, verrouillage conservant les applications et console de ping améliorée. Recettes et limites : [Traitement des tickets](docs/V051-TRAITEMENT-TICKETS.md) et [Bureaux et sessions](docs/V052-BUREAUX-ET-SESSIONS.md). À tester dans ton environnement Windows / Packet Tracer 9.

# v0.50.8 — Impact FTP selon les activités métier

Les incidents partagés concernent les employés dépendants du service. La fiche distingue estimation métier et preuve réseau ; les dépendances sont documentées. Détails : docs/V0508-IMPACT-METIER.md.

# v0.50.7 — Sessions conservées pendant les contrôles indisponibles

Reconnexion distante sans destruction des fenêtres sur preuve inconnue ; opérations AD sans logout général. Recette et limites : docs/V0507-SESSIONS.md.

# v0.50.6 — Fiche ticket et actions dédiées

Trois onglets séparent les échanges, l’intervention et les contrôles pédagogiques. Les suivis, notes et actions de résolution utilisent une fenêtre centrée. Recette visuelle : docs/V0506-FICHE-TICKET.md.

# v0.50.5 — Fenêtre de création d’entreprise

Création dans une fenêtre centrée avec fond flouté, seed facultative et chargement. Message d’accueil adapté sans entreprise active. Voir [la note de version](docs/V0505-CREATION-ENTREPRISE.md). Rendu Windows à tester.

# v0.50.4 — Accueil et sessions

Accueil réorganisé depuis le nouvel export Figma : prochain ticket, état du site, raccourcis et entreprises sauvegardées. Voir [la note de version](docs/V0504-ACCUEIL-SESSIONS.md). Rendu Windows et Packet Tracer à tester.

# v0.50.3 — Détails visuels Figma

Icônes issues de la maquette, bandeau compact, diagnostic en lignes et suppression du double défilement d’inventaire. Voir [le détail et la recette](docs/V0503-FIDELITE-FIGMA.md).

# v0.50.2 — Parc et réseau, maquette Figma

Quatre onglets, recherche d’équipements et cartes reliées aux observations du pont. Voir [la livraison et la recette](docs/V0502-PARC-FIGMA.md). Le rendu visuel reste à confirmer sur Windows.

# v0.50.1 — Accessoires simultanés

Écran, clavier et souris rejoignent les incidents des entreprises à 30 employés : panne avant ticket, intervention locale, clôture sans ping. La fenêtre Équipement local présente trois cartes matériel. Voir [le périmètre et la recette](docs/V0501-ACCESSOIRES-SIMULTANES.md).

# v0.50 — Entreprise de 30 employés

30 postes employés câblés, six services, comptes distincts, pannes avant signalement et interventions simultanées. Voir [le périmètre et la recette PT9](docs/V050-ENTREPRISE-30-EMPLOYES.md). Les anciennes entreprises restent compatibles.

# v0.49.1 — Confort et arrivées

Voir [la livraison et ses limites](docs/V0491-CONFORT-ET-ARRIVEES.md) : scrollbars, chargement du bureau, diversité des arrivées et séparation entre perte réseau et session utilisateur. La refonte des incidents simultanés reste à réaliser.

# pkt_lab — Générateur de labs Packet Tracer (.pka)

## v0.49 — espace d’intervention et cycle des tickets

Écran partagé actionnable avec bureau intégré, panneau redimensionnable et connexion explicite au poste du ticket. Résolution vérifiée, confirmation déclarée du demandeur, clôture avec contrôles frais et réouverture tracée. Les anciennes sauvegardes restent compatibles. Voir [le périmètre, les limites et la recette](docs/V049-ESPACE-INTERVENTION.md).

## v0.48.3 — suivi des interventions

Les tickets conservent des suivis datés et des propositions de solution, distincts du compte rendu modifiable. La prise en charge renseigne le technicien de la session. Ces informations sont exportées ; les contrôles de clôture restent obligatoires et inchangés. Voir [le périmètre et la recette](docs/V0483-SUIVI-TICKETS.md).

## v0.48.2 — documentation de l’entreprise

L’application Documentation rassemble un répertoire des appareils enregistrés, les repères du domaine et du serveur de fichiers, et les procédures de formation. Les articles utilisent l’environnement courant, sans mot de passe ni cause cachée. Ils ne constituent pas une mesure réseau. Voir [le périmètre et la recette](docs/V0482-DOCUMENTATION-ENTREPRISE.md).

## v0.48.1 — nommage et placement

Les nouvelles entreprises utilisent des noms indépendants des personnes et un placement regroupé par branche, avec des variantes issues de la seed. Les anciennes sauvegardes gardent leur présentation, y compris après réinitialisation. Voir [le périmètre et la recette](docs/V0481-NOMS-ET-PLACEMENT.md). La taille du réseau et l'architecture restent inchangées.

## v0.48 — file des tickets

Table métier avec demandeur, poste, statut, sévérité et date ; recherche par identité et équipement ; fiche complète sous la file. Les sauvegardes et la validation restent inchangées. Voir [le périmètre et la recette](docs/V048-FILE-DES-TICKETS.md).

## v0.47.3 — recette et lisibilité des tickets

Lancer toute la recette : `python tests/run_tests.py` (Python 3.10+ et Node.js). Les contrôles automatiques des tickets sont regroupés dans un volet pédagogique et l'application FTP propose une aide de connexion. Voir [le périmètre et les vérifications manuelles](docs/V0473-RECETTE-ET-CONTROLES.md). La refonte métier des tickets, le nommage et les topologies restent les prochains blocs.

Génère des fichiers `.pka` Packet Tracer avec une ou plusieurs pannes cachées
et les consignes embarquées directement dans l'onglet natif « Instructions »
du fichier (objectifs, mise en situation, table d'adressage), en français ou
en anglais au choix — puis vérifie ta réparation. Propose aussi des missions
(déployer un plan d'adressage) et des exercices papier vérifiés par calcul.

> Projet personnel d'entraînement (TSSR / CCST Networking), développé avec
> l'assistance d'une IA (Claude), testé et validé dans Packet Tracer 9.
> Voir `docs/JOURNAL.md` pour la démarche, les découvertes et les bugs résolus.

## Interface web — livraison v0.47.2

La v0.47.2 ajoute des formulations procédurales, une urgence déclarée expliquant la sévérité initiale et conserve la durée choisie lors de la préparation. Voir [le guide](docs/V0472-DEMANDES-CONTEXTUALISEES.md).

La v0.47.1 clarifie la file : scénario actif en tête, filtres À préparer / Intervention active, réglages adaptés au catalogue et compte à rebours des arrivées. Voir [le guide](docs/V0471-ERGONOMIE-FILE.md).

Nouveauté : premier ticket procédural pour les nouvelles entreprises, file de demandes et arrivées réglables (5 minutes / plafond 3 par défaut). Une seule panne préparée à la fois. Voir [la documentation v0.47](docs/V047-FILE-DE-TICKETS.md).

Les fiches et les ordinateurs de l’annuaire donnent accès aux **comptes locaux de formation** : révélation du credential, test de connexion locale et administration distincte d’AD. Le catalogue Applications ajoute **9 incidents d’accessoires externes**, vérifiés sans ping. Voir [v0.46.4](docs/V0464-ACCES-ET-INCIDENTS-LOCAUX.md).

Les fiches proposent désormais **Équipement local** : écran, clavier et souris, connexions, remplacement et aperçu local persistants. Ces actions ne modifient pas le réseau ou la prise en main distante. Voir [v0.46.3](docs/V0463-PERIPHERIQUES.md).

Le bureau du technicien ajoute **Fiches des postes** et **Documentation** : sélection par numéro de série, prise en main ciblée et six procédures consultables. Voir [v0.46.2](docs/V0462-FICHES-DOCUMENTATION.md).

Le bureau du technicien propose **Parc et stock** : réserve, remise à un employé et restitution persistantes. La préparation passe désormais par un atelier visuel lié au numéro de série ; la remise exige un bilan réussi. Aucun appareil réseau n’est ajouté automatiquement. Voir [v0.46.1](docs/V0461-STOCK-DEPLOIEMENT.md). Voir [v0.46](docs/V046-PARC-STOCK.md).

La console d’annuaire propose les vues utilisateurs, groupes, ordinateurs, OU, historique et stratégie, avec protection contre les modifications depuis une vue périmée. Voir [v0.45](docs/V045-ANNUAIRE-CONSOLES.md).

Le référentiel relie désormais personnes représentées, comptes, postes et tickets de la même entreprise. Les liens persistent après renommage et reprise. Voir [v0.44](docs/V044-REFERENTIEL.md).

Diagnostics et correctifs regroupés : [docs/V042-DIAGNOSTICS.md](docs/V042-DIAGNOSTICS.md).

Espace de travail facultatif : [docs/V043-ESPACE-DE-TRAVAIL.md](docs/V043-ESPACE-DE-TRAVAIL.md).

Correctif des événements ICMP et erreurs de connexion : [docs/V041-CORRECTIF-ICMP.md](docs/V041-CORRECTIF-ICMP.md).
Le fonctionnement réel du contrôle discret reste à confirmer dans Packet Tracer 9.

Lance `LANCER-WEB.bat` pour le service desk et les bureaux simulés.
Le générateur de labs Packet Tracer reste accessible dans l’interface et avec `lancer.bat`.

Les nouvelles entreprises disposent de deux bureaux clients distincts et d’un portable technicien,
liés aux appareils de leur unique réseau Packet Tracer. Chaque client conserve ses fichiers locaux,
applications, réglages et sessions ; les services d’entreprise restent partagés.
Les interventions applicatives peuvent cibler un poste choisi ou choisi procéduralement.

Les contrôles internes utilisent désormais l’API ICMP sans injection CLI, par lots.
Le fast forward est réservé aux contrôles manuels ; les changements de statut et les notes
n’attendent plus le verrou réseau. Cette méthode est **à tester dans Packet Tracer 9**.
Mode d’emploi et essai du pont : [docs/V040-CONTROLES-DISCRETS.md](docs/V040-CONTROLES-DISCRETS.md).

Mode d’emploi et limites : [docs/V039-BUREAUX.md](docs/V039-BUREAUX.md).
Les anciennes sauvegardes restent compatibles. La validation visuelle et les essais du pont
sur Packet Tracer restent à effectuer dans ton environnement.

## Démarrage

**Option A — sans rien installer de plus** (Python 3.10+ requis) : double-clic sur `lancer.bat`.

**Option B — un vrai .exe** : double-clic sur `build_exe.bat` (une seule fois).
L'exécutable apparaît dans `dist\pkt_lab.exe`. Copie-le où tu veux : les
labs seront créés dans un dossier `labs` à côté de lui.

Aucune dépendance à installer : le chiffrement des fichiers Packet Tracer
(Twofish) est réimplémenté en pur Python (`twofish_pure.py`).

Réglage Packet Tracer conseillé : Options > Preferences > Interface >
« Always Show Port Labels in Logical Workspace ».

## Utilisation

1. **Nouveau lab** : choix de la langue (FR/EN), puis surprise / par thème /
   pannes précises (sélection multiple possible), difficulté 1 à 3 (niveau 3 =
   deux pannes simultanées sur des appareils différents, score partiel à la
   validation), filtre « pannes cachées » (détectables uniquement depuis la
   supervision PC-ADMIN, jamais par une plainte utilisateur directe), et
   nombre de pannes (par défaut selon le niveau, ou choisi explicitement).
   Le `.pka` généré contient déjà son onglet **Instructions** natif (objectifs,
   mise en situation, table d'adressage attendue) — pas de fichier d'énoncé
   séparé à lire. Le lab s'ouvre dans Packet Tracer.
2. Tu dépannes dans PT, puis **Ctrl+S** (sauvegarde sur le même fichier).
3. **Valider un lab** : verdict, avec
   - la cause racine (réparée ou non) de chaque panne,
   - les dégâts collatéraux (ce que tu as cassé en réparant),
   - un avertissement si la réparation n'est pas sauvegardée sur l'équipement
     (`copy running-config startup-config`).
   En cas d'échec : retenter, indice (appareil, puis thème), ou abandonner.
4. **Historique** : labs, tentatives, indices utilisés, taux de réussite des exercices papier.
5. **Exercices papier** (sans Packet Tracer, vérifiés par calcul) : informations de
   sous-réseau, plan d'adressage VLSM (toute réponse valide acceptée, gaspillage
   signalé), IPv6 abréger/développer, calcul EUI-64. Corrigé détaillé en cas d'erreur.
6. **Plan VLSM puis mise en place** : tu conçois le plan de 3 services, puis tu le
   déploies dans Packet Tracer (R1 + 3 switchs + 6 PC câblés, rien de configuré).
   Plan valide → c'est TON plan qui est vérifié ; sinon le corrigé. La mission se
   valide depuis « Valider un lab », tâche par tâche.

Ne pas ouvrir `labs/Lxxxxx/.solution.json` : c'est la correction.

## Architecture

| Fichier | Rôle |
|---|---|
| `main.py` | Menu, orchestration, dossiers de labs |
| `builder.py` | Topologies saines (surcouche de `core.Lab` du fork) |
| `faults.py` | Catalogue de pannes (dont pannes « cachées »), injection dans le XML |
| `ticket.py` | Textes de mise en situation bilingues FR/EN (symptôme, jamais la cause) |
| `instructions.py` | Contenu (titre, objectifs, mise en situation, table d'adressage) de la page Instructions, bilingue |
| `activity.py` | Assemble le vrai wrapper d'activité PT (racine `PACKETTRACER5_ACTIVITY`, 3 instantanés, `COMPARISONS`/`INITIALSETUP`) à partir d'un gabarit réel — module du fork, resté inutilisé jusqu'ici |
| `worksheet.py` | Fiche HTML compagnon de chaque `.pka` : indices progressifs + résultat attendu derrière des boutons Montrer/Masquer, utilisable sans Packet Tracer ni Python |
| `checker.py` | Vérification cause racine (par panne, score partiel) + collatéral + sauvegarde |
| `exercises.py` | Exercices papier : sous-réseaux, VLSM, IPv6, EUI-64 |
| `missions.py` | Missions (tâches à réaliser) : déploiement d'un plan VLSM |
| `twofish_pure.py` | Chiffrement Twofish sans compilateur |
| `core.py`, `scenarios.py`, `profiles.py`, `layouts.py`, `ptexplorer.py` | Fork TeodorPetrovic/tracketpacin (modifications marquées `[pkt_lab]`) |
| `templates/activities/subnetting_activity.xml` | Gabarit d'activité PT réel utilisé par `activity.py` comme source de prototypes de comparaison |
| `templates/packettracer/catalogue_source.xml` | 74 appareils (catalogue PTBuilder) |
| `docs/RULES_TOPOLOGIES.md` | Règles de construction (adressage, OSPF, NAT, VLAN...) tirées de vrais labs, pour les futurs gabarits multi-sites |

### Modifications apportées au fork
- `core.py` : `shutdown` / `no shutdown` appliqués aux ports (le fork les ignorait).
- `ptexplorer.py` : Twofish pur Python en priorité ; correctif de la détection du
  format (le fork se trompait ~1 fois sur 128 et rendait le fichier illisible).

## Contenu actuel

Topologies simples : `simple_lan` (R1 2911 → S1 2960 → 2 PC en statique),
`dhcp_lan` (R1 serveur DHCP → S1 → 3 PC en DHCP). Dans les deux : S1 est
administrable (SVI Vlan1 en .2 + ip default-gateway), et un poste PC-ADMIN
(service informatique, supervision) est relié à R1 G0/1 dans un réseau
192.168.x.0/24 à part : il rend visibles les pannes qui ne se voient que depuis
un autre réseau.

Topologie multi-sites : `multisite_ospf_nat` — 2 sites (SITE1/SITE2, chacun
routeur + switch administrable + 2 PC) reliés en étoile à un routeur de bordure
(R-EDGE) qui fait du NAT overload (sur son interface de sortie) vers un routeur
ISP et un serveur web, le tout annoncé en OSPF area 0 côté privé. Conventions
(adressage, nommage d'interfaces, NAT, OSPF) tirées de vrais labs NetAcad/CCNA,
voir `docs/RULES_TOPOLOGIES.md`.

Topologie switchée redondante : `switched_redundant` — 3 switchs en triangle
(S1 distribution + S2/S3 accès, 1 PC chacun), donc une boucle sur laquelle le
Spanning Tree doit élire un root bridge. Pas de routeur (lab purement L2).

Topologie VLAN/trunk : `vlan_trunk` — routeur-bâton R1 (sous-interfaces dot1Q
10/20) relié en trunk à S1, lui-même relié en trunk à S2 ; 2 VLAN, 2 PC par
VLAN répartis sur les 2 switchs.

Topologie EtherChannel : `etherchannel` — S1 (LACP active) et S2 (LACP
passive, asymétrie volontaire et valide) reliés par 2 liens agrégés en
Port-channel1, 1 PC par switch.

Le catalogue de pannes ne vient plus seulement de patterns génériques : depuis
l'étude directe des 10 vraies activités officielles "Troubleshoot..." du
programme CCNAv7 (voir `docs/BACKLOG_EXERCICES.md`), certaines pannes sont
désormais confirmées par diff d'un vrai fichier NetAcad plutôt que supposées,
et un catalogue de 51 pistes supplémentaires (fourni par Damien) a été passé
au crible pour en extraire des versions procédurales (35 pannes au total,
6 topologies — le détail de ce qui a été volontairement reporté, et pourquoi,
est dans `docs/BACKLOG_EXERCICES.md`). Table ci-dessous non exhaustive (les pannes les plus récentes
sont listées avec leur source dans `docs/BACKLOG_EXERCICES.md`) :

| Panne | Niveau | Thème | Cachée | Validée dans PT |
|---|---|---|---|---|
| Mauvaise passerelle PC | 1 | adressage | non | ✅ (mécanisme) |
| Mauvaise IP PC | 1 | adressage | non | ✅ (mécanisme) |
| PC éteint | 1 | matériel | non | ✅ (mécanisme) |
| Câble débranché | 1 | câblage | non | ✅ |
| Interface routeur en shutdown | 1 | routeur | non | ✅ |
| Masque /30 sur un PC | 2 | adressage | non | à tester |
| Mauvaise IP routeur | 2 | routeur | non | ✅ (mécanisme) |
| DHCP : mauvaise passerelle distribuée | 2 | dhcp | non | ✅ |
| DHCP : pool sur le mauvais réseau | 2 | dhcp | non | à tester |
| Switch : SVI Vlan1 éteinte | 1 | switch | **oui** | ✅ |
| Switch : ip default-gateway absente | 2 | switch | **oui** | ✅ |
| OSPF : réseau non annoncé (multi-sites) | 1 | routeur | non | ✅ |
| IP erronée sur un lien WAN (multi-sites) | 2 | routeur | non | à tester |
| NAT : `ip nat inside` absent (multi-sites) | 2 | nat | non | à tester |
| Route par défaut : mauvais next-hop (multi-sites) — confirmé officiel CCNA (SRWE 16.3.1) | 2 | routage | non | à tester |
| STP : priorité root bridge absente (switchs redondants) — confirmé officiel CCNA (ENSA 12.5.13) | 2 | switch | non | à tester |

## Développement
- Tests : `python tests/test_all.py` (avant chaque commit)
- Contexte pour Claude Code : `CLAUDE.md` ; historique : `docs/JOURNAL.md`

## Licence
MIT (voir `LICENSE`). Réutilise du code MIT de tracketpacin et ptexplorer :
voir `THIRD_PARTY_NOTICES.md`.

## Feuille de route
- ✅ Fait, validé dans PT 9 : génération en `.pka` avec consignes natives bilingues
  FR/EN (objectifs, mise en situation, table d'adressage) via `activity.py` (vrai
  wrapper d'activité, pas une reconstruction maison — voir §"Modifications apportées
  au fork"), sélection de pannes précises multiples, filtre pannes cachées.
- ✅ Fait, validé dans PT 9 : premier gabarit multi-sites `multisite_ospf_nat`
  (2 sites + routeur de bordure NAT + ISP + OSPF area 0), avec 3 pannes dédiées
  (OSPF, IP de lien WAN, NAT). Règles dans `docs/RULES_TOPOLOGIES.md`.
- ✅ Fait : fiche HTML compagnon de chaque `.pka` (`worksheet.py`) — indices
  progressifs et résultat attendu derrière des boutons Montrer/Masquer, inspirée
  du "lab companion" NetAcad, utilisable en secours sans Packet Tracer ni Python.
- VLAN trunking (router-on-a-stick), variantes NAT statique/dynamique, routage
  statique en chaîne : règles déjà posées, pas encore implémentées en gabarit.
- Mode documentation/exploration (appareils cachés dans un cluster verrouillé) —
  un vrai `<LOCKINGTREE>` a été repéré dans un fichier NetAcad décodé cette
  session, mais sa structure/sémantique précise n'a pas encore été étudiée en détail.
- Niveaux 4 et 5 : leurres dans les consignes, pannes en cascade.
- Demandes de service (faire évoluer un réseau sain) et missions multi-tâches.
- Exercices papier : tableau d'adressage d'une topologie, analyse de sorties « show »
  — bons candidats pour le format fiche HTML (`worksheet.py`) plutôt que `checker.py`.
- Généralisation procédurale des topologies complexes (une fois les gabarits
  validés), IPv6 dans les labs, audit sécurité.
- Choix de la plage d'adressage (10/8, 172.16/12, 192.168/16) ; DNS interne.


## Corrections du 2 octobre 2026

EtherChannel, DNS, équivalences du correcteur et sélection des pannes de management : voir [la note de correction](docs/CORRECTIONS_2026-10-02.md). Les nouveaux mécanismes XML sont **à tester dans Packet Tracer 9**. Les fichiers nécessaires sont dans `validation/`.


## Nouveaux ateliers : services, Wi-Fi et Meraki

**Menu 5** : 3 gabarits supplémentaires et 40 ateliers (17 pannes injectées, 16 missions de configuration et 7 évolutions). Chaque atelier fournit un `.pka`, un `.pkt` et une feuille HTML avec indices et correction finale. Validation manuelle, sans obligation de correcteur automatique.

Voir [le catalogue et les instructions](docs/ATELIERS_PACKET_TRACER.md). Les nouveaux ateliers sont **à tester dans Packet Tracer 9**. Pour les tests de développement, exécuter aussi `python tests/test_workshops.py`.

## Portail web local (branche 0.14)

Le générateur CLI reste accessible avec `python main.py`. Pour les tickets, les sessions chronométrées et les labs indépendants, lancer `web/LANCER-WINDOWS.bat` ou `python web/tickets_app.py`. Garder le dépôt complet : le portail réutilise le moteur et les templates à la racine.

Les tickets de réseaux indépendants tirent désormais un code de site, un demandeur et 2 à 6 postes employés avec leur cause et leur famille IPv4. Le ticket annonce le réseau employés et sa composition ; le PKA et la feuille reprennent les noms préfixés du même site, avec ou sans poste IT dédié. Les postes ajoutés ont chacun une adresse et un port dédiés. Les paramètres conservés permettent de reconstruire le cas après un échec de génération. Les rôles et l’architecture à trois sous-réseaux restent ceux du catalogue.

Voir [le mode d’emploi du portail](web/LIRE-MOI.md). Les données locales de tickets et les réseaux générés sont exclus de Git. Le pont communautaire et son extension sont livrés avec leur licence dans `web/vendor`.

La mission « Ajouter un serveur web » et sa combinaison avec un dépannage HTTP fournissent une topologie complétée en `correction.pkt`. Les missions « Isoler les invités » et « Bloquer un poste précis » y incluent également un exemple de règle ACL sur R1. L’atelier DHCP centralisé, seul ou mixte avec une panne HTTP, y montre le relais et le service rétablis, avec PC-ALICE en attente de bail DHCP : l’adresse attribuée doit être constatée dans Packet Tracer. Le PKA intègre les consignes et conserve la topologie de départ, avec notation native désactivée.

Les nouveautés de nommage, implantation physique et services conditionnels restent **à tester dans Packet Tracer 9**. Les tests Python contrôlent les fichiers et les gardes, pas le fonctionnement réel du réseau.

Les nouveaux profils procéduraux conservent aussi la présence facultative du poste IT. Sans ce poste, le ticket décrit une intervention par un prestataire externe ; aucun poste ni câble IT fictif n’est ajouté. Les anciens profils et les ateliers existants gardent leur comportement par défaut. À tester dans PT 9.

Les profils procéduraux version 5 varient aussi le poste concerné par les incidents DHCP (parmi les employés présents) et la répartition des employés sur un ou deux switches. Les deux switches partagent le même sous-réseau employés ; aucun VLAN supplémentaire n’est annoncé. Cible, câblage, consignes, référence et relance utilisent les mêmes paramètres. À tester dans PT 9.

Les profils procéduraux version 6 ajoutent quatre incidents locaux : IP, masque, passerelle ou DNS incorrect sur un poste employé variable. Une demande d’arrivée d’employé génère aussi un atelier : ajouter le PC désigné avec son adressage, son port et ses tests d’accès. Le réseau initial ne contient pas ce PC ; correction.pkt contient une référence avec le poste ajouté. Validation manuelle, mécanismes à tester dans PT 9. Les demandes utilisent le même plan de site et les mêmes paramètres conservés que les incidents.

## Service desk v0.24

Tickets procéduraux de une à trois couches sur l’entreprise active, portable du technicien, VPN pédagogique et dialogues à choix sans LLM. Le générateur de labs indépendants reste disponible. Voir [le guide v0.24](docs/V024-INTERVENTIONS-MIXTES.md) pour le parcours, les limites et les vérifications Packet Tracer.

## Service desk v0.25

Bureau client avec fichiers locaux, applications installables et lecteur Z:, impression et FTP simulés, 18 causes procédurales supplémentaires et arrivées par famille. Les nouveaux environnements incluent un Printer-PT. Lance **LANCER-WEB.bat** pour le portail. Voir [le guide v0.25](docs/V025-APPLICATIONS-DU-POSTE.md) : fonctionnement, anciennes sauvegardes, limites et vérifications à faire dans Packet Tracer 9.

## Interface v0.26

Navigation et présentation adaptées du design Figma NetOps Lab, contexte de l’entreprise visible, accueil avec prochain ticket réel et bureaux agrandissables/réductibles. Voir [le guide des six rubriques](docs/V026-INTERFACE-FIGMA.md). À tester sur Windows et Packet Tracer 9.

## Interface v0.27

Création et reprise depuis **Accueil et sessions**, ouverture du réseau depuis le bandeau, interventions dans **Tickets**, bureaux dans **Postes**. Le générateur conserve les exercices PKT/PKA indépendants et les tickets de dépannage historiques. Voir [le parcours v0.27](docs/V027-PARCOURS-ENTREPRISE-FORMATION.md). Nouveaux exports et parcours Windows : à tester dans Packet Tracer.

## Interface v0.28

Liste explicite des postes, cible identifiée par numéro de série, icônes de bureau et fenêtres au premier plan. Le portable utilise une lecture d’état non bloquante pendant les pings ; les preuves réseau expirées restent refusées. Voir [les changements et tests manuels](docs/V028-POSTES-ET-BUREAUX.md). Un seul bureau client simulé par entreprise à ce stade ; les autres PC détectés sont signalés sans bureau associé. Affichage Windows et délais réels : à tester.
