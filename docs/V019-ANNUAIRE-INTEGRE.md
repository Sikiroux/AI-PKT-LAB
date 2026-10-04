# v0.19 — Annuaire simulé intégré

## Ce qui change

Le moteur livré sur `codex/ad-simulation-engine` (commit `1dca2a493110cb8372045430173a52ba9db910ae`) est intégré à la branche de développement du prototype, avec corrections. La branche source AD reste intacte et main n'est pas modifiée.

L’annuaire est conservé sous `directory` dans le `session.json` de l’entreprise. Les droits Documents dépendent des groupes Documents-Lecture et Documents-Ecriture. Les anciens booléens de permissions/compte sont migrés puis retirés pour éviter une deuxième source d'autorité. Les anciennes sessions disposant des trois postes reçoivent un annuaire lors de la reprise ; leur fichier original est conservé dans `session.before-directory.json` avant cette migration.

Corrections du moteur : réinitialisation renouvelle l’expiration ; les tentatives d’authentification effectuées font évoluer revision/audit ; `change_password` permet le changement obligatoire après vérification du secret actuel. Aucun secret n’est journalisé. Les échecs réseau/service ne comptent pas comme tentatives de mot de passe.

## Parcours à essayer

1. Reprendre ou créer une entreprise. Ouvrir son fichier Packet Tracer et le pont.
2. Réparer le câble client si le scénario initial le demande, puis Vérifier maintenant.
3. Ouvrir le bureau technicien, puis l’icône **Annuaire**. Consulter les utilisateurs, sélectionner le demandeur du ticket et cocher **Documents-Lecture**.
4. Ouvrir **Accès distant**. Dans le bureau client, ouvrir **Session utilisateur**. Le nom de connexion est affiché ; le mot de passe fictif initial est `Formation!2026`.
5. Se connecter, puis ouvrir Documents. L’écriture est indépendante et exige Documents-Ecriture.
6. Pour tester un compte verrouillé : saisir trois mauvais mots de passe. Déverrouiller depuis Annuaire, puis se reconnecter.
7. Pour tester une réinitialisation : la console affiche le mot de passe temporaire une seule fois. Dans Session utilisateur, saisir ce mot de passe dans le premier champ, un nouveau (8 caractères minimum) dans le second, puis **Changer mon mot de passe**.

Une modification d'annuaire invalide la connexion utilisateur simulée en cours ; se reconnecter ensuite. Reprendre une session ou redémarrer l'application efface les preuves réseau et l'authentification, mais conserve l'annuaire et les groupes. La connexion simulée expire après 30 minutes.

Les boutons historiques Accorder lecture/écriture utilisent les mêmes groupes, sans écrire d'anciens booléens. Ils requièrent désormais l'accès observé du technicien au serveur.

## Règles d’intégration

- `/workspace/directory/state`, `/operation`, `/login`, `/change-password`, `/logout` sont des actions POST du serveur existant, avec jeton local et environnement actif obligatoire.
- L'acteur d'administration est créé côté serveur. Le navigateur ne déclare ni permissions ni authentification.
- Console de formation : le technicien dispose du rôle administrateur simulé. Ce prototype ne réalise pas encore un login distinct du technicien et ne reproduit pas Kerberos/LDAP ou Windows Server.
- L'administration utilise une nouvelle observation ICMP technicien → serveur. La connexion utilisateur et l’accès Documents utilisent client → serveur. Les observations ont une durée de validité de 45 secondes, avec contrôle de provenance source/cible.
- ICMP reste une approximation pédagogique du transport ; ce n'est pas un test LDAP/SMB. Aucun serveur AD réel n'est installé ou contacté.
- Le modèle d'autorisation est simple : groupes/utilisateurs autorisés, lecture/écriture indépendantes, sans refus explicite, héritage NTFS, groupes imbriqués ou jetons Windows conservés.
- L'interface Annuaire expose consultation, activation/désactivation, déverrouillage, reset et appartenance aux groupes. Le moteur supporte d'autres opérations, mais création d'OU/postes/utilisateurs et leurs écrans restent à compléter.
- Aucun VPN, Laptop, Wi-Fi technicien, câble console ou déplacement automatisé n'est ajouté dans cette version.

## Installation et limites de validation

Fermer la console de l’ancienne version, remplacer les fichiers du programme sans supprimer les dossiers de données, relancer et Ctrl+F5. Éviter plusieurs serveurs lancés sur le même port.

Tests Python du moteur et de l'intégration : migration, isolation, preuves distinctes, login et droits, reset d'un secret expiré, changement obligatoire, invalidation et sauvegarde sans secret public. Syntaxe JS vérifiée. La validation visuelle du nouveau parcours et son comportement dans Packet Tracer restent à réaliser par l'utilisateur.
