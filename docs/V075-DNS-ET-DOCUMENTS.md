# v0.75 — DNS et lecture du document demandée

## Défaut corrigé

Le ticket DNS simultané demande de retrouver le partage avec son nom habituel et d'ouvrir un document. Son contrôle précédent vérifiait seulement que le nom se résolvait vers l'adresse attendue. Il pouvait donc être validé alors que la lecture restait refusée, la session absente ou le partage vide.

## Vérification en deux résultats

1. Le nom documentaire se résout vers le serveur attendu depuis le poste du demandeur.
2. Un document du partage est lisible dans la simulation depuis ce même poste.

Le deuxième résultat vérifie l'application et le lecteur attendus, l'authentification du demandeur, la présence d'au moins un document dans le partage concerné et les conditions de lecture du moteur fichiers (compte, droits, service et preuve réseau notamment). Une simple liste d'un partage vide ne vaut pas ouverture d'un document.

Si le nom n'est pas confirmé, la lecture n'est pas évaluée et reste inconnue. Un échec de nom observé reste un échec ; une résolution non vérifiée ne devient pas un échec inventé. Si le nom fonctionne mais qu'il manque la session du demandeur, une consigne invite à ouvrir celle-ci. Les deux résultats doivent être valides pour résoudre/clôturer le ticket.

Les gardes d'identité du demandeur et du poste v0.73 restent appliquées avant ces deux contrôles.

## Dialogue

Les tickets DNS proposent aussi la question de session utilisateur. Le retest distingue le nom non confirmé, le nom retrouvé avec lecture refusée, le nom retrouvé avec lecture non vérifiée et la lecture autorisée. Un résultat de nom seul ne devient pas une confirmation du document. L'essai et son résultat restent inscrits dans le dialogue. Aucune question ne lance de ping ou ne répare un service.

## Limites

Ce bloc concerne les incidents DNS simultanés, pas tous les anciens scénarios DNS. Le ticket demande l'accès à un document du partage, sans désigner un fichier particulier : le contrôle vérifie qu'un document de ce partage peut être lu selon la sélection existante du moteur fichiers. Il ne certifie ni lecture humaine, ni application Windows réelle, ni sauvegarde ou écriture. La résolution et les services sont simulés, le réseau reste un proxy ICMP dans Packet Tracer.

Les validations du transfert FTP et de l'impression d'un document restent à approfondir. Les libellés v0.74 continuent de préciser ces limites.

## Tests

Huit nouveaux tests : réparation DNS et lecture possibles, nom seul insuffisant si droits refusés, partage vide, absence de session, nom non confirmé, application/lecteur incorrects, retest distinguant nom et lecture, absence de mutation des fichiers et de ping par le dialogue. Suite web complète relancée ; générateur, ateliers et JavaScript inchangés depuis leur recette v0.70.

## Recette Windows / Packet Tracer 9 à effectuer

1. Recevoir un ticket DNS et remettre le résolveur attendu sur le poste ciblé.
2. Sans session utilisateur ou sans droit de lecture, vérifier le ticket : le nom peut être valide, mais le deuxième contrôle doit empêcher la résolution/clôture.
3. Ouvrir la session du demandeur et rétablir uniquement les accès nécessaires. Vérifier de nouveau : les deux lignes doivent être valides si les autres conditions sont saines.
4. Demander au client de réessayer : sa réponse doit distinguer le nom et le document, sans prétendre écrire ou sauvegarder.
5. Dans une copie de test, rendre le partage vide : son listing ne doit pas suffire.
6. Couper le réseau ou laisser les observations expirer : ne pas valider le ticket à partir d'une ancienne réussite seule.
