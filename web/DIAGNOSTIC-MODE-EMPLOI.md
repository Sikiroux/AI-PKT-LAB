# Kit de test du pont Packet Tracer

Prototype de diagnostic, pas encore l'application de tickets. Windows et Python 3.10 ou plus récent. Aucune installation pip, aucun compte IA requis. Utiliser une seule instance de Packet Tracer et aucun autre pont MCP actif pendant l'essai.

## Démarrer

1. Extraire entièrement le ZIP dans un dossier (ne pas lancer depuis le ZIP).
2. Dans Packet Tracer : Extensions > Scripting > Configure PT Script Modules > Add. Choisir V5.2.pts inclus dans ce dossier. Si Packet Tracer demande des permissions de script, les examiner et autoriser ce module pour cet essai.
3. Double-cliquer LANCER-WINDOWS.bat. Le navigateur ouvre http://127.0.0.1:8765. Laisser la console ouverte. Si Python manque, installer Python 3.10+ depuis https://www.python.org/downloads/windows/ avec Add Python to PATH.
4. Ouvrir reseau-test.pkt dans Packet Tracer.
5. Ouvrir Extensions > MCP BUILDER. Garder la fenêtre de cette extension ouverte pendant les contrôles. Si un token absent est signalé, fermer puis rouvrir cette fenêtre après le démarrage du lanceur.
6. Sur la page de diagnostic : Tester la connexion, puis Lire le réseau. Vous devez retrouver R1, SW1, AP1, PC-ADMIN et SRV-WEB.
7. Depuis PC-ADMIN, tester manuellement ping 192.168.50.10. Attendre que les liens soient actifs, puis refaire le ping si les premiers paquets sont perdus. Ce réseau est structurellement contrôlé, mais n'a pas été ouvert ici dans Packet Tracer : ce test confirme son fonctionnement réel.
8. Enregistrer l'état de départ. Il est conservé dans la session du diagnostic et exporté dans etat-depart.json. Après un redémarrage du programme, ouvrir une copie du réseau initial et refaire l'enregistrement. Le prototype ne recharge pas automatiquement cet état.

## Réseau de test

- Réseau : 192.168.50.0/24 ; masque 255.255.255.0.
- Routeur R1 : 192.168.50.1 ; pool DHCP à partir de .50.
- Serveur SRV-WEB : 192.168.50.10 ; DNS et HTTP activés.
- PC-ADMIN : 192.168.50.20.
- Point d'accès AP1 : SSID Agence-Lab, sans sécurité pour isoler le test du pont.
- Switch SW1 : port FastEthernet0/4 disponible pour le nouveau PC.

## Test A : ajouter un PC

1. Ajouter un PC-PT et le nommer PC-NOUVEAU (nom affiché).
2. Le raccorder par câble cuivre droit : FastEthernet0 du PC vers FastEthernet0/4 de SW1.
3. Desktop > IP Configuration > DHCP. Alternative pour isoler un problème DHCP : adresse 192.168.50.30, masque 255.255.255.0, passerelle 192.168.50.1, DNS 192.168.50.10.
4. Attendre les liens actifs puis utiliser le contrôle Ajout d'un PC câblé, destination 192.168.50.10.
5. Les critères du test câblé doivent être validés. Une perte partielle au ping n'est pas un succès : refaire après convergence.
6. Débrancher le câble : le contrôle doit échouer. Rebrancher, puis essayer une adresse hors réseau : le contrôle d'adressage doit échouer.
7. Renommer un ancien équipement ne compte pas comme un ajout : la comparaison utilise son numéro de série.

## Test B : ajouter un portable Wi-Fi

1. Ajouter un Laptop-PT et le nommer LAPTOP-WIFI.
2. Dans Physical : éteindre le portable, remplacer sa carte Ethernet par PT-LAPTOP-NM-1W, puis rallumer.
3. Configurer le client sans fil pour rejoindre Agence-Lab (Desktop > PC Wireless ou paramètres Wireless0 selon la version). Ne raccorder aucun câble réseau au portable.
4. Activer DHCP ; alternative statique : 192.168.50.31/24, passerelle .1, DNS .10.
5. Dans le diagnostic choisir Ajout d'un portable Wi-Fi et vérifier.
6. Le prototype contrôle interface Wi-Fi, adressage, absence de liaison filaire active et ping. Le critère SSID/point d'accès reste INCONNU : le ticket Wi-Fi ne sera donc jamais déclaré entièrement validé par ce prototype.
7. Déconnecter le Wi-Fi et refaire le contrôle. Tester aussi un portable qui communique seulement par câble : ce cas ne doit pas être accepté comme Wi-Fi.

## Retour à fournir

Indiquer la version Packet Tracer (Help > About), le résultat de Tester la connexion et copier le JSON de Lire le réseau puis de Vérifier l'intervention. Il contient les noms, numéros de série, interfaces, IP et résultats des tests ; il ne contient pas le secret du pont. Pour réinitialiser le réseau, rouvrir le fichier initial sans enregistrer les modifications dessus ; enregistrer votre travail sous un autre nom.

## Limites et contrôles effectués

- Pas d'injection de panne, pas de suivi multi-instance, pas de validation HTTP/DNS : le ping ne prouve que la communication IP.
- Une lecture d'interface est un état observé ; un contrôle indisponible reste inconnu.
- Le ping utilise le terminal du poste et y laisse sa commande. Pendant la vérification, ne pas utiliser simultanément ce terminal. Langue attendue de ses statistiques : anglais, comme dans le moteur Packet Tracer ; un format non reconnu reste inconnu.
- Tests automatisés : distinction ajout/renommage, refus du câble pour Wi-Fi, critère SSID inconnu, échange HTTP authentifié avec une extension simulée. Chiffrement/déchiffrement du PKT contrôlé. Aucun essai réel de l'extension dans Packet Tracer effectué ici.
- Le programme écoute seulement sur 127.0.0.1, ports 8765 et 54321. Le pont et les actions web utilisent des secrets. Il faut fermer tout programme concurrent utilisant ces ports. Ctrl+C dans la console arrête le diagnostic.

## Sources et attribution

Extension officielle du projet communautaire MCP-Packet-Tracer : V5.2.pts, release v0.9.0, téléchargée depuis https://github.com/Mats2208/MCP-Packet-Tracer/releases/download/v0.9.0/V5.2.pts.
Pont Python et gestion du token repris sans modification du dépôt MIT https://github.com/Mats2208/MCP-Packet-Tracer, commit 846db381bc2c6ee0229d56e1d7ce8847eb6b213d. Licence jointe dans vendor/LICENSE-MCP-Packet-Tracer. Le diagnostic et son interface sont spécifiques à ce kit.
