# v0.89 — Actualisation et accès à la messagerie

- Raccourci Messagerie dans la barre du bureau technicien.
- Filtres Toutes, Non lues et Épinglées ; filtre conservé dans le même onglet et environnement.
- Action Marquer comme lue.
- Actualisation automatique toutes les cinq secondes lorsque la fenêtre peut être consultée.
- Suspension lorsque l’onglet est masqué, le bureau verrouillé ou la fenêtre réduite.
- Arrêt du minuteur à la fermeture et au changement de session ; une réponse tardive ne redessine pas une fenêtre fermée.
- Aucune reconstruction de la conversation si les données n’ont pas changé. Conservation des positions de défilement lors d’une mise à jour.
- Une action lancée pendant une actualisation attend sa fin et conserve son ticket cible.
- Date du dernier rafraîchissement réussi, retour d’erreur et message de rétablissement de la connexion.

## Validation

Tests de messagerie : réponses sûres, notes explicites, filtres/recherche, arrivée automatique d’un message, conservation du DOM inchangé, suspension, reprise après erreur, fermeture pendant une requête et isolation des environnements.

Les tests ne remplacent pas une recette visuelle dans Chrome. Le moteur de dialogue reste scénarisé ; cette version ne contient pas encore l’IA, les discussions libres avec tous les salariés, le canal collectif ni les incidents réseau automatiques.
