# v0.36 — Demande de déploiement liée à l’atelier

Dans **Tickets**, choisir le catalogue Applications, puis **Déploiement · disque d’atelier** et une durée (0 = libre). Le ticket décrit le poste d’atelier, l’image, la région, le clavier et le compte demandés. Dans le bureau du technicien, ouvrir **Déploiement**, réaliser l’atelier, puis vérifier et clôturer le ticket.

La demande appartient à l’entreprise active et conserve le fonctionnement des timers et du journal. Le poste cible affiché est le poste d’atelier, pas le client distant. Les options d’arrivées automatiques peuvent également cibler explicitement Déploiement. Le choix aléatoire Applications reste réservé aux familles existantes poste, impression et FTP pour éviter de mélanger sans choix explicite un atelier et un dépannage.

La génération dérive une seed de la seed de l’entreprise et du numéro d’intervention. Les demandes successives varient de façon reproductible. Recommencer conserve la seed, le poste et la consigne du ticket ; les révisions restent croissantes, ce qui bloque les actions d’une ancienne fenêtre.

## Validation

Aucun point pour l’état initial. L’installation doit être terminée sur le poste cible avec image, sauvegarde, GPT, partition Windows, région, clavier et compte conformes. Une seconde vérification compare les appareils, l’annuaire, le partage et les autres services avec le début de la demande. La clôture suit les contrôles existants des tickets entreprise.

Il s’agit toujours d’un disque virtuel de formation, pas d’un déploiement Windows réel ni d’un nouveau PC Packet Tracer. Le ticket le précise explicitement. La préparation n’altère ni la session distante ni le client. Un incident déjà actif doit être terminé avant une nouvelle demande. La console de déploiement reprend la progression sauvegardée.

Tests : génération reproductible, protection de l’environnement, validation négative et positive, mauvais poste/image, révision, reprise de consigne après reset, dialogues. Les tests automatiques ne valident pas le rendu dans le navigateur ou une installation Windows réelle.
