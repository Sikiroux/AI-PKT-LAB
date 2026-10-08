# v0.47.3 — recette unifiée et contrôles séparés

## Changements

`python tests/run_tests.py` lance les tests du lanceur, le cœur Packet Tracer, les ateliers, les tests Python web et tous les tests JavaScript web, dans des processus séparés. Node.js est requis ; son absence est un échec explicite. Une suite en échec ne masque pas les suites suivantes et le résultat final reste non nul.

Le dossier de travail ne contient déjà plus les copies racine `tickets.html`, `desktop.html` et `workspace.html` citées par l'audit. Le ZIP v0.47.2 les contient encore : elles sont exclues du paquet v0.47.3. Les routes actives utilisent `web/`. Les autres fichiers historiques ne sont pas supprimés par ce bloc.

`CLAUDE.md` décrit désormais aussi le service desk simulé. Les règles de validation réelle dans PT 9, l'absence de dépendances Python et le périmètre sans VM, Windows Server ou Docker sont conservés.

Dans une fiche ticket, les résultats automatiques sont regroupés dans un volet repliable **Contrôles pédagogiques**. Leur état reste indiqué sur le volet. La validation et les preuves ne changent pas. L'ouverture du volet est mémorisée pendant la navigation dans la session web, comme les autres panneaux.

L'application FTP propose une aide de connexion. Les identifiants de formation par défaut sont une référence : ils ne prouvent pas l'état actuel d'un compte et ne sont pas saisis automatiquement. Un refus d'authentification peut avoir plusieurs causes.

## Limites

Ce bloc ne transforme pas encore l'interface en console GLPI et ne crée ni nouveaux statuts métier, ni suivis, ni attribution. La refonte du nommage et du placement reste à réaliser, puis l'extension des entreprises. La roadmap distingue ces objectifs des fonctionnalités livrées.

## Vérifications manuelles

- Ouvrir une fiche après un contrôle : le volet affiche son état ; le déplier montre les mêmes résultats et détails.
- Naviguer vers un autre ticket puis revenir : le panneau garde son ouverture pour le ticket concerné.
- Dans FTP, ouvrir l'aide sans se connecter ; consulter les explications sans changement du compte ni saisie automatique du mot de passe.
- Les tests automatisés ne certifient pas le comportement du pont, ni celui du réseau dans Packet Tracer 9.
