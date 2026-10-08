# v0.44 — référentiel commun du périmètre simulé

## Ce qui change

Une personne représentée dans un bureau distant dispose d’un identifiant d’employé, lié à l’identifiant de son compte d’annuaire. Son poste dispose d’un identifiant matériel, lié au numéro de série Packet Tracer. Les tickets d’intervention conservent désormais ces références et l’environnement auquel ils appartiennent.

Dans Postes, une fiche « Personne et poste » affiche le compte, le numéro de série et les références de la cible choisie. La ligne affiche le nom de la personne et son identifiant de connexion issu de l’annuaire. La prise en main reste dirigée vers le numéro de série sélectionné ; elle ne choisit jamais un poste à partir du prénom.

Un renommage du compte ou du poste met à jour l’affichage sans changer les références. La suppression d’un compte ou d’un matériel représenté conserve sa fiche historique, avec un indicateur d’absence. Ces indicateurs ne constituent ni une preuve de connectivité ni une désactivation AD.

## Initialisation et persistance

`company_registry.py` fournit `ensure`, `links`, `public` et `link_tickets`. Le schéma v1 est enregistré dans `session.json`, sous `company_registry`, par `Workspace.save`.

- Les identifiants logiques sont dérivés de la seed et d’un espace de génération versionné.
- La portée obligatoire est `environment_id` : deux entreprises issues de la même seed peuvent avoir les mêmes identifiants logiques, mais ne sont jamais interchangeables.
- Le compte initial du second bureau utilise désormais un identifiant déterministe. Les anciens comptes et leurs droits sont conservés ; aucune réécriture d’un compte existant.
- La création manuelle d’un compte dans l’annuaire conserve le comportement du moteur AD.
- Les noms, mots de passe salés et dates de création ne sont pas une garantie d’état binaire identique ; la reproductibilité porte ici sur les identifiants et relations initiaux.
- Une sauvegarde `session.before-registry.json` précède la première migration d’une session existante.
- Une projection temporaire vers un autre bureau ne réécrit jamais le référentiel canonique.

Les identifiants matériels sont rattachés aux rôles générés. Le remplacement d’un équipement avec historique d’attribution complet n’est pas encore modélisé : ne pas utiliser ce schéma comme un inventaire patrimonial définitif.

## Tickets

Les tickets `workspace` issus des interventions reçoivent `environment_id`, `asset_id`, `employee_id` et `target_serial`. Le premier ticket historique `INC-1000` est rattaché au client canonique. Un ticket sans cible connue, un laboratoire indépendant ou une référence ambiguë ne reçoit pas d’association inventée.

Le référentiel ne change pas les droits, le résultat des vérifications, le timer ou la clôture. Un ticket provenant explicitement d’un autre environnement n’est jamais réaffecté.

## Limites

Il s’agit du personnel représenté par les bureaux actuellement simulés, pas du personnel complet. Les comptes supplémentaires générés dans AD ne sont pas arbitrairement déclarés comme employés disposant d’un bureau. Le portable de l’apprenant appartient au technicien, sans création automatique d’un employé IT interne.

L’arrivée d’un employé, la messagerie, les licences, la livraison de matériel et les événements d’entreprise restent les blocs suivants. Aucune nouvelle panne ou nouvelle commande Packet Tracer n’est ajoutée dans cette version.

## Vérification

Les tests couvrent les liens reproductibles, renommages, compte supprimé, matériel absent, séries ambiguës, périmètre d’environnement, tickets historiques, copie publique sans secrets et conservation après relecture. Les tests DOM existants vérifient toujours la sélection et la prise en main du poste.

À vérifier visuellement sur l’installation Windows : noms et identifiants de connexion affichés dans Postes, reprise d’une ancienne entreprise, interventions sur le second bureau. Les tests Python ne remplacent pas cette validation.
