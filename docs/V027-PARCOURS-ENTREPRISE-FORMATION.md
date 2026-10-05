# v0.27 — Entreprise et formation

## Un endroit par action

| Page | Rôle |
| --- | --- |
| Accueil et sessions | Créer une entreprise par seed, reprendre une sauvegarde existante. |
| Bandeau permanent | Identifier l’entreprise et ouvrir son unique fichier réseau. |
| Tickets | Recevoir des incidents procéduraux sur cette entreprise, régler leurs arrivées et délais, dialoguer et clôturer. |
| Postes | Portable du technicien et bureau distant, agrandissement, réduction et déconnexion. |
| Parc et réseau | Vérifier le réseau réellement ouvert, inventorier les appareils et associer une sauvegarde. |
| Journal | Historique de l’entreprise active. |
| Générateur de labs | Exercices indépendants : ateliers, tickets de dépannage historiques, mixtes et reproduction. |

La création d’entreprise n’ouvre pas automatiquement le réseau : utiliser le bouton du bandeau, puis connecter MCP BUILDER. Sauvegarder aussi dans Packet Tracer avant de changer d’entreprise. Les labs indépendants n’alimentent pas les tickets de l’entreprise. Après un lab, rouvrir le réseau associé à l’entreprise avant une intervention.

Les outils de détection des services et du masquage sont regroupés dans les outils avancés du pont. Les raccourcis qui accordaient directement des permissions et la correction permanente du premier exercice ne sont plus présentés dans Postes. Utiliser les applications du bureau pour administrer les droits ; les indices se consultent dans le ticket.

## Générateur historique

Les scénarios `classic:` sont accessibles en mode Dépannage. Ils exportent désormais à la fois `lab.pka` (activité avec consignes) et `lab.pkt` (même réseau initial en panne), plus la feuille HTML et le réseau de correction. Les contrôles de correction restent ceux du scénario, avec leurs réserves. Les jobs déjà générés conservent leurs fichiers ; régénérer un ancien job pour obtenir le nouvel export PKT.

## Validation

Tests Python, syntaxe JavaScript et cohérence des contrôles vérifiés avant livraison. La vérification réelle de l’interface Windows et des nouveaux exports dans Packet Tracer reste à faire. Aucune nouvelle capacité du pont n’est annoncée sur la seule base des tests Python.
