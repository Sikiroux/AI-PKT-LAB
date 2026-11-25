# v0.102 — Première intégration du bureau et de la messagerie validés

## Interface

Bandeau supérieur permanent retiré. Les informations du poste et de l’entreprise sont consultables dans le menu NetOps. Le fond bleu est conservé. Barre des tâches réduite à 46 pixels.

Paramètres du poste → Personnalisation : Toujours visible (par défaut) ou Masquage automatique. Le choix est enregistré localement pour le bureau et l’entreprise dans le profil courant. Une poignée reste au bas de l’écran ; survol, clic et Ctrl + Alt + T rappellent la barre. Le masquage attend la sortie du pointeur et préserve le focus clavier ainsi que le lanceur ouvert. Les informations et commandes de verrouillage/fermeture restent accessibles. L’option est également accessible sur le bureau technicien via le menu NetOps.

Messagerie : suppression des gros titres permanents, recherche et filtres dans une colonne Discussions, avatars à initiales sans présence inventée, en-tête compact avec accès au ticket, historique défilant et questions scénarisées dans une zone basse dédiée. Les notes ajoutées volontairement au ticket, épingles, lectures et recherches sont conservées. Aucun champ de dialogue libre, appel ou annuaire de contacts supplémentaire n’est ajouté. Ce premier lot reprend la direction visuelle des maquettes, sans annoncer toutes leurs propositions comme disponibles.

Les correctifs de lancement et de réutilisation du bureau technicien v101.1 à v101.4 sont inclus.

## Vérifications

54 suites JavaScript existantes réussies après intégration, puis une nouvelle suite dédiée au réglage de barre réussie : 55 suites au total. Huit tests du prototype Electron réussis avec adaptateurs simulés. Aucun changement métier Python dans ce lot. La recette visuelle Windows/Electron reste à effectuer ; les tests DOM simulés ne prouvent pas le rendu.

## Installation du correctif

Quitter le simulateur, extraire le correctif à la racine du dossier existant et accepter le remplacement des fichiers. Conserver node_modules, les entreprises et les données. Relancer LANCER-BUREAU.bat. La version complète peut être extraite séparément, mais ne récupère pas automatiquement les données d’un autre dossier.

## Recette

Ouvrir la messagerie et examiner sa taille normale puis maximisée. Consulter une conversation, poser une question, exporter volontairement une note, changer de ticket puis revenir. Tester les deux modes de barre, rappel clavier, navigation clavier dans le menu, verrouillage et plusieurs écrans. Recharger le bureau pour contrôler le réglage mémorisé, puis vérifier son isolation entre postes et entreprises.
