# v0.47 — File de demandes procédurales

## Utilisation

Crée une **nouvelle entreprise**, avec une seed vide pour un nouveau tirage ou une seed connue pour le rejouer. Son réseau initial est sain : le premier ticket est une demande en attente, choisie parmi impression, FTP, poste, accessoires, AD, fichiers et DNS. Les anciennes entreprises conservent leur ticket et leur panne actuels.

Dans **Tickets → Arrivées automatiques**, règle l’intervalle fixe ou aléatoire, le catalogue, le niveau, la durée et le plafond de tickets ouverts. Par défaut, une demande arrive toutes les 5 minutes jusqu’à 3 tickets ouverts. Une seule arrivée est traitée après une longue absence, sans rattrapage massif. Le redémarrage du logiciel met les arrivées en pause ; clique sur Reprendre.

Plusieurs demandes peuvent attendre. **Prendre en charge** prépare le scénario précis et démarre le chronomètre. Termine et clôture ce scénario avant d’en prendre un autre. La réception ne lance aucun ping et ne modifie aucun service. Les accessoires locaux se préparent sans contrôle réseau ; les autres familles demandent une preuve réseau fraîche au moment de la préparation.

## Procédural, précisément

La seed de l’entreprise et le numéro persistant de réception déterminent la famille, le poste compatible et une seed de scénario. Les règles restent dans un catalogue : ce n’est pas un LLM qui invente librement les pannes. Les variantes de pannes applicatives et multi-services utilisent cette seed dédiée. Les demandes de préparation/déploiement explicitement sélectionnées réutilisent leurs moteurs existants.

Le catalogue automatique varié contient **7 familles** ; le catalogue Applications ajoute les préparations de poste et déploiements. Les scénarios multi-services peuvent cumuler 1 à 3 couches simulées AD/fichiers/DNS. Ils n’injectent pas de panne réseau physique à la réception ou à la prise en charge. Les interventions réseau manuelles restent disponibles séparément et utilisent leurs protections existantes.

## Architecture

`ticket_arrivals.py` produit un plan versionné, stocké dans `tickets.json`, puis prépare l’incident lors de la prise en charge. L’identifiant de demande reste identique après préparation. La cadence aléatoire utilise une suite reproductible indépendante du tirage des scénarios. Le plafond compte tous les tickets ouverts.

Un seul exercice préparé à la fois protège les états partagés AD, DNS et fichiers. Ce n’est donc pas encore une simulation de plusieurs pannes techniques simultanées. Les demandes reçues correspondent à des exercices différés ; leur symptôme technique est matérialisé à leur activation.

## Vérification utilisateur à faire dans Packet Tracer 9

Créer plusieurs entreprises avec des seeds différentes ; vérifier que le réseau initial est connecté et que les familles de premier ticket varient. Régler un intervalle de 1 minute et un plafond de 3 ; conserver le ticket courant, observer les nouvelles demandes sans changement réseau, puis clôturer et prendre la suivante. Reprendre une sauvegarde et vérifier que la file reste intacte et les arrivées sont en pause. Les tests Python et JavaScript ne prouvent pas les interactions natives Packet Tracer.
