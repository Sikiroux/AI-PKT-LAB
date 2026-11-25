# v0.93 — Mauvais masque IPv4 et références réseau

Le catalogue Réseau de l’entreprise à 30 employés peut maintenant choisir une adresse IPv4 erronée ou un mauvais masque. La sélection conserve le même signalement de connectivité : la cause n’est pas annoncée dans le ticket.

La panne de masque conserve l’adresse du poste et choisit un masque compatible avec le mécanisme de dépannage existant. Elle est admise seulement si sa modification et un échec de communication sont confirmés par le pont. Le poste peut rester joignable depuis le technicien alors que son accès au serveur échoue.

Le contrôle préalable exige désormais que l’adresse ET le masque correspondent à la référence initiale. Un poste déjà mal configuré ne reçoit pas une nouvelle panne. Les postes générés dans l’entreprise à 30 employés utilisent des sous-réseaux /24 ; les références documentaires affichent ce masque, ainsi que la passerelle et le VLAN enregistrés. Pour un autre environnement incomplet, les valeurs inconnues restent non renseignées.

La vérification finale relit toujours les paramètres réels et contrôle les trajets technicien → poste et poste → serveur. Elle ne modifie aucune configuration.

## Validation

48 suites JavaScript et 47 tests Python ciblés passent : incidents réseau (11), incidents entreprise (25), mutations réseau existantes (5) et documentation (6).

Les tests utilisent un pont simulé. Une recette réelle dans Packet Tracer 9 reste nécessaire. Les pannes de VLAN, trunk et DHCP ne sont pas ajoutées aux arrivées automatiques par cette version.
