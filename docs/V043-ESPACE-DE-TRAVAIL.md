# v0.43 — Ticket épinglé et bureau agrandi

**Épingler le ticket** garde une fiche de contexte pendant le travail dans Postes, Parc et réseau ou Journal. Le ticket sélectionné est utilisé en priorité ; sinon le premier en cours, puis le premier ouvert. Depuis Tickets, épingler mène à Postes.

La fiche présente le numéro, le statut, le titre et la description. Un curseur règle sa largeur entre 280 et 480 pixels. **Revenir au ticket** retrouve le ticket complet et ses actions. Cette première fiche est volontairement une consultation : les actions de traitement restent dans Tickets.

La vue normale utilise toute la largeur. Le panneau disparaît temporairement dans Accueil, Tickets et Générateur ; il revient quand on reprend un outil. **Détacher le ticket** l’enlève. Un changement d’environnement efface l’épingle pour éviter un contexte d’une autre entreprise. Sur petit écran, le panneau se place au-dessus du contenu.

Une nouvelle prise en main dans Postes ouvre désormais le bureau agrandi. Rétablir la taille, réduire, fermer et ouvrir dans un onglet restent disponibles. Une actualisation périodique ne réagrandit pas une session déjà ouverte ; les brouillons ne sont pas rechargés pour changer la disposition.

## Validation à effectuer dans le navigateur

1. Sélectionner un ticket et l’épingler ; régler la largeur.
2. Passer entre Postes et Parc et réseau : conserver le même contexte.
3. Revenir au ticket : retrouver les actions et le brouillon.
4. Ouvrir une prise en main, rétablir sa taille et attendre un contrôle automatique.
5. Reprendre une autre entreprise : vérifier la disparition du ticket épinglé.

Tests DOM disponibles : `node web/test_pinned_ticket_ui.js` et `node web/test_workspace_ui.js`. Ils vérifient l’état et l’identité, mais ne constituent pas une validation visuelle réelle du navigateur.
