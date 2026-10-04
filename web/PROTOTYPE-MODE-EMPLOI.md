# Version intégrée 0.15

Le lancement et le bureau OS.js sont maintenant réunis avec les tickets et le générateur sur le port 8765. Voir docs/INTEGRATION-OSJS.md. Les instructions ci-dessous décrivent le prototype initial ; le port 8766 et le bureau HTML provisoire sont remplacés.

# Prototype 1 — poste et partage

## Installation et lancement

Télécharger toute la branche `codex/procedural-service-desk-prototype`, puis extraire le projet. Python 3.10+ requis, aucune dépendance supplémentaire.

1. Fermer le serveur NetOps Lab/diagnostic actuel : il utilise le même pont.
2. Lancer `web/LANCER-PROTOTYPE.bat` sous Windows, ou `python web/workspace_app.py`.
3. Ouvrir `http://127.0.0.1:8766`. Choisir une seed, puis « Créer l’environnement ».
4. « Ouvrir Packet Tracer » utilise l'association Windows. Sinon ouvrir manuellement `web/workspace-session/network/entreprise.pkt`.
5. Activer l'extension MCP BUILDER habituelle ; enregistrer le .pkt au même emplacement.

La session persiste dans `web/workspace-session/session.json`. Le réseau sain est `reference.pkt`.

## Test guidé

- Sans observation réseau : Inconnu et Bloqué, pas de réussite fictive.
- La connexion distante simulée doit échouer initialement.
- Dans PT, reconnecter FastEthernet0 du poste client à FastEthernet0/1 du switch utilisateurs. Les noms portent le préfixe du site ; le manifeste entreprise.json indique la liaison attendue.
- Attendre la convergence et « Vérifier maintenant », ou la surveillance périodique.
- Se connecter au bureau. L'accès à Documents doit rester refusé.
- Dans Administration du partage, accorder la lecture : ouvrir Documents doit réussir.
- Créer Test.txt doit encore être refusé. Accorder l'écriture permet sa création.
- Vérifier la résolution : le ticket exige uniquement la lecture et une preuve réseau récente.
- Débrancher à nouveau : après contrôle, la session se ferme et la résolution n'est plus vérifiée.
- Redémarrer le serveur : permissions conservées, réseau à vérifier de nouveau.
- Réinitialiser le même exercice restaure ses pannes. Sauvegarder ailleurs le travail à conserver, puis rouvrir le réseau régénéré.

## Limites

L'interface de bureau est actuellement du HTML de test, pas OS.js. Inkjs n'est pas intégré. La console locale attribue les droits sans authentification administrateur ; compte/service sont modélisés mais pas modifiables dans cette interface.

Deux contrôles ICMP indépendants vérifient technicien→client pour la prise en main et client→serveur pour le partage. ICMP est une approximation explicite du transport : ce n'est ni SMB ni RDP ; ICMP seul bloqué peut donc bloquer ce prototype. Les permissions sont simulées dans notre serveur et ne modifient pas FTP/SMB dans PT. Pas de NTFS, Kerberos, héritage ou AD complet.

Le ping affiche l'extrait retourné par le pont existant ; le terminal n'accepte pas encore toutes les commandes CMD. Le contrôle commence dix secondes après la fin du précédent, avec expiration des observations à 45 secondes. L'ouverture automatique est réservée à Windows.

Les tests Python et le décodage ne prouvent pas le fonctionnement dans Packet Tracer. Ouverture, identités après resauvegarde, réparation du câble et pings restent à tester dans PT 9.

## Tests locaux

`python web/test_workspace.py`

Régression : `python tests/test_all.py`, `python tests/test_workshops.py`, `python -m unittest discover -s web -p 'test_*.py'`.

Le contrat et la répartition des futurs lots entre IA sont dans `docs/PROTOTYPE-SERVICE-DESK.md`.
