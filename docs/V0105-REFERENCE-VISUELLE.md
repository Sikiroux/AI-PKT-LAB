# v0.105 — détails du centre de tickets

La maquette validée reste la référence de composition. Cette version corrige les conflits hérités de mise en page : navigation compacte, logo aligné, commandes d’en-tête regroupées, colonne de titres sans largeur résiduelle de tableau. Elle ajoute ou reprend les composants suivants dans le code :

- Identifiant de ticket, priorité et statut séparés ; couleurs rouge pâle pour Élevée et jaune pour Modérée.
- Ligne demandeur avec avatar à initiales, poste avec icône et attribution réelle. Aucun nom de technicien ni présence inventé.
- Temps de travail avec icône de chronomètre, calculé depuis le timer existant et actualisé chaque seconde. Le compte à rebours et ses commandes restent dans Options de suivi ; temps travaillé et délai ne sont pas confondus.
- Raccourcis avec icônes vers messagerie, poste et documentation ; menu Actions ; icônes d’attente, vérification et clôture.
- Historique visible depuis la demande, basé sur les entrées enregistrées ; notes d’intervention consultables et modifiables depuis le panneau droit, sans changer leur portée.
- Filtres avec pastilles de compte, dont À moi pour les tickets attribués dans cette session technicien unique.
- Heure courte dans la file, date complète en infobulle.
- État en bas à droite : Dernière synchronisation avec heure et pastille verte après une réponse /state réussie. En cas d’erreur, pastille orange et dernière réussite conservée. Cela indique la synchronisation du serveur local, pas une preuve de réparation ni l’état global du réseau.
- Recherche rapide, accès aux dernières demandes et paramètres du technicien dans l’en-tête. Les dernières demandes sont les tickets existants, sans notification fictive. Le menu de l’application conserve le lancement du bureau technicien.

Le contact utilise la messagerie, pas un appel téléphonique. Le bouton Clôturer ouvre la procédure de résolution existante : il ne contourne pas les vérifications et confirmations. Les informations métier différentes du ticket illustratif de la maquette restent affichées lorsqu’elles sont utiles.

## Vérification

57 suites JavaScript de régression réussies. Tests ciblés supplémentaires sur les valeurs du footer, les états de synchronisation, le format du temps de travail, l’identité du demandeur, les icônes, les raccourcis, les notes et les garde-fous de résolution. Huit tests Electron simulés réussis. Aucun changement du moteur Python dans ce lot.

Le visuel généré est une référence, pas une capture de code exécuté. La recette visuelle sous Electron Windows est encore nécessaire ; aucune correspondance pixel par pixel n’est annoncée sans cette vérification. Les commandes restent identifiées par leurs libellés accessibles.

## Installation

Quitter le simulateur. Extraire la mise à jour à la racine du dossier existant et accepter les remplacements. Conserver les données et node_modules. Relancer LANCER-BUREAU.bat. La version complète ne migre pas les données d’un autre dossier.
