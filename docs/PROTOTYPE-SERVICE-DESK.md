# Service desk procédural — contrat du prototype

Base : `codex/web-v014-naming-physical`, commit `d79e683799f0cb7301d10ad5d495d7b7d7df11ec`.
Branche dédiée : `codex/procedural-service-desk-prototype`.

## Décisions et périmètre

Seed + version + options -> description commune -> réseau Packet Tracer et environnement web. Préserver le générateur, les tickets et le pont existants. Les nouvelles simulations web sont demandées par Damien et étendent le périmètre historique de CLAUDE.md ; aucun déploiement de VM Windows Server ou AD réel n'est prévu.

Le prototype fonctionne séparément de l'interface actuelle. Il utilise le générateur d'entreprise existant, avec postes supplémentaires et services existants ; il n'est pas encore une topologie minimale à deux appareils. Il garde un poste technicien dédié pour ce premier scénario ; cette contrainte ne s'applique pas à toutes les futures entreprises.

## Modèle commun

`workspace_model.generate(seed)` fournit site, demandeur, famille IP privée et seed réseau. Les tirages entreprise/réseau sont séparés pour éviter qu'une nouvelle variante de texte change toutes les adresses.
`workspace_network.build` génère le XML existant, applique les noms par site, attribue des numéros de série uniques, puis crée les .pkt initial et sain. Le manifeste contient roles client/technician/server, identifiants stables, noms, IP et séries.
Les noms peuvent changer : les séries servent à retrouver les appareils dans les observations. Un remplacement ou une série dupliquée est refusé. Le fichier ouvert doit correspondre au fichier de travail enregistré.
La seed et la version reproduisent les valeurs pédagogiques ; les octets du .pkt ne sont pas garantis identiques, certaines références internes du générateur étant variables.

## Arbres de prérequis

Chaque action possède ses dépendances ; une liste imbriquée les affiche. La prise en main et la lecture/écriture du partage sont des branches distinctes. Un étage positif autorise l'évaluation du suivant ; un étage négatif ou inconnu bloque les descendants dépendants.

Résultats : passed, failed, unknown, blocked. unknown indique une preuve réseau absente ou périmée ; blocked indique que la vérification n'a pas été effectuée. Ne pas transformer les descendants bloqués en échecs observés.
Les causes et permissions sont des propriétés internes ; les capacités sont calculées à partir d'elles et de la connectivité. Ne pas stocker des capacités indépendantes contradictoires. Les futures règles seront contextualisées par utilisateur, poste, destination, ressource et action.

Dans ce prototype : preuve ICMP fraîche -> service actif -> compte actif -> permission de lecture ou écriture. L'approximation ICMP est explicite, ce n'est pas un test de port RDP/SMB. La prise en main vérifie technicien→client ; le partage vérifie client→serveur. Ces deux chemins restent indépendants.

## Pont et sauvegarde

Réutiliser Engine.snapshot et Engine.ping, ainsi que le verrou existant. Une boucle attend la fin du contrôle avant de programmer le suivant dix secondes plus tard. Elle saute un contrôle si une action possède déjà le verrou. Les observations expirent après 45 secondes. Une perte du pont produit unknown, jamais un faux diagnostic de panne.
Le ping demandé par le bureau s'exécute sur le poste client PT vers une IP validée. Aucun ping réel de la machine hôte n'est utilisé.
Sauvegarder le manifeste et les permissions. À la reprise, invalider les observations et la session distante. Réinitialiser l'exercice est une action explicite qui remplace les fichiers de travail.

## Périmètre pédagogique

Ticket : dossier Documents inaccessible. Causes initiales : câble client absent dans PT et lecture refusée dans le web. Réparer le réseau ne répare pas les permissions. Accorder la lecture ne donne pas automatiquement l'écriture.
La correction réseau est référence.pkt. La validation du ticket exige lecture et preuve récente. Les causes sont décrites dans la documentation de correction, pas automatiquement dévoilées dans le ticket.
Le bureau HTML est provisoire ; OS.js et inkjs restent à intégrer. Aucun code du dépôt sans licence it-support-simulator n'a été repris.

## Documentation des services

Prendre les documentations officielles comme référence des comportements, étapes et erreurs ; écrire nos propres textes et écrans. Chaque fiche indique sources, objectif, opérations prises en charge, dépendances, mutations et limites. Ne pas annoncer un Windows/AD complet.

Partages : https://learn.microsoft.com/fr-fr/windows-server/storage/file-server/file-server-smb-overview
Autorisations : https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/access-control
Diagnostic : https://learn.microsoft.com/fr-fr/troubleshoot/windows-client/networking/access-denied-access-smb-file-share
OS.js : https://manual.os-js.org/tutorial/application/ et https://manual.os-js.org/guide/provider/
Dialogues : https://github.com/y-lohse/inkjs

## Répartition entre IA proposée

1. Coordination : contrat, seed, état commun, pont, intégration et revue.
2. Bureau : essai OS.js, puis fenêtres terminal/explorateur utilisant le contrat commun, sans état métier parallèle.
3. Comportements : fiches officielles, règles de comptes/permissions et dialogues inkjs alimentés par les faits du générateur.

Pour chaque lot : fichiers possédés, branche, entrée/sortie, tests et statut. Les modifications au schéma partagé passent par la coordination. Ne pas fusionner des modules concurrents sans tests d'intégration. Cette répartition est un plan ; aucune autre IA n'est présentée comme ayant déjà effectué ces intégrations.

## Suite

Tester l'ouverture et le scénario dans PT 9 ; intégrer OS.js après un essai d'installation ; compléter les preuves ICMP par des contrôles adaptés aux services ; ajouter rôles/authentification, groupes et permissions de ressources ; dialogues ; puis stocks et déploiement. La topologie web modifiable et le mode invisible restent hors de ce prototype.
