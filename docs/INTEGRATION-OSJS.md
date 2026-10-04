# Version 0.15 — interface commune et OS.js

## Lancer

Python 3.10+ et Packet Tracer installés. Extraire entièrement le ZIP, fermer les anciens serveurs, puis lancer LANCER.bat ou web/LANCER-WINDOWS.bat. Une seule interface : http://127.0.0.1:8765.

Tickets, générateur, site et journal restent accessibles. L'onglet Bureau simulé contient l'entreprise procédurale existante. Créer l'environnement, ouvrir entreprise.pkt, activer MCP BUILDER, puis sauvegarder le fichier au même emplacement. Le réseau du bureau est distinct du site de test : ouvrir le bon fichier pour chaque intervention.

Après réparation du câble et vérification, Se connecter au poste ouvre le vrai gestionnaire de fenêtres OS.js. Documents utilise les permissions du serveur Python ; Terminal réseau lance le ping via Packet Tracer. La coupure réseau invalide la session et détruit le bureau. Les droits et fichiers sont conservés.

## Architecture

- tickets_app.py : serveur unique et démarrage d'un seul PTCommandBridge.
- workspace_routes.py : routes /workspace/* ; jeton partagé et ressources locales autorisées explicitement.
- workspace_app.Controller : modèle, identités et observations ; Engine partagé avec les tickets.
- desktop.html : Core et CoreServiceProvider de @osjs/client 3.10.0, fenêtres natives OS.js. Mode standalone sans serveur Node, VFS ou authentification OS.js.
- vendor/osjs : distribution npm originale, licence BSD incluse, sans CDN. Le faux service settings n'enregistre aucune donnée métier : l'état métier reste dans le serveur Python.

L'entrée historique workspace_app.py et LANCER-PROTOTYPE.bat démarrent aussi le serveur unique. Le port 8766 n'est plus utilisé.

## Portée et limites

Le bureau est simulé, pas une session Windows réelle. Seuls Documents et le ping sont intégrés. Pas encore de terminal IOS interactif, AD complet, Inkjs, véritable SMB ou RDP. ICMP reste l'approximation du transport. Le scénario du bureau reste celui du prototype, avec variations procédurales de noms et d'adressage ; il n'est pas encore lié au catalogue des tickets du serveur principal.

La surveillance s'exécute dix secondes après son contrôle précédent. Les commandes partagent un verrou pour ne pas interférer sur le pont. Le bouton Vérifier maintenant attend et réalise réellement son contrôle ; le délai peut inclure un contrôle déjà en cours.

## Vérifications manuelles

1. Vérifier que tickets et catalogue du générateur s'affichent.
2. Créer l'environnement du bureau, ouvrir le .pkt et vérifier le pont.
3. Réparer le câble ; ouvrir le bureau, déplacer/redimensionner/fermer ses fenêtres.
4. Lecture refusée avant attribution du droit ; écriture distincte.
5. Ping dans le terminal : réponses issues de Packet Tracer.
6. Couper le câble : fermeture manuelle et automatique de la session.
7. Rebrancher : droits et fichiers conservés.

Sources : https://manual.os-js.org/guide/standalone/ ; https://github.com/os-js/osjs-client ; https://registry.npmjs.org/@osjs/client/3.10.0.
