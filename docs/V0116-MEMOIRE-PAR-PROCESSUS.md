v116 — Mémoire privée résidente par processus Packet Tracer

Ferme NetOps, remplace les fichiers dans ton dossier actuel, puis lance LANCER-DIAGNOSTIC-RAM.bat.
Chaque PID dispose maintenant de sa propre ligne Mémoire privée résidente et de son écart depuis le départ.
Aucune addition des processus n’est présentée comme valeur principale.
Comparer le même PID dans le Gestionnaire des tâches, avec la colonne Mémoire (ensemble de travail privé).
La colonne Mémoire peut utiliser un autre compteur selon la version de Windows et la vue sélectionnée.
Les rafraîchissements peuvent aussi occasionner de petits écarts.
Résidente totale et mémoire privée engagée restent disponibles comme détails distincts.
Les valeurs sont affichées en Mo avec un diviseur de 1 048 576 octets, pour la comparaison usuelle sous Windows.
Les relevés JSON restent en octets ; nouveau champ private_working_set_bytes par processus.
Si le compteur manque, aucune autre métrique ne le remplace. Une indisponibilité explicite est affichée.
La lecture utilise GetProcessMemoryInfo avec PROCESS_MEMORY_COUNTERS_EX2.
Microsoft documente ce compteur sur Windows 10/11 22H2 avec les mises à jour de septembre 2023 :
https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex2
Sur les versions antérieures, les deux anciennes mesures restent lisibles si l’API les fournit.

Commence par A · Nombre d’appareils uniquement. Après 3 minutes, garde le diagnostic ouvert encore 3 minutes et exporte le JSON.
Redémarre Packet Tracer et reconnecte le bridge entre les essais A, B, C, D.
Aucune commande PT supplémentaire pour mesurer la mémoire. Cadence des tests et surveillance normale inchangées.

Validation : 25 tests locaux réussis, y compris compteur EX2 simulé, repli ancien Windows, absence de valeur, erreur d’accès et affichage séparé de deux PID.
La lecture native Windows reste à confirmer sur le PC utilisateur.
