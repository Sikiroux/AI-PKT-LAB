# Roadmap du simulateur — base v0.100

## Objectif

Un environnement de travail agréable et cohérent avec les logiciels représentés, permettant de recevoir une demande, dialoguer, diagnostiquer, réparer, vérifier et documenter l’intervention. Conserver le bureau bleu et les fenêtres claires.

Les fonctions développées ne sont pas toutes validées en conditions réelles. La recette visuelle Chrome et les essais du pont réel Packet Tracer 9 restent ouverts. Les tests automatisés ne remplacent pas ces recettes. Aucun pourcentage d’avancement global n’est annoncé.

## État actuel

| Domaine | Livré | Limite actuelle |
|---|---|---|
| Interface | Base commune, bureau bleu, premiers raffinements des fenêtres | Inspection visuelle complète non réalisée |
| Espace technicien | Bureau, ticket épinglable, liens vers outils, contexte des tickets mémorisé | Parcours prolongé à vérifier et simplifier |
| Applications | Explorateur, annuaire et liste DNS avec navigation clavier et préférences | Autres consoles à harmoniser ; fidélité fonctionnelle partielle |
| Messagerie | Conversations par ticket, recherche, épingles, non lus, notes explicites et continuité de lecture | Dialogues scénarisés ; pas de conversation générale avec tous les salariés |
| Documentation | Catégories, références réseau, procédures, liens et mémoire de lecture | Couverture à enrichir et vérifier par scénario |
| Aides | Guide par service, indices progressifs, correction séparée, interprétation des contrôles réseau | Branches de diagnostic à éprouver sur les incidents réels |
| Réseau | Adresse IPv4 et masque incorrects dans les arrivées de l’entreprise à 30 employés | Tests avec pont simulé ; recette réelle nécessaire ; VLAN/trunk/DHCP non intégrés à ces arrivées |
| Entreprise | Phase saine de préparation, démarrage explicite, cadence et premiers incidents simultanés | Diversité et signalements collectifs encore limités |
| Bilan | Contrôles enregistrés, compte rendu, correction consultée et export | Explications avant/après à approfondir |

## Lots suivants, dans l’ordre

| Lot | Travail concret | Critère de sortie |
|---|---|---|
| A — Consolider le parcours | Rejouer prise en charge → conversation → documentation → poste/outils → vérification → clôture. Corriger erreurs bloquantes, pertes de contexte, retours d’écran et faux états. | Une intervention complète est réalisable et une reprise conserve les données enregistrées dans la bonne entreprise. Distinguer tests simulés et recette réelle. |
| B — Fidélité et confort des consoles | Poursuivre avec Imprimantes et files, puis FTP, Partages et Paramètres. Harmoniser sélection, propriétés, commandes disponibles, clavier, erreurs et états vides. | Les gestes sont prévisibles entre applications et proches des logiciels représentés ; les limites sont explicites. |
| C — Aides et documentation complètes | Pour chaque famille, fournir emplacements, méthode, observations, interprétation et prochaines vérifications. Séparer les solutions. | Un débutant peut commencer sans connaître le service ; aucun indice initial ne désigne la panne cachée. |
| D — Réseau plus riche | Valider IPv4/masque dans PT9, puis étudier un port indisponible et un mauvais VLAN ciblé ; ensuite trunks, DHCP et routage selon les capacités du pont. | Chaque panne a un état initial sain, une injection confirmée, un impact observé et une réparation vérifiée. Ne pas annoncer comme disponible ce qui reste en étude. |
| E — Messagerie et vie d’entreprise | Contacts recherchables, discussions hors ticket, canal collectif, signalements regroupés et dépendances métier cohérentes. | Un salarié, son poste et son activité restent cohérents ; une panne commune ne crée pas des signalements contradictoires. |
| F — Débriefing pédagogique | Rendre lisibles les observations avant/après, les preuves, les décisions et le pourquoi de la correction. Accepter les variantes de réparation que le moteur sait vérifier. | Le bilan explique ce qui a été rétabli et les limites des preuves, sans confondre déclaration et réparation. |
| G — IA conversationnelle optionnelle | Brancher un modèle sur les dialogues, avec connaissances limitées au salarié et à ses observations. Prévoir un mode sans IA. | Le modèle ne modifie ni la panne ni sa validation et ne révèle pas sa cause par connaissance du scénario. |

Les lots peuvent nécessiter plusieurs livraisons. Les versions sont choisies selon leur contenu ; le passage numérique à v1.00 ne vaut pas validation de stabilité.

## Prochain lot concret

Le lot v0.100 avance les quatre premiers chantiers : confirmation des actions distincte du rafraîchissement, navigation clavier et reprise des rubriques des consoles, procédures transversales et réseau, vérification réseau plus stricte. Les quatre chantiers ne sont pas déclarés terminés.

| Chantier | Apport v0.100 | Reste à réaliser |
|---|---|---|
| 1 — Parcours | Une impression, mutation ou un transfert confirmé conserve son succès si la relecture échoue ; pas de répétition automatique | Recette manuelle complète, reprise longue et interruptions du pont réel |
| 2 — Consoles | Rubriques Partages/DNS/FTP et Paramètres mémorisées par environnement/poste ; flèches, début/fin ; sélection clavier des travaux et fichiers FTP ; filtres des files mémorisés | Inspection visuelle, fidélité approfondie et protection uniforme des brouillons |
| 3 — Aides | Procédure générale de diagnostic et branches réseau ; distinction connexion/transfert, envoi/impression, panne/preuve absente | Parcours débutant réel, couverture détaillée des variantes |
| 4 — Réseau | Une identité ambiguë, remplacée ou une interface illisible ne devient plus une preuve de réparation ; contrôles de régression supplémentaires | Ajouter et éprouver ports/VLAN/trunks/DHCP ; aucune nouvelle famille de panne réseau dans cette version |

Priorité suivante : recette du parcours sur Chrome et Packet Tracer 9, puis port d’accès indisponible avec identité et liaison contrôlées, injection et restauration confirmées. Le catalogue d’arrivées réseau reste IPv4/masque à ce stade.

## Règles permanentes

- Préserver les sauvegardes et les interventions du technicien.
- Distinguer panne observée, observation périmée, résultat inconnu et pont indisponible.
- Garder les aides pédagogiques accessibles sans encombrer les consoles.
- Ne pas ajouter de commande décorative sans comportement correspondant.
- Vérifier sur le bon poste, avec la bonne identité, l’usage réellement demandé.
- Rapporter ce qui a été testé et les limites restantes à chaque livraison.

## Plus tard

Security Simulator : idée conservée, hors du développement actuel. Ne pas détourner la finition du simulateur support/réseau vers ce module.

## Accès bureau — étude après v0.100

Priorité proposée : un prototype d’enveloppe de bureau avant la distribution installable. Le lancement actuel appelle `webbrowser.open` ; le script `build_exe.bat` construit le programme historique `main.py`, pas le serveur web des tickets. L’application utilise déjà `window.open`, y compris une fenêtre `about:blank` ensuite dirigée vers un poste après validation de sa session.

Piste privilégiée à éprouver : Electron autour du serveur Python existant. Cette décision reste un choix de prototype, pas une validation de fonctionnement sous Windows. Conserver les fenêtres Windows indépendantes, leurs contrôles natifs et la possibilité de maximiser sans plein écran. Ne pas imposer de relation modale ni fermer un poste lorsqu’une autre fenêtre est fermée.

Critères du prototype :

- Un lancement démarre le serveur local et ouvre le centre de tickets sans barre d’adresse ; un second lancement retrouve l’instance existante.
- Les ouvertures existantes, notamment `about:blank` puis navigation, deviennent des fenêtres indépendantes avec accès limité aux pages locales attendues.
- Les dimensions et positions sont mémorisées et restent accessibles si un écran a été débranché.
- La fermeture d’une fenêtre secondaire ne coupe pas le moteur ; la sortie de l’application gère les autres fenêtres et arrête proprement le serveur qu’elle a démarré.
- Les sauvegardes restent hors du dossier remplacé par une mise à jour. Prévoir l’export/import des notes locales du navigateur ; elles ne migrent pas automatiquement vers un nouveau profil.

Ensuite : moteur Python embarqué, paquet Windows, installation et mécanisme de mise à jour. Ne pas annoncer un EXE autonome ou une mise à jour automatique avant construction et recette Windows.

Références techniques : https://www.electronjs.org/docs/latest/api/window-open/ et https://pywebview.flowrl.com/guide/usage . Electron est privilégié ici pour la gestion documentée des ouvertures web existantes ; pywebview reste une alternative à évaluer.

## Terminal intégré — différé

Conserver pour plus tard : terminal pour PC, switches et routeurs avec saisie et interactions dans notre interface, sorties et effets réels issus de Packet Tracer. Éprouver `?` sans Entrée, historique, modes IOS, pagination, confirmations et interruption. Le ping existant constitue un point de départ, sans prouver une session interactive complète. Prévoir des extensions autour du terminal sans altérer les commandes. Ce chantier et Security Simulator restent différés au profit de la finition du simulateur.

Prototype v0.101 ajouté : enveloppe Electron, lanceur Windows et tests simulés de cycle de vie. Recette Windows ouverte ; prérequis Python/Node.js, installation initiale Electron et absence de mise à jour automatique explicités dans `V0101-BUREAU.md`.

## v0.102 — première intégration visuelle

Messagerie compacte et barre des tâches personnalisable intégrées selon les maquettes approuvées. Bandeau permanent retiré ; contexte conservé dans le menu NetOps. Réglage local par entreprise et bureau. Recette visuelle Electron Windows encore ouverte. Voir `V0102-BUREAU-MESSAGERIE.md`.

## Refonte visuelle application par application

La maquette validée devient une référence de composition et de composants, pas une simple inspiration. Messagerie et barre des tâches reprises en v0.103 ; comparaison visuelle réelle ouverte. Suite : annuaire, explorateur/partages, imprimantes, FTP, paramètres, documentation. Valider chaque application par captures à dimensions comparables avant de déclarer sa refonte terminée. Voir `V0103-REFONTE-MESSAGERIE.md`.

## v0.104 — centre de tickets

Disposition file/fiche et commandes fixes intégrées selon la maquette ; réglages d’arrivées regroupés dans Simulation. Premier démarrage avec ticket aléatoire immédiat et protection contre les doublons. Régressions fonctionnelles réussies ; comparaison visuelle Electron Windows ouverte. Voir `V0104-CENTRE-TICKETS.md`.

## v0.105 — composants de référence

En-tête, navigation, badges, identité demandeur/poste, temps de travail, notes et synchronisation repris dans le centre de tickets. Données affichées issues du moteur. Comparaison visuelle native encore ouverte : ne pas déclarer une reproduction exacte avant recette.

## v0.106 — points 1 et 2

Cadre commun des onglets harmonisé, chevauchements de la fiche corrigés et temps de travail séparé du délai pédagogique. Contenu de l’accueil, du parc réseau et des postes conservé : créer et valider leurs maquettes avant refonte (point 3). Recette visuelle native ouverte.


## v0.107 — Correctifs de structure

Header et menu corrigés, largeur et marges communes, intégration Postes allégée. Refonte des contenus toujours en attente de maquettes validées.


## v0.108 — Finitions validées

Marges Réseau et inventaire, avatar IT avec indicateur de session locale. Timer de travail inchangé, confirmé par l’utilisateur.


## v0.111 — Intervention en modales

Maquette Intervention validée puis intégrée : actions compactes, compte rendu, tâches et résolution en modales. Refonte des autres contenus toujours soumise aux maquettes.


## v0.112 — Diagnostic mémoire

Quatre modes isolés, essais bornés, journaux exportables. Hausse observée par l’utilisateur dépendante des appels NetOps ; cause interne à isoler. Aucun correctif de fuite revendiqué.


## v0.113 — Isolation du volume de réponse et des logs

Deux tests sans lectures réseau et une comparaison inventaire avec nettoyage des logs informatifs. Diagnostic en cours, sans correctif de fuite revendiqué.
