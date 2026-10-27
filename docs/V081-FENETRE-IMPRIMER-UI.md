# v0.81 — Fenêtre Imprimer

## Livré

- En-tête avec icône, choix document/destination, résumé avant envoi et accès à la file d’attente.
- L’envoi est désactivé sans document local ou destination existante, avec explication dans la fenêtre.
- Les contrôles sont bloqués pendant la requête pour éviter un double envoi.
- Les résultats distinguent travail accepté, impression terminée dans la simulation et refus expliqué avec son code.
- Une impression confirmée reste affichée si l’actualisation ultérieure échoue : cette erreur ne doit pas inviter implicitement à réimprimer.
- Le résumé est recalculé lors de l’actualisation des imprimantes ; les sélections de la fenêtre principale ne redirigent pas le choix de destination de la boîte Imprimer.

## Périmètre

Mêmes routes, mêmes permissions, même moteur d’impression. Aucun document physique n’est produit. Pas de nouvelle gestion des copies, formats de papier ou aperçu de page : le moteur ne les simule pas. Les champs de sélection restent pertinents dans cette boîte de dialogue.

## Vérification

Test dédié `web/test_print_dialog_ui.js` : résumé et destination, double clic, travail accepté vs imprimé, code réseau inconnu, résultat conservé après échec d’actualisation, documents et imprimantes absents.

Les 41 suites JavaScript passent pour cette version. Le cœur Python et les ateliers restent inchangés ; leurs derniers résultats sont 19/19 et 8/8 lors de la validation v0.79, non relancés pour cette passe UI. Les tests web Python ne sont pas relancés.

## Recette visuelle restante

Aucun rendu graphique n’a été vérifié ici. Dans Chrome : ouvrir Imprimantes depuis le bureau client, choisir un document et une destination, vérifier le résumé, envoyer puis consulter la file. Refaire avec une file suspendue. Réduire la largeur de la fenêtre et vérifier le défilement, les libellés et le focus clavier. Le statut accepté ne doit jamais être confondu avec une impression réussie.
