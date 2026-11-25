v115 — Diagnostic RAM automatique sous Windows

Ferme complètement NetOps. Extrais la mise à jour dans ton dossier existant en remplaçant les fichiers.
Lance LANCER-DIAGNOSTIC-RAM.bat et garde Packet Tracer ouvert avec le même réseau et son bridge connecté.
Commence par A · Nombre d’appareils uniquement (3 minutes).

La mémoire de Packet Tracer est relevée au départ, toutes les deux secondes et à la fin.
Garde le diagnostic ouvert trois minutes après la fin pour enregistrer le suivi sans nouveaux appels PT.
Exporte ensuite le journal JSON : il contient les relevés avec PID, temps et phase test/après.
RAM résidente = mémoire physique actuellement résidente du processus.
Mémoire privée engagée = allocations privées engagées, pas uniquement la RAM physique.
Ces valeurs peuvent différer de la colonne Mémoire choisie dans le Gestionnaire des tâches.
Plusieurs Packet Tracer : tous les PID sont affichés, valeurs additionnées ; utilise une seule instance pour comparer.
Un changement de PID invalide la comparaison directe ; redémarre PT entre les essais, pas au milieu.
Processus introuvable ou accès refusé : indisponibilité explicite, aucune valeur zéro inventée.
Mesure via les API Windows, sans bibliothèque à installer ni commande envoyée à PT.
Les exécutables recherchés sont PacketTracer.exe, PacketTracer8.exe et PacketTracer9.exe.

Après A, teste B (identités), C (interfaces sans liens), D (liens sans propriétés IP).
Redémarre Packet Tracer et reconnecte le bridge entre chaque essai.
Les sondes sont indépendantes ; aucun inventaire complet de préparation pour A–D.
La surveillance normale reste inchangée. Le nettoyage des logs est retiré des choix.

20 tests locaux réussis et syntaxe JavaScript vérifiée. Lecture native Windows et évolution réelle de RAM à valider sur ton PC.
