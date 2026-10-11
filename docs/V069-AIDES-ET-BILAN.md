# v0.69 — Aides, corrections et bilan

## Aides

Dans la fiche ticket → Contrôles et aide, les trois indices conservent une progression observer / diagnostiquer / retester. Ils citent le poste et, si ces champs existent, la ressource et le résultat attendu. Leur consultation est maintenant explicite et enregistrée. Les demandes en attente doivent d’abord être préparées.

## Réponses aux tickets difficiles

« Correction et bilan pédagogique » propose « Voir la correction de ce ticket » pour les tickets de bureau préparés. Une confirmation demande de révéler la cause et la marche à suivre. La correction décrit la panne initialement injectée et le poste cible ; elle indique l’intervention et les tests à refaire. Elle couvre toutes les causes du catalogue d’incidents actuels : compte désactivé, mauvais résolveur, lecteur réseau, application absente, impression, service FTP et accessoires.

Aucune commande réseau, ping ou réparation n’est exécuté par cette consultation. Le ticket n’est pas validé et son statut reste inchangé. La correction ne prétend pas expliquer d’autres changements intervenus après l’injection.

Les scénarios actifs AD, fichiers, DNS et multi-services disposent aussi d’une correction quand leur identifiant et leur poste correspondent encore à l’état privé enregistré. Chaque couche est expliquée séparément ; une injection réseau non confirmée ne fournit pas de correction. Les anciens tickets dont cet état a été remplacé ne reçoivent pas de réponse inventée. Les labs conservent leur correction dans la feuille d’intervention. Les anciennes variantes impression/FTP partiellement couvertes et les demandes d’arrivée restent à étendre.

## Bilan et export

Le bilan affiche la clôture enregistrée ou son absence, les indices et la correction consultés. Un export HTML rassemble les interventions de la session, leur poste, domaine travaillé, dernier contrôle enregistré, résultats, notes et texte de résolution du technicien. Le document est imprimable depuis le navigateur. Les textes sont échappés ; aucun diagnostic privé ni état complet du serveur n’est exporté.

Ce bilan décrit l’historique, pas une certification de compétence ni une nouvelle vérification de Packet Tracer. Les contrôles sont ceux enregistrés au moment de l’intervention. Les tests manuels restent distingués. Aucun score arbitraire ne pénalise l’utilisation d’une aide.

## Persistance

Les consultations sont sauvegardées dans le ticket et recopiées dans son événement d’entreprise pour sa récupération. Les contrôles de cible et d’environnement continuent de s’appliquer. Un événement non signalé ou destiné à un autre poste ne peut pas fournir de correction.

## Recette Windows/PT9

1. Prendre un incident puis consulter un indice : celui-ci demeure consulté après actualisation/reprise.
2. Annuler la confirmation de correction : aucun contenu de correction n’apparaît.
3. Révéler la correction : vérifier la cause, le poste et la procédure ; constater que rien n’est réparé automatiquement.
4. Réparer et retester : les contrôles ordinaires restent nécessaires avant résolution et clôture.
5. Exporter le bilan : vérifier les textes, les contrôles, les aides et l’impression du HTML.
6. Consulter un ancien scénario : absence de correction détaillée annoncée sans bloquer le ticket.

Les tests automatisés couvrent la non-modification, la persistance, le ciblage, toutes les causes actuelles, l’échappement de l’export et les actions d’interface. Ils ne remplacent pas cette recette réelle.
