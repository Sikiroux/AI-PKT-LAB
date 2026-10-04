# v0.18 — Bureau du technicien, première étape

Dans **Entreprise → Postes et environnement**, cliquer sur **Ouvrir mon bureau** après création/reprise d’un environnement. Le bureau s’ouvre dans un nouvel onglet et propose des icônes Terminal réseau, Notes locales et Accès distant.

- Le terminal envoie le ping depuis l’identité du poste technicien dans Packet Tracer ; le bureau distant continue d’envoyer le ping depuis le poste client.
- Une coupure réseau dans PT ne ferme pas le bureau technicien. Le ping peut échouer et l’accès distant est refusé selon les préconditions observées.
- Les notes sont locales au navigateur et séparées par environnement. Elles ne sont pas exportées dans la sauvegarde entreprise. Le stockage du navigateur peut les effacer.
- Changer d’environnement invalide un ancien bureau. Les mutations conservent les protections du serveur.
- Accès distant ouvre le bureau client après validation des préconditions déjà présentes. Ce n’est pas une connexion RDP réelle.
- Le bouton Fermer le bureau ferme l’onglet lorsque le navigateur l’autorise ; autrement il affiche le bureau fermé. Il ne déconnecte pas une session client séparée.

## Limites explicites

Cette version réutilise **le PC technicien déjà généré** ; elle ne le transforme pas en Laptop. Aucun changement du XML réseau, aucun déplacement automatisé ni câble console n’est livré. Le Laptop avec Ethernet/Wi-Fi et la console PT viendront après vérification des modèles et capacités du pont. L’ancien PC technicien reste donc présent dans la topologie actuelle.

Le VPN et AD ne sont pas intégrés. Le moteur AD est confié à une autre IA via `BRIEF-IA-MOTEUR-AD.md`. Les fichiers de cette mission restent séparés.

Le ping utilise le même pont et les mêmes délais qu’avant ; aucune accélération annoncée. Les préconditions de connexion distante peuvent attendre le prochain contrôle réseau. Un ping ICMP n’est pas une preuve SMB/LDAP.

Installation : fermer la console, remplacer les fichiers de programme dans l’installation existante sans effacer les dossiers de données, relancer et Ctrl+F5.

Validation : tests Python du choix de source, des anciennes routes, des identités et du refus d’un ancien environnement. Syntaxe JavaScript vérifiée. Comportement réel du bureau/Packet Tracer à vérifier à l’usage.
