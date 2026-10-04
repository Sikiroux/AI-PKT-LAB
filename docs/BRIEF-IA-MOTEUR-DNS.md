# Mission IA — moteur DNS pédagogique

## 1. Base et fichiers autorisés

Projet : https://github.com/Sikiroux/AI-PKT-LAB

Créer `codex/dns-simulation-engine` depuis **le commit exact v0.21 `5af1132e364b3e555cb2ef8fdee9e19392b36a2b`**. La branche source est `codex/procedural-service-desk-prototype` ; elle peut avancer pendant ta mission, ne pas la modifier ou la fusionner. Si ta branche existe déjà, vérifier son origine avant de la reprendre. Aucun changement sur main.

Lire CLAUDE.md, docs/V021-PARTAGES-INTEGRES.md, web/files_adapter.py, web/sim_files.py, web/directory_adapter.py et web/workspace_app.py. Les restrictions anciennes PT uniquement sont remplacées par la demande explicite de simulation web ; les règles de tests et compatibilité restent applicables.

Créer uniquement :

- `web/sim_dns.py` : moteur pur, bibliothèque standard Python.
- `web/test_sim_dns.py` : tests unittest.
- `docs/SIM-DNS-IMPLEMENTATION.md` : contrat exact, limites, exemples exécutés et intégration future.

Ne modifier aucun fichier existant. Pas de route, interface, migration, ticket, bridge, dépendance, réseau réel, socket, commande système ou modification DNS de l'ordinateur hôte. L'intégratrice conserve toutes ces responsabilités. Livrer un nouveau commit sur ta branche, pas un merge.

## 2. Sources et périmètre réel

Sources primaires consultées le 4 octobre 2026 :

- RFC 1034, concepts, alias et cache : https://datatracker.ietf.org/doc/html/rfc1034
- RFC 1035, types et codes de réponses : https://datatracker.ietf.org/doc/html/rfc1035
- RFC 2308, réponses négatives et cache : https://www.rfc-editor.org/info/rfc2308/
- RFC 7766, transport TCP : https://datatracker.ietf.org/doc/html/rfc7766

Le DNS renvoie des informations associées à un nom et un type, pas une preuve que l'application cible fonctionne. Une réponse valide peut pointer vers une mauvaise adresse pour l'exercice. Le cache peut conserver une ancienne réponse jusqu'à expiration du TTL. NXDOMAIN distingue un nom inexistant ; NODATA distingue un nom existant sans enregistrement du type demandé. Le transport DNS n'est pas limité à UDP ; une simulation utilisant une preuve ICMP ne doit prétendre vérifier ni UDP 53 ni TCP 53.

V1 volontairement réduite : un serveur DNS simulé pour une zone interne, clients avec un serveur configuré, A/AAAA/CNAME, un suffixe de recherche simple, cache positif et négatif local par client. Pas de récursion Internet, délégation, DNSSEC, DoH/DoT, SOA sur le fil, DHCP automatique, SRV/MX/PTR, découverte AD, round-robin ou transport binaire. Ne pas prétendre émuler complètement Windows DNS ou les RFC.

## 3. Architecture et contrat public

L'intégratrice stockera ce module dans `session.json` sous `dns_service`. Les identités viennent de l'environnement ; un ID de serveur ne doit jamais être imposé égal à environment_id. Aucun second annuaire ni réseau inventé.

```python
generate_dns(seed, environment_id, server, clients, resources, now) -> dict
validate_dns(service) -> None
resolve(service, client_id, query, context, now) -> dict
apply_operation(service, operation, payload, actor, now) -> dict
public_dns(service, actor) -> dict
```

`server` : `{id, name, ip, zone}`. Zone fournie explicitement, par exemple `agence.test` ; aucune requête réelle vers ce domaine. `clients` : liste `{id, name, dns_server_ip, search_suffix}`. `resources` : liste `{id, dns_name, ipv4, ipv6?}` ; ipv4 peut être null pour une ressource IPv6 seulement. Pas d'adresse inventée, ni d'enregistrement AAAA sans IPv6 fournie. Les noms et adresses existants sont conservés.

`generate_dns` exige des configurations saines : DNS client = server.ip ; suffixe vide ou égal à la zone. La génération peut ajouter des alias déterministes à des ressources fournies. Une zone et les mêmes ressources ne doivent pas conduire à des noms fixes R1/SRV1 sans rapport avec l'environnement.

État JSON : `schema_version=1`, `environment_id`, `server`, `clients` indexés par ID, `records` indexés par ID, `service_status` (running/stopped), `transport_allowed` (booléen de politique simulée), `negative_ttl` (secondes), `cache` indexé par client puis clé de requête, `revision`, `audit`.

Record : `{id, name, type: A|AAAA|CNAME, value, ttl, enabled}`. ID stable après modification. TTL entier strict >=0, borne 86400 pour ce modèle. Un seul record actif par nom/type ; un CNAME actif exclut tout A/AAAA actif au même nom. A et AAAA peuvent coexister. Une cible CNAME absente ou un cycle sont des états valides pour créer des pannes ; ils sont détectés lors de la résolution. Tous les noms et cibles sont dans la zone gérée v1 ; un alias externe est hors périmètre et refusé.

Valider structure et références, IDs non vides, booléens stricts, entiers (pas bool), horodatages finis, adresses avec ipaddress, absence de doublons après normalisation. Limites : 100 clients, 1000 records, 200 entrées de cache par client. Une insertion au-delà du cache évince la plus ancienne `cached_at` (clé lexicale pour départager), pas une exception sur une requête normale.

Seed dédiée SHA-256 de `str(seed)+':dns:v1'`, random.Random local, jamais hash() Python ou RNG global. Aucun appel caché à l'horloge. Même seed et entrées et now => état identique, sain et sans panne aléatoire. Donner le schéma exact et les fonctions dans la doc de livraison.

## 4. Requête, normalisation et résultat

`query` : `{name, type: A|AAAA|CNAME}`. Les noms DNS de cette v1 sont ASCII, labels hostname de 1 à 63 caractères, lettres/chiffres/tiret, sans tiret initial/final ; FQDN max 253 caractères sans point final. Casse ignorée, point final optionnel. Pas d'underscore, joker, URL, espace ou chemin UNC. C'est un sous-ensemble hostname déclaré, pas une règle universelle DNS.

Un nom sans point reçoit le search_suffix client s'il est non vide ; sinon INVALID_NAME. Un nom avec point est considéré complet : pas de liste de suffixes ou tentative implicite supplémentaire. Normaliser avant recherche et cache. Une requête hors zone retourne REFUSED avec `status=failed`, pas NXDOMAIN ; aucune résolution Internet réelle.

`resolve` retourne toujours `{service: copie, result}`. Résultat :

```text
status = resolved|failed|unknown
code, dns_rcode = NOERROR|NXDOMAIN|SERVFAIL|REFUSED|null
canonical_name, query_type, answers = [{name,type,value,ttl_remaining}]
addresses = [adresses finales], cname_chain = [noms successifs]
cache_hit: bool, observed_at, valid_until, evidence, tree
```

NODATA est un code applicatif avec dns_rcode=NOERROR et answers vide, pas un nouveau RCODE DNS. Une réponse A erronée mais syntaxiquement valide doit rester resolved/NOERROR ; seul l'adaptateur des fichiers compare l'adresse attendue à celle reçue. Ne jamais inventer « WRONG_IP » dans le moteur DNS.

Pour CNAME demandé directement, retourner l'alias sans poursuivre vers une adresse. A/AAAA suivent la chaîne vers le type demandé. Détecter boucle et profondeur >8 => CNAME_LOOP/CNAME_DEPTH, SERVFAIL. Nom absent => NXDOMAIN ; nom présent mais type absent => NODATA. La définition v1 d'un nom présent se limite à au moins un record actif à ce nom ; n'émule pas les nœuds vides DNS.

Erreurs de structure d'entrée : ValueError avec code stable documenté. Erreurs et refus ordinaires : résultat sans exception. Requête inconnue d'un autre client/environnement : INVALID_CONTEXT, aucun cache lu ou modifié.

## 5. Preuves de réseau et ordre d'évaluation

`context`, fourni par le serveur web seulement :

```text
environment_id, source_device_id, target_device_id
network = {status: up|down|unknown, source_device_id, target_device_id,
           target_ip, observed_at, valid_until,
           evidence: dns_proxy|icmp_proxy}
```

source_device_id doit être client_id connu ; target_device_id doit être server.id. Une preuve réseau n'est utilisable que pour cette paire ET target_ip égal à l'adresse DNS configurée du client (qui doit correspondre à server.ip pour interroger ce serveur v1). Preuve future/périmée/incomplète/incohérente => OBSERVATION_UNKNOWN. Une preuve down fraîche => NETWORK_DOWN. Exiger observed_at <= now <= valid_until et valid_until >= observed_at. Valider now fini avant tout calcul.

Ordre pédagogique : périmètre et requête, cache valide, configuration du résolveur si cache absent, réseau, politique de transport simulée, service, enregistrements/chaîne. Un cache valide peut fonctionner sans joindre le serveur, même service arrêté ou DNS client désormais incorrect ; c'est un point d'entraînement voulu. La portée client/environnement reste impérative avant tout accès au cache. Changer le DNS client ne vide donc pas le cache automatiquement.

Sans cache : DNS client null => DNS_NOT_CONFIGURED ; adresse DNS différente du serveur modélisé => DNS_SERVER_UNMODELED avec status=unknown. Ne pas affirmer que cette autre adresse ne répond pas : notre moteur ne la modélise pas. Transport simulé bloqué => DNS_TRANSPORT_BLOCKED ; service stopped => DNS_SERVICE_STOPPED. Aucune de ces erreurs ne produit NXDOMAIN ou une entrée négative. Aucun temps d'attente réel ni sleep.

Arbre `{stage,label,status: passed|failed|unknown|blocked,children:[]}`. Après un échec/inconnu, étages dépendants blocked, jamais failed ou validés par défaut. Sur cache_hit, utiliser une branche cache et marquer les étapes serveur non consultées comme blocked avec un libellé explicite « non nécessaire : réponse en cache ». La réponse globale peut néanmoins être resolved. Documenter ce choix : une chaîne stricte all(passed) ne convient pas à cette branche.

Evidence : `simulated_dns` avec `transport_evidence` provenant de la preuve en cas de consultation ; `simulated_cache` sur cache, conserver la provenance initiale. Aucun résultat prétendument reçu du DNS Packet Tracer. Le pont apportera la connectivité seulement ; les réponses viennent de ce moteur.

## 6. Cache et mutations

Clé v1 : nom normalisé + type demandé, séparée par client et environnement. Pour simplifier, le cache NXDOMAIN est également par type demandé ; documenter que la RFC permet une portée plus large par nom. Pas de cache serveur récursif, seulement le cache client pédagogique. TTL négatif : negative_ttl configurable (pas de calcul SOA v1).

Entrée : résultat public immuable de la requête, `cached_at`, `expires_at`, provenance. Valide uniquement si cached_at <= now < expires_at. Au moment exact expires_at, reconsulter le serveur. TTL=0 : réponse utilisable dans cet appel mais non stockée. Sur hit, recalculer ttl_remaining=max(0,expires_at-now), ne pas repousser expires_at. Pour une chaîne CNAME, la réponse simplifiée expire au minimum des TTL de toute la chaîne suivie. Cela évite de retenir un alias au-delà de son TTL ; documenter que c'est un cache de résultat complet, pas de RRsets indépendants.

Mettre en cache les succès et NXDOMAIN/NODATA avec TTL positif. Pas de mise en cache SERVFAIL/refus réseau/politique/unknown dans cette v1 ; cette simplification ne prétend pas couvrir les RFC plus récentes de cache d'échecs. Réparer un record NE purge PAS les caches : ancienne réponse ou réponse négative continue jusqu'à expiration ou flush explicite. Réduire le TTL d'un record ne raccourcit pas un ancien cache.

Chaque appel travaille sur une copie profonde ; résolution sans nouveau cache/éviction ne modifie ni revision ni audit. Insertion/éviction de cache : revision+1 pour cet appel. Audit de cache minimal sans credentials ; choix à documenter, pas de secrets dans les données DNS. Retour refusé : état inchangé (ne pas supprimer même un cache expiré à cette occasion). Ne lire/écrire aucun fichier, le contrôleur gérera verrou et sauvegarde atomique.

`apply_operation` accepte acteur serveur `{id,environment_id,permissions}`. Opérations administratives exigent `dns.manage` : upsert_record (création ou mise à jour via record_id), delete_record, set_record_enabled, set_service_status, set_transport_allowed, set_negative_ttl, set_client_dns. Payloads explicitement autorisés, pas de mutation arbitraire de revision/audit/cache/server.id.

flush_cache(client_id) : soit admin dns.manage, soit acteur du poste avec capacité `dns.flush_own`, `device_id==client_id` et même environnement. Impossible de vider le cache d'un autre poste avec cette capacité. Réussite : copie, revision+1, audit ; échec aucun effet. Tous les retours de mutations : `{service:copie,result}`.

`public_dns(service,actor)` exige dns.manage et même environnement ; expose configuration, records et compte d'entrées de cache par client, sans objets de contexte/authentification. La projection pour une requête utilisateur est son résultat, pas le catalogue des enregistrements.

## 7. Tests d'acceptation

Un ou plusieurs tests significatifs par point, avec entrée immuable après refus et succès :

1. Reproductibilité, seed dédiée, RNG global préservé ; ressources/adresses fournies conservées ; génération saine.
2. server.id indépendant de environment_id ; mauvais environnement/client/target refusé AVANT cache.
3. Noms sans casse/point final équivalents ; suffixe court déterministe ; noms invalides, type inconnu et hors zone.
4. A valide IPv4 ; AAAA valide IPv6 ; mauvaise famille refusée ; pas de AAAA inventé.
5. NXDOMAIN vs NODATA/NOERROR ; record désactivé ; A et AAAA au même nom ; conflit CNAME/A refusé.
6. CNAME direct ; chaîne A/AAAA ; alias cible absente ; boucle ; profondeur 8 permise/9 refusée selon définition documentée.
7. Résolution vers adresse incorrecte pour l'exercice reste un succès DNS, sans mutation de l'adresse.
8. DNS absent ; serveur non modélisé unknown ; adresse de preuve différente du DNS configuré ; paire erronée.
9. Network down vs unknown ; preuve expirée/future/absente et bornes temporelles exactes.
10. Blocage politique/service arrêtés sans faux NXDOMAIN ni cache négatif.
11. Hit positif sans réseau ; DNS client changé/service arrêté ne détruit pas une réponse déjà valide.
12. Cache isolé entre clients et environnements ; same-name A et AAAA séparés.
13. TTL=0 non caché ; expiration exacte ; hit ne prolonge pas l'entrée ; minimum TTL CNAME.
14. Record corrigé mais cache ancien conservé jusqu'à TTL/flush ; réduire TTL ne raccourcit pas l'ancien cache.
15. Cache négatif NXDOMAIN et NODATA ; ajout d'un record pas immédiatement visible ; expiration/flush répare.
16. Erreurs réseau et SERVFAIL non cachées ; refus n'efface pas un ancien cache expiré.
17. Capacités d'admin ; flush_own limité à son poste ; mauvais environnement refusé ; champs non autorisés.
18. IDs stables sur update ; validation des types/références/timestamps ; JSON aller-retour.
19. Revision exacte et audit ; éviction borne du cache déterministe ; aucun IO/réseau/horloge cachée.
20. Arbre complet et blocked après échec ; branche cache n'affirme pas une consultation du serveur.
21. Projection admin protégée ; résultat client ne contient pas tout le catalogue ; provenance simulation explicite.
22. Réparer une entrée ne modifie ni autres records, ni clients, ni caches étrangers.
23. Exemple minimal de doc réellement exécuté ; tableau erreurs, limites et critère→test.

Exécuter les tests moteur, la suite web complète et les suites requises par CLAUDE.md avant chaque commit. Aucune modification des tests existants. Fournir les résultats exacts et le SHA de livraison.

## 8. Intégration réservée et futurs tickets

L'intégratrice réalise la migration sauvegardée, la création du contexte PT, les routes, la console DNS OS.js et le diagnostic type nslookup simulé. Elle raccorde la résolution aux chemins UNC et conserve l'accès par IP sans dépendance DNS. Une résolution réussie ne valide pas SMB : l'adaptateur doit ensuite vérifier adresse attendue, réseau vers la cible et permissions avec sim_files.

Pannes futures : record supprimé, adresse A erronée, alias cassé, cache ancien, mauvaise configuration DNS du client, service DNS arrêté. Les tickets décrivent les symptômes, pas la cause. Ne pas générer ces tickets ou intégrer les autres services pendant cette mission.

Livrer les trois fichiers uniquement et signaler toute ambiguïté résolue. Ne pas substituer une nouvelle architecture sans l'expliquer dans la documentation.
