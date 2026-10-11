# v0.62.4 — Sessions, cache et accès distant

## Correctifs

- Le cache lu par le navigateur reste celui de l’entreprise canonique pendant le contrôle d’un poste secondaire. Une modification du premier poste est publiée à la sortie du contexte, comme pour les autres postes.
- Une modification du journal AD ou du numéro de révision ne déconnecte plus les autres employés. Une modification des propriétés de sécurité invalide seulement les autres sessions du compte concerné.
- Un échec réseau suspend les opérations mais ne ferme plus automatiquement les fenêtres du bureau distant. Déconnexion explicite et changement d’environnement restent des motifs de fermeture.
- Le bureau technicien retrouve le raccourci Accès distant et son entrée dans Applications.
- Depuis les fiches des postes, la nouvelle fenêtre est ouverte au clic, avant l’attente du pont : les navigateurs peuvent bloquer une ouverture trop tardive. Si la connexion échoue, la fenêtre provisoire est fermée.
- L’utilisateur affiché dans la fiche suit l’association du registre d’entreprise.
- La fenêtre Session utilisateur affiche une icône de profil et masque le mot de passe et le bouton de connexion lorsque le compte est authentifié. La déconnexion reste explicite.
- L’annuaire distingue un service arrêté, un échec observé et une preuve non vérifiée récemment.

## Ce qui reste volontairement contrôlé

Les preuves réseau expirent toujours après 45 secondes. Un résultat périmé ne donne pas de droits. Le contrôle périodique existant reste discret sans accélération ; les contrôles manuels restent accélérés. Aucune transformation en moteur Packet Tracer sans interface. La durée maximale d’authentification reste de 30 minutes ; ce correctif ne stocke pas les mots de passe dans le navigateur.

## Recette réelle à effectuer

1. Ouvrir deux bureaux clients, authentifier chacun, puis actualiser leurs sessions : la connexion du second ne doit pas déconnecter le premier.
2. Fermer puis rouvrir Session utilisateur : un compte encore authentifié ne doit pas demander le mot de passe.
3. Ouvrir Accès distant depuis le technicien puis une fiche de poste. Vérifier le numéro de série et l’utilisateur avec le ticket.
4. Laisser le bureau ouvert cinq minutes ; noter les éventuels messages de preuve périmée avec leurs heures.
5. Couper le câble du client : les opérations doivent être refusées mais les fenêtres conservées. Rebrancher et vérifier le réseau : les opérations doivent reprendre sans recréer le bureau.
6. Changer d’entreprise ou se déconnecter explicitement : l’ancien accès distant doit être fermé.
7. Si AD/DNS restent intermittents, enregistrer les durées des contrôles et le nombre de sessions distantes : les tests simulés ne prouvent pas les délais du pont PT9.
