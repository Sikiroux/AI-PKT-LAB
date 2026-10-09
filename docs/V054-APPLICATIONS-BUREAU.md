# v0.54 — Applications de bureau : Explorateur et Annuaire

Basée sur v0.53. Cette livraison transforme les vues principales en espaces de navigation. Les formulaires servent à modifier les propriétés dans des fenêtres dédiées.

## Explorateur

Volet des emplacements Documents locaux / Documents partagés, adresse du contexte, recherche, liste avec icônes et colonnes, sélection et compteur. Un clic sélectionne sans lire le fichier. Double-clic, Entrée ou Ouvrir demande réellement sa lecture au moteur. Nouveau document et ouverture utilisent un éditeur de texte séparé ; Enregistrer garde les routes et révisions existantes. Fermer un éditeur modifié demande confirmation. Une interruption forcée ou un rechargement ne sauvegarde pas un brouillon.

Clic droit ou Maj + F10 ouvre le menu Ouvrir / Propriétés. Échap ou un clic hors du menu le ferme. Les propriétés affichent les métadonnées disponibles ; elles ne prétendent pas présenter les permissions Windows complètes. La suppression conserve confirmation, permission et révision côté moteur. Aucun dossier, renommage ou déplacement non géré par le moteur n’est ajouté.

## Annuaire

Arborescence domaine / unités d’organisation, sélection d’une unité avec descendants, vues d’objets et panneau de résumé. Les objets affichent une icône. Un clic sélectionne ; double-clic, Entrée ou Propriétés ouvre une fenêtre dédiée. Le menu contextuel propose Propriétés et Actualiser. Un utilisateur possède Général, Compte, Membre de, Matériel et Emplacement ; les groupes possèdent Général, Membres et Emplacement. Les ordinateurs disposent de Général / Emplacement. Les OU ont une fiche générale.

Changer la sélection principale ne change pas la cible d’une fenêtre de propriétés déjà ouverte. Les opérations conservent les identifiants et la révision de la vue ; un refus est affiché. Une actualisation indisponible efface les anciennes actions dans la vue et les propriétés. Fermer la console ferme ses fenêtres de propriétés et de création. Nouvel objet ouvre une fenêtre distincte ; les comptes restent indépendants des salariés et des appareils physiques.

La disposition répond à la largeur de la fenêtre grâce aux container queries ; les listes défilent dans leurs panneaux. Les fenêtres restent intégrées à la barre des tâches et au verrouillage du bureau.

## Recette Windows

1. Ouvrir Documents partagés : vérifier la navigation, la liste et les icônes, sans éditeur sur la page principale.
2. Sélectionner puis double-cliquer un fichier : vérifier la lecture, le bon poste et le bon partage.
3. Modifier le texte, fermer et annuler : conserver le brouillon. Enregistrer puis relire.
4. Clic droit sur un autre fichier : vérifier sa fiche et la fermeture du menu par Échap/clic extérieur.
5. Ouvrir Annuaire : naviguer dans une OU puis ses descendants ; rechercher un compte.
6. Ouvrir les propriétés de Bob, sélectionner Alice dans la console, puis agir sur Bob : la cible doit rester Bob.
7. Modifier une appartenance ou un déplacement : vérifier l’état effectif et la révision côté moteur.
8. Ouvrir Nouvel objet, créer un compte puis vérifier la liste ; fermer sans création ne doit rien modifier.
9. Réduire les fenêtres, utiliser le plein écran et verrouiller/déverrouiller : vérifier les panneaux et fenêtres.
10. Simuler une indisponibilité de l’annuaire : les anciens contrôles doivent disparaître, sans présenter une réussite.

## Fidélité et limites

Références Microsoft :
- https://support.microsoft.com/fr-fr/windows/experience/fileexplorer/file-explorer-in-windows
- https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage-user-accounts-in-windows-server

Organisation inspirée de ces outils ; pas une reproduction exhaustive ni une véritable console Windows. Pas de dossiers imbriqués, explorateur complet de lecteurs, associations de fichiers, groupes AD imbriqués, GPO ou réplication. Le journal AD reste celui du moteur simulé. Les tests DOM/API ne prouvent pas le rendu visuel ou la connexion Packet Tracer réelle.
