# v0.66 — Cohérence des preuves et des sessions

## Changements

- AD, impression/FTP et transport distant lisent les preuves ICMP avec le même contrôleur : paire source/cible exacte, statut reconnu et validité de 45 secondes. Une preuve agrégée ne suffit plus pour ouvrir une session distante dans une entreprise liée à des appareils. Les modèles historiques sans appareils conservent leur compatibilité.
- Les preuves communes technicien→serveur et technicien→passerelle VPN sont distribuées aux bureaux. Un ancien résultat ne remplace pas un plus récent. Aucune preuve client→serveur ou technicien→client n’est partagée de cette manière.
- Une observation VPN inconnue ou en échec bloque l’accès selon sa preuve mais ne détruit plus la session VPN. Déconnexion explicite, déplacement, expiration et refus du profil continuent de s’appliquer. L’affichage distingue session VPN ouverte et accès réseau à vérifier/indisponible. Le VPN conserve sa durée de 30 minutes ; il reste simulé.
- Les nouvelles connexions utilisateur produisent une session Windows simulée liée à l’environnement, au compte et au numéro de série du poste. Elle ne disparaît plus après 30 minutes ni à l’expiration d’une preuve réseau. Les anciennes sessions temporaires gardent leur date d’expiration. Une déconnexion utilisateur, une reprise du logiciel, un changement de compte/identifiants ou une désactivation invalident cette session. Changer seulement les groupes ne la ferme pas : les droits sont évalués pour chaque accès.
- L’indicateur utilisateur connecté ne peut plus accepter une session d’un autre compte ou poste. Les applications distinguent un bureau non ouvert d’une session conservée dont le contrôle réseau doit être renouvelé. L’état du partage fourni dans le contexte AD provient du service de fichiers actuel, au lieu du booléen historique quand ce service existe.

## Validation

Dix-huit nouvelles recettes automatisées : session au-delà de trente minutes, compte et poste distincts, identifiants modifiés, groupes, désactivation/expiration historique, mauvaises paires réseau, preuve agrégée, horodatage mal formé, partage des trajets communs, VPN inconnu et reprise du logiciel. Les tests utilisent un pont simulé ; ils ne prouvent pas le comportement réel dans Packet Tracer.

Recette Windows/PT9 : ouvrir deux bureaux, connecter un employé, passer sur Annuaire/DNS puis revenir ; distinguer utilisateur connecté et contrôle réseau périmé. En télétravail, vérifier le VPN sur un poste puis changer de bureau. Une indisponibilité du pont doit conserver la connexion VPN affichée comme session établie tout en suspendant les actions non vérifiables. Une vraie perte réseau doit refuser l’action ; une nouvelle preuve positive permet de reprendre. La déconnexion explicite et la fermeture/reprise du logiciel doivent supprimer les sessions concernées.

## Limites

Ce bloc ne supprime pas l’exigence de preuve réseau récente et ne prolonge pas sa durée. Il ne simule pas les jetons Kerberos, une ouverture de session hors ligne ou tous les comportements de Windows après changement de mot de passe. La signature du compte est une règle locale pédagogique. Aucune session n’est conservée lors d’une reprise du logiciel, car les anciennes observations ne valident pas une nouvelle instance Packet Tracer.

Il s’agit d’un bloc ciblé de cohérence, pas de la totalité des dépendances prévues par le modèle entreprise. Les sessions FTP, les actions détaillées des salariés et l’horloge métier restent sur la feuille de route. L’interface et le réseau réels restent à tester avant de déclarer l’indisponibilité intermittente de l’annuaire résolue dans tous les cas.
