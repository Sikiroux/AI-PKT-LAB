# v0.48.1 — noms et placement des nouvelles entreprises

## Nommage

Les nouvelles entreprises choisissent depuis la seed une convention par rôle (`PC-CPT-01`, `PC-ACC-01`) ou par inventaire (`PC-001`, `PC-002`, `PC-003`). Le portable du technicien est `IT-LT-TECH-01`, l'imprimante `PRN-USR-01`. Les noms ne contiennent pas de prénom et ne portent plus systématiquement le code du site. Le code du site reste dans le contexte de l'entreprise.

L'affectation à une personne reste une information séparée. Ce bloc ne renomme pas un appareil lors d'un changement d'utilisateur et n'ajoute pas encore une interface de changement de convention.

## Placement logique

Le routeur se trouve au-dessus de trois branches : utilisateurs, serveurs et accueil. Les appareils d'une même branche sont regroupés sous son switch. Les serveurs ne sont plus dispersés entre les autres branches. La seed choisit l'ordre des trois zones et un espacement de 500 ou 600 unités : douze dispositions possibles du même réseau logique.

Les coordonnées des appareils concernés sont dans les limites 0–3900, avec des marges. La taille réelle du réseau et son routage restent inchangés : une disposition différente ne constitue pas une nouvelle architecture réseau. Les positions physiques, pièces et baies ne sont pas modifiées par ce bloc.

Le pont ne force pas le zoom ou le défilement de Packet Tracer. Selon la taille de la fenêtre, un ajustement de vue peut encore être nécessaire. La lisibilité des liens et des étiquettes est à tester visuellement dans PT 9.

## Reproductibilité et anciennes sauvegardes

Le tirage de présentation utilise une graine dérivée dédiée et versionnée. Il ne consomme pas les tirages d'adressage ou de panne. Le manifeste `network_design` conserve la convention, l'ordre des zones, les noms et les positions. Réseau initial, référence et appareils simulés utilisent les mêmes identités.

Ouvrir une ancienne sauvegarde ne la renomme pas et ne la repositionne pas. Sa réinitialisation garde le générateur de présentation historique. Une nouvelle entreprise créée dans cette version utilise le nouveau placement ; recréer une ancienne seed comme nouvelle entreprise adopte donc ce nouveau rendu.

## Recette manuelle

1. Créer une nouvelle entreprise, ouvrir son `.pkt` et vérifier les trois branches et les noms.
2. Tester l'accès distant et une intervention : la cible doit correspondre à l'appareil affiché dans Packet Tracer.
3. Recréer la même seed dans la même version : mêmes noms, zones et coordonnées.
4. Essayer plusieurs seeds : variantes de convention et de disposition.
5. Reprendre une ancienne sauvegarde, puis contrôler les anciens noms ; tester aussi la réinitialisation après sauvegarde de son travail.

Les tests automatiques vérifient le XML et les manifestes. Ils ne certifient pas le rendu ni le comportement réseau réel dans PT 9.
