# v0.35 — Atelier visuel de déploiement

Depuis le bureau du technicien, ouvrir **Déploiement**. Créer ou reprendre un environnement et vérifier le réseau du technicien avant les opérations. Le disque virtuel d’atelier est distinct du poste client et du fichier Packet Tracer. Aucune installation réelle ni suppression de fichiers utilisateur.

## Parcours interactif

1. Choisir une image sur des cartes graphiques.
2. Sélectionner le support USB dans un menu de démarrage UEFI.
3. Charger le pilote de stockage si le disque n’apparaît pas.
4. Sauvegarder les anciennes partitions, les supprimer, puis créer un partitionnement GPT. Une barre graphique affiche les partitions et l’espace libre.
5. Sélectionner Windows et parcourir trois phases d’installation avec progression.
6. Retirer le support et redémarrer.
7. Choisir région, clavier et compte local ; consulter le bilan des objectifs.

La seed fait varier la capacité, la visibilité du disque, son ancien partitionnement et la configuration demandée. La session conserve la progression. Recommencer restaure le disque initial avec une révision croissante et un compteur de tentatives. Une requête ancienne est refusée.

## Simplifications explicites

Interface originale HTML/CSS/SVG, pas des captures Windows. Images et support sont simulés ; aucun ISO n’est fourni. Les 64 Gio sont la règle des images de formation. La disposition EFI 300 Mio / MSR 16 Mio / Windows / récupération 1 Gio est un exemple pédagogique. Le retrait USB répond à la priorité de démarrage choisie pour cet atelier. Le compte local remplace les étapes complètes de licence, compte Microsoft et compatibilité matérielle.

Le contrôle du réseau technicien/VPN réutilise la garde administrative du prototype ; il ne signifie pas qu’une installation USB réelle exige une connexion réseau. L’atelier n’installe pas encore un poste client de l’environnement et ne crée pas de tickets de déploiement. Ces intégrations restent à faire.

## Architecture et vérification

`web/sim_deployment.py` : moteur pur reproductible, transitions, objectifs et révisions. `web/desktop_controller.py` : stockage dans la session et autorisation. `web/desktop.html` : assistant visuel. Tests Python du parcours, erreurs, sauvegarde et atomicité ; test DOM JavaScript des cartes et requêtes. Le test DOM ne remplace pas une vérification visuelle dans un navigateur ni un test Packet Tracer réel.

## Références de conception

- [Microsoft : installation depuis un support USB](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/install-windows-from-a-usb-flash-drive?view=windows-11)
- [Microsoft : partitions UEFI/GPT](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/configure-uefigpt-based-hard-drive-partitions?view=windows-11)
- [Microsoft : scripts de déploiement OEM](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/oem-deployment-of-windows-desktop-editions-sample-scripts?view=windows-11)
- [Microsoft : configuration OOBE](https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/oobexml-in-windows-11)
