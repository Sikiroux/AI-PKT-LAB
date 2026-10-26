# v0.74 — Confirmer la connexion du demandeur

## Défaut corrigé

Le ticket AD annonce un refus de compte et demande de rouvrir la session. Sa vérification contrôlait uniquement l'activation du compte et le trajet distant. Réactiver le compte pouvait donc suffire à clôturer sans connexion de l'employé. Le dialogue refusait déjà de confirmer ce cas, créant un désaccord avec le contrôle du ticket.

## Changement

La vérification d'un incident AD simultané exige désormais :

- l'identité du demandeur d'origine, conformément au correctif v0.73 ;
- un compte actif ;
- un trajet distant autorisé, avec preuve réseau récente ;
- une authentification utilisateur valide sur le poste concerné.

Un compte actif et un poste joignable sans authentification donnent un résultat inconnu et une consigne explicite pour ouvrir la session du demandeur puis vérifier. La résolution/clôture est refusée. Le contrôle n'authentifie jamais à la place de l'utilisateur et ne lui demande pas de mot de passe supplémentaire si son authentification est déjà valide. Les règles existantes d'identité, de poste et de révision des identifiants sont conservées.

Les libellés des contrôles simultanés décrivent aussi leur portée réelle : file d'impression utilisable, accès Documents, session AD, résolution DNS ou disponibilité FTP avant authentification. Les détails précisent qu'une file utilisable n'est pas un nouveau document imprimé, qu'une résolution DNS n'est pas un accès fichier, et qu'un service FTP disponible ne confirme ni mot de passe ni transfert.

## Limites et suite

Ce bloc corrige la validation des incidents AD simultanés et clarifie les autres résultats. Il ne complète pas encore la validation métier des incidents FTP, DNS et impression : leur contrat doit être approfondi pour prouver le transfert, l'ouverture du document ou l'impression demandée. Les scénarios historiques restent distincts. L'authentification est celle du modèle pédagogique, pas une connexion Windows/LDAP réelle.

## Tests

Six nouveaux tests couvrent refus sans connexion, connexion du demandeur d'origine puis clôture, session d'un autre poste, jeton d'un autre appareil/révision, preuve réseau périmée et absence de connexion automatique/mutation par le contrôle. Les 25 tests existants des incidents simultanés restent verts. Suite web complète relancée. Générateur, ateliers et JavaScript inchangés depuis leur recette v0.70.

## Recette Windows / PT9 à effectuer

1. Recevoir un incident de compte désactivé. Réactiver le compte depuis l'annuaire, sans ouvrir la session employé.
2. Vérifier le ticket : le contrôle doit indiquer que la connexion du demandeur n'est pas confirmée ; le ticket ne doit pas être clos.
3. Prendre la main sur le poste associé, ouvrir la session avec le compte du demandeur, puis vérifier à nouveau.
4. Le contrôle peut réussir seulement avec ce compte/poste et les autres préconditions valides. Aucun mot de passe supplémentaire ne doit être demandé uniquement par la vérification.
5. Déconnecter explicitement la session utilisateur, puis vérifier : la simple disponibilité réseau ne doit plus suffire.
6. Vérifier que le dialogue et la fiche ticket concordent sur la possibilité de confirmer l'essai.
