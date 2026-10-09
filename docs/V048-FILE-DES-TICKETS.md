# v0.48 — file de tickets et recherche

## Livré

La page Tickets présente une table comparant les demandes : numéro et titre, demandeur, poste, statut, sévérité et date de création. La demande sélectionnée est surlignée ; son bouton indique la sélection aux technologies d'assistance. La fiche complète reste sous la file, avec les échanges, le compte rendu et les actions existantes. Sélectionner un ticket amène la fiche à l'écran et lui donne le focus pour poursuivre au clavier.

La recherche couvre aussi le demandeur, le nom du poste et le numéro de série disponibles dans le contexte. Les anciens tickets sans ces informations restent affichables : les champs absents sont indiqués comme non renseignés. Aucune information d'identité n'est inventée pour combler ces champs.

La file conserve l'ordre opérationnel existant : intervention active, demandes en attente dans leur ordre d'arrivée, puis autres tickets et tickets clos. Les filtres de statut et sévérité restent disponibles. Une liste vide indique explicitement qu'aucun ticket ne correspond aux filtres.

Sur un petit écran, la table défile horizontalement dans son propre conteneur. La fiche reste sur une colonne ; aucune colonne métier n'est supprimée pour faire tenir la table.

## Inchangé

Les règles de prise en charge, de préparation de panne, de validation, de clôture et de chronométrage sont inchangées. Les sauvegardes et les noms techniques des appareils ne sont pas modifiés. Les contrôles pédagogiques restent séparés dans leur volet repliable.

## Limites et prochaines étapes

Cette interface s'inspire de l'organisation d'un outil de tickets ; elle ne reproduit pas encore le cycle complet GLPI. Attribution, suivis distincts des notes, tâches et états Résolu/Clos séparés restent à définir et implémenter. La sévérité actuelle n'est pas une matrice urgence × impact.

Le nommage indépendant des personnes, les variantes de placement, les entreprises plus grandes et la base documentaire interne restent les prochains blocs. Le contexte du demandeur actuellement enregistré ne modélise pas encore systématiquement un bénéficiaire différent.

## Recette manuelle

1. Ouvrir Tickets avec plusieurs demandes et sélectionner chacune par son numéro/titre.
2. Rechercher le nom d'un demandeur, puis le nom d'un poste : seuls les tickets correspondants restent visibles.
3. Combiner recherche, statut et sévérité, puis réinitialiser les filtres.
4. Reprendre une ancienne sauvegarde : un contexte absent ne doit pas empêcher la consultation.
5. À largeur réduite, faire défiler la table sans élargir toute la page ; vérifier la lisibilité de la fiche.
6. Parcourir les boutons au clavier et vérifier la visibilité du focus et de la sélection.

La fidélité visuelle et le fonctionnement réel dans PT 9 restent à vérifier par l'utilisateur ; les tests automatiques ne les certifient pas.
