v114 — Diagnostic ciblé des lectures d’inventaire

Le nettoyage manuel des logs n’a pas entraîné de baisse de RAM observée.
Les essais précédents orientent vers les lectures d’inventaire, sans prouver une fuite définitive.

Ferme complètement NetOps avant de remplacer les fichiers dans ton dossier actuel.
Lance LANCER-DIAGNOSTIC-RAM.bat. Les contrôles ordinaires restent suspendus.

Pour commencer : A · Nombre d’appareils uniquement, pendant 3 minutes.
Note la RAM au départ, à la fin puis une minute après. Exporte le journal JSON.
Ensuite, redémarre Packet Tracer avec le même fichier et reconnecte le bridge avant chaque essai :
B · Identité (nom, modèle, numéro de série), sans interfaces.
C · Interfaces et propriétés IP, sans liens ni voisins.
D · Liens et voisins, sans propriétés IP.
Les lectures sont indépendantes ; C et D doivent parcourir les appareils et leurs ports.
Garde le même onglet du bridge et le même réseau pour tous les essais.
Aucun changement de configuration réseau. Aucun nettoyage automatique dans ces quatre tests.

Les journaux comptent les appels moteur et leurs octets, pas la RAM de Windows.
Une réponse en erreur arrête l’essai. Aucun inventaire complet de préparation pour A–D.
Le mode expérimental nettoyage est retiré de la liste après son échec de confirmation sur PT.
Le fonctionnement de surveillance normal conserve sa cadence actuelle.

Validation locale : 18 tests réussis, dont exécution des scripts dans Node avec API simulée,
isolation des lectures, journalisation, arrêt sur erreur et routes HTTP du diagnostic.
La compatibilité native et la RAM réelle restent à mesurer sur ton Packet Tracer.
