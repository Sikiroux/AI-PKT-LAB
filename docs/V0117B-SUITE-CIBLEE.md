v117b — Suite RAM automatique

1. Sauvegarde et ferme toutes les fenêtres Packet Tracer et NetOps.
2. Dans ton dossier actuel, applique la mise à jour en remplaçant les fichiers.
3. Lance LANCER-DIAGNOSTIC-COMPLET.bat. La suite démarre automatiquement.
4. Garde NetOps ouvert. À la fin, envoie diagnostic-complet-netops.json, téléchargé automatiquement.

La suite ouvre elle-même une copie du fichier network_file de l’entreprise active enregistrée.
Chaque test a sa propre copie identique et un nouveau processus Packet Tracer.
Elle attend jusqu’à 90 secondes le bridge et vérifie le nom du fichier réellement ouvert.
Si PT demande une activation/connexion ou si MCP BUILDER ne démarre pas, cette étape peut nécessiter une intervention.
Sans confirmation, elle s’arrête explicitement ; elle ne teste jamais un autre fichier par supposition.
PacketTracer.exe est recherché dans Program Files/Cisco Packet Tracer*/bin ou à la racine de ce dossier.
Pour une installation ailleurs, définir NETOPS_PACKET_TRACER_EXE avec le chemin complet de l’exécutable.

4 nouveaux essais uniquement, une seule passe bornée : F (objets gardés), E (même appareil), G (objets gardés + liens), H (ramasse-miettes si disponible).
Les tests déjà effectués A à D, pause, OK, texte fixe, pings et inventaire ne sont pas relancés par la suite.
Chaque essai : 3 minutes de mesures + 3 minutes après arrêt. Durée totale environ 25 à 30 minutes.
Le mode surveillance réelle « full » et le nettoyage expérimental ne sont pas inclus : on utilise les sondes isolées.
La suite ferme l’arbre du processus qu’elle a lancé avec sa copie jetable avant le test suivant.
Elle ne ferme aucune instance existante : il faut les fermer avant le lancement.
Le fichier original n’est pas modifié. Ne travaille pas dans les fenêtres de test, qui seront fermées automatiquement.
Limite de 2 Gio de mémoire privée engagée pour les processus PT détectés ; dépassement = arrêt de la suite et conservation du rapport partiel.
Une mesure mémoire indisponible arrête également la suite.
Le bouton Arrêter la suite conserve les résultats déjà disponibles et ferme le processus de test.

Le rapport complet est aussi sauvegardé après chaque test dans web/diagnostics-ram/suite-*/diagnostic-complet.json.
Les copies .pkt restent dans ce dossier. Aucun balayage des fichiers temporaires n’est ajouté dans cette version.
Chaque résultat inclut le mode, le fichier ouvert, les compteurs, erreurs, état du cache et relevés mémoire par PID.
Une sonde en erreur est marquée failed dans le rapport ; une erreur de lancement ou de sécurité arrête la suite.

Validation locale : 32 tests ciblés réussis (sondes, cache, mémoire, routes HTTP, séquence simulée, copies et rapport, annulation et limite mémoire), syntaxe JS et compilation Python.
Ouverture native, reconnexion automatique et fermeture de PT restent à confirmer sur Windows avec ton extension.
