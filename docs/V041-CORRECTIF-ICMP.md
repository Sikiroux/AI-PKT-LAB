# v0.41 — Correctif des événements ICMP

## Diagnostic reçu

La v0.40 retourne « invalid string position » et laisse tous les contrôles réseau inconnus. Le pont reçoit les scripts, mais cela ne prouve pas leur réussite. L’ancien script utilise `p.donePing.connect`, une convention de signal Qt qui ne correspond pas au contrat JavaScript IPC documenté de Packet Tracer.

## Changements

- Enregistrement via `p.registerEvent("donePing", null, callback)` ; callback `(src, args)`, compteurs lus depuis le processus après l’événement.
- Chaque trajet possède son propre gestionnaire d’erreur avec le nom de l’étape (`processus Icmp`, `createPingProcess`, `registerEvent donePing`, etc.). Un échec ne supprime plus les résultats des autres trajets.
- État du lot et fonction de réponse capturés dans une fermeture privée : une requête suivante ne peut pas changer la destination d’un résultat asynchrone.
- Un refus de prise en main affiche maintenant le détail du contrôle réseau, en rouge et ramené dans la zone visible. Une observation absente reste un refus normal.
- Si l’accélération est indisponible, le ping lancé reste actif et peut se terminer normalement ; aucun basculement vers la console.

La surveillance périodique n’accélère jamais le temps. Le contrôle manuel peut demander un fast forward global. Le mode Simulation est conservé et suspend ces contrôles. Aucune commande CLI n’est injectée.

## Essai sur la sauvegarde existante

1. Arrêter l’ancien serveur web et lancer la nouvelle version. Utiliser l’import/reprise de la sauvegarde existante ; ne pas recréer l’entreprise pour masquer le problème.
2. Ouvrir son réseau dans Packet Tracer et garder MCP BUILDER actif, en mode Realtime.
3. Sélectionner le poste concerné, cliquer Vérifier maintenant puis Prendre la main.
4. Si le contrôle reste inconnu, relever son détail : il doit nommer précisément l’étape qui échoue.
5. Si la connexion réussit, couper/rebrancher le câble puis vérifier les deux états. Vérifier l’absence de commandes ping dans les consoles.

**À tester dans Packet Tracer 9.** Le remplacement corrige une incompatibilité démontrable du code avec la documentation ; il n’établit pas à lui seul que cette incompatibilité est l’unique cause du message natif observé. Aucun Packet Tracer n’est disponible ici pour confirmer le résultat réel.

## Sources

- https://tutorials.ptnetacad.net/help/default/scriptModules_scriptEngine.htm (événements JavaScript)
- https://tutorials.ptnetacad.net/help/default/IpcAPI/class_ping_process.html (fin de ping et compteurs)
- https://tutorials.ptnetacad.net/help/default/IpcAPI/class_icmp_process.html (création du processus)
