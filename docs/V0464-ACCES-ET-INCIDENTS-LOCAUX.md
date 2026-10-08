# v0.46.4 — Accès locaux et incidents d’accessoires

## Accès locaux de formation

**Bureau technicien → Fiches des postes → choisir le PC → Accès locaux.** La vue Ordinateurs de l’annuaire propose aussi ce lien pour les postes représentés compatibles. Il ne s’agit pas du mot de passe AD de l’utilisateur.

Chaque poste simulé et portable technicien possède un compte de secours `support.local`, désigné par `.\support.local`. Son mot de passe initial est déterministe pour la seed, le numéro de série et la version de génération. Le registre est initialisé à la première consultation ; reprendre une session conserve ensuite ses changements.

| Action | Comportement |
|---|---|
| Afficher le mot de passe local | Révèle explicitement le credential de formation enregistré pour ce poste ; journalise la consultation |
| Masquer | Vide l’affichage du secret |
| Tester la connexion locale | Vérifie l’identifiant, le mot de passe et l’état du compte dans le moteur |
| Changer le mot de passe local | Met à jour le hash et le registre ensemble ; ferme l’ancienne session locale |
| Activer/désactiver | Modifie le compte local et ferme sa session |
| Fermer la session locale | Efface uniquement son authentification locale |

Le formulaire exige le préfixe local `.\`. Un mauvais identifiant ou mot de passe, ou un compte désactivé, refuse l’authentification. Une réussite n’ajoute aucun groupe AD, droit de partage ou accès réseau, et n’ouvre pas automatiquement de session RDP. Cette console teste le compte ; elle ne remplace pas encore l’écran de connexion complet d’un Windows simulé.

`session.json` contient `local_access` : environnement, révision, comptes avec hash, registre de mots de passe de formation, sessions locales et historique. Le registre est **non chiffré et réservé à ces identifiants fictifs** ; ce n’est ni Windows LAPS ni un gestionnaire de secrets de production. Les vues ordinaires du parc et de l’annuaire ne retournent pas les secrets locaux. Les journaux ne contiennent ni mot de passe saisi ni mot de passe révélé. Au redémarrage, les comptes et le registre persistent, mais les sessions locales sont fermées.

Les routes d’administration `credentials/state` et `credentials/operation` exigent l’environnement actif et un poste simulé unique. Elles refusent un contexte de bureau client. Les modifications et révélations exigent une révision actuelle. Les anciennes commandes et secrets affichés sont retirés après une erreur d’actualisation.

## Tickets d’accessoires externes

Dans **Tickets → Recevoir une nouvelle intervention → Catalogue Applications → Accessoires locaux**, choisir un poste ou laisser le choix procédural. Le même choix est disponible pour les arrivées automatiques du catalogue Applications. Le choix « Aléatoire » historique conserve ses familles existantes ; sélectionner Accessoires locaux pour ces nouveaux incidents.

Neuf variantes procédurales :

- Écran : alimentation coupée, câble vidéo débranché, mauvaise entrée vidéo, défaut matériel.
- Clavier : câble débranché ou défaut matériel.
- Souris : câble débranché, défaut matériel ou accessoire retiré.

Les tickets décrivent les symptômes et le poste, sans donner la cause. Le dialogue client distingue les accessoires externes de la connectivité et de l’accès distant. La seed, le compteur d’interventions et le numéro de série déterminent la variante.

Intervenir **sur place dans Équipement local**. Un défaut matériel exige le remplacement par un accessoire sain ; débrancher/rebrancher ne transforme pas un accessoire défectueux en accessoire sain. Ajouter au stock reste une action de formation, sans achat ou livraison commerciale.

La préparation exige trois accessoires actuellement fonctionnels sur ce poste et refuse un exercice actif non terminé. Elle n’efface pas d’autres défauts pour préparer le suivant. L’injection ne modifie pas le réseau et ne ferme pas à elle seule une session distante.

**Vérifier et clôturer** contrôle les trois accessoires de la cible et l’absence de dégâts sur les autres postes et configurations. Ce ticket local ne lance aucun ping et ne dépend pas de l’accès aux documents du domaine. Caches DNS, journaux et compteurs d’essais ne sont pas assimilés à des dégâts ; les changements de comptes, droits, contenus ou configuration restent contrôlés. La correction de l’accessoire d’un autre PC ne valide pas le ticket.

## Validation et limites

Tests des neuf causes : échec initial, réparation effective, remplacement, zéro réussite gratuite, refus de clôture avant réparation, clôture sans observation réseau, cohérence sur le second client et préservation des autres appareils. Tests des comptes locaux : authentification réelle dans le moteur, indépendance d’AD, absence de secrets dans les vues ordinaires, changement atomique, désactivation, révision périmée et reprise de sauvegarde. Tests DOM : révélation explicite, masquage, ciblage exact, effacement des saisies et anciennes vues.

La validation visuelle dans le navigateur Windows reste à faire. La saisie locale de secours ne fournit pas encore un bureau sur place complet, les composants intégrés du portable ne sont pas modélisés et ces périphériques ne sont pas des périphériques USB émulés. Le mode Packet Tracer discret existant reste inchangé.
