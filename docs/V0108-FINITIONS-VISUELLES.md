# v0.108 — Finitions réseau et profil

- Réseau et inventaire : marges latérales de 24 px pour les onglets et le contenu, 18 px sur petit écran. Les titres et cartes ne touchent plus la navigation.
- Avatar IT commun : cercle de 36 px, initiales centrées, bleu profond, contour discret et pastille verte avec bord blanc. Cette pastille indique la session locale du technicien ; l’état du pont Packet Tracer garde son propre indicateur.
- Timer conservé : démarrage à la prise en charge, pause pendant l’attente, reprise sans remise à zéro. Aucun changement du code de chronométrage.

Validation : tests JavaScript du centre de tickets et des onglets réseau, deux tests Python du temps de travail. Vérification du rendu Windows à effectuer sur le poste utilisateur.

Installation : fermer le logiciel, extraire le patch à la racine du dossier contenant LANCER-BUREAU.bat et accepter le remplacement. Ce patch est cumulatif depuis v107.
