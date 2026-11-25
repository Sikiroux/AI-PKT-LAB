# Packet Tracer 9 : analyse de la rétention mémoire

Cette analyse est statique : les exécutables fournis ont été lus et désassemblés, jamais exécutés. Elle localise des chemins à vérifier, sans annoncer une fuite identifiée. La capture proposée porte sur les allocations natives encore vivantes, pas sur une nouvelle comparaison de compteurs de RAM.

## Résultats établis

Exécutable x64, base préférée `0x140000000`. Empreinte SHA-256 : `c8d3ff710ca27c8dfbf120ced45030be0d1bec5d9b5276e5bb7dd481e4a698b5`. Les RVA ci-dessous restent utilisables si Windows déplace le module par ASLR, à condition de conserver exactement ce binaire.

| Élément | Adresse préférée / RVA | Preuve et limite |
|---|---|---|
| Adaptateur associé à `getDeviceAt` | `0x1403fab80` / `+0x3fab80` | Référence au texte `getDeviceAt implementation error`; chemin de succès vers le constructeur de réponse commun. Ce nom identifie un adaptateur, pas nécessairement le stockage réseau réel. |
| Autre chemin `getDeviceAt` et chemin `getPortAt` | `0x142299e40`, `0x14236ce20` | Les appels `0x14229a00e` et `0x14236d000` atteignent le constructeur de réponse commun `0x142248450`; allocation de 112 octets à `0x142248512`, puis `CIpcRetValMsg`. Ce sont des branches vues statiquement, non des fréquences observées. |
| Construction d’une réponse contenant un pointeur | `0x142249770` / `+0x2249770` | Appel d’allocation à `0x142249839`, taille demandée `0x70` = 112 octets, puis constructeur `0x142272510`. Cette allocation seule n’explique pas les quelques Ko estimés par appel. |
| Type de cette réponse | vtable `0x144c36048` | RTTI explicite `Ipc::CIpcRetValMsg`. L’objet n’est donc pas assimilable sans preuve à un appareil recréé. |
| Destruction de cette réponse | `0x142272780` et `0x1422727b0` / `+0x2272780`, `+0x22727b0` | Destructeur interne puis destructeur de suppression conditionnelle; appel vers la famille `operator delete` avec taille `0x70`. L’absence de destructeur n’est pas l’explication : son exécution et sa fréquence restent inconnues. |
| Allocation de la famille `operator new` | `0x143ccdb8c` / `+0x3ccdb8c` | Appelle le thunk `0x143ccf9bd`, import CRT `malloc`. Chemin de tas natif réel, distinct du seul GC JavaScript. |
| Type du parseur | descripteur `0x145ec16d0` | RTTI `Ipc::CParser`. Le chemin `getDeviceAt` manipule des conversions entre objet/parseur et valeur de retour. Il reste à suivre le propriétaire dans les chemins d’appel et de retour. |
| Publication d’un QObject dans le moteur | `0x14276b130` / `+0x276b130` | Appelle `QJSEngine::newQObject`, puis `setObjectOwnership` avec valeur 0. Propriété C++ confirmée pour l’objet passé à cette fonction, mais aucune preuve que tous les objets retournés par `getDeviceAt` suivent ce chemin. |
| Exemple de QObject exposé | allocation à `0x14276fa53`, constructeur `0x142777a30` | RTTI `CScriptHttpServerRequest`. Cela montre que certains `newQObject` concernent le serveur HTTP de script, et non les appareils réseau. Ne pas mélanger ces classes. |
| GC explicite dans Packet Tracer | `0x142793280`, `0x143a544f0` | Deux fonctions appellent l’import `QJSEngine::collectGarbage`. Leur présence n’indique ni le moteur concerné dans chaque cas ni la fréquence réelle des appels. |
| GC dans Qt fourni | `Qt6Qml+0xa2f20` | Transfert vers `MemoryManager::runFullGC`, `Qt6Qml+0x1b7c90`; le GC existe. Cela ne donne pas la liste des allocations encore retenues à un instant donné. |

Les extraits de désassemblage et leurs annotations d’imports sont dans `evidence/`. `tools/native_memory/pe_audit.py` reproduit une partie de l’extraction. Les bornes proviennent des tables d’unwind PE quand disponibles; les thunks sans unwind utilisent une fenêtre de lecture, qui peut inclure des instructions voisines.

## Ce qui reste à établir

- La quantité de `CIpcRetValMsg` encore vivants après la fin des appels et leur pile d’allocation.
- Le nombre d’enveloppes `QObject`/`QJSValue`, valeurs QVariant et allocations de parseur réellement retenues.
- L’éventuelle rétention par une collection IPC, un parent QObject, une valeur persistante Qt ou une autre structure. Aucun conteneur responsable n’a été prouvé.
- Une hausse de mémoire engagée peut aussi inclure des zones de tas disponibles pour réutilisation; les compteurs seuls ne distinguent pas cela d’objets vivants.

Changer aveuglément `CppOwnership` en propriété JavaScript serait une mauvaise correction : cela pourrait détruire des objets réseau encore utilisés. Aucune modification binaire n’a été faite.

## Capture préparée

Le script `tools/native_memory/Capture-Allocations.ps1` active la base de piles UST avant le lancement, fait exécuter une charge connue de trois minutes sans nettoyage Qt agressif, et prend des instantanés UMDH après l’inventaire initial, pendant les lectures et après leur arrêt. Il compare les instantanés et conserve les adresses de base des modules pour recouper les piles avec les RVA ci-dessus.

UMDH compare les allocations du tas Windows encore vivantes et leurs piles. Il ne fournit pas automatiquement le graphe des références qui les retiennent. Si les allocations privées de Qt ou d’un autre allocateur ne sont pas visibles, ou si aucune pile ne peut être recueillie, il faudra une autre capture (ETW/WinDbg) guidée par cet échec, pas interpréter le silence comme une absence de fuite.

Le traçage UST consomme lui-même de la mémoire et ralentit le processus : cette capture sert à localiser les allocations, pas à comparer sa RAM à v119/v127. Les symboles privés Cisco ne sont pas fournis; les adresses module+offset restent utiles avec les binaires exacts déjà reçus.

## Sources techniques

- Qt, propriété et destruction des QObject : https://doc.qt.io/qt-6/qjsengine.html#ObjectOwnership-enum
- Microsoft, préparation UMDH : https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/preparing-to-use-umdh
- Microsoft, recherche d’une fuite avec UMDH : https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/using-umdh-to-find-a-user-mode-memory-leak
- Microsoft, interprétation de la comparaison : https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/interpreting-a-log-comparison

Validation locale : lecture des PE et exécution de l’extracteur sous Linux. Aucune capture native Windows, aucun fonctionnement PowerShell ni correction de fuite validés dans cet environnement.
