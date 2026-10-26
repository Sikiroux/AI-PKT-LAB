# v0.76 — Confirmer un téléchargement FTP

## Défaut corrigé

La demande FTP annonçait un transfert, mais sa vérification s'arrêtait à la disponibilité du service avant authentification. Un serveur remis en route pouvait donc suffire sans connexion ni téléchargement du demandeur.

## Consigne précise pour les nouveaux incidents

Un nouveau ticket FTP nomme un document existant du dépôt, sélectionné de manière déterministe, et demande de le télécharger dans les fichiers locaux du poste concerné. Le nom du fichier et le sens téléchargement sont conservés dans le ticket et l'incident persistant. Un dépôt vide ne peut pas produire cette demande de téléchargement : la famille est exclue du tirage aléatoire, et une demande FTP explicite est refusée clairement.

La correction détaillée indique de rétablir le service, puis de se connecter au client FTP du poste demandeur et de télécharger le document indiqué. Aucun transfert n'est déclenché par l'aide.

## Traces de réussite

Après un téléchargement autorisé et la copie effective dans les fichiers locaux simulés, le serveur conserve une trace : environnement, rôle et numéro de série du poste source, compte affecté au poste, compte FTP utilisé, nom, horodatage et empreinte du contenu.

Cette trace ne contient ni mot de passe ni contenu du fichier. Elle n'est pas exposée dans l'état public du client FTP. Son historique partagé est limité aux 100 derniers téléchargements ; une trace sortie de cet historique ne peut plus confirmer un ancien transfert. Les refus de transfert et les simples listings ne créent aucune trace.

## Vérification en deux résultats

1. Service FTP accessible depuis le poste du demandeur avec preuve réseau récente.
2. Téléchargement confirmé depuis ce poste, après l'application de la panne, dans le même environnement et pour le fichier demandé. La copie locale doit correspondre au contenu actuel du dépôt et à l'empreinte enregistrée.

Une copie locale seule, un ancien téléchargement, un autre poste, un autre document, une trace étrangère ou future ne suffisent pas. Si la copie locale ou le document du dépôt ont changé, un nouveau téléchargement du document courant est nécessaire pour confirmer cette copie. Le compte du demandeur reste contrôlé selon les règles v0.73.

Une trace valide témoigne d'un téléchargement effectué avec un compte FTP autorisé à cet instant. Elle n'exige pas de maintenir cette connexion FTP ouverte jusqu'à la clôture. Aucun mot de passe supplémentaire n'est demandé par la vérification elle-même.

## Dialogue et anciennes sauvegardes

Le retest distingue le service encore indisponible, le service accessible sans téléchargement confirmé et le téléchargement confirmé sur le poste. Il ne se connecte pas et ne télécharge rien à la place de l'utilisateur.

Les anciens incidents FTP sans nom de fichier précis exigent également un téléchargement réel, postérieur à la panne, d'un document encore présent dans le dépôt, depuis le poste concerné. Aucune trace passée n'est inventée à partir d'une copie locale. Ces anciens tickets n'imposent pas rétroactivement un nom qu'ils n'avaient pas donné.

## Limites

Il s'agit du client et du dépôt FTP pédagogiques, pas d'un serveur FTP réel dans Packet Tracer. Le contrôle réseau reste un proxy ICMP. Le téléchargement du poste demandeur ne vérifie pas les comptes et transferts de chaque salarié affecté par une panne partagée. Les nouvelles demandes portent sur un téléchargement, pas un envoi. La validation d'un document réellement imprimé reste à approfondir.

## Tests et recette réelle

Dix nouveaux tests couvrent consigne précise, service seul/copie préexistante insuffisants, réussite puis clôture, autre poste/fichier, traces anciennes/étrangères/futures, contenu modifié, transfert refusé, absence de transfert automatique, ancien ticket et historique borné/privé. Tests existants client FTP (40), incidents (25), dialogue (13) et aides (8) verts. Suite web complète relancée ; générateur, ateliers et JavaScript inchangés depuis leur recette v0.70.

Recette Windows / PT9 à faire :

1. Recevoir un nouveau ticket FTP et relever le fichier ainsi que le poste demandés.
2. Rétablir le service, vérifier : le premier résultat peut être valide, le téléchargement doit rester non confirmé.
3. Depuis le bon bureau client, se connecter au client FTP avec un compte autorisé et télécharger le fichier nommé.
4. Vérifier de nouveau : les deux résultats doivent être valides si les préconditions réseau et d'identité le sont.
5. Refaire dans une copie de test en téléchargeant depuis un autre poste ou avec un autre fichier : cela ne doit pas compléter la demande.
6. Sauvegarder/reprendre l'entreprise et vérifier la conservation du transfert déjà effectué, sous réserve de nouveaux contrôles réseau.
