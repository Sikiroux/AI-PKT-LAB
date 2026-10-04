# Mission pour une autre IA — moteur d’annuaire AD simulé

## 1. Objectif et base de travail

Projet : [Sikiroux/AI-PKT-LAB](https://github.com/Sikiroux/AI-PKT-LAB).
Base : branche `codex/procedural-service-desk-prototype`, v0.17, commit applicatif `914d689507a761fd658a16f8f920b36ec6430b55`.

Lis ce document intégralement, puis `CLAUDE.md`. Crée ta propre branche `codex/ad-simulation-engine` depuis la branche ci-dessus, en incluant le commit qui ajoute ce brief. Fais des commits sur cette nouvelle branche, sans modifier ni fusionner la branche source. Si cette branche de travail existe déjà, vérifie son origine et son contenu avant de la reprendre.

**Livrer un moteur Python testable, sans interface graphique ni connexion à un vrai AD.** Le but est de permettre des exercices de support : compte verrouillé, désactivé, mot de passe expiré, mauvais groupe, accès à un dossier partagé refusé.

Ce brief décrit une cible à implémenter ; aucun moteur AD n’est encore intégré. Les contraintes anciennes de CLAUDE.md limitant le projet à Packet Tracer sont dépassées par la demande explicite de Damien de simuler les postes et services côté web. Les règles de validation, de compatibilité et de tests restent applicables.

## 2. Architecture existante à respecter

- `web/tickets_app.py` : serveur local unique et tickets.
- `web/workspace_app.py` : contrôleur d’environnement et observations du pont PT.
- `web/workspace_model.py` : état persistant du prototype, préconditions, sauvegarde JSON atomique.
- `web/environment_store.py` : catalogue de sessions ; chacune a son `session.json` et ses tickets.
- `web/workspace_routes.py` : routes existantes, contrôle d’environnement actif.
- `web/desktop.html` : bureau OS.js, Documents et terminal ping.

Une entreprise possède un état commun et un fichier Packet Tracer associé. Le moteur AD est une partie de cet état, pas un deuxième serveur ou une base autonome.

Actuellement, le prototype utilise `account_enabled`, `read_allowed` et `write_allowed`. **Ne les remplace pas et ne les synchronise pas dans cette mission.** Leur migration vers l’annuaire sera intégrée ensuite par l’IA qui maintient le contrôleur. Ne crée pas deux sources d’autorité concurrentes.

Les applications futures seront des icônes OS.js selon le poste et les logiciels installés. Voir l’icône ADUC ne donne pas de droits. Un portable du technicien sera ajouté côté PT et web ; il n’est pas nécessaire de le créer pour cette mission.

## 3. Fichiers autorisés et périmètre

Créer uniquement :

- `web/sim_ad.py` : modèle, génération, opérations et évaluations ; bibliothèque standard Python.
- `web/test_sim_ad.py` : tests `unittest` du moteur.
- `docs/SIM-AD-IMPLEMENTATION.md` : règles, fonctions, simplifications, intégration prévue.

Ne modifier aucun fichier existant : contrôleur, routes HTTP, bureau, générateur, bridge, vendor OS.js ou anciens tests. Pas de dépendance, serveur supplémentaire, Supabase, VM, Docker, LDAP réel, appel réseau ou commande système.

Sont hors périmètre : UI ADUC, réplication multi-DC, Kerberos/LDAP complets, GPO, liens de confiance, FTP, VPN, terminal IOS et migration des anciennes sessions. Fournir des points d’intégration documentés pour ces fonctions ultérieures.

## 4. Contrat de données v1

Le futur adaptateur conservera le résultat de `generate_directory` sous `workspace.state['directory']`. Le moteur ne lit ni n’écrit les fichiers de session lui-même.

Structure proposée, à documenter exactement dans le livrable :

```json
{
  "schema_version": 1,
  "environment_id": "identifiant-de-session",
  "domain": {"id": "dom-...", "dns_name": "agence.lab", "netbios_name": "AGENCE"},
  "ous": {},
  "users": {},
  "groups": {},
  "computers": {},
  "policy": {"lockout_threshold": 3, "lockout_seconds": 300},
  "revision": 0,
  "audit": []
}
```

Les dictionnaires d’objets sont indexés par des ID stables. Chaque référence utilise un ID, jamais uniquement un nom affiché. Le nom du domaine `.lab` est une convention de simulation locale, pas un domaine à contacter réellement.

- OU : `id`, `name`, `parent_id` (null pour racine). Interdire les cycles.
- Utilisateur : `id`, `username`, `display_name`, `ou_id`, `enabled`, `locked_until` (timestamp ou null), `password_expires_at` (timestamp ou null), `must_change_password`, `failed_attempts`, `credential` (structure privée de vérification).
- Groupe : `id`, `name`, `ou_id`, `member_user_ids`. Groupes de sécurité seulement ; groupes imbriqués hors v1.
- Ordinateur : `id`, `name`, `ou_id`, `device_id`, `domain_joined`. `device_id` désigne une identité de poste fournie par notre environnement ; le moteur n’invente pas d’équipement PT.

Les noms de connexion et de groupes sont uniques sans tenir compte de la casse, dans leur catégorie. Les OU peuvent avoir le même nom sous des parents distincts. Valider les références et refuser les données incohérentes. Le renommage conserve l’ID.

La seed génère les noms, OU, groupes et ID de façon reproductible. Utiliser `random.Random` avec une dérivation SHA-256 dédiée `seed + ':directory:v1'`, jamais `hash()` Python ni le générateur aléatoire global. Ne pas consommer le flux réseau existant. Les horodatages partent du paramètre `now`, pas d’un appel caché à l’horloge.

Pour les secrets, utiliser des identifiants fictifs de formation seulement. Aucun mot de passe réel demandé. Les vérificateurs de mots de passe utilisent une fonction dédiée basée sur PBKDF2-HMAC-SHA256 et comparaison constante ; sel aléatoire, donc sa représentation peut varier entre deux générations. La reproductibilité du monde concerne les objets et règles, pas les sels ni les sessions d’authentification. Ne jamais inclure les secrets/verificateurs dans une projection publique, une erreur ou l’audit. Un secret temporaire explicitement demandé peut être retourné une seule fois dans la réponse privée de l’opération ; son contenu n’est pas journalisé.

## 5. Fonctions attendues

Les noms ci-dessous sont le contrat proposé à implémenter, pas des fonctions déjà présentes :

```python
generate_directory(seed, environment_id, devices, requester, now) -> dict
public_directory(directory) -> dict
validate_directory(directory) -> None
apply_operation(directory, operation, payload, actor, now) -> dict
authenticate(directory, username, password, context, now) -> dict
evaluate_user(directory, user_id, context, now) -> dict
evaluate_access(directory, user_id, resource, action, context, now) -> dict
```

`devices` est une liste explicite de `{id, name, role}` fournie par l’adaptateur. `requester` est `{id, username, display_name, device_id}` ; son identité doit être conservée. Documenter les contraintes des entrées et un exemple minimal runnable.

`generate_directory` construit un état sain, avec demandeur et groupes usuels. Le générateur de tickets injectera ensuite une panne par une opération précise. Ne pas cacher une panne aléatoire dans l’état sain. Proposer dans la documentation comment créer une variation de scénario avec les opérations, sans créer de ticket.

`apply_operation` retourne un nouveau dictionnaire complet de résultat. **Ne pas modifier l’entrée**, même en cas d’erreur ; une opération validée produit `directory` avec une nouvelle `revision`. L’adaptateur réalise ensuite la sauvegarde atomique sous le verrou du contrôleur. L’audit est dans la copie retournée.

Opérations minimales : `create_user`, `update_user`, `reset_password`, `unlock_user`, `set_user_enabled`, `create_group`, `add_group_member`, `remove_group_member`, `create_ou`, `move_object`, `join_computer`, `leave_computer`.

`update_user` permet nom affiché, nom de connexion, expiration et changement obligatoire ; pas d’écriture arbitraire dans `credential`, compteurs, audit ou revision. Éviter un endpoint générique qui accepterait tous les champs sans contrôle.

Convention de retour des mutations : `{directory: copie, result: résultat}`. Une opération invalide lève `ValueError` avec un code stable documenté, sans mutation. Un refus d’authentification normal retourne son résultat et la copie (compteurs éventuellement mis à jour), sans exception. `public_directory` ne retourne que les objets nécessaires à une console autorisée : l’adaptateur contrôle qui peut la consulter.

`authenticate` peut modifier les compteurs/verrouillage dans une copie retournée selon le même principe. Échec réseau ou service = aucune tentative de mot de passe comptabilisée. Login inconnu ou mot de passe incorrect = erreur publique générique ; ne pas dévoiler le vérificateur.

Le contexte d’authentification reçu par `evaluate_access` est lui aussi fourni par le serveur à partir d’une session, jamais déclaré par le navigateur. V1 accepte une preuve de session seulement pour le même utilisateur et environnement.

`actor` est un contexte de confiance créé par le futur serveur, jamais accepté directement depuis le navigateur : `{id, environment_id, permissions}`. Capacités distinctes, par exemple `directory.users.manage`, `directory.passwords.reset`, `directory.groups.manage`, `directory.ous.manage`, `directory.computers.manage`. Chaque opération vérifie sa capacité et l’environnement. Les évaluations ne confèrent pas ces capacités.

**Authentification et autorisation sont séparées.** Actif/déverrouillé n’équivaut pas à authentifié. Un mot de passe réinitialisé avec changement obligatoire nécessite un traitement distinct ; ne pas annoncer une connexion normale réussie avant ce changement.

## 6. Préconditions réseau, services et permissions

Le pont Packet Tracer reste autorité sur les observations réseau. Ce module ne fait pas de ping et ne transforme pas un ping en preuve LDAP/SMB/FTP. Il reçoit un contexte fourni par l’adaptateur :

```json
{
  "environment_id": "identifiant-de-session",
  "source_device_id": "poste-source",
  "target_device_id": "serveur-cible",
  "network": {"status": "passed", "observed_at": 1000, "valid_until": 1045, "evidence": "icmp_proxy"},
  "directory_service": "running",
  "resource_service": "running",
  "authentication": {"user_id": "usr-...", "status": "authenticated"},
  "vpn": {"mode": "none", "status": "disconnected"}
}
```

Valeurs réseau : `passed`, `failed`, `unknown`. Une preuve périmée, future, manquante ou provenant d’un autre environnement est inconnue/refusée ; pas de succès par défaut. La provenance source/cible doit être vérifiée par l’adaptateur avant d’appeler le moteur. `vpn` est réservé pour une extension, pas une preuve réseau : aucun succès accordé par le seul état VPN connecté.

Pour `evaluate_access`, `resource` contient : `id`, `server_device_id`, `allowed_user_ids`, `allowed_group_ids`. Les deux derniers sont des dictionnaires par action `read` et `write`, dont les valeurs sont des listes d’ID. La cible doit correspondre au contexte. V1 : permissions positives seulement, pas d’ACL de refus, héritage NTFS ou approximation de toutes les règles Windows. Lecture et écriture sont indépendantes.

Arbre d’accès : réseau observé → service ressource → service annuaire → état du compte → authentification → droit sur la ressource. Renvoyer `blocked` pour les étapes non exécutées après un échec. Cette chaîne est une simplification pédagogique du domaine en ligne : pas d’authentification hors ligne/cachée, ni maintien automatique d’anciens jetons après changement de groupe.

Les vérifications locales d’une console hors ligne et les vérifications d’accès au domaine sont distinctes. Le bureau portable reste ouvert sans réseau ; cela ne donne pas le droit d’atteindre l’annuaire.

Format commun de résultat :

```json
{
  "allowed": false,
  "status": "failed",
  "code": "ACCOUNT_DISABLED",
  "tree": {"id": "network", "label": "Connectivité observée", "status": "passed", "children": []}
}
```

Statuts des nœuds : `passed`, `failed`, `unknown`, `blocked`. Réutiliser cette forme de `workspace_model.result` sans dépendre de l’état global. Codes stables documentés ; messages français. `allowed` ne vaut true que si toutes les préconditions requises sont prouvées. Une erreur de contrat ou d’opération ne doit pas produire un faux arbre de réussite.

## 7. Intégration future, à ne pas coder dans cette mission

L’IA intégratrice ajoutera les routes sous `/workspace/directory/...`, vérifiera le jeton local et l’environnement, construira l’acteur et le contexte réseau, puis appliquera la copie retournée et sauvegardera. Pour l’état futur : `directory` imbriqué dans le `session.json` existant ; aucun fichier AD partagé entre entreprises.

Elle reliera ensuite les groupes aux permissions de Documents, ajoutera l’icône Annuaire au portable du technicien si les outils sont installés et construira les fenêtres ADUC. Elle gérera la migration des anciens booléens, l’identité du portable, le VPN simulé et l’invalidation des sessions.

Le VPN aura des profils, une authentification, une passerelle et des ressources autorisées. Sa version purement web devra être présentée comme simulée, sans prétendre créer un tunnel PT. Ce moteur ne réalise ni ces tunnels ni leurs règles.

## 8. Tests d’acceptation obligatoires

- Même seed et mêmes entrées : mêmes identités/noms/groupes/règles, hors sels privés.
- La génération AD ne modifie pas le flux aléatoire global ni les devices d’entrée.
- Deux environnements restent isolés ; rejet d’un acteur/contexte d’un autre environnement.
- Un compte actif n’accorde pas l’accès sans authentification et droit.
- Mauvais mot de passe, seuil de verrouillage, expiration du verrou, déverrouillage, désactivation, expiration du mot de passe et changement obligatoire.
- Échec réseau/service : nœuds descendants bloqués et aucun compteur d’échec de mot de passe ajouté.
- Réseau inconnu/périmé/futur : jamais de succès.
- Groupes : ajout/retrait change le résultat d’accès ; lecture ne donne pas écriture.
- Permissions d’administration absentes : opérations refusées ; l’icône n’entre pas en jeu.
- Doublons sans tenir compte de la casse, références invalides, cycles d’OU et opérations inconnues refusés.
- Copie sans mutation d’entrée ; erreur sans changement de revision ni audit ; succès journalisé sans secret.
- Projection publique sans mots de passe, sels, digests ni codes de récupération ; ne pas muter le modèle lors de la projection.
- Aller/retour JSON préserve le modèle et ses règles, sans créer une preuve réseau persistante dans l’annuaire.

Exécuter `python -m unittest discover -s web -p 'test_sim_ad.py'`, puis la suite web existante et `python tests/test_all.py` avant chaque commit, conformément à CLAUDE.md. Pas besoin d’annoncer une validation PT pour ce moteur pur ; ne pas prétendre que son integration PT est testée.

## 9. Livraison

Fournir les trois fichiers, commits et branche. Dans la description : comportement livré, commandes de tests et résultats, simplifications, intégration restante. Pas de merge automatique, pas de remplacement de l’application existante et pas de ZIP présenté comme version intégrée.

Documenter les éventuelles ambiguïtés résolues et garder le contrat cohérent. Si une modification hors des trois fichiers est nécessaire, expliquer laquelle ; ne pas la faire silencieusement.

## 10. Message court pour démarrer

> Travaille sur AI-PKT-LAB. Lis `docs/BRIEF-IA-MOTEUR-AD.md` sur la branche `codex/procedural-service-desk-prototype`, puis crée ta branche `codex/ad-simulation-engine` à partir de cette version. Implémente le moteur AD simulé et ses tests selon le brief. Ne modifie pas les routes, le pont Packet Tracer ou le bureau ; l’intégration sera faite séparément. Fais des commits et donne-moi la branche, les résultats de tests et les limites. Ne merge pas.
