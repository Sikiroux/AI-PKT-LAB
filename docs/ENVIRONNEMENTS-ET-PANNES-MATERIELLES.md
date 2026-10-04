# Gestion des environnements — première étape

## Livré

Le Bureau simulé propose plusieurs environnements procéduraux. Chaque création
conserve une seed, un réseau de travail et un état web dans son propre dossier.
La liste permet de reprendre une entreprise. Le dernier choix est conservé après
redémarrage. L'ancien workspace-session/session.json reste à son emplacement :
il apparaît comme environnement existant, sans déplacer son fichier réseau.

Changer ferme la session distante, invalide les observations réseau et conserve
les permissions et fichiers simulés. Les onglets distants sont liés à l'identité
de l'environnement ; ils ne peuvent pas agir sur une autre entreprise.
Le réseau doit toujours être sauvegardé dans Packet Tracer, au chemin affiché.
Le logiciel ne sauvegarde pas automatiquement le fichier ouvert dans PT.

## Limites actuelles

Le Site de test et le catalogue de tickets historiques restent distincts du
Bureau simulé. Cette livraison prépare leur unification, elle ne la termine pas.
Les nouveaux environnements utilisent encore le même scénario de dossier partagé.
Il n'y a pas encore d'import/export global, de duplication de lab complet ni de
sélecteur général à l'accueil. Les labs du générateur restent indépendants.

## Prochaines étapes

1. Relier inventaire et tickets au contexte actif et au même fichier de travail.
2. Accueil Reprendre / Nouvel environnement / Mes environnements ; afficher le
   bon fichier et distinguer pont connecté / environnement reconnu.
3. Suspendre les arrivées et injections lors du changement de contexte.
4. Générer les tickets à partir des services et appareils réellement présents.
5. Formation : PT seul (PKT/PKA) ou environnement complet ; copie indépendante.
6. Terminal web, ergonomie du bureau, puis scénarios matériels et stock.

# Recherche : appareil HS dans Packet Tracer

Recherche du 4 octobre 2026. Aucun état matériel permanent « HS » identifié dans
les sources consultées. Cela ne prouve pas qu'une extension privée ne le propose
pas. Aucune nouvelle panne matérielle n'est injectée par cette livraison.

## Mécanismes documentés

- Cisco Device.setPower(bool) éteint/rallume un appareil. Ce n'est pas une panne
  définitive. API publiée pour 8.1 ; disponibilité à vérifier dans notre pont PT9.
  https://tutorials.ptnetacad.net/help/default/IpcAPI/class_device.html
- Les modules amovibles peuvent être retirés ou remplacés après mise hors tension.
  Une carte absente n'est pas une carte défectueuse ; ne pas les confondre.
  Un redémarrage de routeur/switch recharge la startup-config : sauvegarder la
  running-config avant un essai pour éviter une panne collatérale.
  https://tutorials.ptnetacad.net/help/default/devicesAndModules.htm
- jenaro1804/PacketTracer_mcp propose pt_power via le SDK IPC Java. Le README annonce
  des tests sur PT9. Le projet demande JDK21 et le SDK Cisco local : il ne faut pas
  remplacer notre pont existant uniquement pour cette fonction.
  https://github.com/jenaro1804/PacketTracer_mcp
- Deiviidsito/MCP_Packet_Tracer documente aussi setPower dans son Script Engine.
  https://github.com/Deiviidsito/MCP_Packet_Tracer/blob/main/WIKI.md

## Proposition pour une véritable panne matérielle simulée

Conserver dans le moteur web une cause matérielle liée à une identité d'appareil.
Utiliser l'extinction PT uniquement comme conséquence observable, après validation
sur un réseau jetable. Le remplacement doit être reconnu par une nouvelle identité
et des tests fonctionnels ; un simple renommage ne suffit pas.
Ne pas éteindre en boucle un appareil que l'apprenant essaie de réparer. Ce procédé
créerait une course avec l'interface et pourrait perdre sa configuration.
Ne pas fabriquer un XML « irréparable » : le projet a déjà rencontré un switch
2960 éteint par XML impossible à rallumer dans son interface.

## Essai réel à préparer avant activation

Copie de réseau, modèle et numéro de série connus ; lire l'état initial, sauvegarder
la configuration, éteindre par API, observer ports et communication, rallumer depuis
l'interface PT puis par API, sauvegarder/réouvrir. Consigner les résultats par modèle.
La panne reste marquée « à tester » tant que cet essai n'a pas été effectué dans PT.
