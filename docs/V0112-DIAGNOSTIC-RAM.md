# v0.112 — Diagnostic RAM Packet Tracer

## Lancement

Fermer complètement NetOps normal (toutes ses fenêtres). Extraire le patch dans le dossier contenant LANCER-BUREAU.bat puis lancer **LANCER-DIAGNOSTIC-RAM.bat**. Le lanceur habituel conserve le fonctionnement standard. Si une instance NetOps est encore ouverte, Electron peut simplement la remettre au premier plan : il faut la fermer puis recommencer. Le diagnostic affiche un titre explicite et quatre modes, sans écran de tickets.

Utiliser une entreprise déjà créée et son même fichier réseau. Cette version ne crée pas d’entreprise dans le diagnostic ; le faire au préalable dans NetOps normal si nécessaire.

## Protocole

Avant chaque essai, redémarrer Packet Tracer, ouvrir exactement le même fichier puis son extension MCP BUILDER. Ne pas démarrer les tickets. Noter la RAM du groupe Packet Tracer avant l’essai. Choisir successivement Pause, Inventaire seul, Pings seuls, Complet. Démarrer un essai de trois minutes, noter la RAM à l’arrêt, puis une minute après. Exporter le journal JSON avant de démarrer un autre essai (le journal affiché est remplacé à chaque démarrage). Donner les trois relevés de RAM avec chaque journal.

- Pause : aucun contrôle PT, comparaison du réseau avec le bridge connecté sans travail NetOps.
- Inventaire : lecture répétée de l’inventaire uniquement.
- Pings : un inventaire au départ, comptabilisé comme préparation, puis contrôle des mêmes trajets ICMP sans nouvel inventaire.
- Complet : méthode de surveillance habituelle, avec délai d’une seconde après chaque cycle. Les résultats observés sont enregistrés comme dans le fonctionnement habituel ; aucune configuration du réseau n’est modifiée.

Un seul essai peut s’exécuter. Aucun nouveau cycle ne commence après 180 secondes. L’appel en cours peut terminer après l’échéance ou la demande d’arrêt ; attendre l’état stopped avant le relevé final. Le diagnostic reste en pause après un essai et ne reprend pas spontanément.

## Mesures

Le compteur « appels moteur » dénombre les tentatives engine.call de NetOps ; il n’est pas égal aux sous-commandes du compteur MCP BUILDER. Les tailles comptées sont celles des scripts et réponses au niveau moteur, sans l’enveloppe HTTP/bridge. Les événements incluent les durées, erreurs et résultats ICMP (inconnus inclus). Le journal est borné à 1 000 événements ; les compteurs restent cumulés pour l’essai. Aucun script ni jeton du bridge n’est exporté. La RAM est relevée manuellement, pas estimée par NetOps.

La surveillance périodique normale et les arrivées de tickets ne sont pas lancées dans ce mode. Les routes d’actions ordinaires sont bloquées, même depuis une ancienne fenêtre. Le lancement normal ne change pas la fréquence des contrôles : cette version sert à trouver la cause, elle ne prétend pas réparer une fuite.

## Vérification

10 tests Python diagnostic : isolation des quatre modes, échéance, arrêt, exclusion des essais simultanés, erreurs, journal borné, export indépendant, routes HTTP, jeton et blocage des actions. Deux tests de route CSS ; huit tests Electron. Suites JavaScript existantes vérifiées. Mesure RAM et bridge réel à effectuer sous Windows par l’utilisateur.
