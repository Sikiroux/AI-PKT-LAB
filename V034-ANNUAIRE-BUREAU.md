# v0.34 — Annuaire et session utilisateur

L’interface du bureau technicien utilise désormais la console Annuaire pour chercher un compte, consulter son état, gérer ses groupes et créer des objets. Les opérations passent par les fonctions déjà présentes dans `sim_ad` et le contrôleur existant ; cette version ne change pas le schéma des sauvegardes.

## Console Annuaire

- Liste d’utilisateurs triée par nom, recherche sur le nom affiché ou l’identifiant.
- Filtre par unité d’organisation (OU), incluant ses unités descendantes. Les chemins indiquent les parents : `Entreprise / IT`.
- Fiche du compte sélectionné : identifiant, emplacement, activation, verrouillage et état du mot de passe.
- Actions explicites : déverrouiller, activer/désactiver, réinitialiser le mot de passe, ajouter/retirer un groupe et déplacer le compte vers une OU.
- Confirmation avant activation/désactivation ou réinitialisation. Le mot de passe temporaire est affiché avec l’identifiant du compte concerné ; il n’est pas conservé dans un historique UI.
- Recherche et filtre ne changent pas le compte sélectionné. La fiche affiche toujours son nom pour rendre la cible explicite.
- Une actualisation refusée retire les comptes et la fiche précédemment affichés. Les anciennes données ne permettent pas de lancer une nouvelle opération.
- Les requêtes simultanées sont bloquées et les champs de création sont désactivés pendant une opération.

« Créer un objet dans l’annuaire » expose trois opérations :

| Objet | Informations | Effet |
| --- | --- | --- |
| Utilisateur | Nom affiché, identifiant, OU, mot de passe initial facultatif | Compte actif, changement de mot de passe obligatoire. Sans mot de passe saisi, le moteur utilise `Formation!2026`. |
| Groupe | Nom et OU | Groupe sans membres ; les comptes peuvent ensuite y être ajoutés. |
| Unité d’organisation | Nom et parent, ou racine du domaine | Nouveau conteneur dans l’annuaire simulé. |

Créer un utilisateur ne crée **pas** un PC dans Packet Tracer, un nouveau bureau distant ou une association automatique avec un poste. Le prototype conserve son compte client lié à l’environnement. Cette limite doit rester claire dans les scénarios.

Les autorisations et preuves réseau du technicien sont contrôlées par le serveur. L’interface n’accorde aucun droit supplémentaire. Toute opération AD conserve le comportement existant d’invalidation de l’authentification ; une reconnexion peut donc être nécessaire pour les documents partagés.

## Application Session utilisateur

Le compte associé au poste et son état de connexion sont affichés en haut. La connexion, la déconnexion et le changement de mot de passe sont séparés. La rubrique de changement possède un champ pour le mot de passe actuel et un autre pour le nouveau, sans réutiliser le champ de connexion qui a déjà été effacé.

Les mots de passe sont effacés après chaque tentative correspondante. Les refus usuels sont traduits : compte verrouillé, compte désactivé, mot de passe expiré, changement obligatoire ou annuaire inaccessible. Cette application ne permet pas de choisir un autre compte.

## Vérification

- `node web/test_desktop_ui.js` : cible du compte conservée malgré une recherche, groupe et OU envoyés avec les bons identifiants, création avec changement obligatoire, effacement du mot de passe initial, retrait d’un annuaire inaccessible et champs séparés de changement de mot de passe. Les contrôles des autres applications restent exécutés.
- Deux tests Python d’intégration supplémentaires : création OU/groupe/compte, appartenance, déplacement et persistance ; refus sans réseau technicien avec conservation de l’état.
- Suites web, générale et ateliers avant livraison.

Les tests DOM ne remplacent pas une inspection visuelle OS.js dans le navigateur Windows. Aucun nouveau comportement de Packet Tracer annoncé comme validé ; aucune dépendance ajoutée et aucun LLM intégré dans ce bloc.
