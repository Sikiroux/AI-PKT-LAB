# v0.68 — Surfaces et navigation des applications

Livraison groupée avec v0.67, sur le socle v0.66.

## Design system

`web/app-system.css` introduit des tokens communs : surfaces, bordures, texte, sélection, accent, focus, couleurs sémantiques, rayon et espacement. Les tableaux, barres d’outils, retours d’action, boutons et focus clavier suivent ces conventions. Les scrollbars natives restent celles du système partagé existant. Le thème OS.js conserve les titres, icônes et boutons de fenêtre validés par Damien ; ce bloc ne change pas leur géométrie.

Les retours d’action utilisent une surface dédiée avec rôle `status`. Les boutons désactivés sont visibles. Les règles de mouvement réduit existantes restent en place ; les couleurs forcées conservent une sélection et un focus identifiables.

## Applications retravaillées

- Documentation : recherche et catégorie dans une barre dédiée, liste d’articles avec icônes natives, article dans sa propre zone de lecture, largeur de ligne limitée, distinction entreprise/formation. Sur une petite fenêtre, liste et article se superposent verticalement. Les deux zones défilent indépendamment ; aucune requête PT n’est ajoutée.
- Serveur FTP : liste des comptes à gauche et droits du seul compte sélectionné à droite. La sélection est conservée à l’actualisation si le compte existe. Les permissions restent administrées par les mêmes opérations ; leur modification invalide la connexion FTP conformément au moteur. Réinitialisation et capacité gardent leurs protections.
- Fiche ticket : ressource distincte et identifiants repliables, détails dans v0.67.

## Ce qui reste

Le fichier est une couche commune appliquée aux interfaces existantes, pas l’achèvement de leur refonte. Les autres consoles n’ont pas toutes été converties à des inspecteurs d’objets. Les formulaires restent nécessaires pour saisir une propriété ou créer un compte ; leur séparation des listes se poursuit. Le bilan pédagogique et l’export restent prévus pour v0.69.

La recette automatisée vérifie notamment la sélection FTP sur plusieurs comptes, le destinataire des modifications, la recherche documentaire, les articles filtrés, la lecture seule et les anciens tickets. Elle ne remplace pas une recette visuelle réelle sous Windows avec Packet Tracer 9.

## Vérifications visuelles à faire

1. Ouvrir Documentation, rechercher un terme avec ou sans accent, puis filtrer Entreprise : article sélectionné toujours visible dans la liste.
2. Redimensionner Documentation : titre lisible, colonne de lecture contenue, scroll de l’article sans déplacer le bureau.
3. Serveur FTP, Comptes et droits : passer entre deux comptes, modifier un droit et vérifier la bonne identité après actualisation.
4. Parcourir les contrôles au clavier : focus visible, sélection distincte, boutons inactifs identifiables.
5. Vérifier le chargement de `/app-system.css` ; fermer et rouvrir les fenêtres existantes pour contrôler leur barre de titre.
