# v0.100 — Consolidation des chantiers 1 à 4

## 1. Fiabilité du parcours

Les opérations d’impression, de partage, de configuration FTP et de paramètres distinguent désormais la réussite de la mutation de la réussite de sa relecture. Une relecture indisponible affiche explicitement que la modification est enregistrée. Elle invalide les données de la console plutôt que de permettre une nouvelle intervention sur un ancien état. Les transferts FTP conservent leur résultat confirmé et avertissent si la liste ne peut pas être actualisée. Aucun nouvel envoi automatique n’est ajouté.

## 2. Confort et cohérence des consoles

Les consoles Partages, DNS et Serveur FTP mémorisent leur rubrique dans le même onglet, pour le même environnement et poste. Flèches, Début et Fin changent de rubrique. La navigation est bloquée pendant une opération ; le contenu de la console devient inerte. Les Paramètres mémorisent aussi leur rubrique avec la même navigation.

Les travaux d’impression se sélectionnent au clavier, avec une sélection bleue visible. Les filtres et recherches de chaque file sont conservés à sa réouverture. Les boutons d’annulation restent explicites et demandent confirmation. Dans FTP, les flèches, Début et Fin sélectionnent un fichier et déplacent le focus ; elles ne lancent pas de transfert. Les mots de passe et les brouillons ne sont pas mémorisés par ces préférences.

## 3. Aides

Deux articles recherchables dans Documentation : « Méthode : isoler la panne et vérifier la réparation » et « Réseau : lire, comparer, puis mesurer ». Ils structurent la qualification, les branches de diagnostic, les mesures avant/après et la vérification. Ils distinguent les étapes de chaque usage et ne révèlent pas la cause du ticket actif.

## 4. Preuves réseau

Une interface non lisible, une identité remplacée ou ambiguë donne une preuve de configuration inconnue, jamais une réparation validée. La comparaison IPv4 refuse les doublons de nom, d’identité ou de port. Les tests couvrent ces cas ainsi que les cycles de panne et réparation déjà présents.

Cette livraison n’ajoute pas encore de panne port/VLAN/DHCP aux arrivées de l’entreprise. Le catalogue reste adresse IPv4 et masque incorrects. Les quatre chantiers ont progressé ; ils ne sont pas déclarés achevés. Security Simulator reste différé.

## Recette à effectuer

La recette visuelle Chrome et les essais avec le pont réel Packet Tracer 9 restent ouverts. Les tests utilisent un DOM simulé et un pont simulé ; ils ne prouvent pas le rendu ni le fonctionnement dans Packet Tracer réel. Le bureau bleu est conservé, sans refonte de sa palette.

1. Recevoir une demande, la prendre en charge, dialoguer et consulter la documentation.
2. Aller au poste concerné, inspecter la console, modifier une seule cause justifiée, reproduire l’usage.
3. Interrompre le pont après une mutation : vérifier le message de succès avec actualisation indisponible, sans répétition automatique.
4. Reprendre le pont, actualiser, vérifier puis clôturer ; contrôler le compte rendu et l’isolation entre entreprises.
5. Vérifier visuellement les sélections et le focus au clavier, les petits écrans et les fenêtres multiples.

## Vérifications automatisées

- 54 suites JavaScript réussies, dont les régressions de navigation, de mémorisation et de succès suivi d’une relecture indisponible.
- 856 tests Python réussis en 142,705 secondes, dont 13 tests ciblant les incidents réseau de l’entreprise.
- Archive vérifiée : intégrité ZIP et correspondance des fichiers livrés avec les sources.
