# v0.50.7 — Reconnexion et sessions AD

Une observation ICMP inconnue ou périmée ne ferme plus la prise en main déjà ouverte. Le bureau garde ses fenêtres et présente un écran de vérification/reconnexion ; les interactions sont suspendues jusqu’à une preuve valide. Un échec observé ferme toujours le transport. L’ouverture initiale exige toujours une vérification réussie : une absence de preuve ne donne aucun accès.

Le compte du demandeur ne commande plus le transport distant du technicien. Désactiver le compte bloque les authentifications suivantes, sans déconnecter à lui seul la prise en main. Une opération administrative AD conserve les sessions ; les droits sont réévalués aux accès suivants. Le logout ou l’échec d’authentification concerne uniquement le poste sélectionné. Changer d’environnement invalide toutes les authentifications de l’environnement quitté.

Les libellés parlent d’équipements enregistrés et de traitement des commandes clients. Ce dernier est une activité métier descriptive, pas un processus complet. L’impact FTP reste une estimation large à affiner dans une livraison ultérieure.

## Limites
Les contrôles restent des preuves ICMP utilisées comme approximation du transport, pas une validation TCP 3389/445. Il ne s’agit ni d’un client RDP réel ni d’un modèle complet de jetons Kerberos. Les droits de groupes sont réévalués immédiatement dans la simulation.

## Recette Packet Tracer 9 / Windows
1. Prendre la main, ouvrir une application et saisir un brouillon. Interrompre le pont : vérifier le message et la conservation des fenêtres.
2. Rétablir le pont et vérifier le réseau : retrouver le bureau.
3. Débrancher réellement le câble puis vérifier : la prise en main doit fermer. La session Windows simulée doit rester distincte.
4. Avec un utilisateur connecté, créer une OU sans rapport : conserver son authentification.
5. Retirer un droit de partage : l’accès suivant doit être refusé sans déconnecter tous les employés.
6. Désactiver son compte : nouvelle authentification refusée ; le transport du technicien reste distinct.
