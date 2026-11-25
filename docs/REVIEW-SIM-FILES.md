# Relecture du moteur de fichiers — corrections avant intégration

Livraison examinée : 8d7738f4d922b3e498b7aee056d70123878cf5a1, base v0.19 exacte. Trois fichiers ajoutés, conformément au périmètre. Relecture et exécution sur v0.20 ; aucune fusion distante effectuée.

## 1. Fichier d'un autre partage (bloquant)

Dans evaluate_access, target_file est recherché globalement par file_id, mais son share_id n'est pas comparé au partage de la requête. Les ACL sont donc celles d'un partage A tandis que perform_file_action peut lire, modifier ou supprimer un fichier de B. Reproduction effectuée : read avec partage A autorisé et file_id de B dont les deux ACL read sont vides -> allowed=True et contenu retourné.

Correction : une recherche de fichier doit être restreinte au share_id demandé. Un file_id d'un autre partage doit produire FILE_NOT_FOUND, sans contenu ni mutation, pour read, write et delete. Ajouter un test par action et vérifier aussi les calculs de quota et occupation après refus. Le contrôle doit être commun à evaluate_access et perform_file_action.

## 2. Identités absentes du catalogue (bloquant contractuel)

_context_scope_ok vérifie la forme des IDs mais pas leur appartenance au principal_catalog. Reproduction : user_id=inconnu avec groupe grp-staff connu et grant de ce groupe -> allowed=True. Le contrat exige un utilisateur et des groupes connus.

Correction : rejeter un user_id absent ou tout group_id absent avec INVALID_CONTEXT, sans lecture ni mutation. Tester utilisateur inconnu + groupe autorisé, utilisateur connu + groupe inconnu, liste mixte. Le contexte restera fourni par l'adaptateur serveur, mais le moteur doit appliquer ses propres préconditions de contrat.

## 3. Serveur et environnement sont deux identités distinctes

Retirer la contrainte server.id == environment_id dans generate_file_service et validate_file_service. Notre modèle utilise environment_id pour la session et server.id pour l'appareil (par exemple server). Conserver les contrôles séparés : context.environment_id == service.environment_id et context.target_device_id == service.server.id, avec même paire dans la preuve réseau.

Corriger les tests et la doc qui supposent leur égalité. Ajouter un cas positif env-01 / server-01 et des cas négatifs mauvais environnement ou mauvaise cible. Ne pas renommer les identités de l'environnement ou du moteur AD pour contourner ce défaut.

## 4. DNS inconnu ou périmé n'est pas une panne prouvée

_name_resolution_status retourne failed pour status=unknown, absence de preuve et horodatages périmés. Reproduction effectuée : résolution unknown -> résultat global failed. Le modèle doit conserver la distinction entre échec observé et absence de preuve.

Retourner unknown pour résultat inconnu/absent/périmé/futur/invalide ; failed pour échec frais explicitement observé ou résolution fraîche vers une mauvaise adresse. Adapter les codes de manière documentée (par exemple OBSERVATION_UNKNOWN pour unknown, NAME_UNRESOLVED pour failed). Les étapes suivantes restent blocked. En mode ip, DNS reste non applicable.

## Livraison corrective attendue

Faire un nouveau commit sur codex/file-sharing-simulation-engine, toujours uniquement les trois fichiers autorisés. Ne pas fusionner la branche source ou main. Garder les anciennes assertions pertinentes ; modifier seulement celles qui codent la contrainte erronée d'identité ou confondent DNS inconnu avec failed. Exécuter la suite moteur et web complète, ainsi que les suites requises dans CLAUDE.md avant commit. Fournir SHA et résultats exacts.

L'intégratrice conserve la migration, les routes, les fenêtres, le raccordement AD/PT et les tickets. Les corrections ci-dessus concernent le moteur, pas la simulation SMB réelle dans Packet Tracer.
