# v0.20 — incidents procéduraux d'annuaire

## Utilisation

1. Reprendre ou créer un environnement. Ouvrir son fichier dans Packet Tracer, réparer la liaison client initialement coupée et sauvegarder au même emplacement.
2. Dans Postes et environnement, cliquer Vérifier maintenant. Le client ET le technicien doivent communiquer avec le serveur (preuves ICMP fraîches du pont).
3. Cliquer **Nouvel exercice d'annuaire** et confirmer. Le réseau reste le même. Le logiciel prépare l'état du demandeur, lui accorde les groupes Documents lecture/écriture puis injecte une seule panne AD. Son ancien mot de passe est conservé ; la session distante et l'authentification sont invalidées.
4. Lire le nouveau ticket dans Tickets. Ouvrir le bureau technicien puis Annuaire pour investiguer. La description ne révèle pas la cause interne.
5. Réparer, ouvrir la prise en main, connecter l'utilisateur via Session utilisateur, puis tester Documents. Pour le ticket d'enregistrement, la lecture ET l'écriture sont requises.
6. Vérifier et fermer le ticket. On peut ensuite démarrer l'incident suivant. Une vérification réussie autorise également le suivant sans fermeture : fermer auparavant évite de laisser un ancien ticket en cours.

## Cinq familles, ordre reproductible

La seed de l'environnement et un compteur persistant déterminent l'ordre. Chaque cycle de cinq mélange : compte désactivé, compte verrouillé, mot de passe expiré, groupe lecture absent, groupe écriture absent. L'ordre est indépendant du flux de génération du réseau. Noms du client, demandeur et adresses restent ceux de l'environnement, jamais ceux d'un réseau de démonstration fixe.

Le ticket conserve son ID, son objectif et son historique dans tickets.json. Il n'expose pas la famille interne ni les credentials. Reprendre une sauvegarde conserve l'incident et son compteur, mais exige de nouvelles observations et une nouvelle authentification.

## Réparations et limites pédagogiques

- Désactivé : réactiver le compte dans Annuaire, puis connecter l'utilisateur.
- Verrouillé : déverrouiller ou attendre la durée de verrouillage prévue par la politique ; les deux solutions sont acceptées si l'accès revient.
- Expiré : changer le mot de passe avec l'ancien, ou réinitialiser puis effectuer le changement obligatoire. Le mot de passe initial est Formation!2026 sauf s'il a déjà été changé.
- Lecture/écriture : rétablir les memberships appropriés. Les opérations de groupes invalident l'authentification ; reconnecter l'utilisateur.

Les autres comptes et le réseau sont préservés. La préparation modifie explicitement l'état du seul demandeur et ajoute ses droits de départ ; elle ne vise pas à simuler un incident spontané de production. Les prochains tickets ne sont pas injectés automatiquement par un intervalle : déclenchement manuel dans cette version.

Il s'agit du moteur AD pédagogique existant, pas d'un AD réel ni de SMB dans Packet Tracer. Les preuves ICMP restent une approximation du transport. La clôture vérifie l'accès actuellement évalué, pas le fait d'avoir tapé une commande précise. Un ancien incident AD ne peut pas être vérifié contre l'état d'un nouvel incident.

Les indices et correction de la page actuelle sont renommés « premier exercice réseau » : ils ne constituent pas la correction des incidents AD. Une interface d'indices adaptée à chaque famille viendra ensuite. Les diagnostics détaillés restent consultables dans les préconditions du prototype ; aucun niveau expert ne les masque encore.

La réinitialisation de l'environnement revient au premier exercice réseau, pas à l'incident AD courant. Le moteur de partages de fichiers confié à l'autre IA n'est pas encore intégré. Le brief correspondant est inclus dans docs/BRIEF-IA-PARTAGES-FICHIERS.md.

Validation : tests Python de génération, injection, réparation par les opérations AD, objectifs lecture/écriture, clôture des tickets, isolement, persistance et prérequis. Le parcours UI et le comportement avec une vraie instance Packet Tracer restent à tester.
