# v0.103 — Reprise de la composition de la maquette

Cette livraison remplace l’adaptation v102 par une structure explicite : rail bleu avec icônes SVG, liste Discussions, filtres en pastilles, recherche avec loupe, avatars, aperçus et compteurs non lus, en-tête avec poste, bandeau du ticket, messages et zone de questions. Les heures utilisent les données existantes ; aucune présence ou conversation n’est inventée.

La fenêtre de messagerie reçoit une dimension initiale de 1200 × 760, limitée par l’écran ; les dimensions déjà mémorisées restent prioritaires. Maximiser la fenêtre pour comparer à la maquette de référence.

La barre des tâches devient un ensemble de commandes plates avec icônes, libellés courts, séparateurs, indicateur bleu de sélection, entreprise, horloge et épingle. Verrouillage, plein écran et fermeture se trouvent dans le menu NetOps. Les deux modes de visibilité sont conservés. L’épingle permet également de basculer leur mode.

Les actions pédagogiques existantes restent disponibles. Les options d’épinglage et de lecture sont dans le menu de conversation. Ajouter une note au ticket utilise une commande à icône avec libellé accessible et infobulle. Contacts ouvre les fiches des postes existantes ; ce n’est pas encore un annuaire de messagerie hors ticket. Tickets revient au centre de tickets. Aucune saisie libre ou conversation IA ajoutée.

## Validation et limites

55 suites JavaScript de régression réussies ; tests ciblés de messagerie, défilement et personnalisation repassés après les derniers ajustements. Huit tests Electron simulés réussis. Tests de sécurité adaptés pour autoriser uniquement le balisage SVG statique des icônes, en conservant les contenus utilisateur comme texte.

Le navigateur Chromium nécessaire à la capture locale n’a pas pu être installé : téléchargement invalide dans cet environnement. Aucune capture du logiciel exécuté n’est donc fournie et aucune conformité pixel par pixel n’est affirmée. La composition a été reprise dans le code ; comparaison visuelle sur Electron Windows encore nécessaire, à même taille que la référence.

## Installation

Quitter le simulateur. Extraire la mise à jour à la racine du dossier actuel et remplacer les fichiers, sans supprimer données ni node_modules. Relancer LANCER-BUREAU.bat, ouvrir la messagerie puis la maximiser. Une liste vide reflète l’absence de tickets ; elle ne sera pas remplie de contacts fictifs.

## Refonte des applications suivantes

Traiter ensuite l’annuaire, l’explorateur et les partages, les imprimantes, FTP, les paramètres et la documentation. Pour chaque application : référence validée, composants et icônes réutilisables, intégration fonctionnelle, états vide/chargement/erreur, contrôle clavier et comparaison de captures réelles. Adapter la structure au logiciel représenté plutôt que répéter un formulaire commun. L’ordre peut être ajusté après recette de la messagerie.

## v0.103.1 — finition après capture utilisateur

Barres de titre des applications internes réduites de 48 à 32 px, contrôles et icônes redimensionnés. En-tête de conversation réduit à 56 px. Pastille de connexion dans la barre : vert pour serveur local joignable, rouge après échec de communication, orange si non vérifié. Ce voyant ne certifie pas l’état de tout le réseau Packet Tracer. Pastilles des avatars : vert pour dialogue simulé disponible, gris indisponible, orange lors d’une synchronisation non confirmée. Ce n’est pas une présence humaine détectée. Infobulles explicatives associées. Alignement des icônes de tâches et commande d’ajout de note affinés.

Trois suites ciblées messagerie/défilement/personnalisation réussies avec assertions sur les nouveaux états. Inspection visuelle Windows à confirmer après installation.
