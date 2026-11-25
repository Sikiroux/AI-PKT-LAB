# Audit de consolidation — AI-PKT-LAB v0.62.5

Date : 11 octobre 2026. Audit sans modification du fonctionnement.

## Conclusion

Le projet possède des moteurs pédagogiques structurés et un catalogue réseau conséquent. Son défaut principal est leur intégration : plusieurs parcours, horloges, états et conventions coexistent. Le nombre de fonctionnalités ne prouve pas la fidélité de l'expérience. Priorité : fiabiliser l'observation et rendre cohérents ressource, incident, activité, signalement, dialogue et validation avant d'élargir le catalogue.

## Méthode et limites

Inventaire des entrées de génération, lecture des contrôleurs/adaptateurs, moteurs, catalogues, interfaces HTML/JS/CSS, documentation et tests. Catalogue web chargé réellement. Suite unifiée exécutée avec succès (résultats en fin de rapport). Aucun ping, fast-forward, changement réseau ou interaction avec les applications de Damien.

Les constats ci-dessous distinguent défaut confirmé, limite assumée et hypothèse. Aucun audit statique ne certifie tous les comportements PT9, le rendu Chrome/Windows, les clics, le contraste effectif ou toutes les combinaisons de sauvegardes. Les captures de cette conversation sont indisponibles aux chemins fournis. Ce rapport couvre les sous-systèmes et parcours ; il ne prétend pas que chaque ligne ou chaque état visuel a été testé.

## 1. Générateur : capacités vérifiées

Catalogue obtenu par `web/lab_engine/web_worker.py::catalogue()` : **93 entrées**, soit 59 dépannage, 24 atelier, 7 mixtes et 3 reproduction. Ce sont des entrées de scénario, pas 93 architectures différentes. Les 7 associations mixtes sont une liste explicite, pas un assemblage universel.

Topologies identifiées dans le catalogue : simple_lan, dhcp_lan, switched_redundant, vlan_trunk, etherchannel, multisite_ospf_nat, enterprise_services, meraki_branch et wifi_deployment. Les scénarios classiques peuvent accepter plusieurs de ces gabarits.

Le formulaire web valide : mode, niveau 1–5, nombre 1–5, seed, famille IPv4 privée, scénario, code de site ; les variantes entreprise acceptent 2–6 employés, cible et répartition single/split. Une entreprise persistante de 30 employés utilise une autre entrée de construction. Même chiffre de niveau ne doit pas être présenté comme une difficulté homogène entre catalogues.

| Parcours | Production et validation | Placement |
|---|---|---|
| Classique | Injection de panne, PKT/PKA, références/checks selon catalogue | Coordonnées du gabarit ; organisation avancée peut être ignorée faute de fichiers initial/baseline |
| Ateliers | Réseau initial, consignes, référence/correction selon exercice ; validation manuelle | `organization.finalize` traite noms et implantation physique |
| Mixte | Sept associations atelier/panne définies | Parcours ateliers, pas nouvelle architecture libre |
| Reproduction | Évolution puis exemple de panne ; correction étiquetée selon parcours | Parcours ateliers |
| Entreprise persistante | PKT de travail et états web sauvegardés ; vérifications réelles par pont + moteurs simulés | `enterprise_design.plan/apply_positions`, notamment disposition compacte 30 postes |

**G01 — Confirmé, P1 : absence de règle commune de placement logique.** `organization.finalize` réorganise le physique et renomme les XML ; il n'appelle pas `enterprise_design`. Le correctif des 30 postes ne s'applique donc pas automatiquement à tous les labs. L'implantation physique des pièces/racks ne doit pas être confondue avec X/Y de la vue logique.

**G02 — Limite, P1 : disposition de 30 postes par parité.** Deux groupes suivent les switches réels et les postes sont disposés en cercle. Cela assure une correspondance câblage/placement, mais ne construit pas des bureaux par département. Nommage départemental ne signifie pas segmentation réseau départementale.

**G03 — Limite, P2 : encombrement estimé.** Pas de mesure prouvée des icônes/étiquettes PT au zoom utilisé. Le plafond 3900 est une contrainte d'espace, pas une raison de remplir le canevas. Vérifier collisions, ports, câbles, labels et cadrage initial pour chaque gabarit.

**G04 — Limite, P1 : différences de correction.** Certaines activités évaluent un état ; d'autres demandent une recette manuelle ; une référence complétée n'est pas toujours la solution unique. Ne jamais faire passer une déclaration manuelle pour une vérification automatique.

**G05 — Limite, P2 : génération contrainte.** Seed sélectionne/paramètre un gabarit et une cause. Pas de génération arbitraire de toute entreprise, ni raccordement automatique de chaque demande RH au PKT existant.

## 2. Procédural et vie d'entreprise

**P01 — Confirmé, P1 : catalogue entreprise sans panne réseau.** `enterprise_incidents.CATALOGUE` contient impression, endpoint, AD, FTP, DNS et périphériques ; aucun câble, port, VLAN, DHCP ou Wi-Fi. Le catalogue réseau général est riche, mais il n'alimente pas cette boucle.

**P02 — Confirmé, P1 : comportements historiques différents.** `ticket_arrivals.receive` crée une demande sans panne pour les anciennes entreprises ; `activate` prépare ensuite le scénario. Pour 30 employés, il délègue à `enterprise_incidents.receive`, qui mute avant le signalement. L'effectif choisit implicitement le modèle de vie : ce n'est pas une simple différence de taille.

**P03 — Limite, P1 : événements et tickets restent étroitement couplés.** La réception choisit la cause, la mute et produit immédiatement le ticket. Il manque un événement autonome avec délai de découverte, activité en cours, propagation et plusieurs signalements reliés.

**P04 — Confirmé, P1 : activité évaluée par causes connues.** `work_status` parcourt les tickets non clos et teste les champs correspondant à chaque famille. Il ne calcule pas toute l'aptitude au travail depuis toutes les dépendances. Une panne créée manuellement dans PT, sans ticket correspondant, ne devient pas automatiquement une interruption métier.

**P05 — Limite, P2 : variation contrainte, pas anti-répétition absolue.** La sélection évite les postes déjà occupés et privilégie une autre famille que la précédente ; des replis existent. Ne pas promettre « jamais deux signalements du même utilisateur » sans politique explicite de regroupement/délai.

**P06 — Limite, P2 : impact simplifié.** FTP utilise des dépendances métier ; d'autres familles affectent principalement une cible. Critique selon nombre de personnes, bloqué selon famille : il manque durée, échéance et activité réellement nécessaire.

**P07 — Limite, P2 : reproductibilité.** Seed et compteur déterminent les choix, mais heures, état courant, liste des tickets ouverts et historique interviennent. Pour reproduire un bug il faut version, sauvegarde, seed, ticket, horodatages et historique ; seed seule ne suffit pas.

## 3. Bugs et fiabilité des sessions

**B01 — Confirmé, P0 : réponse réseau du dialogue faussement inconnue.** `enterprise_incidents.dialogue` teste `observation.valid_until`. `_observe_one` écrit `observation.at/status/probes`, sans `valid_until`. Le TTL appartient aux preuves des adaptateurs. Même un contrôle récent positif passe donc par défaut dans « Je ne dispose pas encore d'un contrôle réseau récent ». Reproduction minimale : observation `{at:1000,status:'passed'}` ; test `get('valid_until',0)>1001` faux.

**B02 — Hypothèse forte, P0 : expiration plus rapide que le tour de surveillance.** TTL de 45 s dans `directory_adapter`. La boucle observe puis attend 10 s. Pour 30 postes, deux postes de fond par tour plus sessions actives ; le tour de 29 secondaires prend au minimum environ 15 passages, hors durée des appels. Les preuves de nombreux postes peuvent expirer normalement. L'annuaire technicien est aussi recontrôlé par cible. À mesurer, sans transformer « périmé » en « panne ».

**B03 — Confirmé, P1 : verrou maintenu pendant les appels PT.** `observe` conserve le verrou du contrôleur ; `_observe_one` utilise aussi le verrou moteur pendant snapshot et pings. Plusieurs clients actifs multiplient le travail. Cela peut retarder lectures/actions ; latence exacte à instrumenter.

**B04 — Confirmé, P1 : dégradation globale sur exception.** Une exception d'observation remplace la preuve par unknown et efface `network_observation`. Distinguer dernier succès, dernier essai et erreur actuelle ; ne pas réutiliser un succès périmé comme autorisation, mais le conserver pour diagnostic.

**B05 — Limite, P1 : suspension distante globale.** `desktop.check` pose un écran bloquant lorsque `checks.remote.allowed` est faux, même pour une preuve inconnue. Lecture de `workspace_model.evaluate` : remote utilise sa propre preuve, le service distant et la politique technicien ; il ne dépend pas des permissions documentaires ni du compte actif du demandeur. Cette séparation est correcte. Reste à tester le caractère excessivement bloquant de l'écran lors des renouvellements de preuve.

**B06 — Confirmé, P1 : erreurs d'arrivées silencieuses.** `arrival_loop` fait `except Exception: pass`. Un échec de génération périodique peut rester invisible. Journal structuré et compteur d'échecs nécessaires.

**B07 — Limite, P2 : expiration d'identité fixe.** Authentification créée pour 1800 s ; pas un véritable système de tickets Kerberos ou de renouvellement d'activité Windows. Séparer ouverture locale, verrouillage, session distante et durée des droits.

**B08 — Limite, P2 : persistance du bureau.** Positions et préférences sont mémorisées dans sessionStorage ; rechargement ne restaure pas toutes les apps/brouillons. OS.js fonctionne avec session désactivée. La documentation doit distinguer ces périmètres.

## 4. Textes, consignes, questions et aides

**T01 — Confirmé, P1 : chronologie vide.** Pour les incidents entreprise, « Depuis quand ? » renvoie toujours « avant mon signalement ». L'incident possède pourtant une date de création. En historique, deux formulations sont tirées sans chronologie détaillée.

**T02 — Confirmé, P1 : questions non spécialisées.** Huit questions communes, dont document/ping/nom/connexion. Dans la boucle entreprise, plusieurs branches renvoient simplement qu'un test est nécessaire. Un utilisateur avec une souris débranchée ne doit pas répondre à un questionnaire documentaire.

**T03 — Confirmé, P1 : symptôme trop vague.** La famille endpoint annonce dossiers inaccessibles pour un lecteur mal mappé OU l'absence de l'application Documents. Ce ne sont pas les mêmes symptômes. Spécifier ressource/chemin, action, message observé, dernier succès et portée ; garder la cause cachée.

**T04 — Limite, P1 : client omniscient ou passif.** Certaines réponses proviennent directement des contrôles techniques ; d'autres ne donnent aucune observation utile. Définir connaissances, actions réellement essayées et mémoire du client. Un LLM éventuel reformule ces faits, ne les invente pas.

**T05 — Confirmé, P1 : aide périmée.** Article `desktop-lock` dans `trainingDocuments` annonce qu'une coupure confirmée peut fermer la session ; le correctif récent conserve les fenêtres en cas d'échec transport. Relecture systématique des docs après changement de contrat.

**T06 — Limite, P2 : aide générale utile mais insuffisante.** v0625 distingue observer/comparer/valider. Il manque les liens contextuels vers l'outil, le poste et la ressource ; distinguer procédure entreprise, tutoriel débutant et indice de scénario.

**T07 — Confirmé, P2 : vocabulaire technique et implémentation dans les parcours.** Codes, octets, JSON et références internes apparaissent dans certaines consoles. Utile dans diagnostic avancé, beaucoup moins dans la plainte ou les écrans principaux. Fournir explication/action, détail technique repliable.

**T08 — Limite, P2 : documentation mixte.** `company_documents` contient maintenant ressources/politiques/dépendances seed ; ce n'est plus seulement le manuel du logiciel. Mais l'application agrège manuel et entreprise, rend chaque article comme des paragraphes et affiche une réserve générique. Donner procédures structurées, prérequis, exemples de chemins et documents métier sans dévoiler les causes.

## 5. UI/UX et design system

Mesures statiques : tickets.html 465 lignes, desktop.html 447 ; beaucoup de lignes regroupent une interface complète. tickets.html comporte 25 `!important`, desktop.html 14, desktop-theme.css 20. Comptage indicatif d'expressions de styles inline : 8 dans Tickets, 13 dans Desktop. Ce n'est pas un score de qualité, mais une trace de couches de overrides. Le thème desktop n'utilise pas de variables CSS ; tickets en comporte 24 identifiants distincts. Un design system partagé n'est pas encore centralisé.

**U01 — Confirmé, P1 : styles dispersés.** HTML inline, ui-comfort, desktop-theme et OS.js. Définir tokens communs, composants et variantes avant nouvelle couche de CSS.

**U02 — Confirmé, P2 : multiples redéfinitions.** Exemple `#status::before` successivement NETOPS LAB, NetOps Lab puis neutralisé dans topbar. Nettoyer uniquement après captures de référence, pour éviter régression.

**U03 — Limite, P1 : composants non homogènes.** `consoleFrame`, tables, property-tabs et modales existent ; certaines fonctions restent des contrôles successifs directement dans le contenu. Une modale ne suffit pas à transformer un formulaire en application.

**U04 — À tester, P1 : clavier/focus.** Modales natives et inert pour verrouillage sont présents. Vérifier focus initial/retour, Escape, menus contextuels, tabulations des tables, fenêtres OS.js, contrastes et états désactivés. Aucune certification accessibilité par lecture seule.

**U05 — À tester, P1 : scroll.** Définir un propriétaire du défilement par zone : liste, article ou contenu de fenêtre. Bureau extérieur sans scroll. Tester petites fenêtres, écran partagé, longues erreurs et 30 utilisateurs. Ne pas simplement cacher overflow pour masquer du contenu.

**U06 — Limite, P2 : attentes irréalistes de chargement.** Plusieurs appuis dépendent de contrôles synchrones et verrous réseau. Séparer lecture disponible, vérification en cours, attente PT et erreur. Animation ne répare pas latence.

**U07 — Confirmé, P2 : erreurs destructrices de vue.** Des fonctions d'apps vident leur contenu après erreur et demandent une actualisation. Conserver données précédentes clairement marquées périmées et brouillon lorsque possible.

### Combien font encore « formulaire » ?

Estimation structurelle, non note visuelle. Dix-huit familles d'applications principales ci-dessous ; variantes client/admin et sous-fenêtres ne sont pas comptées séparément. Les formulaires de propriétés sont normaux dans une app réelle : le problème est lorsqu'ils constituent toute l'app.

| Famille | Classement | Observation |
|---|---|---|
| Explorateur local/partagé | Application structurée | Liste, sélection, actions ; dossiers/arborescence encore limités |
| Annuaire | Application structurée | Arbre, liste, propriétés ; modèle AD partiel |
| DNS | Application structurée | Console/listes ; propriétés simplifiées |
| Parc/stock | Application structurée | Vues et opérations ; raccordement PT absent lors de remise |
| Fiches/accès distant | Application structurée | Recherche/liste/détails ; associations à vérifier |
| Imprimantes | Application structurée | Files/propriétés ; pas toute la pile Windows |
| Arrivées/messagerie/licences | Application structurée | Listes/tabs ; première connexion est un essai administratif |
| Déploiement | Atelier visuel | Étapes/choix ; pas un OS installé |
| Services/événements | Application structurée | Tables ; événements globaux limités |
| Documentation | Application structurée, contenu plat | Liste/recherche/article ; ergonomie à revoir |
| Partages | Hybride fortement formulaire | ACL à checkboxes, quotas/capacité et toggles |
| Administration FTP | Hybride | Listes et édition de comptes/droits |
| Client FTP | Hybride | Connexion + transfert ; explorer distant limité |
| Périphériques | Hybride | État matériel et actions ; vérifier représentation visuelle |
| Session utilisateur | Formulaire dominant | Identité/mot de passe ; devrait aussi être un état de session |
| Mobilité/VPN | Formulaire dominant | Sélecteurs, mot de passe, rapports ; peu de représentation raccordement |
| Paramètres poste | Formulaire dominant | Contrôles de configuration |
| Terminal réseau | Formulaire dominant | Interface de ping, pas une console générale |

**Bilan : 4 familles principalement formulaires, 4 hybrides, 10 structurées/visuelles.** Ce découpage n'inclut pas Notes, Accès locaux, Diagnostics et éditeurs secondaires. Il ne mesure ni finesse visuelle ni fidélité Windows. Ne pas annoncer « toutes les apps refondues » sur cette base.

## 6. Fidélité aux services réels

| Domaine | Acquis pédagogique | Écart à ne pas masquer |
|---|---|---|
| AD | Comptes, groupes, OU, politique et refus cohérents | Pas DC réel, réplication, Kerberos/LDAP ou GPO complète |
| SMB/fichiers | ACL deux couches, droits, quotas/capacité | Pas sous-dossiers/héritage/deny ni protocole SMB réel |
| DNS | A/AAAA/CNAME, suffixe, caches | Une zone ; pas DNS Internet, SRV/MX/PTR/DNSSEC ; AD réel dépend aussi de SRV |
| FTP | Comptes/droits, contrôle/données, transferts simulés | Le service web et le service Server-PT ne forment pas automatiquement un seul état |
| Impression | File/spooler/états et prérequis | Pas pilotes/processus/événements Windows complets |
| VPN | Politique d'accès/location/session | Pas tunnel réseau réel |
| Mail/licences | Boîtes internes, envoi, capacités et attributions | Pas SMTP/IMAP/Exchange ; politiques de rétention sans purge automatique |
| Installation | Atelier disk/image/étapes | Pas installation Windows réelle ; pratique de navigation et décisions, pas toutes les procédures Windows |
| Tickets | Suivis/tâches/priorité/solution/réouverture | Confirmation déclarative ; ni portail demandeur complet ni tous les workflows GLPI |
| Inventaire | IDs, affectation, préparation/restitution | Cycle administratif séparé du raccordement réseau et de l'OS |

Références officielles consultées : GLPI cycle de vie/solution/gestion, Microsoft AD DS, SMB et autorisations, Cisco campus. Ces références montrent des écarts de périmètre ; elles ne justifient pas de tout reproduire. Objectif : gestes enseignés exacts, état causal crédible et limites explicites.

## Contrôles transversaux supplémentaires

**X01 — Confirmé, P1 : prise en main serveur non représentée.** `_observe_one` recense PC-PT/Laptop-PT ; `workstations()` propose les bureaux clients simulés et marque les autres postes observés sans prise en main. Un serveur qui répond au ping n'acquiert donc pas un bureau serveur. La demande antérieure de prise en main des serveurs reste hors de ce parcours.

**X02 — Limite, P1 : tests UI sans navigateur réel.** Plusieurs suites JS extraient des fonctions HTML et emploient un DOM factice. Elles vérifient contrats et actions, pas pixels, géométrie, comportement OS.js réel, focus navigateur ou scroll. Compléter par parcours navigateur et captures de référence.

**X03 — Acquis, contrôle partiel : garde-fous locaux.** Host localhost, token d'action et IDs environnement/cible sont vérifiés dans les routes principales ; états et secrets sont séparés dans plusieurs moteurs. Cela ne constitue pas un audit de sécurité complet. Le coffre des comptes locaux conserve volontairement les mots de passe de formation : ne jamais y mettre de vrais secrets.

**X04 — Limite, P2 : documentation de développement historique.** CLAUDE.md décrit surtout le générateur historique et ses fichiers ; les clauses ajoutées décrivent le service desk. La feuille de route y conserve des cases anciennes. Réconcilier README, roadmap et contrats de version pour éviter des instructions contradictoires.

**X05 — À mesurer, P1 : polling et re-rendu.** Plusieurs lectures périodiques existent : desktop 2 s, workspace 2 s, lectures Tickets 4 s et suivi labs 3 s. La documentation de certaines apps est assemblée à l'ouverture. Vérifier trafic redondant, données périmées, brouillons, fenêtre en arrière-plan et chargement ; ne pas attribuer automatiquement un problème à Chrome.

## 7. Architecture proposée — à discuter avant implémentation

Un état persistant commun décrit personnes, appareils, locaux, services, ressources, droits, sessions et activités. Trois niveaux séparés : état effectif, observation disponible, connaissance du client. Les tickets référencent cet état et ne servent pas de source unique de l'état de santé.

Événements indépendants : panne/modification survient, ressources touchées calculées, activité interrompue, employé constate, signalement reçu après délai, autres signalements reliés, réparation, retest, confirmation. Les demandes planifiées (arrivée/mobilité) restent distinctes des incidents.

Chaque ressource possède son identité et sa portée : fichier local `C:\…`, partage UNC `\\serveur\partage`, lecteur mappé, dépôt FTP, imprimante, compte. Un client ne connaît que ses symptômes et essais. Les diagnostics techniques restent dans les outils du technicien.

Pont PT : observations source/cible/service avec dernier succès, dernier essai, expiration et erreur ; surveillance ciblée ordonnancée selon budget. Le fast-forward manuel est global à la simulation PT, pas une accélération isolée d'un seul PC. Aucun fast-forward périodique. Pas de preuve SMB déduite d'ICMP.

Topologies : familles PME compacte, bureaux segmentés/VLAN/Wi-Fi, multisite ; complexité choisie pour une compétence. Placement commun basé sur graphe, zones physiques, réserves d'encombrement et câblage ; appliquer aux réseaux initiaux ET références/PKA, sans déplacer silencieusement les sauvegardes existantes.

## 8. Plan de consolidation et critères de sortie

1. **Fiabilité P0** : reproduire annuaire intermittent, corriger contrat d'expiration dialogue ; instrumentation locale de latence/âge/preuves/verrous, sans nouveau ping implicite lors de lecture. Test changement de fenêtre, 30 postes, erreur du pont, câble coupé/rétabli.
2. **Contrats P1** : identités et ressources communes, chronologie, statuts unknown/failed séparés ; supprimer ambiguïtés entre parcours anciens/nouveaux.
3. **Procédural P1** : incidents réseau réversibles dans PT9, avant signalement ; couverture par familles et regroupement ; activité calculée depuis dépendances. Tester collatéral et reprise sauvegarde.
4. **Textes/dialogues P1** : titre/action/ressource/symptôme, questions utiles par famille, retest observé ; audit manuel de chaque formulation et guide.
5. **Disposition P1** : contrat partagé de layout ; matrice gabarit×taille×PKT/PKA×initial/correction. Vérifications géométriques et recette PT réelle.
6. **UI P1/P2** : tokens/composants, documentation structurée, apps dominées par formulaires, focus/scroll/erreurs ; comparaison visuelle Windows aux maquettes.
7. Ensuite seulement : événements d'entreprise élargis, dialogue libre facultatif, bilan pédagogique/portfolio.

### Recette indispensable

| Test | Attendu |
|---|---|
| Annuaire après changement fenêtre et attente | Session conservée ; disponibilité expliquée ; absence de preuve n'annonce pas une panne |
| 30 postes, plusieurs sessions actives | Âge mesuré ; contrôles ciblés réactifs ; pas de blocage silencieux |
| Câble client coupé puis rétabli | Échec réel puis nouvelle preuve ; pas d'accès accordé sur ancien succès |
| Pont interrompu | État inconnu, erreur visible, aucune validation inventée |
| Dossier local vs partage vs FTP | Plainte/action et outil distincts |
| Incident réseau vs application | Réparer dans la bonne couche ; conserver les autres services |
| Signalement répétitif/shared | Regroupement et impact cohérents, chronologie persistée |
| PKT et PKA d'un même lab | Position/noms cohérents ; correction non dévoilée prématurément |
| App petite/grande/partagée | Contrôles accessibles, scroll contenu, focus et brouillons conservés |

## Références externes

- https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketmanagement
- https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketlifecycle
- https://help.glpi-project.org/documentation/modules/assistance/tabs/solution
- https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/active-directory-domain-services
- https://learn.microsoft.com/fr-fr/windows-server/storage/file-server/file-server-smb-overview
- https://learn.microsoft.com/fr-fr/iis/web-hosting/configuring-servers-in-the-windows-web-platform/configuring-share-and-ntfs-permissions
- https://www.cisco.com/c/en/us/td/docs/solutions/CVD/Campus/cisco-campus-lan-wlan-design-guide.html

## Validation automatisée

Exécution de `python tests/run_tests.py` terminée avec code de sortie 0 : lanceur 2 tests, cœur 19/19, ateliers 8 tests, web Python 710 tests et les 32 suites JavaScript. Journal joint : `AUDIT-V0625-TESTS.log`. Les 108 modules Python de premier niveau dans web ont également été analysés syntaxiquement sans erreur.

Aucun test réel Windows/PT9 ni contrôle visuel navigateur effectué. Les tests créent leurs propres artefacts ; aucun état réseau actif de Damien n'a été modifié. Aucun code fonctionnel corrigé ni nouveau numéro de version livré.
