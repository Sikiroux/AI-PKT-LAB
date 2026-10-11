# v0.64 — Première découverte par activité

## Portée

Dans les entreprises de trente employés, les arrivées périodiques appliquent d’abord une panne locale persistante. Une tentative d’activité est programmée 20 à 60 secondes plus tard (délai reproductible depuis la seed et le compteur d’événements). La fonction concernée est alors réévaluée : si elle reste défaillante, le ticket apparaît et son chronomètre démarre. Si elle a été réparée, aucun signalement obsolète n’est ajouté.

Les créations manuelles et la file initiale restent immédiates. Les petits sites et les labs indépendants conservent leur fonctionnement historique.

## Sauvegarde et charge

L’événement, sa mutation et le futur signalement sont enregistrés dans la même sauvegarde entreprise. Les événements en attente réservent leur poste et comptent dans le plafond des interventions. La reprise ne réinjecte pas la panne. Une récupération de tickets ne révèle pas les événements encore en attente. Le statut métier public ne présente pas de ticket caché comme un signalement existant.

La découverte enregistre sa chronologie avant de publier le ticket dans la file indépendante. La pause des arrivées suspend aussi le traitement des découvertes ; les échéances restent des heures réelles, donc les activités échues sont traitées à la reprise. Ce n’est pas encore une horloge métier qui se fige pendant la pause.

## Limites à conserver visibles

Il s’agit d’un contrôle programmé de la fonction locale touchée, pas d’un employé autonome exécutant toutes ses tâches. Les activités sont issues du contexte métier existant ; leur moteur détaillé, les alternatives de travail et les journées simulées restent à développer. Pas de météo, coupure de courant, nouvelle panne VLAN ou Wi-Fi dans cette version. Aucun ping n’est lancé par la découverte. La clôture conserve ses exigences de preuve réseau récente : ce contrôle local ne prouve pas la connectivité Packet Tracer.

## Validation

Tests de mutation avant signalement, absence de récupération anticipée, échéance, publication unique, chronomètre, réparation avant découverte, réservation du poste et reprise depuis la sauvegarde. Suite unifiée requise avant livraison. Le comportement du réseau V2 dans Packet Tracer 9 demeure soumis à sa recette réelle.
