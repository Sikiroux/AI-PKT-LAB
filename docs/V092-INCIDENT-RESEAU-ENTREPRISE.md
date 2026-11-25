# v0.92 — Première panne réseau dans l’entreprise

## Périmètre

Une adresse IPv4 erronée sur un poste statique peut désormais être choisie dans les arrivées variées ou multi-services d’une entreprise à 30 employés. Le choix Réseau est aussi disponible dans les réglages des arrivées et dans la réception manuelle.

Le catalogue Applications n’inclut pas cette panne. Les scénarios réseau historiques restent inchangés. Un seul incident réseau de ce type peut être ouvert à la fois.

## Fonctionnement

- Le pont doit proposer les lectures, écritures et contrôles ICMP requis.
- Le poste et le serveur doivent être joignables avant injection.
- Le fichier et l’identité matérielle du poste sont contrôlés ; la carte doit être statique et modifiable par API.
- Le journal d’injection est enregistré avant modification.
- L’adresse est modifiée dans Packet Tracer. La configuration appliquée et l’effet ICMP sont contrôlés avant création du signalement.
- Si l’effet n’est pas confirmé, rétablissement des valeurs antérieures uniquement si la configuration est encore celle attendue. Une intervention concurrente n’est pas écrasée.
- Une injection incertaine ou interrompue bloque les nouvelles arrivées. Le message nomme le poste à contrôler. Après rétablissement manuel selon les références, une nouvelle tentative relit la configuration et débloque le cycle.
- La prise en charge du ticket ne déclenche pas de mutation supplémentaire.
- La vérification relit la configuration réelle, puis exploite les contrôles récents technicien → poste et poste → serveur. Aucun ping ne prouve des autorisations applicatives.

## Aides

Le Guide indique où relever IP, masque, passerelle et DNS et comment tester les trajets. La conversation du demandeur reste fondée sur le scénario et ses observations. La correction explicite explique la remise en conformité.

## Recette Packet Tracer 9 à effectuer

1. Utiliser une entreprise saine à 30 employés et son fichier de travail associé.
2. Démarrer la simulation. Dans la réception d’incident, choisir Multi-services → Réseau et un poste disponible.
3. Vérifier que le ticket correspond au poste et que les symptômes réseau existent dans Packet Tracer.
4. Depuis ce poste : Desktop → IP Configuration. Comparer les valeurs au référentiel de l’entreprise.
5. Effectuer la correction identifiée puis tester la passerelle et le serveur depuis ce poste ; tester le poste depuis le portable technicien.
6. Lancer la vérification du ticket et contrôler les trois résultats avant résolution.
7. Tester ensuite la cadence automatique avec la famille Réseau, puis revenir à un catalogue varié.

## Validation et limites

Suite Python complète passée ; neuf tests réseau ciblés couvrent injection, réparation, échec initial, identité remplacée, effet non confirmé, interruption, observation périmée et passage par le planificateur. Les tests utilisent un pont simulé : ils ne constituent pas une recette réelle dans Packet Tracer 9.

Les pannes de VLAN, trunk, DHCP et de liaisons collectives ne sont pas intégrées par cette version aux arrivées de l’entreprise.
