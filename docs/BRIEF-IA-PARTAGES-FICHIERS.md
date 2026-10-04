# Mission IA — moteur de partages de fichiers simulés

## 1. Livraison et base exacte

Projet : https://github.com/Sikiroux/AI-PKT-LAB

Base applicative v0.19 : commit `344716d6e60c2fd0acb4116604b756144b1091a3`, branche `codex/procedural-service-desk-prototype`. Créer `codex/file-sharing-simulation-engine` depuis ce commit. Ne pas fusionner, pousser ou modifier la branche source ou main. Lire ce brief, `CLAUDE.md`, `web/sim_ad.py`, `web/directory_adapter.py` et `docs/V019-ANNUAIRE-INTEGRE.md` avant de coder.

Livrer exactement trois nouveaux fichiers :

- `web/sim_files.py` : moteur pur Python, bibliothèque standard seulement.
- `web/test_sim_files.py` : tests unittest.
- `docs/SIM-FILES-IMPLEMENTATION.md` : contrat, exemples exécutables, limites et intégration.

Ne modifier aucun fichier existant. Pas d'UI, routes, pont, migration, tickets, OS.js, serveur réel, VM, dépendance ni accès aux fichiers du système hôte. L'IA intégratrice fera le raccordement. Ce module est une simulation pédagogique, pas un serveur SMB.

Le périmètre web est explicitement autorisé par Damien et remplace l'ancienne restriction PT uniquement. Les autres règles de CLAUDE.md restent applicables, notamment les tests avant commit. Livrer les commandes et résultats de tests, SHA et branche, sans déclarer une validation réelle dans Packet Tracer.

## 2. Fonctionnement réel retenu et sources

Documentation consultée le 4 octobre 2026, sources primaires :

1. Microsoft, SMB overview : https://learn.microsoft.com/en-us/windows-server/storage/file-server/file-server-smb-overview
2. Microsoft, dépannage connexion TCP SMB : https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/tcp-three-way-handshake-fails
3. Microsoft, permissions partage et NTFS : https://learn.microsoft.com/en-us/iis/web-hosting/configuring-servers-in-the-windows-web-platform/configuring-share-and-ntfs-permissions
4. Microsoft, ACL et restriction combinée (Azure Files ; illustration du principe, pas modèle RBAC à recopier) : https://learn.microsoft.com/en-us/azure/storage/files/storage-files-identity-configure-file-level-permissions
5. Microsoft, quotas de dossiers, limites dures et souples : https://learn.microsoft.com/en-us/powershell/module/fileserverresourcemanager/new-fsrmquota?view=windowsserver2022-ps
6. Microsoft, définition des quotas : https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fsrm/592dad39-f14e-4c5b-b7bc-a1c0bc4724b3

Un client accède à une ressource par un chemin UNC ou un lecteur mappé. Le serveur traite des opérations distinctes de lecture, création et modification. Le transport TCP SMB traditionnel utilise le port 445 : ICMP ne démontre pas sa disponibilité. Les droits du partage et du système de fichiers limitent conjointement l'opération. Un quota dur interdit une écriture dépassant sa limite ; un quota souple signale le dépassement sans le bloquer.

La simulation adopte un sous-ensemble déclaré : deux couches d'autorisations positives, actions `list/read/write/delete`, quota par partage, fichiers texte UTF-8. Ne pas appeler ces ACL une implémentation NTFS complète. Pas d'ACE de refus, héritage, propriétaire, groupes imbriqués, verrou de fichier, DFS, cache hors connexion, Kerberos, négociation SMB, dialectes ni accès local au disque serveur en v1. Ajouter ces comportements plus tard exige un contrat distinct. Ne jamais conseiller de désactiver les protections SMB réelles pour résoudre un exercice.

## 3. Sources de vérité et intégration

L'environnement possède son fichier PT et son `session.json`. Le futur adaptateur stockera `state['file_service']`. Ce moteur ne sauvegarde rien lui-même.

- Réseau : observations PT fournies par le contrôleur, pour une paire source/cible précise.
- Identités, état du compte, groupes : `state['directory']`, moteur AD v0.19 existant.
- Session authentifiée : preuve serveur actuelle, jamais une affirmation du navigateur.
- Partages, fichiers, permissions, capacités : ce moteur uniquement.

Ne pas dupliquer les comptes ou inventer un deuxième annuaire. Ne pas utiliser `directory_resource` comme troisième restriction concurrente des nouvelles ACL : la migration sera réalisée par l'intégratrice. Ne pas changer les anciens booléens ou les évaluations Documents actuelles.

La v0.19 exige actuellement un annuaire pour Documents. V1 de ce module couvre ce profil de domaine seulement. Prévoir la documentation d'un futur adaptateur de comptes locaux, sans faire apparaître automatiquement un AD dans chaque petite entreprise.

## 4. Contrat de génération et données

Fonctions publiques obligatoires :

```python
generate_file_service(seed, environment_id, server, principals, now) -> dict
validate_file_service(service) -> None
public_file_service(service, actor) -> dict
evaluate_access(service, request, context, now) -> dict
perform_file_action(service, request, context, now) -> dict
apply_operation(service, operation, payload, actor, now) -> dict
```

`server` : `{id, name, ip, dns_name}` ; son ID est celui de l'environnement. `principals` : `{user_ids: [...], group_ids: [...]}` fournis par l'intégratrice. Pas de nom, adresse ou ID PT inventé par le moteur.

État : `schema_version=1`, `environment_id`, `server`, `principal_catalog`, `service_status` (`running/stopped`), `firewall_tcp445_allowed` (booléen), `volume` (`capacity_bytes`, `background_used_bytes`), `shares`, `files`, `revision`, `audit`.

- Partage : `id`, `name`, `enabled`, `hidden`, `share_acl`, `folder_acl`, `quota`.
- Chaque ACL : dictionnaire des quatre actions, chacune `{user_ids:[], group_ids:[]}`. Pas de droit implicite administrateur ou Tout le monde. `read` n'implique pas `list`, `write` n'implique pas `delete` : représenter les profils usuels par plusieurs grants explicites.
- Quota : `{mode: off|hard|soft, limit_bytes: entier positif ou null}`. Mode off exige null.
- Fichier : `id`, `share_id`, `name`, `content`, `read_only`, `updated_at`. Pas de sous-dossiers v1. Nom unique sans casse dans un partage. Taille dérivée de `len(content.encode('utf-8'))`, jamais acceptée aveuglément du client.

Les IDs sont stables après renommage. Références existantes, noms non vides, valeurs booléennes strictes, entiers non négatifs (rejeter bool comme entier), capacité positive, horodatages finis, aucune référence transversale à un environnement. Nom de fichier : pas de `/`, `\\`, `..`, NUL ou caractère de contrôle ; aucun chemin du système hôte.

Génération saine reproductible à seed, environment_id, server, principals et now identiques. Flux dédié SHA-256 de `str(seed) + ':files:v1'`, random.Random local ; pas de hash() Python, RNG global ou horloge cachée. Générer 2 à 4 partages nommés, quelques fichiers fictifs variés et des IDs déterministes. Au moins le premier utilisateur fourni doit pouvoir effectuer les quatre actions sur le premier partage. Exiger un utilisateur fourni ; accepter zéro groupe. Pas de panne cachée ni d'AD supplémentaire. La capacité saine doit dépasser l'occupation initiale. Les contenus restent fictifs, courts et plafonnés à 64 Kio UTF-8 par fichier, 100 fichiers et 10 partages.

Calculer `used_bytes = background_used_bytes + somme des tailles de tous les fichiers`. Calculer le quota par somme du partage. Ne pas maintenir un compteur libre contradictoire. Un changement administratif de capacité/quota peut produire un dépassement existant : état valide pour exercice. Bloquer les écritures qui augmentent ce dépassement, autoriser les réductions et suppressions conformes aux permissions.

## 5. Requête et contexte imposés

`request` : `{action, share_id, file_id?, name?, content?, expected_revision?}`. Pour un accès par nom ou lecteur, l'adaptateur résout d'abord le partage et fournit son ID ; le moteur reçoit `context.address_mode` (`ip/name`) et, pour name, la preuve de résolution. Pas d'analyse DNS réelle ou d'UNC complète ici.

`context` vient uniquement du serveur :

```text
environment_id, source_device_id, target_device_id
network = {status: up|down|unknown, observed_at, valid_until,
           source_device_id, target_device_id, evidence: tcp445|icmp_proxy}
address_mode = ip|name
name_resolution = {status: resolved|failed|unknown, resolved_ip,
                   observed_at, valid_until}  # requis en mode name
identity = {user_id, group_ids, account_allowed, authentication_valid}
```

`account_allowed` provient de sim_ad.evaluate_user avec les vérifications v0.19, et `authentication_valid` de la session contrôlée par le serveur (environnement, poste et expiration). Un compte AD ne devient pas désactivé parce que le moteur de fichiers retourne une erreur. L'intégratrice renouvelle cette projection à chaque action. Le moteur exige user_id connu et group_ids connus ; il ne prouve pas les memberships tout seul. Le navigateur ne peut fournir ce contexte.

Vérifier environment_id et cible égale server.id. Preuve réseau correspond exactement à source_device_id/cible. Observation fraîche : observed_at <= now <= valid_until, avec valid_until >= observed_at ; sinon unknown. Une preuve ip/name échouée n'est pas une autorisation d'essayer une autre cible. En mode name, resolved_ip doit correspondre à server.ip. En mode ip, DNS n'est pas requis.

## 6. Évaluation ordonnée, diagnostic imbriqué

Chaque résultat : `{allowed: bool, status: passed|failed|unknown, code, tree, evidence}`. `tree` est une chaîne imbriquée de `{stage, status: passed|failed|unknown|blocked, children:[...]}`. Au premier failed/unknown, les étages suivants sont blocked, pas failed et pas évalués. Refuser toute valeur manquante qui pourrait donner un succès gratuit.

Ordre pédagogique déterministe (ne prétend pas reproduire l'ordre interne exact Windows) :

1. Périmètre environnement/source/cible et forme de la requête.
2. Résolution du nom si utilisée.
3. Connectivité observée source → serveur.
4. Pare-feu simulé TCP 445, puis service running.
5. Partage existant et enabled.
6. Compte utilisable puis authentification valide.
7. Droit de l'action dans share_acl ET folder_acl.
8. Fichier existant pour read/update/delete ; nom disponible pour création.
9. read_only pour modification/suppression.
10. Capacité et quota dur pour écritures qui augmentent l'occupation.

L'autorisation dans une couche est un grant direct utilisateur OU un grant par l'un de ses groupes. Il faut un grant dans CHACUNE des deux couches. Ne pas limiter une lecture parce que le disque est plein. Le masquage `hidden` masque la découverte dans une future UI, pas l'accès direct par ID/chemin.

Codes au minimum : OK, INVALID_CONTEXT, NAME_UNRESOLVED, NETWORK_DOWN, OBSERVATION_UNKNOWN, TCP445_BLOCKED, SERVICE_STOPPED, SHARE_NOT_FOUND, SHARE_DISABLED, ACCOUNT_UNAVAILABLE, NOT_AUTHENTICATED, SHARE_ACCESS_DENIED, FILESYSTEM_ACCESS_DENIED, FILE_NOT_FOUND, NAME_CONFLICT, FILE_READ_ONLY, DISK_FULL, QUOTA_EXCEEDED, REVISION_CONFLICT. Mauvaise structure d'entrée : ValueError avec code stable documenté. Refus normal d'accès : résultat, pas exception. Les codes internes détaillés seront filtrés par l'intégratrice pour ne pas donner la cause dans le ticket.

`evidence` conserve notamment tcp445 ou icmp_proxy. Un succès avec icmp_proxy signifie seulement « accessible dans le modèle pédagogique avec hypothèse de transport » ; jamais « SMB réellement testé ». Aucun faux ping, aucun faux résultat TCP prétendument extrait de PT.

## 7. Actions, administration et mutations

`perform_file_action` appelle la même évaluation (pas un chemin de contournement) et retourne `{service: copie, result}` :

- list : retourner les métadonnées des fichiers du partage, pas tous leurs contenus.
- read : retourner le contenu du fichier demandé seulement après autorisation.
- write : file_id absent crée un fichier avec name ; présent remplace entièrement son contenu. Contrôler expected_revision pour write/delete ; l'intégratrice fournit la revision courante, absence = INVALID_REQUEST.
- delete : retirer un fichier autorisé et libérer son occupation dérivée.

Succès de write/delete : revision+1 et audit. Lectures/évaluations sans mutation, sans revision supplémentaire. Refus : copie identique, aucun fichier ou compteur modifié. Le serveur pourra journaliser les tentatives séparément. Audit de mutation : at, actor_id, opération, share_id/file_id, code ; aucun contenu ni credential.

`apply_operation` retourne la même enveloppe et exige acteur serveur `{id, environment_id, permissions}`. Capacité distincte `files.manage`, sans privilège implicite lié au nom technician. Opérations : set_service_status, set_firewall, set_share_enabled, rename_share, set_acl (remplace une couche entière validée), set_quota, set_volume_capacity, set_background_usage, set_file_read_only. Chaque payload a des champs explicitement autorisés ; interdire écriture arbitraire de revision/audit/principal_catalog. Administrateur inconnu ou mauvais environnement = refus documenté sans mutation.

`public_file_service` est une projection pour console d'administration autorisée files.manage : métadonnées, ACL, quota, occupation et état, sans contenus ni contexte d'authentification. Refuser l'acteur non autorisé. Le client utilisateur passe par list/read ; aucune projection globale ne doit exposer des fichiers non autorisés.

Tout opère sur copies profondes ; aucune mutation de l'entrée ou de listes partagées, même après échec. Validation avant et après mutation. L'intégratrice exécutera sous verrou, contrôle revision et sauvegarde atomique ; ce moteur ne gère pas la concurrence ou persistance lui-même.

## 8. Catalogue pédagogique à documenter

Documenter les mutations, symptômes et résultats attendus de ces huit familles, sans générer de tickets dans ce module :

| Panne | Symptôme possible | Réparation observable |
|---|---|---|
| Réseau PT coupé | Dossier et prise en main inaccessibles | Rétablir le réseau, obtenir une preuve fraîche |
| DNS simulé incorrect | IP fonctionne, nom échoue | Résolution vers l'adresse serveur exacte |
| TCP 445 bloqué simulé | Ping possible, dossiers inaccessibles | Autoriser le service dans le modèle |
| Service arrêté | Partages indisponibles | Service running |
| Partage désactivé | Un partage inaccessible | Réactiver le partage ciblé |
| Droit incomplet | Lecture possible, écriture refusée | Grant approprié dans les deux couches |
| Quota dur atteint | Lecture possible, nouveau fichier refusé | Libérer l'espace ou ajuster la limite autorisée |
| Disque plein ou fichier lecture seule | Écriture impossible | Corriger la ressource concernée sans changer le reste |

Ne pas choisir une panne par hasard dans evaluate_access. Le générateur sain puis les mutations produisent la panne et ses conséquences. Les comptes AD verrouillés/désactivés et mots de passe restent gérés par sim_ad. Distinguer un quota de dossier du quota disque Windows par utilisateur ; v1 ne simule que le premier, sur la racine du partage.

## 9. Tests d'acceptation obligatoires

Chaque point doit avoir une assertion qui échoue en présence d'une régression :

1. Même seed/contexte/now → même état ; seeds variées → variations utiles ; RNG global intact.
2. Identités et serveur fournis conservés ; zéro groupe accepté ; utilisateur absent refusé.
3. État sain permet list/read/create/update/delete au premier utilisateur/partage.
4. Mauvais environnement/source/cible ou preuve d'une autre paire refusés.
5. Preuve down refusée ; inconnue/périmée/future unknown ; étages suivants blocked.
6. IP contourne seulement le besoin DNS ; name failed/unknown/mauvaise IP refuse.
7. TCP445_BLOCKED/service stopped/share disabled indépendants ; réparation restaure.
8. Compte refusé/auth expirée refusent ; aucun secret ou état AD modifié.
9. Grant direct et groupe fonctionnent ; les deux couches sont requises ; manque de grant refuse.
10. Lecture autorisée et écriture refusée ; delete séparé ; hidden n'interdit pas accès direct.
11. Aucun contenu via list/projection ; read refusé ne contient aucun contenu.
12. Fichier absent/nom en doublon sans casse ; noms invalides et traversée refusés.
13. Tailles UTF-8 correctes ; création augmente, remplacement applique delta, suppression libère.
14. Écriture exactement à la capacité/limite permise ; +1 octet refusé.
15. Disque plein : lecture/suppression/réduction permises avec droits ; croissance refusée.
16. Quota dur refuse croissance ; souple autorise avec warning QUOTA_WARNING ; off n'impose rien.
17. Volume commun : fichiers d'autres partages comptent ; quota ne compte que le partage.
18. read_only bloque update/delete mais pas read ; mutation restaure.
19. Administration sans files.manage/mauvais environnement refusée ; inconnu/champ arbitraire refusé.
20. Entrées inchangées après succès/refus ; copie indépendante après modification du retour.
21. Mutations réussies revision+1, audit sans contenu ; lecture/refus revision inchangée.
22. Revision obsolète write/delete = REVISION_CONFLICT sans mutation.
23. Validation refs/types/timestamps/capacités et plafonds ; dépassement administratif valide.
24. Réparer une ACL/un partage ne modifie aucun autre partage/fichier/service.
25. Aller-retour JSON conserve le comportement ; exemple minimal de doc réellement exécuté.
26. Succès icmp_proxy distinct de tcp445, jamais présenté comme observation SMB réelle.

Exécuter : `python -m unittest discover -s web -p 'test_sim_files.py'`, la suite web complète, puis les deux suites exigées par CLAUDE.md. Aucun test historique modifié pour faire passer le module.

## 10. Travail réservé à l'intégratrice

Migration sauvegardée depuis Documents v0.19, mapping des groupes existants vers les ACL, chemins UNC et lecteurs mappés, routes sous contrôle d'environnement, identité du technicien, fenêtres OS.js et contenu, dialogues client, tickets à seed, validation des réparations et observations réelles du pont. La correction ne sera pas un bouton booléen : les objectifs du ticket doivent être vérifiés par des opérations dans l'état réparé, avec contrôle des effets collatéraux.

Dans le retour final : SHA de base et livraison, les trois fichiers, tests exacts, ambiguïtés résolues et limites. Ne pas démarrer DNS/VPN/impression ni intégrer ce moteur sans nouvelle mission.
