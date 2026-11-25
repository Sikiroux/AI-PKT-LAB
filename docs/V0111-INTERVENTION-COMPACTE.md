# v0.111 — Intervention compacte

Intégration de la maquette validée : barre d’actions avec icônes (compte rendu, tâches, résolution, export), aperçu compact du compte rendu et des tâches. Les options supplémentaires de suivi et de bilan restent accessibles en modale. Les contrôles de résolution, de confirmation et de clôture sont conservés.

L’éditeur de compte rendu reprend le texte existant ou le brouillon local, avec Annuler / Enregistrer. Une erreur d’enregistrement laisse la modale et le brouillon ouverts. Fermer la modale conserve le brouillon pendant la session de la page ; il n’est pas présenté comme enregistré. Un ticket clos reste en lecture seule. Les tâches s’ajoutent dans la modale existante sans ouvrir une seconde fenêtre modale.

La mise en page passe sur une colonne quand la fenêtre est plus étroite. Le défilement de secours de la fiche reste disponible.

Validation : 58 suites JavaScript, dont la nouvelle vérification de l’éditeur, du brouillon après refus, de l’export, des tâches et des restrictions des tickets clos ou en préparation. Rendu Electron Windows non vérifié dans cet environnement.

Installation : fermer le logiciel, extraire Mise-a-jour-v111.zip à la racine du dossier contenant LANCER-BUREAU.bat et accepter le remplacement. Patch depuis v110, sans données de session ni node_modules.
