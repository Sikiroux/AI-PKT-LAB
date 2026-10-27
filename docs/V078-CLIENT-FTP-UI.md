# v0.78 — Client FTP : navigation et transferts

## Refonte visible

Le client FTP conserve son modèle à deux panneaux, mais présente désormais :

- des en-têtes local/distant avec les icônes du bureau ;
- une recherche indépendante dans chaque liste, un tri naturel par nom et un compteur affiché/total ;
- une sélection lisible avec les noms local et distant rappelés près des actions ;
- un panneau de transferts repliable, ouvert lorsqu'un transfert est lancé, avec états en cours/terminé/échec ;
- le journal et l'aide de connexion séparés de la navigation principale.

Le formulaire de connexion reste dans sa propre fenêtre. Le mot de passe n'est pas rempli automatiquement et est effacé après la tentative ou la fermeture de cette fenêtre. Une recherche locale ne lance aucune requête. Si elle masque le fichier sélectionné, la sélection est annulée : une action ne peut pas continuer à cibler silencieusement ce fichier.

## Session et disponibilité

Le bandeau parle de **session FTP ouverte**, sans prétendre que tous les services sont actuellement opérationnels. Les retours réseau non vérifié, liaison en échec et service FTP indisponible sont indiqués séparément. La session reste conservée lors d'une incertitude de transport ; le client ne se reconnecte pas automatiquement. Un refus d'authentification retire la liste distante et désactive les transferts jusqu'à une nouvelle connexion.

Les principaux refus disposent d'un texte explicatif et du code technique conservé. Les erreurs de canal de données et de permissions ne sont pas présentées comme des erreurs de mot de passe. Le retour à un état positif nécessite une opération FTP réussie, pas un simple changement de sélection.

## Design et limites

Les surfaces, couleurs, contrastes de focus et bordures utilisent les tokens communs `app-system.css`. Les listes ont leur défilement borné. Une requête de conteneur adapte les deux panneaux à la largeur de la fenêtre de l'application, pas uniquement à celle de la page entière.

Le tableau de transferts conserve les tentatives de la fenêtre courante, comme auparavant. Il ne remplace pas les traces serveur persistantes de validation des tickets livrées en v0.76. Les fichiers restent simulés et aucun serveur FTP réel n'est contacté. Les API, règles de permission, confirmations d'écrasement et contrôles de révision sont conservés.

Ce bloc porte sur le client FTP. Il ne refond pas encore l'administration FTP ni les autres applications du bureau. Il ne restaure pas automatiquement l'état visuel du client après fermeture de sa fenêtre.

## Tests

38 suites JavaScript vertes, dont une nouvelle recette du client : recherches sans requête, sélection masquée désactivée, sélection stable, panneau de transferts, distinction session/transport/service, refus d'authentification et absence de reconnexion automatique. Les tests existants conservent les vérifications d'écrasement annulé, révision d'envoi, effacement du mot de passe et refus de transfert. Analyse syntaxique du script du bureau verte.

Backend Python et générateur inchangés ; pas de nouvelle recette de ces suites pour ce bloc UI. Le rendu réel n'est pas validé ici : Chromium était indisponible lors de la v0.77 et son téléchargement avait échoué. Les tests de cette version utilisent un DOM simulé, pas un navigateur graphique.

## Recette Chrome / Windows à effectuer

1. Ouvrir le client FTP : mot de passe absent de la fenêtre principale ; listes locale/distante identifiables ; aucune connexion déclenchée seule.
2. Filtrer chaque liste : compteur correct, aucune opération réseau induite. Masquer une sélection puis effacer le filtre : le fichier ne doit pas redevenir sélectionné automatiquement.
3. Se connecter, choisir un fichier distant et télécharger : constater le panneau de transfert ouvert et le résultat réel de l'API simulée.
4. Refuser un écrasement local ou distant : aucun nouveau transfert ne doit être lancé.
5. Tester un retour réseau non vérifié, un service arrêté et un compte refusé : ne pas confondre la session avec le réseau ou les droits.
6. Redimensionner la fenêtre à environ 900 puis 500 pixels : listes utilisables, boutons lisibles, aucun débordement hors de la fenêtre. Vérifier les focus clavier et les longs noms.
7. Fermer/rouvrir l'aide, le journal et le panneau de transferts. Vérifier que l'interface ne perd pas la sélection au simple clic.
