# v0.49.1 — confort et arrivées
## Livré
- Barres de défilement natives fines et arrondies, communes aux tickets, bureaux et vue environnement. Prise en charge du contraste forcé.
- Écran de chargement du bureau, retiré à la fin du démarrage ou en cas de refus ; aucune authentification fictive.
- Transitions courtes des boutons et apparition des fenêtres ; animations désactivées lorsque le système demande une réduction des mouvements.
- Catalogue varié : deux arrivées consécutives ne choisissent pas la même famille. Mode varié et applications : choix aléatoire évitant le poste précédent quand plusieurs postes existent. Les cibles explicites restent respectées.
- Perte réseau : fermeture de la prise en main sans effacer la session utilisateur. Les contrôles de compte, délais d'authentification et invalidations administratives restent applicables.

## Limites et suite du bloc entreprise
Cette livraison ne transforme pas encore le modèle d'incidents. Les demandes sont toujours reçues avant l'injection ; Prendre en charge prépare la panne. AD/fichiers/DNS restent liés au client principal. Un catalogue mixte imposé reste lié au client principal ; le catalogue varié choisit une application sur un autre poste quand nécessaire pour éviter une répétition consécutive.
Avant de permettre plusieurs pannes actives : remplacer les cinq emplacements de scénario uniques par un registre d'incidents avec ressources touchées et contrôles propres ; gérer les conflits ; migrer les anciennes sauvegardes ; déclencher le signalement après application confirmée ; regrouper les signalements de panne commune.
Ensuite étendre employés et postes réellement représentés dans Packet Tracer, ajouter impacts par activité, puis écran de connexion et persistance explicite des sessions. Aucun poste fictif n'est présenté ici comme un appareil Packet Tracer réel.

## Recette manuelle
Vérifier sous Windows/PT9 les barres, la molette dans les applications, les animations avec/sans réduction des mouvements. Ouvrir une session utilisateur puis couper le câble : accès distant fermé ; après réparation et reconnexion, session utilisateur encore présente si non expirée. Un compte désactivé ou réinitialisé doit conserver son comportement de refus.
