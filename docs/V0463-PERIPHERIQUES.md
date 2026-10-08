# v0.46.3 — Équipement local des postes

## Parcours

Depuis le bureau du technicien : **Fiches des postes → choisir le numéro de série → Équipement local**. Une fenêtre distincte est ouverte pour chaque poste. L’aperçu représente une intervention sur place et reste indépendant de la prise en main à distance.

| Accessoire | Manipulations | Conséquence locale |
|---|---|---|
| Écran | Brancher/débrancher le câble, allumer/éteindre, choisir HDMI ou DisplayPort, retirer/remplacer | Image présente, écran noir ou absence de signal |
| Clavier | Brancher/débrancher, retirer/remplacer | Test de saisie disponible ou désactivé |
| Souris | Brancher/débrancher, retirer/remplacer | Test de clic disponible ou désactivé |

Cette vue modélise des accessoires externes ; elle ne prétend pas que débrancher un écran externe éteint aussi l’écran intégré d’un portable. Les composants intégrés ne sont pas encore représentés. Le câble vidéo de ce premier modèle est HDMI. Sélectionner DisplayPort produit une absence d’image. Éteindre un écran ne coupe ni le réseau, ni les services, ni la session distante. Aucun de ces boutons ne lance de ping ou de commande Packet Tracer.

**Ajouter au stock simulé** crée un accessoire sain de formation ; ce n’est pas un achat réel. **Installer** remplace celui du même type sur le poste choisi et conserve l’ancien au stock. **Retirer** le rend disponible sans effacer son identité ni son état. Un accessoire défectueux demeure défectueux après retrait : le remplacement utilise un autre matériel.

## État et sauvegarde

`session.json` contient `peripherals` : environnement, révision, accessoires identifiés, poste associé, état du câble, alimentation, entrée vidéo, état matériel et historique. Les trois accessoires initiaux de chaque poste simulé ont des identifiants reproductibles issus de la seed et du numéro de série. Les sessions existantes les obtiennent à la première ouverture de cette fenêtre ; aucun fichier réseau n’est régénéré.

Les routes `peripherals/state` et `peripherals/operation` exigent l’environnement actif. Le contrôleur refuse un numéro de série inconnu ou ambigu et les appareils simplement observés sans poste simulé. Une mutation requiert la révision actuelle et ne peut manipuler l’accessoire installé sur un autre poste. L’application efface les anciennes commandes après une erreur et demande une actualisation.

## Fidélité et limites

Il s’agit d’un modèle local d’accessoires, pas d’une émulation USB ou graphique Windows. La saisie et le clic sont des tests dans l’aperçu ; ils ne commandent pas le bureau du technicien ni le bureau distant. Les appareils réseau et leur alimentation restent sous la responsabilité de Packet Tracer.

L’état matériel défectueux est pris en charge par le moteur et les tests, mais aucun bouton de réparation magique n’est exposé. Cette livraison ne génère pas encore de tickets de périphérique et ne crée pas spontanément de pannes. Aucun stock commercial, coût d’achat, livraison ou câble virtuel détaillé n’est simulé.

Le coffre des accès locaux reste à intégrer. Le mot de passe AD n’est pas transformé en secret lisible dans l’annuaire.

## Validation

Tests de remplacement, conservation de l’ancien accessoire, mauvaise entrée vidéo, alimentation, connexions indépendantes, identité reproductible, sauvegarde, refus de révision périmée et isolation entre postes. Tests DOM des requêtes ciblées, désactivation des tests locaux et effacement des contrôles après erreur. Rendu dans le navigateur Windows encore à vérifier ; les tests DOM ne prouvent pas sa qualité visuelle.
