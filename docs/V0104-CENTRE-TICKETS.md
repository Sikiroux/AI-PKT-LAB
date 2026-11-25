# v0.104 — Centre de tickets et premier incident immédiat

## Organisation du centre

La file est à gauche et la fiche à droite. À taille de bureau, chacune peut défiler sans déplacer tout l’écran. Les actions de prise en charge, attente et vérification restent en bas de la fiche. La résolution conserve son formulaire et ses contrôles métier existants ; elle n’est pas une clôture automatique. Les contrôles manuels des scénarios historiques restent distincts des preuves automatiques.

La navigation reçoit Paramètres en bas. Les compteurs deviennent des filtres compacts : ouverts, en cours, en attente, résolus et tous. Recherche, sévérité et filtres existants restent accessibles dans la colonne de file. Le contexte d’entreprise et la connexion sont condensés dans l’en-tête ; les informations réseau détaillées restent accessibles dans Parc et réseau. Les commandes secondaires sont regroupées sous Outils. Les autres pages conservent leur contexte réseau.

Les liens vers demandeur et documentation sont accessibles depuis le panneau latéral de la fiche. Les onglets, les notes, la priorité, les vérifications, l’historique et les dialogues de résolution existants sont conservés. Les écrans étroits reviennent à une disposition empilée pour garder les commandes accessibles.

## Où sont les arrivées automatiques ?

Bouton Simulation, dans la barre de filtres en haut à droite. Il ouvre un panneau contenant cadence, catalogue, plafond, durée des tickets, application des réglages et démarrage/pause. Le bouton Nouvelle demande ouvre séparément les paramètres de réception manuelle. Les réglages s’appliquent toujours à l’entreprise active.

## Commencer la simulation

Le premier démarrage d’une entreprise en préparation crée immédiatement une demande aléatoire, sans délai de découverte. Dans les entreprises actuelles à 30 employés, le scénario est appliqué et son signalement est immédiatement visible. Les anciennes entreprises conservent leur mécanisme de demande à préparer lors de la prise en charge.

La programmation des arrivées suivantes commence ensuite avec l’intervalle configuré. Reprendre, mettre en pause ou recliquer ne recrée pas un premier ticket. Un ticket déjà ouvert est conservé. En cas de refus ou de pont indisponible, le démarrage retourne l’erreur et reste en préparation ; aucune réussite fictive n’est affichée. Les prérequis de réseau sain et d’identité du poste continuent de s’appliquer.

Le premier ticket devient la sélection courante ; les filtres précédents sont retirés pour ne pas le masquer. Les filtres sont préservés lors d’une simple reprise des arrivées. Les boutons dépendant d’une vérification ne sont plus réactivés par la fin d’une requête générique.

## Validation

- Suite web Python complète : 860 tests réussis en 149,411 secondes.
- Suite web JavaScript : 57 suites réussies, dont nouveaux tests de structure et de premier démarrage.
- Prototype Electron : huit tests simulés réussis.
- Vérifications ciblées supplémentaires après les derniers ajustements ; syntaxe du script vérifiée.

Les adaptateurs DOM et Packet Tracer de ces tests sont simulés. Aucun navigateur local exploitable pour produire une capture n’est disponible ici. La structure de la maquette est reprise dans le code, mais la correspondance visuelle exacte et le comportement natif Electron Windows restent à confirmer par recette réelle.

## Installation

Quitter le simulateur. Extraire la mise à jour à la racine du dossier actuel et accepter le remplacement. Ne pas supprimer entreprises, sauvegardes ni desktop/node_modules. Relancer LANCER-BUREAU.bat. Tous les correctifs 103.1 sont inclus. La version complète extraite séparément ne transfère pas automatiquement les données d’un autre dossier.

## Recette

1. Ouvrir Tickets maximisé : file à gauche, fiche à droite, actions visibles sans défilement global.
2. Vérifier filtres, recherche, changement de ticket, onglets et notes enregistrées/brouillons.
3. Ouvrir Simulation : modifier et appliquer une cadence, puis démarrer ou mettre en pause.
4. Avec une entreprise en préparation et un réseau sain, commencer : contrôler l’apparition immédiate d’un premier ticket et son identification. Un deuxième clic ou une reprise ne doit pas le dupliquer.
5. Vérifier l’incident dans Packet Tracer, son impact et ses critères de réparation. Une observation inconnue ne devient pas un succès.
