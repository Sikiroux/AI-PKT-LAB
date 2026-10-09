# v0.55 — Imprimantes et client FTP

## Livré

La fenêtre Imprimantes présente les équipements et leurs états. Chaque file s’ouvre séparément : travaux filtrés par imprimante, suspension, mode hors connexion et annulation confirmée. Les propriétés restent liées à l’imprimante ouverte même après changement de sélection : Général, Port et Maintenance. Les actions réseau/papier sont désactivées pour PDF. Le spouleur est commun au poste ; un rafraîchissement refusé retire les commandes périmées.

Le client FTP conserve les fichiers locaux et distants côte à côte. Le compte et le mot de passe sont dans une fenêtre Connexion distincte ; le mot de passe est vidé après tentative et à la destruction de la fenêtre. La sélection ne reconstruit plus la ligne cliquée. Le tableau des 30 dernières tentatives affiche direction et résultat des appels de transfert : en cours, terminé ou code d’échec. Le journal de connexion est repliable. Un échec du rafraîchissement après transfert ne transforme pas un transfert déjà réussi en échec.

Les moteurs, routes, autorisations, confirmation d’écrasement et révision d’envoi sont conservés. Aucun transfert réel, vitesse fictive ou nouvelle preuve réseau n’est ajouté. L’historique est limité à la fenêtre courante ; il n’est pas une file persistante ni un système de reprise.

## Références de conception

- Microsoft : [consulter une file d’impression](https://support.microsoft.com/en-au/windows/hardware/printer/view-a-printer-s-print-queue-in-windows).
- Microsoft : [rôle et dépannage du spouleur](https://support.microsoft.com/en-us/windows/hardware/printer/fix-print-spooler-service-not-running-errors-in-windows).

Cette livraison reprend la séparation équipement / file / propriétés ; elle ne reproduit pas toutes les fonctions de Windows ou d’un client FTP complet.

## Recette Windows / Packet Tracer 9

1. Ouvrir Imprimantes : équipements visibles, aucune liste globale de travaux dans la fenêtre principale.
2. Ouvrir Bureau puis PDF : chaque file ne montre que ses travaux. Changer la sélection principale : la file déjà ouverte garde sa cible.
3. Dans les propriétés PDF, Port et ajout de papier sont désactivés. Dans Bureau, modifier le port et vérifier la cible.
4. Annuler un travail : refuser puis accepter la confirmation et vérifier le résultat.
5. Sur un poste utilisateur, choisir Imprimer… puis un document local et une destination ; vérifier le résultat dans sa file.
6. Ouvrir FTP : aucun champ de mot de passe dans la fenêtre principale. Ouvrir Connexion…, essayer un refus puis une connexion valide ; vérifier le nettoyage du champ.
7. Sélectionner un fichier local/distant puis transférer : la bonne direction et le résultat du moteur apparaissent. Refuser un écrasement : aucun nouveau transfert.
8. Provoquer un refus de transfert puis un refus de liste : codes visibles, fichiers distants périmés retirés, commandes indisponibles.
9. Vérifier tailles, contraste, défilement, fenêtres au premier plan et utilisation clavier sur un petit écran.

Les tests automatiques vérifient les interactions et charges utiles ; ils ne valident pas le rendu Windows ni une session Packet Tracer réelle.
