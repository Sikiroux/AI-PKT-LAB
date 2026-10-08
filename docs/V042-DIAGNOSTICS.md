# v0.42 — Diagnostics et correctifs regroupés

Ce bloc reprend les correctifs reçus après v0.41 : `IcmpProcess` confirmé par le diagnostic réel de Damien, fond transparent OS.js pour les icônes, et absence de défilement global du bureau.

## Utilisation

Dans le bandeau principal, ouvrir **Paramètres et diagnostics**. Sur le portable du technicien, la même fenêtre est une application **Diagnostics**.

- **Actualiser les informations** lit le dernier état web : aucun ping et aucune modification réseau.
- Sélectionner un poste affiche son identité, son numéro de série, son IP, l’environnement et les fichiers associés.
- **Vérifier ce poste** demande un contrôle discret ciblé. Un contrôle manuel peut accélérer le temps global de Packet Tracer ; cela ne concerne pas seulement ce PC. La surveillance périodique reste sans accélération.
- **Exporter le rapport** produit un JSON limité aux identités et preuves nécessaires. Aucun mot de passe, jeton HTTP ou contenu de l’annuaire n’est inclus.

Les prérequis de prise en main distinguent la preuve ICMP, l’accès du technicien, le service distant et le compte actif. Un refus du technicien ne réécrit plus la preuve réseau en échec. Un service arrêté n’affiche plus un ping réussi comme explication du refus.

Une preuve absente ou périmée reste **non vérifiée**, jamais une panne Internet confirmée. ICMP est un indicateur de transport : il ne prouve pas SMB, RDP ou l’accès Internet. Les préconditions restent ordonnées ; une étape bloquée ne signifie pas que tous les services suivants sont en panne.

## Limites

La fenêtre présente les contrôles existants. Elle ne répare rien, ne relance pas automatiquement le pont et ne révèle pas le catalogue interne des causes. Les observations ne sont pas des mesures CPU/mémoire. Aucun mécanisme de reprise des anciennes sauvegardes n’est changé dans ce bloc.

Le nom `IcmpProcess` et l’affichage des icônes ont été confirmés par Damien avant regroupement. La nouvelle fenêtre et la nouvelle disposition doivent encore être essayées dans son navigateur et Packet Tracer.
