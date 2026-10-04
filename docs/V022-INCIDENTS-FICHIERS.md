# v0.22 — Tickets procéduraux de fichiers

Depuis l’environnement actif, « Nouvel incident de fichiers » prépare un ticket lié au document et au demandeur de cette session. Aucun autre réseau Packet Tracer n’est créé. La seed détermine l’ordre des familles : un cycle couvre les huit familles avant de recommencer. Les noms, appareils et documents viennent de l’environnement, pas d’un exemple fixe.

## Catalogue

| Famille | Objectif utilisateur |
|---|---|
| Service de partage arrêté | Ouvrir le document |
| Partage désactivé | Ouvrir le document |
| Pare-feu du service bloquant | Ouvrir le document |
| Droit de lecture au partage manquant | Ouvrir le document |
| Droit d’écriture au dossier manquant | Enregistrer le document |
| Quota du partage atteint | Enregistrer avec du texte supplémentaire |
| Volume plein | Enregistrer avec du texte supplémentaire |
| Fichier en lecture seule | Enregistrer le document |

La préparation remet le compte du demandeur et les prérequis simulés en état sain, puis injecte la panne. Elle déconnecte la session distante et invalide l’authentification : il faut se reconnecter. Les observations réseau restent nécessaires. Un incident non résolu bloque la préparation du suivant, y compris un incident d’annuaire.

## Validation

La vérification évalue le fichier ciblé, avec une observation récente et l’identité authentifiée. Pour un objectif d’écriture, elle teste une croissance réelle du contenu ; réenregistrer un texte identique ne suffit pas à prouver qu’un quota permet une sauvegarde. Le contrôle n’écrit pas lui-même sur le fichier.

Les autres fichiers doivent rester identiques. Les autres comptes et leurs droits effectifs doivent être préservés, y compris les accès qui étaient refusés. Le document ciblé doit conserver son identité et son nom. Le supprimer pour contourner la panne ne permet pas de valider. Les nouveaux fichiers sont autorisés.

La fiche publique affiche le symptôme et l’objectif, sans la famille technique ni l’état de référence utilisé par le correcteur.

## Limites et test réel

Le service et son pare-feu sont pédagogiques, pas un serveur SMB réel. Packet Tracer fournit une preuve réseau ICMP ; celle-ci ne prouve pas qu’un port SMB répond. Aucun changement de câble ou configuration IOS n’est injecté par ces huit familles.

À tester dans l’application avec Packet Tracer : créer un environnement, vérifier le réseau, préparer un incident, se reconnecter, réparer depuis Partages/Annuaire, puis vérifier et fermer le ticket. Les tests Python vérifient le moteur ; ils ne prouvent pas le comportement de Packet Tracer ou le rendu du navigateur.
