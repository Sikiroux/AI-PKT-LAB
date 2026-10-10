# v0.62 — Bloc regroupé 0.60–0.62

## Livré

- Documentation **métier du scénario** distincte des modes d’emploi : politique d’accès, convention mail, préavis et procédure d’arrivée. Domaine pédagogique `.example`, paramètres déterministes dérivés de `seed:corporate:v1`, enregistrés dans la session.
- Icône **Arrivées et services** sur le bureau du technicien. Trois vues : arrivées, messagerie, licences. Listes et détails ; création, rédaction, propriétés et attribution dans des fenêtres séparées. Recherche locale et suppression des données affichées si l’actualisation échoue.
- Messagerie **interne simulée** : boîtes rattachées aux identifiants AD, activation, dossiers réception/envoyés, lecture des messages, envoi atomique. Service arrêté, compte désactivé/verrouillé/expiré, changement de mot de passe requis, licence absente ou quota plein bloquent la livraison. Un destinataire absent ne reçoit jamais de message.
- Deux licences de formation : Messagerie et Bureautique. Attribution, retrait et capacité ; impossible de descendre sous les places attribuées. Les utilisateurs initiaux reçoivent leur boîte et les licences au moment de la migration ; les nouveaux arrivants doivent être préparés.
- Demande d’arrivée : nom, identifiant, service, responsable, date et groupe demandé (l’API accepte plusieurs groupes). Mail et Bureautique demandés dans l’interface. Création d’un ticket `DEM-ARR-…` sans panne réseau ni injection à la prise en charge.
- Première connexion **de formation** : depuis la console, vérification du mot de passe initial et changement via `sim_ad`. L’ancien mot de passe ne fonctionne plus. Cet essai n’ouvre pas une session sur un nouveau PC. Les champs secrets sont vidés après chaque essai.
- Lettre d’accueil sauvegardée dans la demande et livrée par le moteur mail. Le contrôle exige ce contenu exact dans la boîte de l’arrivant, provenant de la boîte Accueil, et un message sortant vers une autre boîte après la création de la demande.
- Préparation et remise du portable de réserve par les moteurs **déjà existants** de déploiement et stock. L’arrivant est une identité administrative du parc, séparée des 30 postes représentés. Aucune case « préparé » ne suffit.
- Vérification/résolution dans Tickets : six contrôles relus à chaque tentative, compte rendu requis. Retirer une licence, changer la lettre non relivrée ou restituer le matériel invalide la préparation. Distinction Résolu / Clos et confirmation du demandeur conservées. Aucun ping lancé par ces actions administratives ; une preuve réseau fraîche du technicien reste requise.

## Contrats et stockage

`web/sim_corporate.py` : `policy`, `ensure`, `public`, `operate`, `evaluate`, `sync_people`. Stdlib uniquement. `operate` travaille sur une copie complète ; refus sans mutation de l’entrée. Révision entière obligatoire (un booléen est refusé). Toutes les identités sont évaluées dans l’environnement actif.

Routes : `desktop/corporate/state` et `desktop/corporate/operation`. Les opérations sont contrôlées côté serveur et interdites dans une vue de poste distant. État et politiques sous `session.json → corporate`. Comptes/groupes restent dans `directory`, préparations/remises dans `inventory`, traitement des tickets dans `tickets.json`.

Migration additive : sauvegarde `session.before-corporate.json` avant initialisation des services sur une ancienne session. La seed ne régénère pas les services à chaque démarrage. Les demandes sont réconciliées vers Tickets par ID, ce qui permet de récupérer un ticket après une interruption entre les deux sauvegardes. Pas de fusion ni remplacement des anciens incidents.

Les messages sont des données de formation sauvegardées localement. La projection publique de la console ne transmet aucun hash ou mot de passe AD. La documentation métier ne publie pas le contenu des boîtes.

## Recette Windows / PT9 — à réaliser

1. Extraire le ZIP dans un nouveau dossier, puis copier les sauvegardes comme habituellement. Vérifier la présence de la sauvegarde de migration et le maintien des anciens tickets.
2. Ouvrir la bonne entreprise dans PT et vérifier le réseau du technicien. Ouvrir son bureau, icône **Arrivées et services**.
3. Créer l’arrivée d’Alex Nouveau, identifiant `alex.nouveau`, service Comptabilité, responsable et date ; choisir le groupe demandé. Vérifier qu’un seul ticket `DEM-ARR-…` apparaît. Les contrôles initiaux doivent échouer.
4. Dans Annuaire, créer exactement ce compte et ce nom, dans l’OU voulue, avec un mot de passe initial de formation ; ajouter le groupe demandé. Dans la console d’arrivée, tester **Première connexion…** avec ce mot de passe et choisir un nouveau mot de passe (8 caractères minimum). Un mot de passe incorrect doit être refusé.
5. Vue Licences : attribuer Messagerie et Bureautique au nouveau compte. Tenter une capacité inférieure au nombre d’attributions : refus sans retrait de licences.
6. Vue Messagerie : créer sa boîte. Lire/copier la lettre dans la vue Arrivées. Depuis la boîte `accueil@…`, envoyer ce texte exact à l’adresse affichée de l’arrivant. Ouvrir sa boîte et vérifier la réception ; envoyer une réponse vers Accueil. Aucun message réel ne sort du logiciel.
7. Parc et stock : préparer le portable de réserve dans l’atelier visuel, puis enregistrer sa remise à Alex. Vérifier qu’Alex est proposé pour la remise, et qu’aucun PC PT n’a été créé ou remplacé.
8. Tickets : prendre en charge, ajouter un compte rendu, vérifier puis proposer la résolution. Les six contrôles doivent être satisfaits. Confirmer le retour du demandeur pour clôturer.
9. Avant clôture d’une autre demande résolue, retirer sa licence : clôture refusée après relecture des moteurs. Rétablir la licence, vérifier de nouveau.
10. Tester service mail arrêté, destinataire inconnu, réactualisation réseau refusée, sauvegarde/reprise, fenêtre étroite, clavier et scroll. Une fenêtre d’action restée ouverte après refus d’actualisation ne doit pas envoyer une modification.

## Limites assumées

Ce n’est ni Outlook, ni Exchange, ni SMTP. Aucun serveur de mail ou trafic mail dans PT ; pas de boîte client authentifiée depuis le bureau du salarié, IMAP/POP, pièces jointes, dossiers personnalisés, règles ou synchronisation. L’administration peut simuler les échanges de toute boîte ; cela ne prouve pas une connexion de l’utilisateur sur son poste.

La licence Bureautique est un droit de catalogue, pas une installation d’Office. Les groupes ne valident pas automatiquement les ACL de fichiers. La demande est créée manuellement, pas encore par le moteur d’arrivées périodiques. Le responsable est une information de la demande, sans circuit d’approbation. Le stock existant comporte un portable de réserve : il faut du matériel disponible pour satisfaire une nouvelle remise.

Les valeurs de préavis/rétention décrivent une politique fictive pour l’exercice ; aucune purge automatique n’est effectuée. La lettre est un texte de formation, pas un fichier Word ou une expédition physique. Rendu visuel et fonctionnement réel du pont restent à tester dans Windows/PT9.
