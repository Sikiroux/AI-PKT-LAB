# v0.77 — Fiche ticket : une vue de travail à la fois

## Refonte visible

La fiche conservait la description et beaucoup de contexte au-dessus ou à côté de ses trois onglets. La v0.77 propose quatre vues :

- **Demande**, ouverte par défaut : plainte du demandeur, identité, ressource et résultat attendu. Si le contexte structuré existe, la plainte remplace le texte assemblé répétant ressource et résultat ; les autres informations restent dans leurs blocs dédiés. Les anciens tickets conservent leur description.
- **Échanges** : questions client, fil d'activité et accès à la rédaction d'un suivi.
- **Intervention** : solution, tâches, compte rendu et export.
- **Vérifications et aide** : résultats détaillés, indices et correction volontaire.

Le titre, le statut et la sévérité restent visibles. Un compteur de vérifications ouvre leur onglet sans lancer de contrôle. Il compte les résultats enregistrés et ne signifie jamais « ticket clos ».

La colonne **Actions et suivi** conserve le poste, l'accès distant, la prise en charge, le contrôle, le chronomètre et la priorité. Le détail de l'impact et de l'activité est repliable. L'ouverture d'un outil est moins mise en avant que l'action de vérification.

## Direction visuelle

Carte principale blanche, bordures discrètes, onglets avec les icônes SVG existantes, indicateur actif souligné, lecture de la plainte sur fond neutre, résultat attendu sur fond bleu léger, métadonnées moins présentes. La présentation utilise la palette existante du projet.

Sur écran étroit, la fiche précède la colonne d'actions et les onglets peuvent défiler horizontalement dans leur propre bande. La fiche n'ajoute pas de zone interne de défilement vertical. Les formulaires de suivi/solution continuent d'utiliser les fenêtres existantes.

## Interactions

Un seul panneau affiché, rôles et relations ARIA conservés. Flèches gauche/droite, Début et Fin permettent de changer d'onglet. Le choix de vue est mémorisé par entreprise et ticket pour éviter les collisions des numéros entre entreprises. Les détails repliables sont également mémorisés dans la portée de l'entreprise. Le raccourci de vérifications place le focus sur l'onglet correspondant.

Aucune modification du moteur, de l'authentification, des droits ou des critères de résolution. Choisir une vue ou ouvrir le compteur ne déclenche pas de ping, transfert ni validation.

## Tests et limites

Les 37 suites JavaScript sont vertes. La recette d'onglets couvre les quatre panneaux, le déplacement du contexte, l'unique panneau visible, les relations ARIA, le clavier, le raccourci de vérifications et l'isolation par entreprise. Les scripts intégrés passent l'analyse syntaxique.

**Le rendu visuel n'est pas validé dans un navigateur ici** : Chromium n'est pas installé et sa tentative de téléchargement a échoué. Aucun alignement ni responsive n'est donc présenté comme visuellement validé. Générateur, ateliers et backend Python inchangés ; leur recette n'a pas été relancée pour cette modification HTML/CSS/JavaScript.

Ce bloc porte sur la fiche ticket. Les applications du bureau, les états de connexion et les autres pages restent à poursuivre.

## Recette Windows / Chrome à effectuer

1. À 1440 puis 1280 pixels de large, ouvrir un ticket : titre et actions doivent rester lisibles, sans débordement horizontal de la page.
2. Vérifier que Demande présente la plainte, le demandeur, la ressource et le résultat attendu sans afficher les tâches ou les contrôles détaillés en même temps.
3. Ouvrir les quatre onglets, puis revenir au même ticket : conserver la vue de travail choisie. Changer d'entreprise avec le même numéro de ticket : revenir à Demande.
4. Naviguer au clavier dans les onglets, puis activer le compteur de vérifications. Le focus et le panneau doivent correspondre.
5. Ouvrir puis annuler un suivi ou une proposition de solution ; vérifier les brouillons et le retour à la fiche. Aucun envoi ne doit résulter d'un simple changement d'onglet.
6. Déplier Impact et activité ; vérifier que les informations restent présentes. Recharger les données de la même entreprise : préserver son état ouvert/fermé.
7. À environ 390 pixels de large, vérifier les onglets défilants, l'ordre fiche puis actions et l'absence de débordement de la page. Les longs chemins doivent revenir à la ligne.
8. Tester un ticket ancien sans contexte structuré et un ticket résolu/clos : conserver description, historique, confirmation et réouverture selon les règles existantes.
