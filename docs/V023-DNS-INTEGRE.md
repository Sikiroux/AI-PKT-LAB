# v0.23 — DNS intégré au bureau et aux tickets

Le moteur de la branche `codex/dns-simulation-engine` est raccordé à l’environnement existant. Il n’ajoute pas de second réseau Packet Tracer. Le serveur de cet environnement héberge logiquement la zone interne simulée ; les noms et adresses proviennent du réseau et de l’annuaire générés.

## Utilisation

1. Reprendre ou créer un environnement, ouvrir son réseau Packet Tracer et vérifier sa connectivité.
2. Ouvrir le bureau du technicien puis l’icône **DNS**.
3. Saisir un nom court ou complet, choisir A/AAAA/CNAME, puis Résoudre. Le résultat indique le code, les adresses, l’usage du cache et les étapes de diagnostic.
4. La console du technicien permet d’ajouter/modifier/supprimer un enregistrement, de démarrer/arrêter DNS, de bloquer/autoriser son transport et de configurer le résolveur du client. Un accès récent du technicien au serveur est requis pour administrer.
5. Le poste client possède aussi un bouton DNS pour résoudre depuis ce poste et vider son propre cache. Le cache du technicien est distinct. Les noms du poste client se testent donc depuis sa session distante.

Le cache est sauvegardé dans `session.json`. Une réponse valide en cache peut fonctionner sans accès au serveur DNS. Une modification d’enregistrement ne vide pas automatiquement les caches. Les résolutions de contrôle du correcteur n’ajoutent pas d’entrée en cache ; les résolutions explicitement demandées dans la console le font.

## Tickets procéduraux

**Nouvel incident DNS** couvre sept familles, mélangées par seed sans répétition au cours d’un cycle : mauvais résolveur client, entrée désactivée, mauvaise adresse, service arrêté, transport bloqué, cache négatif, ancienne adresse en cache.

Cette action prépare le compte et le droit de lecture du demandeur, puis injecte l’incident. Elle ferme la session distante et invalide l’authentification. Les autres exercices sont bloqués tant que l’incident courant n’a pas été vérifié comme résolu.

Le ticket exige : le nom du partage résout vers le bon serveur ; le document partagé est lisible ; les autres enregistrements, la configuration DNS du technicien et les fichiers sont préservés. Une réponse NXDOMAIN est une réponse DNS définitive mais ne permet jamais de valider l’accès aux fichiers.

Les incidents DNS imposent l’accès par nom au moteur de fichiers. Les anciens incidents de fichiers et d’annuaire conservent leur fonctionnement par IP. Les paramètres du résolveur et le pare-feu DNS de cette console sont simulés côté web, pas des changements injectés dans les paramètres DNS natifs de Packet Tracer.

## Migration et limites

Avant d’ajouter le DNS à une sauvegarde existante, une copie `session.before-dns.json` conserve les octets du fichier d’origine. La migration conserve le réseau, l’annuaire et les fichiers.

Les preuves Packet Tracer sont des observations ICMP associées au poste source et au serveur cible, avec une durée de validité. Elles ne prouvent pas un échange DNS UDP/TCP 53 ou SMB réel. Le transport DNS et les enregistrements sont simulés. Pas de récursion Internet, MX, SRV, PTR, DNSSEC ou synchronisation avec le service DNS natif de Packet Tracer dans cette version.

À tester dans le navigateur avec Packet Tracer : reprise d’une ancienne sauvegarde, console DNS sur les deux bureaux, réparation d’un incident, cache négatif après correction puis vidage du cache client, vérification et fermeture du ticket. Les tests Python et la vérification syntaxique JavaScript ne remplacent pas ces essais.
