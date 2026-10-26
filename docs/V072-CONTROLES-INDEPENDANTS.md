# v0.72 — Contrôles réseau indépendants

## Défaut constaté

La surveillance appelait la résolution stricte de toutes les identités déclarées avant de lancer le moindre contrôle. Une imprimante ou un autre poste absent ou ambigu bloquait ainsi également le contrôle technicien → annuaire, sans que ce trajet ait été mesuré.

## Changement

La surveillance accepte une résolution partielle des identités par numéro de série. Elle mesure seulement les trajets dont les appareils source et cible ont une identité unique. Les autres trajets reçoivent un résultat inconnu, avec les appareils non identifiés indiqués dans le détail. Une identité sans numéro de série n'est jamais acceptée.

Le fichier Packet Tracer ouvert doit toujours correspondre à celui de l'entreprise. Un mauvais fichier ou un échec global du snapshot rend toute l'observation inconnue : aucune ancienne réussite n'est recyclée.

Les contrôles distants, fichiers, annuaire, impression et passerelle VPN sont collectés par trajet. En mode discret, les trajets disponibles, y compris la passerelle VPN extérieure, utilisent un même lot. Les erreurs des résultats individuels restent locales ; une erreur globale du lot ou une longueur de réponse incohérente laisse les trajets du lot inconnus. Le mode ancien par ping garde les exceptions locales au trajet.

Pas de commande de configuration, pas de création d'appareil, pas de réparation, pas de reconnexion Windows automatique. La surveillance périodique ne demande pas d'accélération ; les demandes explicites conservent leur paramètre existant. Les opérations de modification continuent d'exiger toutes les identités via le mode strict par défaut.

## Limites

Un résultat positif reste un proxy ICMP entre les adresses attendues. Il ne démontre pas un fonctionnement réel de SMB, AD, DNS ou FTP. L'état simulé de ces services reste évalué séparément. Un lot discret globalement indisponible ne permet pas de connaître ses résultats individuels ; aucun ping de secours supplémentaire n'est ajouté.

## Recette Windows / Packet Tracer 9 à faire

Dans une copie d'entreprise de test :

1. Mesurer l'état initial, puis retirer une imprimante. Le contrôle impression doit devenir non vérifié ; le trajet annuaire doit encore être mesuré et ne peut être positif que s'il répond réellement.
2. Retirer un poste secondaire : les autres postes et les services du technicien ne doivent pas devenir inconnus uniquement à cause de cette absence.
3. Retirer le poste ciblé : sa connexion distante doit être refusée, mais le contrôle technicien → serveur doit rester possible.
4. Couper un câble au lieu de retirer l'appareil : un échec ICMP observé doit rester un échec, distinct d'une identité introuvable.
5. Ouvrir un autre fichier PT : tous les contrôles doivent rester bloqués, sans réparation ni clôture implicite.
6. En télétravail, vérifier que le lot comprend le trajet passerelle VPN et que la surveillance périodique n'accélère jamais PT.

## Tests

Neuf nouveaux tests couvrent appareils manquants, isolation des exceptions, résultats discrets invalides, taille de lot, passerelle VPN, identité stricte et refus d'un mauvais fichier. Adaptation du double de test de cohérence à l'argument de résolution partielle. Suite web relancée ; générateur, ateliers et JavaScript inchangés depuis leur recette v0.70. Validation réelle PT9 requise.
