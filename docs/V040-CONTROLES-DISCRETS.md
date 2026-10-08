# v0.40 — Contrôles discrets et actions de ticket

## Comportement

| Action | Contrôle | Accélération |
| --- | --- | --- |
| Surveillance périodique | ICMP IPC direct sur les deux clients | Jamais |
| Vérifier maintenant | ICMP IPC direct ; cible sélectionnée si fournie | Une demande de fast forward par lot |
| Vérifier / clôturer un ticket | ICMP IPC direct sur son poste cible | Une demande de fast forward par lot |
| Prendre la main sur un client | Contrôle frais du poste sélectionné | Une demande de fast forward par lot |
| Prendre en charge, attente, notes, sévérité, chronomètre | Métadonnées du ticket seulement | Aucune |
| Ping tapé dans le terminal web | Ancienne injection CLI explicite | Aucune |

L’API ICMP crée deux requêtes par trajet. Les trajets d’un poste sont lancés ensemble ; le résultat est corrélé à chaque processus. Un lot dure au maximum 12 secondes d’attente du pont. Les observations périodiques gardent l’intervalle existant de 10 secondes après la fin du cycle ; il n’y a pas d’accélération périodique.

Le fast forward concerne le réseau entier. Si Packet Tracer est en mode Simulation, le contrôle retourne **inconnu** et n’avance pas le temps : il ne change pas le mode et ne réinitialise pas le réseau. Un contrôle inconnu ne permet pas la clôture.

## Interface et réactivité

Les boutons de statut utilisent un verrou de métadonnées indépendant des vérifications du pont. La lecture des tickets ne prend plus le verrou réseau. L’ouverture d’un bureau et les vérifications manuelles restent synchrones, mais utilisent un lot concurrent et une cible précise au lieu d’une succession de pings CLI. L’interface distingue l’enregistrement des métadonnées d’une vérification du réseau.

La suppression de tous les blocages de l’environnement et une progression détaillée par étape ne sont pas livrées ici : une opération manuelle peut encore attendre la fin d’un contrôle périodique en cours. Le bénéfice réel de l’accélération et les délais du pont doivent être mesurés sur Packet Tracer.

## Méthode et prudence sur les résultats

`quiet_checks.py` utilise `Device.getProcess("Icmp")`, `IcmpProcess.createPingProcess`, `PingProcess.donePing`, les compteurs et `RealtimeToolbar.fastForwardTime`. L’interface source doit être la seule interface adressée du poste ; une source absente ou ambiguë retourne un état inconnu. Aucune commande n’est entrée dans la console par les contrôles internes, et aucune console n’est effacée. Une erreur de l’API ne bascule pas silencieusement vers la CLI : elle retourne un résultat inconnu avec l’erreur du pont.

Un succès exige toutes les réponses du processus achevé ; une réponse partielle est un échec du contrôle strict. Un premier contrôle peut donc échouer pendant l’ARP/convergence : relancer après stabilisation. Le contrôle ICMP reste un proxy de connectivité ; les droits et services simulés sont vérifiés séparément. Il ne valide pas SMB ou FTP réel.

**Statut : prototype documenté et testé hors Packet Tracer ; à essayer dans PT 9.** La disponibilité des événements JavaScript IPC et l’absence de traces visibles doivent être confirmées dans la version installée. Packet Tracer reste lancé ; ce n’est pas un moteur réellement headless.

## Essai dans Packet Tracer

1. Créer une nouvelle entreprise et ouvrir son réseau ; laisser MCP BUILDER actif.
2. Attendre un cycle périodique. Vérifier que les consoles des clients/du technicien ne contiennent plus de commandes ping ajoutées automatiquement.
3. Pendant un contrôle, prendre en charge un ticket et enregistrer une note. Le statut et la note doivent être conservés sans attendre le lot réseau.
4. Choisir un poste et prendre la main. Vérifier la cible puis couper son câble : le contrôle doit refuser la connexion et la clôture.
5. Rebrancher, utiliser Vérifier maintenant ; vérifier le résultat et la visibilité des consoles.
6. Passer en mode Simulation : Vérifier doit afficher un état inconnu, sans changer ce mode ni avancer la simulation.
7. Si les contrôles restent inconnus, recopier le détail d’erreur ICMP IPC. Ne pas considérer le réseau comme réparé sur cette seule observation.

## Références officielles

- https://tutorials.ptnetacad.net/help/default/IpcAPI/class_icmp_process.html
- https://tutorials.ptnetacad.net/help/default/IpcAPI/class_ping_process.html
- https://tutorials.ptnetacad.net/help/default/IpcAPI/class_realtime_toolbar.html

Tests : `test_quiet_checks.py` (format, limites, erreurs, indépendance des métadonnées) ; `test_quiet_checks.js` exécute le script réellement généré avec des signaux asynchrones contrôlés. `test_client_workspaces.py` vérifie les lots ciblés et l’absence d’accélération automatique. Ces tests ne sont pas une validation du pont réel.
