# v0.67 — Comprendre le signalement

Livrée avec la v0.68. Ce bloc clarifie les tickets existants ; il n’ajoute aucune famille de panne.

## Comportement

Les nouveaux incidents périodiques et manuels identifient la ressource concernée : chemin du partage Documents, compte du salarié du poste cible, imprimante du poste, dépôt FTP ou accessoire local. Le résultat attendu décrit l’action à retester. Les demandes historiques en attente reçoivent aussi un objectif ; AD/fichiers/DNS indiquent leur partage attendu. Aucun texte ne révèle une cause privée ni un mot de passe.

La fiche conserve le poste cible et la prise en main, mais replie la série et le récit initial dans « Identifiants et demande initiale ». Elle ne répète plus l’urgence quand un impact métier est disponible. Priorité, gravité et nombre de personnes restent évalués par les moteurs existants.

« Résolu · retour client à confirmer » signifie que le technicien doit faire retester l’action au demandeur, sur son poste et avec son compte. La clôture conserve la confirmation explicite et refait les contrôles existants. La déclaration du technicien n’est pas une réponse automatique du salarié.

## Compatibilité et limites

Les anciens tickets gardent leurs textes sauvegardés ; aucun chemin ou résultat historique n’est inventé. Les champs absents restent absents ou affichés « Non renseigné ». La chronologie, les dialogues et le cycle de découverte v0.64–0.65 sont conservés. Aucun ping n’est déclenché par la consultation de la fiche.

Ce bloc ne constitue pas une réécriture de tous les textes du catalogue de labs, une simulation autonome complète des employés, ni une confirmation client générée par IA.

## Recette

1. Créer un incident de compte sur un poste secondaire : le compte affiché appartient à ce salarié, pas au premier poste.
2. Créer un incident Documents : le chemin commence par le serveur de l’entreprise ; la distinction ressource distante / fichiers locaux est lisible.
3. Ouvrir un ancien ticket : consultation possible sans inventer des champs.
4. Déclarer une résolution : les contrôles réseau et service restent exigés ; la clôture demande la confirmation.
5. Vérifier les actions de prise en main, les brouillons et les onglets après actualisation.

Les tests automatisés couvrent le ciblage, l’affichage et les garde-fous. Recette Windows/PT9 encore requise.
