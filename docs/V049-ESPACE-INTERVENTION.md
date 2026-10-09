# v0.49 — Espace d’intervention et cycle des tickets

## Parcours livré

Sélectionner un ticket puis activer Écran partagé ouvre Postes avec un panneau de ticket actionnable à gauche et un outil intégré à droite. Le panneau reprend la demande, les statuts, les suivis, la proposition de solution, les notes, le chrono et l’export. La prise en charge, l’attente et la vérification restent disponibles selon le statut et la préparation du scénario. Les actions ciblent le ticket épinglé, pas une sélection implicite d’un autre onglet.

Le bureau du technicien s’ouvre par défaut. Prendre la main sur le poste du ticket utilise son numéro de série et déclenche la connexion uniquement sur clic. Aucun poste par défaut n’est choisi quand l’identité manque. La liste des postes est aussi accessible. Le bureau intégré n’est pas rechargé par les rafraîchissements ordinaires ; une reconnexion explicite recharge une session distante fermée. Les sessions web continuent de surveiller leurs prérequis réseau avec le mécanisme existant.

Le panneau se redimensionne avec son curseur ou sa séparation, à la souris et au clavier (flèches gauche/droite, limites 300–640 pixels). L’espace des outils peut être agrandi, réduit puis rouvert. Sur un petit écran, les parties se présentent verticalement. Quitter l’écran partagé masque l’outil mais ne constitue pas une déconnexion distante ; utiliser la commande Déconnecter du bureau pour cela.

Les rafraîchissements périodiques ne reconstruisent pas le panneau pendant la saisie. Les notes, suivis et motifs de réouverture ont des brouillons séparés. Les suivis et motifs sont indexés par entreprise et ticket. Un changement d’entreprise détache le ticket et retire le bureau intégré de l’ancienne session.

## Résolution

1. Enregistrer une proposition de solution, ou à défaut un compte rendu d’au moins 20 caractères.
2. Vérifier et marquer résolu : les mêmes critères de réparation qu’à la clôture précédente sont exécutés. Un échec ou un résultat inconnu ne donne pas une réussite automatique. Les ateliers à tests manuels conservent leur déclaration explicite.
3. Le ticket passe à Résolu, confirmation attendue. Il reste ouvert et ne libère pas le scénario pour une autre intervention. Le chrono de réparation est terminé à cette étape.
4. Déclarer le retour favorable du demandeur puis Confirmer et clôturer. La déclaration est faite par l’apprenant, pas générée par le client ou un LLM. La confirmation porte sur l’identifiant de la résolution actuelle ; une ancienne confirmation est refusée. Les contrôles de réparation sont exécutés de nouveau : une panne revenue empêche la clôture.

Le statut Résolu n’est pas une preuve de disponibilité permanente. L’attribution reste celle du technicien de la session, pas un système multi-utilisateurs.

## Réouverture

Un ticket résolu ou clos peut être rouvert avec un motif de 5 à 1000 caractères. Son ancienne résolution et son chrono sont archivés dans l’historique. Les résultats de contrôle, la date de vérification et les dates finales actives sont effacés ; un nouveau contrôle est obligatoire. Un nouveau chrono de même durée démarre si le ticket était chronométré.

La réouverture ne recrée pas de panne. Pour un ticket d’entreprise, elle est refusée si une autre intervention utilise déjà l’environnement ou si le scénario original a été remplacé. Les incidents historiques de même famille ne peuvent pas être rouverts en parallèle d’un autre ticket de cette famille. Les observations Packet Tracer ne sont pas inventées ni réécrites comme réussies.

## Compatibilité et limites

Aucune migration obligatoire. Les tickets anciens clos restent clos. L’ancienne action API close reste compatible pour les anciens usages, avec ses contrôles de réparation ; le nouveau parcours de l’interface utilise resolve puis close avec confirmation. Ce n’est pas une reproduction complète de GLPI : pas de droits multi-techniciens, de notification réelle, d’escalade, de tâches planifiées ni de réponse autonome du demandeur. Les services, les topologies et le pont ne sont pas étendus par ce bloc.

L’export contient la résolution courante, sa confirmation déclarée, les changements de statut et les anciennes résolutions/chronos archivés. Les tests automatisés ne valident pas le rendu sous Windows ni le fonctionnement réel de Packet Tracer 9.

## Recette manuelle

- Reprendre une ancienne sauvegarde ; sélectionner un ticket puis Écran partagé. Vérifier que la bonne entreprise et le bon poste sont affichés.
- Redimensionner le panneau avec souris, curseur et clavier ; agrandir/réduire/rétablir les outils. Sur petit écran, contrôler la présentation verticale.
- Ouvrir les applications du technicien. Écrire un suivi et attendre plusieurs rafraîchissements : le champ et son brouillon doivent rester stables.
- Prendre la main sur le poste du ticket, contrôler son identité. Après une déconnexion ou coupure, reconnecter explicitement ; le bureau doit se recharger.
- Enregistrer une solution sans réparer : marquer résolu doit être refusé.
- Réparer puis marquer résolu : le chrono s’arrête, le ticket reste ouvert. Sans confirmation, la clôture doit être refusée.
- Couper la connexion après résolution, puis demander la clôture avec confirmation : le contrôle frais doit la refuser. Rétablir, confirmer et clôturer.
- Rouvrir avec motif : ancien résultat archivé, contrôles effacés, nouveau chrono. Si un autre scénario a remplacé celui du ticket, la réouverture doit être refusée.
- Exporter le compte rendu ; vérifier résolution, confirmation déclarée, suivis et historique.
- Reprendre une autre entreprise : aucun ancien bureau ni ticket épinglé ne doit rester affiché.

Les tests couvrent les transitions, la confirmation liée à la résolution, les critères frais, les anciennes actions, les scénarios remplacés, les archives, la protection de la saisie, les identités ciblées et la reconnexion explicite.
