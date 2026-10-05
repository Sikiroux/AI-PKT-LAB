# v0.24 — Interventions mixtes, portable et échanges client

Cette version conserve le générateur Packet Tracer indépendant et ajoute des interventions sur l’entreprise active. Le réseau, les postes web, l’annuaire, les fichiers et le DNS appartiennent à une même session. Aucun OS réel, tunnel VPN réel ou serveur SMB n’est lancé.

## Parcours

1. Décompresser le ZIP, lancer `lancer.bat`, ouvrir l’interface locale.
2. Accueil → reprendre une entreprise ou Postes et environnement → créer une seed.
3. Ouvrir **son** entreprise.pkt. Réparer la première liaison client, vérifier maintenant, ouvrir le bureau distant, authentifier le demandeur et rétablir la lecture du partage. Clôturer ce premier ticket.
4. Dans Postes et environnement, choisir difficulté (1, 2 ou 3 couches), orientation et délai, puis Recevoir un ticket procédural. Les causes sont privées ; la plainte présente le poste, le document et le résultat attendu.
5. Contacter le demandeur depuis le ticket ou l’environnement. Diagnostiquer avec le portable, le bureau client et Packet Tracer. Vérifier puis clôturer dans Tickets.
6. Pour les arrivées : choisir Site persistant, difficulté/orientation, délai et intervalle, appliquer et démarrer. L’intervention aléatoire devient un ticket mixte sur l’entreprise active. Une panne en cours diffère l’arrivée suivante ; on n’empile pas des changements non réparés sur le même demandeur.

Sauvegarder le réseau **dans Packet Tracer avant de changer d’entreprise**. La sauvegarde web conserve les données simulées mais ne sauve pas la topologie actuellement ouverte. Changer d’environnement ferme les bureaux associés au précédent.

## Catalogue et procédural

| Couche | Causes |
|---|---:|
| Annuaire | 5 : compte désactivé/verrouillé, mot de passe expiré, groupe lecture/écriture absent |
| Fichiers | 8 : service arrêté, partage désactivé, transport bloqué, permission partage/écriture absente, quota plein, disque plein, lecture seule |
| DNS | 7 : résolveur incorrect, entrée absente/incorrecte, service/transport interrompu, cache négatif/périmé |
| Réseau PT | 1 : câble client retiré |

21 causes élémentaires ; 151 combinaisons de deux couches et 411 de trois couches, soit **583 ensembles de causes** avant les variations d’entreprise, noms, adresses et index d’intervention. Chaque couche apparaît au plus une fois dans un ticket. L’orientation impose une couche, les autres restent tirées. La difficulté désigne le nombre de couches, pas une estimation du temps.

La seed et l’index alimentent un flux dédié `mixed:v1`. Une même seed, un même index et les mêmes options produisent les mêmes causes. L’état actif peut ensuite varier avec les actions réalisées et les observations Packet Tracer. Les horodatages ne sont pas déterministes. Les booleans ne sont pas une preuve réseau : oui/non/inconnu/bloqué restent distincts.

La validation porte sur **le fichier exact** du ticket, la lecture et, si nécessaire, l’écriture avec croissance. Elle conserve les autres fichiers, les identités et droits des autres utilisateurs, les entrées DNS non ciblées et la configuration DNS du technicien. Une panne câble conserve en plus une référence des autres ports observables. Les ports réservés au portable sont exclus de cette référence. Plusieurs causes doivent être réparées ; activer le compte seul ne restaure pas un service arrêté.

## Portable du technicien

Les nouveaux réseaux possèdent un Laptop-PT nommé `<SITE>-LT-TECH-01`, identifiable par son numéro de série. Un prestataire peut l’utiliser même sans IT résident ; il ne signifie pas que chaque entreprise emploie un administrateur. Les anciennes sessions gardent leur appareil existant et peuvent afficher un déplacement indisponible si elles n’ont pas les destinations réservées.

Bureau du technicien → **Mobilité et VPN** : Bureau utilisateurs, Salle serveurs, ou Télétravail. Chaque destination dispose d’un switch identifié, d’un port Ethernet réservé, d’une adresse et d’une passerelle. Le déplacement concerne le raccordement logique et l’adresse, **pas encore le déplacement du pictogramme ou du châssis dans la vue physique PT**.

- Ethernet : adresse statique du site, passerelle et câble ; pings depuis cet appareil PT.
- Console : RS232 vers Console, sans transport IP. Configurer IOS dans Packet Tracer ; le terminal web IOS n’est pas ajouté dans ce bloc.
- Déconnecté : liens réseau et console retirés.

Avant mutation, le serveur vérifie le fichier ouvert et les numéros de série. Un port réservé occupé ne doit pas être remplacé. Le bridge vérifie l’existence de ses méthodes avant de modifier. Si l’API locale refuse une opération ou perd sa réponse, la session conserve une **destination en attente** : appliquer le raccordement/adressage indiqué dans PT puis Confirmer après raccordement manuel. La confirmation contrôle liaison, pair, adresse et masque ; la passerelle n’est pas exposée dans notre snapshot et doit être vérifiée dans PT, puis testée par le réseau.

Le télétravail utilise le segment invités du lab comme réseau extérieur pédagogique, pas un Internet réellement isolé. Vérifier le réseau puis connecter le VPN avec `Formation!2026`. Le VPN est une politique web de formation, valable 30 minutes, conditionnée à un ping PT récent du portable vers sa passerelle. Le ping passerelle reste disponible avant connexion VPN. Les accès d’entreprise du technicien sont bloqués sans VPN ; aucune promesse de cryptage/tunnel Cisco réel. Déconnexion, déplacement, preuve périmée ou reprise d’une sauvegarde empêchent de réutiliser cette autorisation.

## Dialogue sans LLM

Huit questions à choix : poste/document, depuis quand, connexion physique, accès IP, résolution par nom, session utilisateur, sauvegarde et nouveau test. Le demandeur répond selon l’état **actuel**, sans corriger la panne. Les constats IP et câble nécessitent leurs propres observations récentes. Une absence de constat n’est pas transformée en câble débranché. Les échanges sont conservés dans session.json et le ticket ; 60 échanges maximum par incident. Les anciens tickets restent lisibles mais ne peuvent pas interroger un nouvel incident.

## Architecture

| Fichier | Responsabilité |
|---|---|
| web/mixed_incidents.py | Tirage, préparation, objectifs et préservation |
| web/client_dialogue.py | Questions autorisées et réponses dépendantes de l’état |
| web/technician_model.py | Mobilité logique, invalidation et politique VPN |
| web/workspace_links.py | Scripts limités aux câbles, gardes d’identité et signature des ports |
| web/workspace_app.py | Orchestration, persistance et bridge |
| web/workspace_routes.py | Routes liées explicitement à l’environnement |
| web/service_desk.py / tickets_app.py | Arrivées, délais, historique et clôture |

Routes POST : `/workspace/mixed-incident` (level, target, minutes), `mixed-confirm`, `dialogue` (ticket_id, question), `technician/move` (location, connection), `technician/confirm`, `technician/vpn-connect` (password), `technician/vpn-disconnect`. Toutes exigent l’identifiant actif et le token diagnostic. Le serveur construit les identités, destinations et preuves ; il n’accepte pas une destination matérielle arbitraire du navigateur.

Une injection réseau persistée avant mutation reste non validable si son résultat est incertain. Le bouton de confirmation relit le bon appareil et son câble d’origine. Les erreurs ne déclenchent pas une restauration implicite d’une autre topologie. Le scheduler possède le verrou de session ; le controller prend le verrou bridge seulement pour les opérations réseau, sans le reprendre récursivement. Les callbacks de dialogue/création ne recréent plus le scheduler ni ne mettent les arrivées en pause.

## Vérifications et limites

Tests Python : toutes les causes simulées refusent l’objectif avant réparation et l’autorisent après, panne partiellement réparée, preuve périmée, cible supprimée, droits/DNS tiers altérés, dialogue courant, mauvais environnement, VPN et expiration, câble incertain et confirmation, mobilité manuelle et persistance du scheduler. Tests bridge **avec doublures**, pas une certification des méthodes PT.

À vérifier lors de ton utilisation : ouverture des nouveaux Laptop-PT, raccordement Ethernet automatique selon ton API, connexion console, rejet d’un port occupé, maintien des autres câbles, expiration VPN, coupure/reconnexion réelle et arrivée d’un ticket après clôture. Si un raccordement automatique n’est pas supporté, la confirmation manuelle est prévue. Les textes exacts d’erreur IOS, SMB/RDP réels et durées de réponse ne sont pas simulés fidèlement ; ICMP reste une preuve proxy explicitement affichée.
