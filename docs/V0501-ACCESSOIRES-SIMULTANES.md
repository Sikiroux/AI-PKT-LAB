# v0.50.1 — Accessoires dans les incidents simultanés

## Livraison

Les entreprises à 30 employés peuvent maintenant recevoir des tickets d’écran, clavier et souris dans le nouveau moteur. La panne est présente avant le signalement, le poste concerné est nommé, et sa prise en charge ne modifie pas les autres incidents. Les tirages aléatoires et le catalogue Applications incluent cette famille.

Neuf causes : écran éteint, câble vidéo débranché, mauvaise entrée vidéo, écran défectueux ; clavier débranché ou défectueux ; souris débranchée, défectueuse ou absente. Le symptôme décrit l’accessoire, pas la cause cachée. L’activité locale est signalée comme bloquée tant que les accessoires restent indisponibles.

## Intervention

Ouvrir **Fiches des postes**, sélectionner le poste du ticket, puis **Équipement local**. L’application affiche l’aperçu de l’écran et trois cartes matériel avec état, commandes et stock de remplacement. Les actions conservent le contrôle du numéro de série et de la révision.

Brancher le câble, allumer l’écran, sélectionner HDMI, ou installer un accessoire sain selon le diagnostic. Un appareil défectueux doit être remplacé ; ajouter au stock simulé puis installer permet de le faire. L’ancien matériel reste au stock. Cette intervention représente une action sur place, pas une réparation par RDP.

## Vérification

La vérification et la clôture demandent que les trois accessoires externes du poste soient opérationnels. **Aucun ping ni fast forward n’est lancé** : l’état local simulé suffit pour ce type de ticket. Une panne d’écran ne coupe pas le réseau et n’interrompt pas la prise en main distante. Une preuve réseau positive ne valide pas un clavier cassé.

Les contrôles refusent un équipement absent ou appartenant à un autre environnement. Les incidents AD, fichiers, DNS, impression et FTP continuent d’utiliser leurs contrôles propres. Une panne matérielle sur un second poste ne réinitialise pas le compte AD d’un premier poste.

## Limites

Il s’agit d’accessoires externes simulés, pas des composants internes d’un portable. HDMI est le raccordement vidéo attendu dans cette version. Le nouveau moteur ne compare pas toute l’entreprise à un instantané ancien : cette comparaison rejetterait à tort les autres pannes et réparations simultanées. Les mutations ciblent uniquement l’accessoire choisi.

La préparation de poste et le déploiement restent hors du catalogue simultané, dans leurs moteurs historiques. Les anciennes sauvegardes utilisent toujours leur mode de fonctionnement historique. Cette livraison ne change pas la taille des réseaux.

## Recette manuelle

1. Sur une entreprise v0.50, recevoir un ticket Accessoires en ciblant un poste.
2. Vérifier que son équipement est déjà perturbé avant la prise en charge.
3. Prendre en charge ; vérifier que Packet Tracer n’ouvre pas de console ni de ping.
4. Réparer depuis Équipement local puis vérifier et clôturer le ticket.
5. Conserver un incident AD sur un autre poste pendant cette intervention : il doit rester ouvert et son compte désactivé.
6. Tester la prise en main distante pendant une panne d’écran : elle ne doit pas être coupée à cause de l’accessoire.

Les tests automatiques couvrent les neuf causes et la séparation entre matériel, réseau et incidents parallèles. Le rendu graphique et le parcours complet sur Windows restent à tester par Damien.
