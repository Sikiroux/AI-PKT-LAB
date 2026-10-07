# v0.29 — Premier bloc UI/UX

Les réglages de création de tickets sont repliés dans « Recevoir une nouvelle intervention ». Les arrivées automatiques restent dans leur propre panneau. Le bandeau de contexte reste visible sur grand écran et affiche l’entreprise et le fichier réseau ; l’identifiant technique reste disponible dans le DOM mais n’encombre plus ce bandeau.

Le bureau utilise des icônes SVG locales dessinées pour le projet, sans CDN ni nouvelle dépendance. Les applications conservent leurs autorisations et leur moteur actuels. OS.js reste le gestionnaire de fenêtres.

À tester sous Windows : déplier la création et recevoir un ticket ; ouvrir le portable et plusieurs applications ; agrandir/réduire une fenêtre ; vérifier les icônes, le défilement et le bandeau sur un écran étroit.

Ce bloc ne migre pas vers Tabler, ne réduit pas les délais du pont et n’ajoute pas de bureaux aux postes seulement détectés. Prochain bloc : maquette détaillée des tickets et découpage des composants, avant intégration d’une bibliothèque graphique.
