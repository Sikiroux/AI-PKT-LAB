# Ateliers Packet Tracer — services, Wi-Fi et Meraki

## Utilisation

Lancer `python main.py`, choisir **5 — Ateliers services / Wi-Fi / Meraki**, puis un gabarit et une mission. Ouvrir `lab.pka` (consignes embarquées) ou `lab.pkt` (réseau simple), puis `consignes.html` dans un navigateur. Les indices sont repliés ; la correction complète est à la fin. Les nouveaux ateliers sont en français. Les anciens labs FR/EN restent disponibles.

Le menu **Valider un lab** dirige les ateliers vers une vérification manuelle. Le statut « vérifié manuellement » est une déclaration de l’utilisateur, sans score automatique. `checker.check` renvoie `success=None` pour les fichiers marqués `validation=manual` : aucune mission vide n’est considérée réussie par défaut.

### Ligne de commande

```bash
python workshops.py --list
python workshops.py --scenario configure_mail --seed 123 --output atelier_mail
python workshops.py --scenario meraki_dashboard --seed 123 --output atelier_meraki
python workshops.py --scenario dns_record_wrong --seed 123 --output atelier_dns
```

La même seed conserve l’adressage du gabarit. `--pkt-only` produit uniquement le réseau .pkt et la feuille HTML, sans wrapper .pka. Chaque atelier contient aussi un JSON avec les résultats attendus.

## Gabarits

| Gabarit | Contenu | État de départ |
|---|---|---|
| Entreprise avec services | R1, 3 switches, 3 postes, DNS/DHCP/NTP/Syslog/TFTP, WEB, FTP, MAIL | Réseau routé configuré ; services DNS, HTTP, FTP et infrastructure préparés. MAIL est à configurer dans les missions correspondantes. |
| Agence Wi-Fi | Routeur DHCP, switch, AP, PC admin filaire, serveur DNS/web | Socle filaire préparé ; portables et cartes Wi-Fi à ajouter dans PT. |
| Agence Meraki | MX65W, switches LAN/WAN, ISP DHCP, serveur Meraki/DNS, serveur public distant, 2 postes | MX non câblé/non enregistré : câblage, WAN, dashboard et politiques à réaliser par l’apprenant. |

Les trois gabarits supplémentaires sont gérés par `workshops.TOPOLOGIES`, distincts des six anciens gabarits `builder.THEMES`. Les anciennes pannes restent dans `faults.CATALOGUE`. Les nouveaux ateliers sont dans `workshops.CATALOGUE`. Cette séparation évite que le mode automatique attribue un score aux tâches manuelles.

## Catalogue

| Identifiant | Type | Niveau | Gabarit | Objectif |
|---|---|---|---|---|
| `dns_service_off` | fault | 1 | enterprise_services | DNS arrêté |
| `dns_record_delete` | fault | 1 | enterprise_services | Enregistrement DNS absent |
| `dns_record_wrong` | fault | 1 | enterprise_services | Enregistrement DNS incorrect |
| `http_service_off` | fault | 1 | enterprise_services | Serveur web arrêté |
| `ftp_service_off` | fault | 1 | enterprise_services | Service FTP arrêté |
| `ftp_write_denied` | fault | 2 | enterprise_services | FTP : écriture refusée |
| `ftp_password_wrong` | fault | 1 | enterprise_services | FTP : authentification refusée |
| `server_gateway_wrong` | fault | 2 | enterprise_services | Serveur : passerelle incorrecte |
| `dhcp_server_off` | fault | 1 | enterprise_services | DHCP arrêté |
| `dhcp_gateway_wrong` | fault | 2 | enterprise_services | DHCP : mauvaise passerelle |
| `dhcp_dns_wrong` | fault | 2 | enterprise_services | DHCP : mauvais DNS |
| `dhcp_mask_wrong` | fault | 2 | enterprise_services | DHCP : mauvais masque |
| `dhcp_relay_missing` | fault | 2 | enterprise_services | Relais DHCP absent |
| `dhcp_relay_wrong` | fault | 2 | enterprise_services | Relais DHCP vers le mauvais serveur |
| `ntp_destination_wrong` | fault | 2 | enterprise_services | NTP : mauvaise destination |
| `syslog_destination_missing` | fault | 2 | enterprise_services | Syslog : collecte absente |
| `tftp_service_off` | fault | 2 | enterprise_services | TFTP : sauvegarde impossible |
| `configure_dns` | configuration | 1 | enterprise_services | Publier les noms des services |
| `configure_mail` | configuration | 2 | enterprise_services | Déployer la messagerie |
| `configure_ftp` | configuration | 2 | enterprise_services | Déployer un dépôt avec permissions |
| `configure_dhcp_relay` | configuration | 2 | enterprise_services | Déployer DHCP centralisé |
| `guest_firewall` | evolution | 2 | enterprise_services | Isoler les invités |
| `ban_one_device` | evolution | 2 | enterprise_services | Bloquer un poste précis |
| `add_web_server` | evolution | 2 | enterprise_services | Ajouter un serveur web |
| `configure_aaa` | configuration | 3 | enterprise_services | Centraliser les accès avec AAA |
| `wifi_add_client` | configuration | 2 | wifi_deployment | Connecter un portable Wi-Fi |
| `wifi_secure` | configuration | 2 | wifi_deployment | Sécuriser le Wi-Fi |
| `wifi_diagnose_client` | configuration | 2 | wifi_deployment | Créer puis résoudre un incident Wi-Fi |
| `wifi_add_ap` | evolution | 2 | wifi_deployment | Étendre la couverture |
| `meraki_commission` | configuration | 2 | meraki_branch | Mettre en service l’agence Meraki |
| `meraki_dashboard` | configuration | 2 | meraki_branch | Enregistrer le MX dans le dashboard |
| `meraki_wifi` | configuration | 2 | meraki_branch | Déployer le Wi-Fi du MX |
| `meraki_filter` | evolution | 2 | meraki_branch | Bloquer un client au pare-feu Meraki |
| `meraki_wan_incident` | configuration | 2 | meraki_branch | Diagnostiquer une passerelle WAN erronée |
| `dns_alias` | evolution | 1 | enterprise_services | Publier un alias DNS |
| `web_publish` | evolution | 1 | enterprise_services | Publier une page web |
| `backup_restore` | configuration | 2 | enterprise_services | Sauvegarder et restaurer R1 |
| `monitoring_deploy` | configuration | 2 | enterprise_services | Déployer NTP et Syslog |
| `mail_client_incident` | configuration | 2 | enterprise_services | Diagnostiquer un client mail |
| `mail_pop3_incident` | configuration | 2 | enterprise_services | Diagnostiquer la réception de mails |

## Validation et limites

- Le socle est généré à partir des templates du projet ; les ateliers serveur utilisent le Server-PT complet du catalogue (les vieux templates DNS n’offrent pas tous les services).
- Les pannes DHCP commencent avec PC-ALICE sans bail, pour empêcher qu’un bail précédent masque l’incident. Le pool EMPLOYEES fournit .100 à .149 ; l’adresse statique .21 de la table n’est pas imposée au client DHCP.
- Les incidents mail et Wi-Fi en plusieurs étapes font établir un état sain, injecter une mauvaise configuration dans l’interface, constater le symptôme puis réparer. Ils sont présentés comme des missions guidées, pas comme des pannes déjà injectées.
- Les missions Meraki restent dans le simulateur. `dashboard.meraki.com` est résolu vers MERAKI-CLOUD du lab ; aucun compte cloud réel n’est requis. Le service DHCP du dashboard Meraki n’est pas proposé comme tâche de modification.
- Le site public Meraki est derrière ISP sur 198.51.100.0/24 ; il permet de tester la passerelle WAN, contrairement à un serveur situé sur le réseau WAN directement connecté.
- Les tests Python contrôlent génération, schémas XML, mutations, consignes, enveloppes .pka chiffrées et absence de faux verdict automatique. Ils ne prouvent pas la connectivité dans Packet Tracer.
- **Tous les nouveaux ateliers sont à tester dans Packet Tracer 9.** Le gabarit Meraki et son enregistrement dans le dashboard méritent une vérification réelle en priorité. Si le wrapper .pka d’un modèle GUI pose problème, tester le .pkt simple fourni dans le même dossier.
- Ces ajouts ne promettent pas encore toutes les combinaisons de pannes ni des missions multi-incidents : chaque nouvel atelier sélectionne un scénario explicite.

## Vérification conseillée dans Packet Tracer

1. Tester le socle entreprise : PC-ALICE ouvre l’intranet par IP et par nom ; FTP accepte les comptes de la feuille. Passer un poste en DHCP et vérifier masque/passerelle/DNS.
2. Ouvrir un lab DNS ou HTTP piégé : observer l’échec décrit, puis vérifier le retour du service après réparation.
3. Wi-Fi : PC-ADMIN ouvre le site ; ajouter un portable avec carte Wi-Fi, association et DHCP ; tester navigateur et refus avec une mauvaise clé.
4. Meraki : câbler le MX depuis l’interface PT, WAN DHCP, accès au site public et au dashboard local ; enregistrer le MX et tester le filtrage depuis les deux postes.
5. Pour chaque atelier : documenter la version de PT, le symptôme avant réparation, les changements et les tests finaux.

## Tests de développement

```bash
python tests/test_all.py
python tests/test_workshops.py
```

Le premier conserve la couverture du générateur historique ; le second parcourt les 40 fiches, teste les mutations et produit/recharge un .pka de chaque nouveau gabarit.
