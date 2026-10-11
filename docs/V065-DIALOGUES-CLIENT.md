# v0.65 — Dialogue client contextualisé

## Livré

Pour les incidents simultanés des grandes entreprises, les questions du centre de tickets sont adaptées à la famille : les accessoires ne proposent plus des questions sur les fichiers ou le ping. Poste, ressource et tâche sont identifiés depuis le contexte du signalement : adresse UNC de Documents, file d’impression, dépôt FTP et compte utilisateur.

Le récit initial est conservé séparément de l’état actuel. Les essais au signalement et les nouveaux retests sont datés et limités à vingt entrées ; le fil de conversation garde soixante réponses. Le demandeur ne donne pas la cause technique privée. Il ne prétend pas avoir vérifié les autres postes ni connaître une intervention technique non observée.

Un nouveau retest évalue le poste ciblé avec les moteurs existants. Il ne lance ni ping ni modification de fichier, ne connecte pas automatiquement le compte et ne répare aucun paramètre. La question d’enregistrement est un contrôle des autorisations, pas une écriture effective. Une résolution DNS réussie ou un service FTP joignable ne sont jamais présentés comme une preuve d’accès aux fichiers. Une preuve réseau du poste principal, d’un autre poste, périmée ou datée dans le futur ne suffit pas pour répondre au nom du poste concerné.

Si l’affectation du compte a changé depuis le signalement, les essais de session et d’accès ne valident pas l’ancien demandeur. Les tickets précédents restent lisibles ; faute d’historique initial, aucune tentative ni heure n’est inventée. Les événements en attente de découverte ne peuvent pas être interrogés comme des clients ayant déjà signalé une panne.

## Portée et limites

Moteur déterministe à questions proposées, sans LLM et sans dialogue libre. La nouvelle logique concerne les incidents `INC-LIVE` ; les scénarios historiques et les demandes de déploiement conservent leur moteur. Les boutons de l’ancien panneau Workspace gardent leurs libellés historiques : la sélection par famille est livrée dans le centre de tickets.

Le moteur ne simule pas encore un salarié autonome, des conversations entre collègues ou une procédure métier complète. Les retests restent des évaluations de fonction : imprimer n’envoie pas réellement une feuille, et le contrôle FTP ne réalise pas un transfert. Packet Tracer demeure la source de preuve réseau.

## Validation

Treize tests ciblés : questions par famille, ressource distante précise, imprimante nommée, historique stable, absence de divulgation administrative, isolation des preuves, application manquante, absence de mutation et de ping, anciennes sauvegardes, événement caché, changement de compte, limites d’historique et distinction DNS/fichiers. Suite unifiée et syntaxe du centre Tickets vérifiées avant livraison. La recette visuelle sous Windows et PT9 reste à faire.
