# v0.98 — Retrouver son contexte de travail dans les tickets

La liste conserve recherche, filtre de statut, filtre de sévérité et identifiant sélectionné dans le stockage de session du navigateur, par entreprise. Les paramètres sont contrôlés avant réutilisation ; un identifiant supprimé n’est pas réactivé.

Le détail conserve son onglet : Demande, Communication, Intervention, Vérifications et aide ou Guide. Le stockage reste séparé par entreprise et ticket.

Un compteur indique les tickets affichés par rapport au total. Réinitialiser les filtres remet les trois contrôles à leur état général. Le bouton reste masqué lorsqu’aucun filtre n’est appliqué.

Un lien explicite depuis la messagerie prend la priorité sur les filtres mémorisés uniquement s’il désigne un ticket de l’entreprise active. Il ne sélectionne pas une autre entreprise. Les filtres sont alors remis à zéro pour permettre l’affichage du ticket demandé.

## Limites

La préférence est locale au même onglet et navigateur. Elle n’enregistre pas les brouillons de notes ou de messages et ne remplace pas leur enregistrement explicite. Elle n’affecte ni les statuts ni les vérifications des tickets.

## Validation

52 suites JavaScript passent. Les tests couvrent les filtres et sélections séparés par entreprise, le lien direct, les identifiants obsolètes, l’indisponibilité du stockage et le rétablissement de l’onglet du ticket.

La recette visuelle et l’utilisation prolongée dans Chrome restent ouvertes.
