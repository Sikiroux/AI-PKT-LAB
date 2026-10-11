# v0.63 — Réseau entreprise V2

## Périmètre

Nouvelles entreprises de trente employés seulement. Le générateur de labs/ateliers conserve ses modèles pédagogiques et le placement commun livré en v0.62.8. Les sauvegardes existantes ne sont pas modifiées.

| VLAN | Usage | Raccordement routeur |
|---|---|---|
| 10 | Comptabilité, Commercial, Accueil, Opérations et imprimante | G0/0.10 |
| 15 | RH et Direction, postes 11 à 20 | G0/0.15 |
| 20 | Serveurs | G0/1.20 |
| 40 | Visiteur / emplacement extérieur simulé du technicien | G0/2.40 |
| 99 | Administration des switches employés et portable IT au bureau | G0/0.99 |

Les départements restent des groupes métier ; les deux switches utilisateurs représentent des zones physiques, pas un switch obligatoire par département. Leurs ports FastEthernet0/24 transportent les VLAN 10, 15 et 99. Les liaisons vers le routeur utilisent GigabitEthernet0/1 côté switch. Les ports FastEthernet0/20 restent réservés au déplacement du portable : VLAN 99 au bureau, 20 en salle serveurs, 40 à l’extérieur.

Le routage entre VLAN est autorisé : la segmentation sépare les domaines de diffusion, **pas une politique de sécurité**. Il n’y a pas encore d’ACL visiteurs. « Extérieur » reste un réseau pédagogique, pas Internet ni un véritable tunnel VPN.

Chaque VLAN a un /24 privé distinct, issu de la seed. Serveurs et imprimante conservent leurs adresses de référence ; les postes sensibles et le portable sont réadressés dans leur VLAN. Le manifeste utilise les valeurs inscrites dans le XML. Running-config et startup-config sont identiques.

## DHCP : infrastructure prête, postes encore statiques

Le serveur infrastructure contient quatre pools (utilisateurs, sensibles, visiteurs, administration), avec relais sur les sous-interfaces correspondantes. Les plages .150 à .199 ne chevauchent aucune adresse statique générée. Le suivi des baux observés n’est pas implémenté : ne pas annoncer une entreprise dynamique, ni basculer les postes en DHCP en supposant que le simulateur suivra automatiquement leur nouvelle IP.

## Recette Packet Tracer 9 — à effectuer avant validation réelle

Ouvrir le spécimen `entreprise.pkt`, seed `reseau-v063`, sans panne initiale.

1. Sur chaque switch : `show vlan brief` puis `show interfaces trunk`. Contrôler les VLAN des ports et la liaison entre les deux switches utilisateurs.
2. Sur le routeur : `show ip interface brief` et `show ip route`. Cinq sous-interfaces et cinq réseaux connectés doivent apparaître après convergence.
3. Depuis un poste utilisateurs et un poste RH : ping leur passerelle puis le serveur fichiers. Un succès ICMP ne prouve pas l’accès aux fichiers simulés.
4. Dans l’application : vérifier l’annuaire, les fichiers et une prise en main ; déplacer le portable dans les trois emplacements et vérifier son adressage.
5. Enregistrer dans PT, fermer/réouvrir le fichier, refaire les contrôles.
6. Sur une copie : passer un poste en DHCP, vérifier .150-.199, passerelle et DNS. Ceci valide le pool dans PT, pas le suivi dynamique dans notre application.

Les tests Python contrôlent la cohérence des IP, la configuration des ports/trunks, les plages DHCP et l’intégration du manifeste. Ils ne démontrent pas que PT9 importe correctement les nouvelles sous-interfaces et VLAN.

Référence IOS : [Cisco, routage inter-VLAN avec routeur externe](https://www.cisco.com/c/en/us/support/docs/lan-switching/inter-vlan-routing/14976-50.html). La documentation IOS ne remplace pas la recette PT9.

## Suite

Après recette réelle : suivi des baux, Wi-Fi testé, incidents réseau liés à l’état de l’entreprise et signalements après apparition de la panne. Aucune nouvelle panne n’est injectée par cette version.
