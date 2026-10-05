# v0.26 — Interface NetOps issue du design Figma

L’export « Design NetOps Lab Dashboard » sert de référence visuelle : navigation sombre, panneaux clairs, accent bleu, six vues et contexte permanent.

## Les six rubriques

| Rubrique | Utilité |
|---|---|
| Accueil et sessions | Reprendre une entreprise sauvegardée et ouvrir le prochain ticket réel. |
| Tickets | Recherche, statuts, sévérité, délais, dialogues, compte rendu, vérification et arrivées automatiques. |
| Parc et réseau | Ouvrir le fichier associé, vérifier le bon réseau, observer l’inventaire et associer une sauvegarde. |
| Postes et environnement | Créer/reprendre un environnement, ouvrir le portable technicien ou une session distante et préparer une intervention. |
| Journal | Consulter les événements réels du site actif. |
| Générateur de labs | Ateliers, dépannage, mixte et reproduction de panne sur des fichiers indépendants. |

Le bandeau indique l’entreprise, son identifiant, le fichier associé, l’état du pont et le dernier contrôle du réseau. Un pont connecté ne prouve pas que le bon fichier est ouvert. Le statut réseau correspond au dernier contrôle, pas à une observation continue du fichier.

## Intégration

Les données de démonstration du Figma (noms, IP, tickets, dates) ne sont pas reprises. Les données viennent des routes existantes, avec les mêmes contrôles d’environnement et de jeton. Le générateur conserve ses modes, scénarios, niveaux, nombre de pannes, seed et fichiers de consignes/correction. Les sauvegardes ne changent pas de format.

Le style est adapté en HTML/CSS/JavaScript natifs dans les pages existantes. Aucun React, Node.js ou CDN n’est nécessaire pour lancer cette version. Les applications OS.js et les moteurs de simulation restent en place.

## Bureaux

Dans Postes et environnement, « Agrandir l’espace » utilise toute la fenêtre web ; « Réduire » masque l’espace sans déconnecter. Dans la session distante, Agrandir/Rétablir et Réduire/Rouvrir changent seulement l’affichage. « Fermer la session » appelle la déconnexion réelle de la simulation. Une perte réseau confirmée continue de fermer la session. Échap rétablit la taille de l’espace ; le bouton reste utilisable si le clavier est dans le bureau intégré.

## Navigation et petits écrans

L’accueil s’ouvre par défaut. Les six vues ont une ancre URL pour revenir à la vue choisie. La navigation mobile se replie après sélection, et Échap ferme le menu. Les tableaux restent défilables ; les champs et contrôles restent accessibles au clavier.

## Vérifications à faire sur Windows / Packet Tracer 9

Ouvrir LANCER-WEB.bat, reprendre un environnement, confirmer le chemin du bandeau puis ouvrir ce réseau. Essayer un ticket, les quatre modes du générateur, le portable et la session distante. Agrandir, réduire, rouvrir, déconnecter ; confirmer la fermeture automatique après coupure réseau. La présentation reprend la maquette mais conserve les contrôles détaillés du logiciel, absents de la maquette.
