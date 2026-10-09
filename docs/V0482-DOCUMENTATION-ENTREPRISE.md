# v0.48.2 — Documentation de l’entreprise

## Livré

Dans le bureau du technicien, l’application Documentation présente les ressources de l’environnement en plus du manuel de formation existant. Les quatre articles d’entreprise décrivent le parc représenté, les conventions d’identification, les repères du domaine et du serveur de fichiers, et une méthode générale d’intervention.

Les noms et adresses viennent de la sauvegarde : la seed les détermine lors de la génération. Aucun tirage indépendant n’invente une autre entreprise. Les changements enregistrés sont repris dans le prochain état chargé ; fermer et rouvrir Documentation renouvelle son instantané.

La lecture utilise l’état déjà chargé par le bureau, sans ping, connexion distante, modification ni requête supplémentaire. Une ancienne sauvegarde bénéficie des articles sans migration. La recherche porte sur les titres, catégories et paragraphes des deux sources.

## Limites explicites

Les adresses sont des références configurées, pas une preuve de disponibilité. Aucun secret, diagnostic courant, droit caché ou cause de panne n’est extrait. Les consignes génériques sont annoncées comme pédagogiques ; aucune politique interne propre à l’entreprise n’est inventée. Le répertoire ne prétend pas couvrir tout le personnel. Ceci ne livre pas encore une base documentaire éditable ni des politiques procédurales complètes.

## Recette manuelle

1. Reprendre une session existante, ouvrir le bureau du technicien puis Documentation.
2. Rechercher un nom de poste ; ouvrir Ressources de l’entreprise et comparer les noms/adresses aux fiches.
3. Ouvrir les repères d’accès : comparer le domaine et le serveur documentaire à l’environnement. Une donnée manquante doit rester « non renseignée ».
4. Vérifier que les procédures Stock et FTP restent accessibles depuis leurs aides.
5. Couper un câble : la documentation seule ne doit pas lancer de ping ni affirmer que le service est disponible.
6. Reprendre une autre entreprise puis son bureau : les ressources doivent correspondre à cette entreprise.

Tests automatisés : absence de fuite de secrets et causes cachées, absence de mutation, stabilité malgré des observations différentes, compatibilité d’un état ancien/incomplet ; intégration UI avec recherche et lecture sans requête réseau supplémentaire. Le visuel et le comportement sous Windows / Packet Tracer 9 restent à tester réellement.
