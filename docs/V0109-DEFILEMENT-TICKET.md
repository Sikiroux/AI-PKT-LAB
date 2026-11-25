# v0.109 — Défilement du ticket

Le contenu de l’onglet Intervention pouvait dépasser la hauteur disponible et être coupé au niveau du compte rendu. Sur la disposition à colonnes (largeur supérieure à 950 px), la fiche centrale possède maintenant son propre défilement vertical. Ses onglets n’ajoutent plus de défilement imbriqué. La barre d’actions reste hors de cette zone. La disposition étroite conserve son défilement existant.

Aucun changement de validation, de sauvegarde du compte rendu ou du timer.

Vérifications : quatre suites JavaScript ciblées (onglets, centre de tickets, résolution, persistance de vue). Le défilement réel dans Electron Windows reste à vérifier sur le poste utilisateur.

Installation : fermer le logiciel ; extraire le patch dans le dossier contenant LANCER-BUREAU.bat et accepter le remplacement des fichiers.
