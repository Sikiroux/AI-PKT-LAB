# v0.32 — Explorateur et paramètres du bureau

Cette version améliore les applications existantes du bureau OS.js. Elle ne modifie pas le réseau généré, les tickets, les moteurs AD/DNS/fichiers ni les sauvegardes existantes.

## Explorateurs

Les icônes **Fichiers locaux** et **Documents partagés** ouvrent désormais une application avec une barre d’actions, un emplacement, une recherche, une liste de fichiers et un éditeur de texte.

- Cliquer sur un nom ouvre son contenu.
- La recherche filtre la liste sans modifier le document ouvert.
- Nouveau document prépare un fichier à enregistrer.
- Enregistrer utilise les routes et contrôles existants.
- Le partage permet aussi de supprimer le document ouvert après confirmation.
- Changer de document ou créer un nouveau document demande confirmation si le texte a été modifié.
- Une actualisation en échec retire la liste ancienne et affiche l’erreur. L’éditeur conserve le texte afin de ne pas perdre les modifications.

Les fichiers locaux restent des textes stockés dans l’état simulé. Les documents partagés passent par les contrôles existants de réseau, DNS, identité, permissions, quota et révision. Les opérations partagées conservent la révision du document ouvert : actualiser la liste ne doit pas masquer une modification concurrente.

## Paramètres

Trois rubriques remplacent le formulaire unique :

| Rubrique | Fonction |
| --- | --- |
| Réseau | Affiche les dernières interfaces observées dans Packet Tracer : IP, masque, câble et protocole. Une observation absente apparaît explicitement comme non observée. |
| Applications | Affiche les applications disponibles et leur installation simulée. Les applications essentielles sont protégées. |
| Lecteur réseau | Permet de modifier le chemin UNC du lecteur Z:. L’accès doit ensuite être vérifié dans Documents partagés. |

L’installation et le chemin UNC restent soumis aux autorisations du contrôleur existant. L’écran Réseau ne reconfigure pas Packet Tracer. « Actualiser les paramètres » relit l’état déjà observé ; « Vérifier maintenant » dans la session principale lance la vérification réseau.

## Vérification

- `node web/test_desktop_ui.js` : intégration des applications avec des réponses API contrôlées. Vérifie les sauvegardes locale/partagée, la révision, la conservation d’un brouillon, le retrait d’une liste devenue inaccessible et la navigation des paramètres.
- Vérification syntaxique du JavaScript embarqué.
- Suite Python web, suite générale et ateliers avant livraison.

Les tests DOM ne remplacent pas un contrôle visuel dans un navigateur. Le rendu OS.js et l’utilisation avec Packet Tracer 9 restent à tester sur le poste Windows de Damien.

## Limites et suite

- Le modèle reste lié au poste client simulé existant, pas à tous les appareils de l’inventaire.
- Pas d’arborescence locale complète, fichiers binaires, corbeille ni suppression locale.
- La protection des brouillons couvre le changement de fichier et la création ; fermer une fenêtre, recharger la page ou perdre la session peut perdre le texte non enregistré.
- Imprimantes, FTP et consoles administratives conservent leur interface précédente.
- Aucun LLM ajouté ni requis. La messagerie locale sera une brique facultative : le moteur fournit les faits accessibles au client, un modèle peut reformuler ses réponses, et le logiciel garde les dialogues déterministes en secours. Le modèle ne doit jamais modifier le réseau, les droits ou la validation d’un ticket. Un contrat de faits et un test de réponses contradictoires doivent précéder son intégration.
