# v0.33 — Impression et transferts sur le bureau

Cette version reprend les interfaces Imprimantes et Client FTP. Elle utilise les moteurs, routes, contrôles d’accès et fichiers de session existants. Aucun changement du format de sauvegarde, aucune dépendance Python ajoutée.

## Imprimantes

L’application affiche une imprimante sélectionnée, son état et un tableau des travaux qui lui appartiennent. Choisir la file PDF n’affiche plus les travaux de l’imprimante de bureau, et inversement.

- Le tableau présente document, état, détail et annulation pour un travail encore en attente ou bloqué.
- Le document local à imprimer et la file sont choisis séparément.
- Les réglages sont regroupés dans « Configurer cette imprimante » : imprimante par défaut, suspension, mode hors connexion, pilote, spouleur, adresse du port et papier.
- Les actions de suspension, hors connexion et spouleur indiquent leur effet selon l’état courant. Les réglages de papier et de port sont désactivés pour la file PDF.
- La sélection de l’imprimante est conservée lors de l’actualisation.
- Les opérations simultanées sont bloquées et le sélecteur d’imprimante est désactivé pendant une requête.

L’actualisation est manuelle dans cette application. Le moteur reste responsable de l’évolution des travaux, des pannes et des autorisations administratives. Un travail accepté peut rester bloqué ; le message d’envoi n’annonce pas qu’il a été imprimé.

## Client FTP

Deux panneaux distinguent les fichiers du poste et du dépôt. Sélectionner un fichier ne déclenche aucun transfert. Les boutons indiquent la direction : téléchargement vers le poste ou envoi vers le dépôt.

- L’utilisateur se connecte explicitement avec le compte de formation.
- Les transferts sont indisponibles sans connexion et sans fichier sélectionné.
- Une liste distante devenue inaccessible est retirée ; le code d’erreur apparaît dans le message et l’historique.
- Remplacer un fichier homonyme demande confirmation avant l’envoi ou le téléchargement.
- L’envoi transmet la révision retournée par le moteur, pour conserver la détection des conflits.
- Le mot de passe est effacé après la tentative de connexion. L’historique n’enregistre ni mot de passe ni contenu de fichier.
- L’historique affiche les trente dernières entrées de cette fenêtre et disparaît à sa fermeture.
- Plusieurs opérations ne peuvent pas être lancées simultanément depuis la même fenêtre.

Le statut « connecté » signifie que la connexion de contrôle a été acceptée. Le moteur peut encore refuser une liste ou un transfert : canal de données bloqué, permissions, réseau, capacité ou session expirée. Un transfert effectué peut être suivi d’une erreur d’actualisation ; son succès reste alors inscrit dans l’historique.

## Validation et limites

`node web/test_desktop_ui.js` vérifie les applications avec des réponses API contrôlées : filtrage des travaux, annulation avec le bon identifiant, connexion FTP, effacement du mot de passe, téléchargement, confirmation avant remplacement, révision lors de l’envoi, retrait d’une liste inaccessible et désactivation après déconnexion. Les tests existants de l’explorateur et des paramètres restent exécutés.

Suites Python web, générale et ateliers requises avant livraison. Les tests DOM et Python ne constituent pas une validation visuelle de Windows/OS.js ni un nouveau test réel du pont Packet Tracer.

L’impression et FTP restent simulés. Les preuves ICMP provenant de Packet Tracer ne valident pas les protocoles réels d’impression ou FTP. Pas de dossiers FTP imbriqués, fichiers binaires, reprise de transfert ni barre de progression : l’interface attend la réponse réelle du moteur. Aucun LLM intégré dans ce bloc.
