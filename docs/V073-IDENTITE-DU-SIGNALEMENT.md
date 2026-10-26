# v0.73 — Demandeur, poste et vérification du ticket

## Défauts constatés

Le référentiel rattachait à nouveau les tickets à l'occupant courant du poste lors d'une actualisation. Le dialogue détectait déjà certaines réaffectations, mais le contrôle de résolution pouvait encore tester le nouveau compte et valider la demande initiale. La question « État de la connexion » donnait uniquement le résultat du contrôle IP vers le serveur.

## Changement

Les nouveaux incidents simultanés enregistrent l'identifiant du compte du demandeur dans le ticket et dans l'incident persistant, avant le signalement. Les liens de référentiel déjà enregistrés ne sont plus réécrits lors des actualisations. Au premier rattachement, le compte déclaré au signalement prévaut sur l'occupant courant du poste.

La vérification d'un incident simultané contrôle cette identité avant la fonction demandée. Si le compte affecté au poste a changé, le résultat est inconnu et la résolution/clôture automatique est refusée. Cela ne supprime ni le ticket, ni les notes, ni la panne. Un contrôle avec le nouvel occupant ne confirme pas la demande de l'ancien.

Compatibilité : pour un ancien incident, le compte peut être retrouvé depuis le récit client enregistré ou le demandeur du référentiel. Sans identité exploitable, la vérification reste inconnue. Le logiciel ne réécrit pas rétrospectivement l'histoire des tickets dont le mauvais rattachement aurait déjà été sauvegardé avant ce correctif.

La réponse « État de la connexion » distingue désormais un relevé récent de liaison débranchée, une liaison présente et l'absence de relevé. La question IP conserve son propre résultat. Un ancien constat de câble ne devient pas une panne actuelle. Ces réponses utilisent les observations existantes ; aucune commande ni nouveau ping n'est lancé par la messagerie.

## Limites

Ce bloc concerne les incidents simultanés de l'entreprise. Les anciens scénarios et leur dialogue ne sont pas tous refondus. Il ne fournit pas une interface complète de réaffectation/transfert de ticket : une réaffectation réelle doit faire l'objet d'un traitement explicite, pas d'un changement silencieux de demandeur. Le contrôle de la fonction conserve ses limites existantes, notamment le proxy ICMP et les simulations de services.

## Tests

Huit nouveaux tests couvrent le gel des liens historiques, le premier lien après réaffectation, l'identité enregistrée dans les deux sauvegardes, le refus de clôture avec un autre utilisateur, la validation du demandeur d'origine après réparation, les anciens récits, la cible absente et la distinction liaison/IP avec expiration du relevé. Suite web complète relancée. Générateur, ateliers et JavaScript inchangés depuis leur recette v0.70.

## Recette Windows / PT9 à effectuer

1. Créer un incident AD puis noter le demandeur et le poste. Réparer ce compte, ouvrir la bonne session et vérifier le ticket.
2. Tester une sauvegarde de recette dont l'affectation du poste a changé : l'actualisation ne doit pas changer le demandeur du ticket ; la vérification doit refuser la validation personnelle avec le nouveau compte.
3. Reprendre une sauvegarde et vérifier que le compte du signalement reste lié au même ticket.
4. Couper le câble d'un poste de test, renouveler les observations puis demander l'état de la connexion : le récit doit mentionner le relevé de liaison. La réponse au contrôle par IP doit rester distincte. Sans relevé récent, ne pas présenter le câble débranché comme un fait actuel.
5. Vérifier que les questions client ne modifient pas les services et ne lancent pas de ping.
