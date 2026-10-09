# v0.50.5 — Création d’entreprise

Le formulaire repliable a été remplacé par une fenêtre modale centrée. Elle reprend les couleurs bleu ciel, les icônes SVG et les arrondis du simulateur, avec fond assombri et flouté. La seed reste facultative et les sauvegardes existantes sont conservées.

## Comportement
- Sans entreprise active : « Bonjour, commençons une intervention » et bouton de création directe.
- Avec entreprise active : « Bonjour, reprenons ton intervention ».
- Ouverture depuis Nouvelle entreprise ou Créer ma première entreprise.
- Focus sur la seed, clavier limité à la fenêtre par le dialogue natif, fermeture par croix, Annuler ou Échap. Retour du focus au bouton d’origine quand il existe encore.
- Pendant la génération : chargement indéterminé, commande bloquée contre les doubles soumissions. La fermeture est temporairement bloquée car fermer l’interface n’annulerait pas la création serveur.
- Erreur de création : message dans la fenêtre et seed conservée pour réessayer.
- Succès : fenêtre fermée, affichage de l’entreprise et des tickets. Si l’actualisation échoue après la création, le message demande de synchroniser plutôt que recréer.
- Animations discrètes, désactivées avec la préférence de réduction des animations.

## Recette Windows
1. Sans entreprise active, vérifier le titre et le bouton de création.
2. Ouvrir la fenêtre, vérifier centrage, couleurs, flou et champ visible sur fenêtre étroite.
3. Tester Tab, Maj+Tab, Échap, Annuler et la croix.
4. Créer avec une seed ou sans seed ; vérifier le chargement, l’absence de double création et le retour aux tickets.
5. Vérifier qu’une erreur reste lisible dans la fenêtre.

Tests automatisés : états d’accueil, focus, annulation, doubles soumissions, chargement, erreur et reprise, succès, navigation existante. Le rendu visuel sous Windows reste à vérifier par Damien ; aucun navigateur de rendu disponible ici.
