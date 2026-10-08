# v0.47.2 — Demandes contextualisées

## Ce qui change pour l’utilisateur

Les nouveaux tickets ont trois formulations par famille, avec le nom réel du demandeur, l’entreprise, le poste et son numéro de série. Une urgence déclarée accompagne la demande : préparation habituelle, travail en attente ou besoin prioritaire. Le panneau de contexte explique la priorité initiale. Tu peux ajuster la sévérité après diagnostic.

Le titre de ces nouvelles demandes reste identique après leur prise en charge. La plainte initiale reste visible dans le contexte et figure dans l’export du compte rendu. Les consignes techniques détaillées restent produites par le moteur de panne : les fichiers, services et actions nécessaires ne sont pas remplacés par un texte libre.

La durée choisie avant prise en charge est transmise à la préparation du scénario. Cela inclut les exercices sans limite. Le mode Entraînement/Défi sélectionné sur le ticket est conservé ; le chrono démarre seulement après préparation réussie.

## Réalisme et limites

L’impact déclaré reste **une personne**. Le logiciel ne prétend pas avoir observé une panne générale ou vérifié l’urgence du demandeur. Une sévérité critique n’est pas tirée au hasard pour un incident individuel. Les trois niveaux initiaux sont faible, modérée et élevée ; leur origine est affichée et ils restent modifiables.

Le catalogue couvre 9 familles (7 dans le catalogue automatique Varié), avec 27 formulations et 3 profils d’urgence. Il s’agit de variations de présentation, pas de 81 nouvelles pannes techniques. Les causes et les contrôles restent ceux des moteurs existants.

La formulation utilise un sous-tirage dédié `:ticket-wording:v1`, indépendant du choix de famille, de poste et de cause. Même seed et même numéro de réception : mêmes variantes. Les textes n’ont pas accès à la cause privée et ne dévoilent aucun mot de passe.

Les entreprises et tickets déjà sauvegardés ne sont pas réécrits. Un ancien ticket sans contexte déclaré reste utilisable. Les nouvelles demandes créées dans ces entreprises profitent des nouvelles formulations.

## Données

`request_context` stocke la version, le demandeur, l’entreprise, le poste, le numéro de série, la plainte, la portée déclarée, l’urgence et son motif. Le plan original conserve sa durée initiale pour la traçabilité ; la durée réellement choisie figure dans le chronomètre du ticket et dans `timer_minutes` de l’incident préparé.

## Vérification manuelle

Créer des demandes de la même famille avec des seeds différentes ; observer les formulations et le contexte. Rejouer une seed pour retrouver le même tirage. Choisir 15 minutes ou Sans limite sur une demande avant prise en charge ; vérifier le chrono après préparation. Le titre doit être conservé et les consignes de réparation apparaître. Vérifier un ancien ticket sans contexte déclaré.

Les tests Python vérifient les tirages, l’identité du poste, la priorité et la durée transmise au moteur. Les tests JavaScript vérifient le contexte affiché et la compatibilité avec les anciens tickets. Le rendu visuel et les interactions natives Packet Tracer restent à vérifier dans l’environnement utilisateur.
