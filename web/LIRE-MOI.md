# Version 0.14 — portail intégré au dépôt

Lancer `web/LANCER-WINDOWS.bat` depuis une copie complète du dépôt, ou `python web/tickets_app.py`. L’interface utilise les modules et templates du générateur à la racine : ne pas déplacer le dossier web seul.

Nouveaux labs d’ateliers : code de site configurable (AG1 par défaut), noms par rôle, pièces physiques et baie informatique. Sept combinaisons atelier + dépannage sont proposées. `implantation.json` et les consignes décrivent les emplacements. Les slots sont ceux du modèle Packet Tracer, pas un calcul d’encombrement en unités U. Le rendu physique doit être testé dans PT 9.

Les réseaux existants et les labs associés aux tickets conservent leurs noms pour préserver les contrôles et les consignes. Les anciens scénarios réseau classiques gardent leur implantation initiale.

Les services HTTP/DNS/DHCP du site persistant utilisent des adaptateurs expérimentaux : détection en lecture seule, injection bloquée si aucun adaptateur compatible n’est détecté. Les noms de processus et méthodes candidats ne sont pas encore confirmés dans PT 9. Une API compatible prouve seulement un état de configuration ; les tests fonctionnels restent déclarés manuellement après compte rendu.

# Nouveautés 0.13 — panne de VLAN d’accès

La cause « Mauvais VLAN » est disponible pour les incidents manuels et les arrivées du site persistant. Choisis explicitement cette cause et le mode « traces visibles — erreur humaine simulée ». Elle n’est pas ajoutée au tirage aléatoire actuel : le mode masqué reste incompatible avec cette lecture IOS tant que l’effacement de l’historique n’est pas confirmé.

Avant toute modification, le logiciel lit fraîchement `show interfaces <port> switchport`, vérifie le port demandé, son mode d’accès et son VLAN. Un résultat incomplet, un trunk, une sortie ancienne ou un mode inconnu bloque la préparation. L’inventaire VLAN est également contrôlé via le pont ; aucun VLAN de départ n’est présumé.

Le ticket crée un VLAN d’isolement libre entre 900 et 999 sur SW1 et y place seulement le port du PC directement raccordé. Le mode administratif du port est conservé. Le ping doit fonctionner avant et échouer après, sinon l’injection est annulée ou signalée comme incertaine. La consigne indique le VLAN attendu du poste.

La réparation contrôle le VLAN d’accès initial et le mode du port, l’identité du PC, la liaison et le ping. Le bouton « Rétablir le test » remet le VLAN initial ; il refuse une restauration automatique si le câblage ou le mode du port a changé. À la clôture, le VLAN temporaire est supprimé seulement si son nom correspond encore au ticket et si aucune affectation de port n’est détectée dans `show vlan brief`. Un VLAN renommé, utilisé ou mal lu est conservé et signalé dans le ticket.

Limite importante : la CLI laisse des commandes dans l’historique. Le mode masqué refuse cette cause avant d’envoyer des commandes ; les autres causes continuent de fonctionner selon leurs propres capacités. Aucune nouvelle extension n’est nécessaire. Les essais réels Packet Tracer peuvent attendre ton retour d’utilisation.

Mise à jour : conserve `donnees-netops.json`, `labs/`, `travail/` et les fichiers réseau associés.

# Nouveautés 0.12 — incidents IPv4 et réponses HTML

Les incidents du site proposent trois causes : port désactivé, adresse IPv4 incorrecte, masque incorrect. Le choix « Aléatoire compatible » conserve uniquement les causes applicables. Les deux mutations IPv4 exigent un PC statique en /24, une interface FastEthernet0 et la confirmation des capacités de lecture et modification de l’API. Un PC DHCP ou une capacité inconnue reste limité au port désactivé. Les arrivées de la session possèdent leur propre sélection de causes.

Pour les mutations IPv4, l’adresse et le masque de départ sont conservés dans le ticket. L’injection modifie uniquement ces valeurs via l’API : aucune commande de configuration n’est saisie dans la CLI. La passerelle et le DNS ne sont pas changés. Le plan d’adressage attendu figure dans la consigne. La réparation exige l’adresse et le masque attendus, l’identité du poste, une liaison active et un ping réussi vers le serveur. Le bouton de rétablissement remet les valeurs de départ.

Toutes les causes exigent désormais un échec de ping confirmé après injection. Si la modification ne provoque pas ce symptôme, le logiciel tente de la rétablir et conserve un ticket à contrôler. Une communication incertaine ne suffit pas à annoncer une panne validée. Un rétablissement incertain reste signalé. Les incidents de port conservent les contrôles de masquage des commandes ; les mutations IPv4 passent directement par l’API.

Les nouvelles feuilles HTML sauvegardent automatiquement les réponses dans le navigateur. Elles restaurent les réponses à la réouverture et proposent un export/import JSON. L’import refuse un fichier associé à une autre feuille. Cette sauvegarde dépend du navigateur : utilise l’export pour conserver une copie durable ou changer de navigateur. Les anciennes feuilles générées ne sont pas modifiées automatiquement.

Il reste à intégrer les incidents de VLAN et de services dans le site persistant, ainsi que leur validation adaptée. Ces changements ont été testés avec un pont simulé ; leur fonctionnement dans ta version de Packet Tracer reste à éprouver ultérieurement.

Mise à jour : conserve `donnees-netops.json`, `labs/`, `travail/` et les fichiers réseau associés.

# Nouveautés 0.11 — arrivées sur le site persistant

La session propose deux sources :
- « Réseaux indépendants — services » : conserve les familles DNS, HTTP, FTP, DHCP et sauvegarde, chacune sur son réseau dédié.
- « Site persistant — demandes et incidents » : crée les interventions directement sur le site enregistré, sans générer un nouveau fichier.

Dans le second mode, une arrivée peut demander l’ajout d’un PC, la connexion d’un portable Wi-Fi ou le dépannage d’un PC filaire présent. Les choix sont calculés depuis une nouvelle lecture du réseau, pas uniquement depuis l’inventaire sauvegardé. Un nouveau PC requiert un port FastEthernet libre sur SW1. Les demandes d’un type déjà ouvert sont évitées. Les incidents sont différés tant qu’une intervention du site reste ouverte, et la communication initiale du poste vers le serveur doit être confirmée avant injection. La découverte du port et les contrôles du site restent obligatoires.

Les six dernières interventions réduisent les répétitions du type ou du poste concerné. Le délai par ticket est appliqué aux interventions reçues ; le chronomètre démarre à la prise en charge. Le plafond compte les tickets ouverts des deux sources. Un échec ou l’absence d’une intervention compatible diffère l’arrivée de 15 secondes sans accumuler de tickets en attente. Les arrivées restent en pause au redémarrage.

Dans « Session de service IT », sélectionne la source et le mode de traces puis clique « Appliquer les réglages ». Tu peux recevoir une intervention immédiatement ou démarrer les arrivées. Le mode de traces de cette session est indépendant de celui des boutons de création manuelle. Le masquage reste obligatoire par défaut : une injection dont les traces ne peuvent pas être masquées est bloquée ou annulée.

Cette version n’injecte toujours pas les pannes DNS/HTTP/FTP/DHCP dans le site persistant. Les incidents automatiques du site concernent uniquement un PC filaire directement raccordé à SW1. Le Wi-Fi conserve une confirmation manuelle du SSID. Les essais avec un pont simulé ne remplacent pas les essais dans Packet Tracer.

Mise à jour : conserve `donnees-netops.json`, `labs/`, `travail/` et les fichiers réseau associés. Les réglages existants gardent par défaut la source « Réseaux indépendants ».

# Nouveautés 0.10 — inventaire et interventions successives

Le site conserve désormais son inventaire observé : nom, modèle, numéro de série, interfaces, adresses et dates d’observation. Le bouton « Actualiser depuis Packet Tracer » met à jour cet inventaire après contrôle du réseau ouvert. Les appareils absents restent dans l’historique. La clôture des demandes actualise aussi l’inventaire.

Après PC-NOUVEAU, les demandes suivantes utilisent PC-NOUVEAU-02, puis -03, etc. Même principe pour LAPTOP-WIFI. Un nom déjà utilisé dans l’historique n’est pas réattribué.

Un incident réseau peut maintenant concerner un PC filaire ajouté au site : sélectionne-le dans la liste des postes. Le pont détermine le port de SW1 directement raccordé au PC et désactive ce port uniquement. La réparation contrôle l’identité du PC, sa communication vers le serveur et la préservation des autres ports de SW1 initialement actifs. Les liaisons via un autre commutateur et les incidents Wi-Fi ne sont pas injectés par cette fonction.

Le masquage reste bloquant par défaut : si la suppression des traces n’est pas confirmée, l’injection est bloquée ou annulée. Le mode erreur humaine permet explicitement de conserver ces traces.

Cette étape fait évoluer le site de test existant. Les tickets de services DNS/HTTP/FTP/DHCP restent sur des réseaux indépendants ; ils ne sont pas encore injectés dans ce site. L’inventaire est une observation sauvegardée, pas une surveillance continue. Sauvegarde toujours ton fichier réseau dans Packet Tracer : les données web ne sauvegardent pas sa topologie.

Mise à jour : ferme l’application, extrais le nouveau kit, copie `donnees-netops.json`, `labs/` et, si utilisé, `travail/` depuis l’ancienne version. Conserve le fichier .pkt associé. Lance `LANCER-WINDOWS.bat`, puis actualise l’inventaire une fois le site ouvert.

# Nouveautés 0.9

Les tickets regroupent désormais 8 familles de plaintes et 11 causes concrètes. Deux familles proposent plusieurs causes : enregistrement DNS absent ou erroné ; absence de bail DHCP causée par le service ou le relais. Une seule cause est injectée par réseau. Les six derniers incidents sont pris en compte pour limiter les répétitions et une famille déjà ouverte n’est pas proposée à nouveau.

Le plan conserve la graine, la version des règles et la famille IPv4 privée. Une relance de génération réutilise ce plan. Les réseaux dédiés varient entre 10/8, 172.16/12 et 192.168/16. Les fichiers et les consignes emploient les mêmes valeurs. Les causes restent dans les données locales pour la correction, sans apparaître dans les propriétés publiques du ticket.

La validation des tickets de service reste manuelle : le programme ne prouve pas encore le fonctionnement HTTP, FTP ou DHCP dans Packet Tracer. Les incidents ne dépendent pas encore de l’état d’un site persistant. L’automatisation d’arrivée et les chronomètres existants restent disponibles.

Pour mettre à jour : ferme l’ancienne application, extrais ce kit, puis copie `donnees-netops.json` et le dossier `labs/` de l’ancienne version. Lance `LANCER-WINDOWS.bat`.

# Version pilote 0.9 — premiers tickets procéduraux

**11 types de tickets** : les 3 pilotes du site de test et 8 nouveaux incidents à réseau indépendant (DNS global, nom intranet absent, HTTP indisponible, FTP indisponible, écriture FTP refusée, authentification FTP refusée, DHCP arrêté, sauvegarde TFTP impossible).

Dans Tickets, ouvre **Session de service IT**. Choisis un intervalle fixe ou aléatoire entre 1 et 120 minutes, un plafond de 1 à 10 tickets ouverts, et un délai d’intervention par ticket (0 = sans limite). Applique les réglages puis démarre les arrivées. Le premier ticket est attendu après le premier intervalle ; Recevoir un incident maintenant permet de le créer immédiatement. Pause arrête les arrivées, pas les timers des interventions.

Les nouvelles arrivées automatiques concernent uniquement les 8 incidents à réseau indépendant. Aucun nouveau ticket de même scénario tant qu’un précédent est ouvert. Le plafond compte tous les tickets ouverts, y compris les pilotes. Une génération est traitée à la fois ; une arrivée empêchée par le plafond ou une génération est réessayée après 15 secondes, sans accumulation. La session revient en pause au redémarrage.

Chaque nouvel incident génère son propre réseau et sa feuille d’intervention, puis le bouton Ouvrir le réseau lance son PKA sous Windows. Il ne modifie ni le site actif ni les réseaux des autres tickets. Les pannes sont préparées dans les fichiers, sans commandes injectées dans une console live. Après un tel ticket, rouvre le site de test avant de reprendre les trois pilotes.

**Validation des 8 nouveaux tickets : manuelle.** Effectue les tests de la feuille dans Packet Tracer, enregistre un compte rendu précis, coche la déclaration des tests et clôture. Le logiciel conserve cette déclaration et ne la présente pas comme une réussite automatique. Le bouton de vérification rappelle cette limite. Le réseau de référence sain permet de comparer après le diagnostic. Une préparation échouée ou interrompue peut être relancée.

Ces incidents ne représentent pas encore des pannes qui arrivent sur le même site persistant. Le nettoyage des historiques live et la vérification automatique des services restent à développer. Le comportement des services doit être testé dans Packet Tracer. Les titres des feuilles de tickets décrivent le symptôme ; les indices/corrections sont accessibles volontairement.

Mise à jour : arrête l’ancienne application, conserve `donnees-netops.json` et le dossier `labs/` dans le nouveau kit, puis lance `LANCER-WINDOWS.bat`.

---

# Version pilote 0.7 — compte à rebours optionnel

Tickets et labs : sans limite (par défaut), 15, 30, 60 minutes ou durée personnalisée de 1 à 1440 minutes. La durée et le mode se verrouillent une fois le compteur démarré.

**Tickets** : applique la durée avant de prendre en charge ; le timer démarre à la prise en charge. Si le ticket est déjà en cours, appliquer une durée le démarre immédiatement. Il s’arrête uniquement après une clôture validée. Mettre le ticket en attente ne pause pas automatiquement le compteur ; utilise Pause en mode entraînement.

**Labs** : configure la durée, puis clique Commencer l’exercice lorsque tu es prêt dans Packet Tracer. Terminer mon exercice arrête le compteur sur déclaration manuelle, sans valider la configuration. L’ouverture d’un fichier ne démarre pas le timer automatiquement.

**Entraînement** : pause/reprise autorisée. **Défi** : aucune pause. Affichage orange dans les derniers 20 % du délai, rouge après dépassement. Le dépassement n’interdit pas de finir. Le timer est conservé avec les tickets et les labs ; tant qu’il n’est pas en pause, il continue même si le navigateur ou l’application est fermé. Il repose sur l’horloge du PC : modifier l’heure affecte le calcul.

L’export JSON du compte rendu d’un ticket inclut son chronomètre. Les timers de labs restent conservés dans leurs fichiers job.json. Ils sont affichés dans l’interface web, pas dans les PKA ni les HTML autonomes. Les arrivées automatiques de tickets ne sont pas encore implémentées.

Mise à jour : arrête l’ancienne application, conserve `donnees-netops.json` et le dossier `labs/` dans le nouveau kit, puis lance `LANCER-WINDOWS.bat`.

---

# Version pilote 0.6 — Reproduire une panne

Nouveau mode du générateur, avec trois exercices inverses : un seul nom inaccessible (DNS), serveur joignable mais page HTTP indisponible, connexion FTP acceptée mais dépôt refusé.

Le PKT et le PKA initiaux démarrent sur un réseau sain. Vérifie d’abord son fonctionnement, puis provoque les symptômes décrits sans interrompre les services à préserver. Les mêmes consignes figurent dans le PKA et le HTML. Le HTML fournit les indices progressifs et une méthode de correction, avec tests avant/après et restauration. Le fichier **correction.pkt** montre un exemple de panne reproduite, contrairement aux autres modes où il représente le socle sain. Plusieurs méthodes sont acceptables si les symptômes et les contraintes sont respectés.

Validation manuelle dans Packet Tracer : aucune panne n’est injectée dans ton site de tickets. La génération des fichiers et les mutations sont vérifiées en Python ; les tests réseau doivent être confirmés dans Packet Tracer. Les anciens labs ne sont pas modifiés.

Mise à jour : arrête l’application précédente, extrais le nouveau kit, conserve **donnees-netops.json** et le dossier **labs/**, puis lance **LANCER-WINDOWS.bat**.

---

# Version pilote 0.5 — générateur intégré

L’onglet **Générateur de labs** propose 23 ateliers, 55 dépannages (38 réseau et 17 services) et 3 scénarios mixtes. Choisis un mode, un niveau maximal de catalogue et un scénario précis ou aléatoire. Une graine permet de reproduire un exercice.

La génération tourne en arrière-plan. Les labs sont conservés dans `labs/`, indépendamment du site de tickets. Les fichiers proposés sont : PKA avec instructions, HTML avec indices/correction et champs de compte rendu, PKT initial pour les ateliers/services, et réseau de référence sain. Les dépannages réseau classiques proposent le PKA initial. Le nombre de pannes s’applique à ces derniers et peut être réduit si aucune autre panne compatible ne reste.

**Limites explicites** : validation manuelle des labs ; comportements des modèles de services/Meraki à confirmer dans Packet Tracer ; réseau de référence sans les appareils additionnels demandés par certaines évolutions. Les trois mixtes combinent deux tâches non contradictoires sur le même réseau. Les niveaux filtrent le catalogue existant, sans implémenter encore les cinq profils pédagogiques complets. Les réponses HTML ne sont pas sauvegardées automatiquement : utilise l’impression.

Pour conserver tes tickets et labs : arrête l’ancienne application, extrais le kit dans un nouveau dossier, copie `donnees-netops.json` et, si présent, le dossier `labs/`. Garde ton PKT de travail actuel, puis lance `LANCER-WINDOWS.bat`. Rouvre le site de tickets après avoir travaillé sur un lab.

Le catalogue de labs ne devient pas automatiquement un catalogue de tickets : seuls les trois tickets pilotes existent encore. Le masquage de l’historique reste bloquant quand il ne peut pas être confirmé. Aucune extension nouvelle à installer.

---

# Version pilote 0.4 — changements

- Résultats détaillés : un poste absent affiche son nom attendu et les noms détectés. Les détails du ping sont consultables.
- Recherche dans les identifiants, titres et consignes des tickets.
- Export JSON du compte rendu, y compris notes en cours (pas forcément enregistrées), contrôles et confirmation manuelle du SSID.
- Suppression de `clear cli history`, rejetée sur le switch testé. Le diagnostic utilise seulement la lecture des historiques et le nettoyage du tampon via l’API. Un historique non vide ou illisible bloque toujours l’injection masquée. Ce blocage n’est pas corrigé par une fausse validation.

Pour mettre à jour : arrête l’ancienne application, extrais le nouveau kit dans un autre dossier, copie ton `donnees-netops.json` dans ce dossier, puis lance `LANCER-WINDOWS.bat`. Garde ton fichier de travail Packet Tracer : il reste associé par son chemin actuel. Ne lance pas deux versions en même temps.

Le catalogue élargi, le générateur web et la gestion de plusieurs sites restent à intégrer. Le SSID reste une vérification manuelle.

---

# NetOps Lab — pilote 0.3

Une interface locale de tickets reliée à Packet Tracer. Python 3.10 minimum, aucune dépendance à installer avec pip. L’extension communautaire V5.2.pts est incluse et inchangée.

## Premier lancement sous Windows

1. Arrête l’ancien diagnostic (Ctrl+C dans sa console). Ne lance pas deux ponts à la fois.
2. Extrais entièrement ce nouveau ZIP dans un nouveau dossier. Ne lance pas le BAT depuis le ZIP.
3. Ouvre le fichier `reseau-test.pkt` fourni. Pour un premier essai, pars de cette copie propre, sans PC-NOUVEAU ni LAPTOP-WIFI.
4. Si V5.2 est déjà installée, conserve-la. Sinon : Extensions → Scripting → Configure PT Script Modules → Add, puis sélectionne `V5.2.pts`.
5. Ouvre Extensions → MCP BUILDER et laisse sa fenêtre ouverte. Utilise une seule instance Packet Tracer pendant ce pilote.
6. Double-clique `LANCER-WINDOWS.bat`. Garde la console ouverte. L’interface est disponible à http://127.0.0.1:8765.
7. Pour un nouveau site, tu peux aussi utiliser « Ouvrir le réseau dans Packet Tracer » : une copie de travail est créée dans travail/agence.pkt. Attends la confirmation de connexion et de reconnaissance du fichier, puis clique « Enregistrer ce site ». Si tu as déjà ouvert manuellement le PKT fourni, enregistre le site directement.

## Les trois tickets

### Incident réseau

Dans Tickets, clique « Créer un incident réseau ». Le logiciel vérifie le bon réseau, le câblage et le ping initial, puis provoque une coupure sur le raccordement de PC-ADMIN. Le ticket présente les symptômes et conserve des indices repliés.

Prends le ticket en charge, diagnostique et répare dans Packet Tracer. Clique « Vérifier l’intervention », puis « Vérifier et clôturer ». La clôture relance les contrôles, même si un contrôle précédent était réussi.

Si l’injection reste incertaine ou si tu veux annuler la panne, ouvre les « Outils de test » du ticket puis « Rétablir le test ». Cela réactive le port utilisé par ce scénario et lance une vérification. Attends la convergence puis réessaie si nécessaire. Une deuxième panne de ce type est refusée tant que ce ticket reste ouvert.

### Ajout d’un PC

Crée la demande AVANT d’ajouter l’appareil. Ajoute un PC nommé `PC-NOUVEAU`, raccordé à un port libre de SW1. Active DHCP. Le poste doit recevoir une adresse de `192.168.50.0/24` et joindre `192.168.50.10`.

Le logiciel vérifie sa présence, son ajout par comparaison des numéros de série, la liaison filaire, l’adresse et un nouveau ping lancé depuis le poste.

### Portable Wi-Fi

Crée la demande AVANT d’ajouter l’appareil. Ajoute `LAPTOP-WIFI` avec une carte Wi-Fi compatible. Selon le modèle disponible, WPC300N est la carte utilisée dans l’interface PC Wireless de ton test ; éteins l’appareil avant de remplacer la carte. Choisis le SSID ouvert `Agence-Lab`, active DHCP et retire tout câble réseau du portable.

Les contrôles automatisés portent sur la nouvelle identité, la radio, l’adressage, l’absence de câble actif et le ping. Le SSID et le point d’accès exacts ne sont PAS prouvés par ce pont. La clôture demande donc une confirmation manuelle explicite du SSID. Cette confirmation ne permet pas de contourner un ping échoué.

## Sauvegarde et reprise

Les tickets, leurs notes, leurs résultats, le journal et l’identité du site sont conservés dans `donnees-netops.json`, créé à côté du logiciel. Ne le supprime pas et conserve-le quand tu reprends ce pilote.

Sauvegarde AUSSI ton travail dans Packet Tracer (par exemple `agence-en-cours.pkt`). Au redémarrage, rouvre cette sauvegarde, ouvre MCP BUILDER et relance le BAT. Le logiciel refuse les opérations s’il ne retrouve pas les équipements de référence.

Ce pilote gère un seul site, une seule instance et les trois scénarios ci-dessus. Il ne crée pas encore automatiquement d’autres sites ou réseaux. Le générateur complet reste séparé. Aucun redémarrage ne doit être fait pendant une injection ; une injection interrompue peut avoir eu lieu, utilise le rétablissement du ticket avant de poursuivre.

## Nouveautés 0.3 et mise à jour

- Statuts avec couleur et libellé : nouveau bleu, en cours orange, en attente violet, clos vert, à contrôler rouge.
- Sévérité séparée : faible gris, modérée jaune, élevée orange, critique rouge. Elle représente l’impact, pas la difficulté. Elle est modifiable et sauvegardée.
- Filtres par statut et sévérité.
- Bouton d’ouverture du réseau du site depuis la page Site et les tickets. Le générateur complet reste séparé ; ce mécanisme pourra y être réutilisé lorsqu’il sera intégré.
- Contrôle séparé de l’adresse configurée et du lien : une interface inactive ne transforme plus une adresse correcte en erreur IP.

Pour conserver ta progression : arrête l’ancienne version, extrais la nouvelle dans un nouveau dossier et copie `donnees-netops.json` depuis ton ancien dossier. Conserve ta sauvegarde PKT actuelle. Aucun fichier de progression n’est inclus dans le ZIP.

Dans « Site de test », renseigne le chemin complet de ta sauvegarde existante, puis « Associer cette sauvegarde ». Cette sauvegarde doit être ouverte dans Packet Tracer au moment de l’association : le logiciel compare le nom du fichier courant et les équipements du site. Après chaque Enregistrer sous, associe le nouveau chemin. Le bouton « Ouvrir le réseau » demande à Windows d’ouvrir ce fichier avec son application associée (Packet Tracer doit être associé aux .pkt/.pka).

Après ouverture, l’interface attend jusqu’à une minute le pont et la reconnaissance du fichier. Les boîtes de dialogue Packet Tracer (travail non sauvegardé, activité, etc.) restent à traiter manuellement. Si le délai est dépassé, clique « Vérifier la connexion et le site ». MCP BUILDER démarre déjà automatiquement sur ton installation. Respecte la règle d’une seule instance pour ce pilote.

## Console et discrétion des pannes

Le mode par défaut est « Masquées ». Le moteur teste le nettoyage AVANT l’injection. Il utilise `clear cli history`, vérifie les historiques utilisateur et configuration exposés par l’API, vide le tampon avec `TerminalLine.flush`, puis relit le résultat. La commande et les structures d’historique doivent être effectivement supportées par ta version : leur succès n’est pas supposé.

Si le test préalable échoue, aucune panne n’est injectée. Si le nettoyage échoue après injection, le moteur tente de réactiver le port et contrôle son état ; le ticket passe à « À contrôler ». Si le rétablissement n’est pas confirmé, il reste explicitement incertain. Le logiciel ne prétend pas que la panne est discrète.

Dans « Site de test », « Tester le nettoyage de SW1 » affiche séparément le résultat du tampon et celui des historiques. Ce test efface les anciennes commandes et l’affichage de la console locale SW1, sans modifier sa configuration. Les journaux globaux et les preuves réseau ne sont pas effacés. Ferme la CLI SW1 pendant le test ou la création d’une panne ; après, rouvre-la et vérifie également la flèche haut. Le rendu réel de la console doit encore être validé dans ton installation Windows.

Le mode « Visibles — erreur humaine simulée » conserve volontairement les commandes. Il faut le sélectionner explicitement avant la création du ticket. Les tickets provenant de la version 0.2 ne sont pas nettoyés rétroactivement ; leur ancienne console peut donc conserver des traces.

Documentation utilisée : https://tutorials.ptnetacad.net/help/default/IpcAPI/class_terminal_line.html et https://tutorials.ptnetacad.net/help/default/IpcAPI/struct_command_history.html .

## Ordre des essais dans Packet Tracer

1. Reprends tes tickets et vérifie les couleurs, les filtres et le statut En attente.
2. Associe ta sauvegarde ouverte. Ferme Packet Tracer après l’avoir sauvegardé, puis utilise « Ouvrir le réseau ». Vérifie la reconnexion et le fichier reconnu.
3. Sur le site sain, ferme la CLI SW1 et lance le test de nettoyage. Rouvre la CLI et vérifie l’affichage ainsi que ↑. Si le contrôle reste inconnu, transmets le diagnostic affiché ; ne présente pas cette panne comme masquée.
4. Crée un nouvel incident en mode masqué si le test passe, puis effectue réparation, vérification et clôture.
5. Crée la demande PC AVANT l’ajout. Ajoute PC-NOUVEAU, câble-le et configure DHCP. Vérifie, puis débranche le câble : la clôture doit échouer. Rebranche, attends, vérifie et clôture.
6. Crée la demande Wi-Fi AVANT l’ajout. Ajoute LAPTOP-WIFI, associe-le à Agence-Lab et active DHCP sans câble. Vérifie, puis déconnecte le Wi-Fi : même avec confirmation du SSID, la clôture doit échouer. Reconnecte, vérifie et clôture en confirmant manuellement le SSID.
7. Sauvegarde le PKT, relance l’application et vérifie la conservation des tickets et notes.

## Limites des vérifications

Les réponses inconnues ne sont pas transformées en réussites. L’adresse est contrôlée par appartenance au réseau ; le masque et la passerelle ne sont pas évalués séparément. Un ping réussi prouve la communication ICMP testée, pas le fonctionnement du service HTTP. Le terminal du poste est utilisé pour le ping : laisse-le libre pendant une vérification. Le pont ne sauvegarde pas le PKT automatiquement et n’empêche pas d’ouvrir plusieurs fenêtres Packet Tracer ; il faut respecter la règle d’une seule instance.

## Validation de cette version

19 tests Python passent : échange du pont et authentification, ajout d’un appareil, refus d’un simple renommage, sauvegarde/reprise, mauvais réseau, cycle incident, doublons, clôture après un ancien succès, confirmation Wi-Fi et interruption d’injection. La syntaxe JavaScript de l’interface est vérifiée. Le script de nettoyage a aussi été testé avec un terminal simulé : succès et refus pour API absente, commande rejetée ou affichage non effacé.

Les tests de tickets utilisent un simulateur du pont. Le pont réel, les contrôles filaires et Wi-Fi et le cycle panne/réparation ont été testés dans la version diagnostic précédente. Le parcours incident et la reprise des tickets 0.2 ont été confirmés par tes essais. Le nouveau lancement depuis le navigateur, le nettoyage réel et les deux demandes doivent encore être confirmés dans ton Packet Tracer Windows.

## Dépannage

- Ports occupés : ferme l’ancien diagnostic ou l’autre kit utilisant 54321 et 8765.
- Pont déconnecté : ouvre MCP BUILDER, laisse la fenêtre ouverte, vérifie son indicateur HTTP.
- Python absent : installe Python 3.10 ou plus récent et active « Add Python to PATH ».
- Mauvais site : rouvre le fichier sauvegardé correspondant au site enregistré. Ne remplace pas les équipements de départ par des copies nouvelles.
- Pour recommencer à zéro : ferme le logiciel, conserve une copie de `donnees-netops.json`, déplace ce fichier hors du dossier, puis rouvre le PKT propre. Les anciens tickets restent dans ta copie.

L’ancien outil reste accessible en lançant `python diagnostic.py` séparément ; voir `DIAGNOSTIC-MODE-EMPLOI.md`. Ne le lance pas en même temps que NetOps Lab.

## Sources et licence

Extension et pont communautaires : https://github.com/Mats2208/MCP-Packet-Tracer (licence MIT incluse dans vendor). Documentation de déploiement : https://mats2208.github.io/MCP-Packet-Tracer/live-deploy/ . L’extension fournie n’a pas été modifiée. Ce kit n’est pas un produit officiel Cisco.
