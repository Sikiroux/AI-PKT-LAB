# v0.50 — Entreprise de 30 employés et incidents simultanés

## Ce qui change

Une nouvelle entreprise contient **30 employés, six services de cinq personnes, 30 postes Packet Tracer câblés et 30 comptes utilisateurs distincts**. Le portable du technicien, le poste visiteur, les serveurs et l’imprimante s’ajoutent à cet effectif. Les noms des appareils restent indépendants de leur utilisateur ; les comptes et les noms de personnes sont reproductibles depuis la seed.

Deux commutateurs desservent les employés. Les adresses IPv4 et les ports sont distincts ; les raccordements du portable restent réservés. Le placement utilise le canevas 3900 × 3900 avec deux orientations déterministes. Il ne s’agit pas encore de plusieurs architectures réseau (routage/VLAN différents selon la seed).

## Une panne précède désormais son ticket

Pour ces nouvelles entreprises, la réception choisit un poste disponible, applique la panne à son état simulé, persiste l’incident, puis inscrit son signalement dans la file. **Prendre en charge ne déclenche plus la panne** et ne lance pas de ping. Deux interventions sur deux postes différents conservent leurs paramètres propres : l’une ne réinitialise pas l’autre.

Le nouveau catalogue initial contient huit causes dans cinq familles :

| Famille | Causes | Portée |
|---|---|---|
| Impression | File suspendue, spooler arrêté, mode hors connexion | Un poste |
| Poste/documents | Lecteur mal configuré, application Documents absente | Un poste |
| Annuaire | Compte désactivé | Un compte |
| DNS | Résolveur du client incorrect | Un poste |
| FTP | Service arrêté | Entreprise |

Un poste ayant un ticket non clos n’est pas sélectionné à nouveau. Le tirage aléatoire évite également la dernière personne et la dernière famille lorsque le choix reste possible. Un nouveau signalement explicite FTP est rattaché à l’incident partagé ouvert. Les arrivées aléatoires évitent de recréer cet incident partagé.

Les tickets montrent le demandeur, le poste, l’activité concernée et le nombre de personnes touchées. Une panne FTP commune est critique. La liste des postes indique l’activité bloquée, dégradée ou sans panne suivie. **Ce statut mesure l’impact des incidents simulés enregistrés ; il ne certifie pas l’accès Internet ou la productivité réelle.**

Les arrivées automatiques conservent leurs réglages de cadence, pause et plafond (jusqu’à dix tickets ouverts). La pause ne répare pas les incidents existants. La reprise du logiciel laisse les arrivées en pause pour éviter une rafale.

## Validation et persistance

Vérifier et clôturer cible le poste du ticket, demande une observation PT récente et vérifie la fonction simulée correspondante. Le contrôle réseau reste une preuve ICMP, jamais une preuve SMB/FTP réelle. Pour FTP, cette version vérifie la disponibilité de connexion ; elle ne demande pas un transfert de fichier. Pour AD, elle vérifie que le compte est réactivé et que le poste est joignable ; elle ne valide pas un changement de mot de passe.

Les incidents sont enregistrés dans `session.json` avec leur ticket de récupération. Si la sauvegarde de la file manque après interruption, le rattachement de l’environnement restaure le signalement sans injecter une deuxième panne. Les causes privées ne sont pas exposées dans le statut métier des postes.

Les anciennes entreprises gardent leur réseau et le moteur historique « demande → prise en charge → panne ». Leur réinitialisation conserve l’effectif historique. Créer une **nouvelle entreprise** permet de bénéficier des 30 employés. Les pannes d’accessoires, les ateliers de préparation/déploiement et les scénarios multi-couches historiques ne sont pas encore intégrés au nouveau moteur simultané ; ces orientations sont désactivées dans son sélecteur, sans supprimer leurs moteurs.

## Performance et interface

La surveillance périodique observe le poste principal, les bureaux distants ouverts et deux autres postes par rotation. Elle ne lance pas trente séries de pings à chaque cycle. Une demande explicite de connexion/vérification vise toujours le poste choisi ; une preuve expirée n’est pas considérée comme valide.

Le confort visuel de v0.49.1 est conservé : scrollbars harmonisées, animation d’ouverture et écran de chargement. Cette livraison ajoute les repères d’impact dans la fiche ticket et dans la liste des postes. Elle n’installe pas un vrai Windows et n’ajoute pas de modèle LLM. Les sessions ne deviennent pas des sessions Windows durables : les protections d’invalidation et de redémarrage existantes sont conservées.

## Recette manuelle Packet Tracer 9

1. Créer une nouvelle entreprise, ouvrir **son réseau associé**, vérifier les 30 postes employés et le portable.
2. Recevoir un incident AD sur un poste identifié : avant de prendre en charge, son compte doit déjà être désactivé dans l’annuaire.
3. Recevoir une panne d’impression sur un autre poste : la panne AD doit rester présente.
4. Réparer seulement la première panne, vérifier le bon ticket et confirmer que le second reste non rétabli.
5. Débrancher le poste ciblé : sa clôture doit être refusée malgré la réparation applicative.
6. Recevoir une panne FTP, puis un second signalement FTP : un seul incident commun doit apparaître, avec un suivi ajouté.
7. Sauvegarder/reprendre : mêmes personnes, appareils et tickets ; arrivées en pause.
8. Reprendre puis réinitialiser une ancienne entreprise à deux postes : elle doit conserver deux postes.

La génération XML, les identités, les ports, les contrôles de réparation et les suites automatiques sont vérifiés avant livraison. **Le comportement et les temps de réponse dans Packet Tracer 9 sur Windows restent à tester avec cette version.**

## Suite prévue

Intégrer progressivement les accessoires et le déploiement au registre d’incidents ; enrichir les pannes et les droits ; persister les sessions sans supprimer les invalidations nécessaires ; enrichir les applications graphiques et le dialogue client ; simuler horaires, arrivée/départ d’employés et dépendances métier. L’effectif est livré, mais il ne constitue pas encore une simulation complète de la vie d’entreprise.
