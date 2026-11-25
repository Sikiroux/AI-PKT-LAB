# v0.107 — Correctifs d’affichage communs

- Header : annulation de l’ancienne marge automatique, commandes alignées à droite.
- Menu : déclencheur fixe, liste ancrée sous le bouton, cinq actions existantes conservées et texte lisible du bureau technicien.
- Même présentation des états du pont dans tous les onglets.
- Suppression de la limite de largeur héritée de 1 440 px sur les pages principales.
- Accueil : cartes alignées en haut, nom du fichier réseau au lieu du chemin Windows complet. Le chemin reste accessible dans Parc et réseau.
- Journal : marges communes et contenu dans un encadré distinct du fond de page.
- Postes : bandeau interne masqué uniquement lorsque la page est intégrée, largeur adaptée au conteneur, barre d’outils compacte. La liste conserve son défilement propre pour parcourir les postes sans déplacer le cadre principal.
- Pied de page sans marge supérieure inutile.

Le contenu métier et les actions ne sont pas refondus. Les maquettes Accueil / Parc et réseau / Postes restent à valider avant refonte.

Validation : 57 suites JavaScript et 8 tests Electron. Pas de validation visuelle native Windows réalisée dans cet environnement.

Installation : fermer le logiciel avant extraction. Pour mettre à jour une v106, extraire Mise-a-jour-v107.zip à la racine du dossier contenant LANCER-BUREAU.bat et accepter le remplacement des fichiers. Le patch ne contient pas de données de session ni de node_modules.

Contrôle sur Windows : ouvrir chaque onglet en fenêtre maximisée et réduite ; vérifier l’alignement du profil, ouvrir le menu et utiliser Bureau technicien / Fichier réseau ; vérifier le défilement d’Accueil et de la liste des postes.
