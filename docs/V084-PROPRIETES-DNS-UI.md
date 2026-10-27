# v0.84 — Propriétés des enregistrements DNS

La fenêtre identifie l’enregistrement et sa zone avec une icône DNS. Les champs sont regroupés dans une grille ; une aide et un exemple adaptés au type A, AAAA ou CNAME accompagnent la valeur. Changer de type ne remplace pas la valeur saisie et ne déclenche aucune requête.

L’explication du TTL précise que les caches ne sont pas purgés par une modification. La suppression, avec confirmation, occupe une section distincte du bouton Enregistrer.

Les commandes et champs sont bloqués pendant l’opération. Une entrée supprimée, une entrée disparue ou une console devenue indisponible ne réactive plus ses commandes à la fin de la requête. Un retour de la console peut réactiver les propriétés encore valides sans écraser les saisies. Une fenêtre explicitement supprimée reste bloquée.

## Périmètre et limites

Aucune modification des permissions, routes ou règles DNS. Les types disponibles restent A, AAAA et CNAME. Cette interface de propriétés conserve des champs : ils correspondent aux valeurs que l’administrateur doit configurer. Pas de nouvelle simulation de réplication ou de zone secondaire.

Les saisies ne sont pas sauvegardées comme brouillon après fermeture. Après création, la fenêtre reste une fenêtre de création ; ouvrir l’entrée depuis la liste pour en modifier les propriétés. Un échec d’actualisation après mutation peut encore nécessiter une vérification dans la liste avant de soumettre à nouveau.

## Vérification

Test dédié : icône et zone, aide par type sans perte de saisie ni requête, protection contre un double envoi, confirmation annulée sans mutation, suppression suivie de commandes désactivées, création sans bouton Supprimer. Les 44 suites JavaScript passent pour cette version.

Derniers résultats du cœur et des ateliers Python : 19/19 et 8/8 en v0.79 ; ces fichiers sont inchangés et les suites ne sont pas relancées pour cette passe UI. Tests web Python non relancés. Aucun rendu navigateur graphique vérifié ici.

## Recette Chrome restante

Ouvrir les propriétés d’une entrée, changer son type et vérifier l’aide, le focus et la conservation de la valeur. Réduire la largeur de la fenêtre. Vérifier le défilement et la séparation visuelle de la suppression. Tester un refus d’opération, une console indisponible puis son retour. Supprimer une entrée : la fenêtre doit rester bloquée. La configuration client DNS reste à retravailler.
