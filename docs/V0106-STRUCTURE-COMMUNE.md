# v0.106 — structure commune et corrections du centre de tickets

## Portée

Points 1 et 2 demandés : structure de l’application commune aux onglets et corrections du centre de tickets. La refonte du contenu de l’accueil, du parc réseau et des postes n’est pas réalisée ; elle reste conditionnée à des maquettes validées.

## Structure commune

Logo, navigation compacte, paramètres en bas, en-tête à trois zones, menus, profil et barre de synchronisation sont désormais utilisés sur Accueil, Tickets, Parc et réseau, Postes, Journal et Formation. Le contexte réseau n’est plus répété dans un bandeau permanent : l’entreprise et le pont figurent dans l’en-tête, et Fichier réseau est accessible dans le menu de l’application ainsi que dans Parc et réseau. La barre de synchronisation appartient au cadre global au lieu de disparaître avec la page Tickets.

Les panneaux et fonctions existants des autres pages sont conservés ; seuls leur cadre et la gestion du défilement extérieur changent. Sur petit écran, la navigation reste rappelable par le bouton de menu.

## Corrections de la fiche

- Identifiant, priorité, statut et menu Actions occupent des cellules explicites pour éviter les dispersions et chevauchements.
- Le titre des notes et son crayon sont placés dans deux colonnes, sans positionnement absolu.
- Contraste et tailles des informations du panneau droit renforcés.
- Ressource identique au poste non répétée ; les ressources distantes utiles restent affichées.
- Messages informatifs retirés après 4,5 secondes ; les erreurs restent affichées.

## Deux compteurs distincts

Le compteur d’exercice existant représente un délai démarré dès le signalement dans les entreprises actuelles. Il reste inchangé et accessible dans Options de suivi.

Le temps de travail utilise maintenant un champ work_timer séparé. Il commence à la prise en charge, s’arrête en attente, reprend à la nouvelle prise en charge ou réouverture, puis s’arrête à la résolution/clôture réussie. Les refus ne modifient pas ce compteur. Il est enregistré avec le ticket. Aucun temps de travail ancien n’est inventé : une ancienne intervention déjà engagée sans mesure affiche Non mesuré ; une nouvelle demande non prise en charge affiche zéro. Le délai d’exercice n’est pas réinitialisé.

## Vérifications

57 suites JavaScript de régression réussies ; tests ciblés supplémentaires sur le cadre global, la barre de synchronisation et la distinction des compteurs. Huit tests Electron simulés réussis. Deux tests Python ajoutés pour le temps de travail, dont un cycle persistant de prise en charge/attente et un refus de clôture. Le contrat de navigation reconnaît les identifiants créés par le constructeur de dialogue.

La suite Python complète a exécuté 862 tests : une assertion statique de contrat ne reconnaissait pas le dialogue créé dynamiquement. Ce contrat a été corrigé, puis ses cinq tests et les deux nouveaux tests du compteur ont réussi. Les autres tests de cette exécution complète avaient réussi. Les tests ne constituent pas une recette visuelle native ; celle-ci reste à confirmer sur Electron Windows.

## Installation

Quitter le simulateur, extraire la mise à jour à la racine du dossier courant puis accepter les remplacements. Conserver données et desktop/node_modules. Relancer LANCER-BUREAU.bat. La version complète extraite ailleurs ne migre pas les données d’un autre dossier.

## Recette

Passer entre Accueil, Tickets, Parc et réseau et Postes : mêmes dimensions de navigation et d’en-tête, paramètres accessibles et synchronisation visible. Vérifier les menus et le rappel mobile de la navigation. Dans Tickets, contrôler les badges, Actions et le crayon des notes à plusieurs largeurs. Pour un nouveau ticket : temps de travail à zéro, prise en charge pendant quelques secondes, attente, reprise et résolution. Le compteur d’exercice doit continuer selon ses propres règles. Les contenus des autres onglets attendent encore leurs maquettes de refonte.
