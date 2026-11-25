# Correctif v111 — Chargement CSS

Le lien versionné /workspace-design.css?v=111 n’était pas reconnu par la route HTTP comparant le chemin complet. Le HTML revient au lien canonique ; la route utilise maintenant urlparse pour accepter également une query string. Les réponses CSS utilisent déjà Cache-Control: no-store.

Validation : deux tests Python sur le véritable corps du gestionnaire HTTP (CSS canonique et versionnée, contenu de la feuille, lien HTML) ; test JavaScript de l’intervention compacte. Aucun changement de surveillance Packet Tracer.

Fermer complètement le logiciel puis extraire le correctif à la racine du dossier contenant LANCER-BUREAU.bat. Relancer ensuite le logiciel.
