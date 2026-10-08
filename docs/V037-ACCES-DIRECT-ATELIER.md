# v0.37 — Accès direct à l’atelier

Dans un ticket de déploiement, **Ouvrir l’atelier de déploiement** ouvre le bureau du technicien dans un nouvel onglet et lance directement l’application après le démarrage OS.js. Le lien conserve l’identifiant de l’environnement ; les gardes existantes refusent un bureau d’une ancienne entreprise.

La consigne s’affiche ouverte au début et lors du choix d’image. Aux étapes suivantes elle reste disponible dans le panneau latéral. Les autres tickets gardent leur bouton Voir les postes.

Le serveur reconnaît le chemin du bureau même avec le paramètre `?app=deployment`. Ce paramètre sélectionne seulement une application connue, sans exécuter de commande fournie par l’utilisateur. Un bureau client n’ouvre pas cet atelier automatiquement.

Vérification : syntaxe JavaScript, intégration DOM des applications, route du bureau avec paramètre, tests généraux et ateliers. L’ouverture réelle du nouvel onglet et le rendu visuel demandent encore une vérification dans le navigateur de l’utilisateur.
