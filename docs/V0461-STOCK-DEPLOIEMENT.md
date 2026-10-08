# v0.46.1 — Préparation visuelle du matériel de réserve

## Parcours

Dans le bureau du technicien, ouvrir **Parc et stock**, puis **Préparer ce matériel**. L’atelier affiche le nom et le numéro de série de l’article choisi. Suivre la consigne affichée : image, support de démarrage, pilote de stockage si nécessaire, sauvegarde, partitions, installation et paramètres du premier démarrage.

Le bilan doit être entièrement réussi pour enregistrer la remise à un employé. Cliquer sur **Retour au stock**, actualiser le stock, puis choisir l’employé et enregistrer la remise. Une image incorrecte ou un autre contrôle en échec bloque la remise. L’atelier générique Déploiement reste indépendant : réussir cet atelier ne prépare pas arbitrairement un article du stock.

La restitution efface la préparation du cycle précédent et demande une nouvelle installation simulée. Une ancienne fenêtre ne peut pas appliquer une action au nouveau cycle. Une réinitialisation dans le même cycle incrémente aussi la révision de l’atelier.

## Sauvegarde et compatibilité

L’article contient désormais son propre état `deployment`. Le premier état est déterminé par la seed, l’identifiant de l’article et son cycle. Chaque action de l’atelier est sauvegardée et incrémente la révision du stock. Reprendre la sauvegarde reprend les étapes déjà réalisées ; consulter un état initial ne modifie pas la session.

Les articles déjà attribués en v0.46 restent attribués. Une ancienne déclaration manuelle de préparation ne suffit plus pour une nouvelle remise. L’historique antérieur est conservé. Les nouvelles routes sont `/workspace/inventory/deployment-state` et `/workspace/inventory/deployment-operation`, toujours limitées à l’environnement actif et au contexte entreprise.

## Limites

Il s’agit d’une installation simulée sur un disque virtuel pédagogique. Aucun Windows réel ou poste Packet Tracer n’est réinstallé. Le matériel de réserve n’est pas encore inséré dans le réseau et ne remplace pas automatiquement le PC de l’employé. L’identité, le cycle d’installation et la remise sont liés ; la connexion réseau reste un chantier distinct.

L’atelier reprend les mécanismes existants : ce n’est pas une reproduction intégrale du programme d’installation Microsoft. Pas de nouveaux protocoles réseau ou de ping automatique pour une opération locale de stock.

## Tests

Cycle complet par les opérations du moteur, mauvaise image, contournement par déclaration manuelle, atelier générique sans effet sur le stock, protection contre un ancien cycle, sauvegarde/reprise et état réseau inchangé. Le test DOM vérifie l’identifiant matériel, le cycle et la révision transmis depuis la fenêtre d’installation. La validation visuelle dans un navigateur et la validation native Packet Tracer restent séparées.
