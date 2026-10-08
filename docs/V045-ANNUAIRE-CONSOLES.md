# v0.45 — Console d’annuaire

La console conserve le moteur AD existant et propose six vues : Utilisateurs, Groupes, Ordinateurs, Unités d’organisation, Historique et Stratégie. Elle ne crée pas une seconde entreprise ni un nouveau réseau.

## Utilisation

Depuis le bureau du technicien, ouvrir l’application Annuaire. Une preuve réseau récente vers le serveur et un service d’annuaire démarré restent nécessaires. Une lecture de la console ne lance pas de ping et ne renouvelle pas une preuve.

- Utilisateurs : sélectionner un compte, ouvrir ses propriétés générales ou son appartenance aux groupes. Les personnes et appareils associés viennent du référentiel commun ; renommer un compte conserve son identifiant.
- Groupes : consulter les membres directs, ajouter ou retirer un utilisateur et déplacer le groupe dans une OU.
- Ordinateurs : consulter l’objet AD et le matériel associé, puis déplacer l’objet dans une OU. Ce déplacement ne déplace pas le matériel et ne change pas son câblage. L’appartenance au domaine est affichée, sans inventer un bouton de sortie du domaine dans cette console.
- Unités d’organisation : parcourir les objets. La recherche dans une OU comprend ses descendants ; les compteurs indiquent les objets directs.
- Historique : lire les dernières opérations du moteur. Il ne s’agit pas du journal d’événements Windows.
- Stratégie : consulter les règles effectivement utilisées par le moteur : verrouillage et durée des mots de passe. Cette vue ne prétend pas reproduire une console GPO.

## Cohérence et sauvegarde

Les modifications issues de cette console portent la révision affichée. Si l’annuaire a changé entre-temps, le serveur refuse la modification avant de toucher les comptes, permissions ou sessions. Actualiser la console puis refaire la modification. Les anciens clients sans ce champ restent compatibles.

Les opérations restent sérialisées par le verrou du contrôleur et suivent la sauvegarde existante. L’état public n’expose pas les credentials. Une association ambiguë entre un objet ordinateur et plusieurs matériels n’est pas choisie arbitrairement. Un référentiel d’un autre environnement n’est pas utilisé.

## Réalisme et limites

Références Microsoft consultées le 8 octobre 2026 :

- [Gestion des comptes dans AD DS](https://learn.microsoft.com/fr-fr/windows-server/identity/ad-ds/manage-user-accounts-in-windows-server)
- [Groupes de sécurité AD](https://learn.microsoft.com/fr-fr/windows-server/identity/ad-ds/manage/understand-security-groups)

L’organisation en objets, OU, propriétés et appartenance aux groupes reprend les concepts ADUC. Les fenêtres sont une interface pédagogique propre au simulateur, pas une copie intégrale de Windows.

Le moteur reste limité aux membres utilisateurs directs : pas de groupes imbriqués, de portées globale/universelle/locale de domaine, de réplication, LDAP ou Kerberos réels, de GPO ou de jeton Windows complet. Le mot de passe de formation ne doit jamais être remplacé par un vrai secret. Un objet ordinateur présent dans l’annuaire ne prouve pas sa connectivité.

Les applications de messagerie et licences restent prévues pour v0.47. Cette livraison ne les ajoute pas.

## Vérification

Tests ciblés : lecture sans mutation, refus de révision périmée sans effets de bord, maintien de la condition réseau, isolation du référentiel et types de révision stricts. Les tests DOM existants vérifient aussi les opérations de compte, groupe, OU et rafraîchissement en échec. Ces tests ne remplacent pas une validation visuelle dans un navigateur ni une validation native Packet Tracer.
