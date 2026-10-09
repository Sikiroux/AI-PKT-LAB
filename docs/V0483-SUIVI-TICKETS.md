# v0.48.3 — Suivi des interventions

## Livré

La fiche ticket distingue le compte rendu modifiable et une chronologie de suivis. Chaque entrée enregistrée conserve son texte, son type (suivi ou proposition de solution), sa date serveur et l’auteur « Technicien de la session ». Cet auteur représente l’utilisateur du simulateur : ce n’est pas une authentification multi-utilisateurs.

Prendre en charge renseigne l’attribution pour les nouvelles prises en charge. Les tickets déjà en cours restent « Non attribué » si leur ancienne sauvegarde ne contient pas ce renseignement : aucun historique antérieur n’est inventé.

Les entrées ne sont pas modifiables par l’interface. Une correction se formule dans un nouveau suivi. Un ticket clos conserve son historique en lecture seule. L’export JSON du compte rendu contient l’attribution et les suivis. Le brouillon reste dans la page après un refus d’enregistrement, et les changements d’entreprise le réinitialisent.

La lecture et l’ajout d’un suivi ne déclenchent pas le pont Packet Tracer. Les limites sont explicites : 2000 caractères par entrée, 100 entrées par ticket. Les notes existantes restent disponibles ; aucune migration de fichier n’est requise.

## Ce qui reste inchangé

Une proposition de solution n’accorde aucun droit, ne valide aucun contrôle, n’arrête pas le timer et ne clôture pas le ticket. Les critères de réparation et les contrôles frais à la clôture restent ceux des familles de tickets actuelles. Une déclaration manuelle reste annoncée comme telle.

Ce premier incrément ne livre pas un cycle GLPI complet : pas de statut Résolu séparé de Clos, d’approbation du demandeur, de réouverture, d’escalade ni d’attribution entre plusieurs techniciens. Les conversations avec le client restent distinctes des suivis rédigés par l’apprenant.

## Recette manuelle

1. Reprendre une ancienne sauvegarde et ouvrir un ticket : les notes restent présentes, et l’historique initial est vide.
2. Prendre en charge un nouveau ticket : vérifier l’attribution au technicien de la session.
3. Ajouter un suivi décrivant un symptôme. Ajouter ensuite une proposition de solution. Vérifier le texte, le type, la date et l’auteur.
4. Rafraîchir la page et reprendre la sauvegarde : les deux entrées doivent rester présentes et dans le même ordre.
5. Modifier le compte rendu : le texte des suivis précédents ne doit pas changer.
6. Laisser une panne non réparée, proposer une solution puis demander la clôture : les contrôles doivent encore refuser cette clôture.
7. Après réparation et clôture validée, vérifier la lecture seule et exporter le compte rendu : attribution et suivis doivent figurer dans le JSON.
8. Saisir un brouillon, provoquer un refus d’enregistrement (serveur indisponible), vérifier sa conservation. Changer d’entreprise doit effacer ce brouillon.

Tests automatisés : persistance, compatibilité des anciennes données, auteur/date serveur, absence d’appel réseau pour les métadonnées, non-validation par une proposition, refus des entrées invalides et des tickets clos, rendu textuel sûr et conservation du brouillon après échec. Visuel Windows / Packet Tracer 9 à tester réellement.
