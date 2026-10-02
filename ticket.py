"""
ticket.py — Textes de mise en situation (bilingue FR/EN) à partir du rapport de
faults.py, utilisés dans le bloc <INSTRUCTIONS> natif du .pka (voir instructions.py).

Règle inchangée depuis la v1 "ticket helpdesk" : le texte décrit ce que
l'UTILISATEUR constate, avec ses mots, jamais la cause technique. Plusieurs
formulations par panne, tirées au hasard, pour ne pas reconnaître la panne à
la phrase.
"""

import random

# {device} = poste concerné. Formulations utilisateur, jamais de vocabulaire technique.
SYMPTOMS = {
    'pc_wrong_gateway': {
        'fr': [
            "Depuis ce matin je n'ai plus Internet ni le serveur de fichiers, mais je vois l'imprimante du bureau à côté.",
            "Mon poste ({device}) n'arrive plus à sortir du réseau. Les collègues à côté n'ont aucun souci.",
        ],
        'en': [
            "Since this morning I have no more Internet or file server access, but I can still see the printer next door.",
            "My computer ({device}) can't reach anything outside our network anymore. My coworkers nearby have no issue.",
        ],
    },
    'pc_wrong_ip': {
        'fr': [
            "Plus rien ne marche sur mon PC ({device}) : ni Internet, ni les dossiers partagés. Les autres postes vont bien.",
            "Un prestataire est passé hier sur mon poste ({device}) et depuis je n'ai plus de réseau du tout.",
        ],
        'en': [
            "Nothing works on my PC ({device}) anymore: no Internet, no shared folders. The other computers are fine.",
            "A contractor worked on my computer ({device}) yesterday and I've had no network at all since then.",
        ],
    },
    'pc_wrong_mask': {
        'fr': [
            "C'est bizarre : j'arrive à joindre le poste de mon voisin mais pas Internet ni le reste du réseau ({device}).",
            "Depuis que j'ai 'bidouillé' mes paramètres réseau ({device}), certaines choses marchent et d'autres non.",
        ],
        'en': [
            "It's strange: I can reach my neighbor's computer but not the Internet or the rest of the network ({device}).",
            "Since I 'tweaked' my network settings ({device}), some things work and others don't.",
        ],
    },
    'pc_power_off': {
        'fr': [
            "Le poste {device} ne répond plus du tout, on n'arrive pas à s'y connecter à distance.",
            "Le PC {device} de la salle de réunion ne répond pas au ping de la supervision.",
        ],
        'en': [
            "Computer {device} doesn't respond at all anymore, we can't connect to it remotely.",
            "PC {device} in the meeting room doesn't answer the monitoring team's ping.",
        ],
    },
    'cable_missing': {
        'fr': [
            "Mon ordinateur ({device}) affiche une petite croix rouge sur l'icône réseau. Le ménage est passé hier soir.",
            "Plus de réseau sur {device} depuis qu'on a déplacé les bureaux.",
        ],
        'en': [
            "My computer ({device}) shows a small red cross on the network icon. Cleaning staff came by last night.",
            "No more network on {device} since we moved the desks around.",
        ],
    },
    'router_interface_shutdown': {
        'fr': [
            "Plus personne n'a accès à Internet dans tout le service, mais on peut encore s'échanger des fichiers entre nous.",
            "Toute l'équipe est coupée de l'extérieur depuis l'intervention de maintenance de cette nuit.",
        ],
        'en': [
            "Nobody in the whole department has Internet access anymore, but we can still share files among ourselves.",
            "The whole team has been cut off from the outside since last night's maintenance work.",
        ],
    },
    'router_wrong_ip': {
        'fr': [
            "Aucun poste du service n'arrive à sortir du réseau local depuis la reconfiguration du routeur.",
            "Tout le monde a perdu Internet d'un coup. Entre nous, on se voit encore.",
        ],
        'en': [
            "No computer in the department can leave the local network since the router was reconfigured.",
            "Everyone lost Internet access at once. We can still see each other locally, though.",
        ],
    },
    'dhcp_wrong_default_router': {
        'fr': [
            "Les PC ont bien une adresse IP mais aucun n'arrive à joindre l'extérieur.",
            "On a redémarré nos PC ce matin et depuis, plus d'accès en dehors du service.",
        ],
        'en': [
            "The PCs do get an IP address, but none of them can reach anything outside.",
            "We restarted our PCs this morning and since then, no access outside the department.",
        ],
    },
    'switch_no_default_gateway': {
        'fr': [
            "La supervision (sur PC-ADMIN, au service informatique) signale S1 injoignable depuis ce matin. "
            "Pourtant, personne dans le service ne se plaint.",
            "Depuis le poste d'administration, impossible de joindre S1 pour la maintenance de ce soir. "
            "Les utilisateurs, eux, travaillent normalement.",
        ],
        'en': [
            "Monitoring (on PC-ADMIN, IT department) reports S1 unreachable since this morning. "
            "Yet nobody in the department is complaining.",
            "From the admin workstation, S1 can't be reached for tonight's maintenance. "
            "Regular users are working normally, though.",
        ],
    },
    'switch_svi_shutdown': {
        'fr': [
            "Le switch S1 ne répond plus à la supervision, ni au ping, alors que tous les postes "
            "du service fonctionnent.",
            "Impossible d'administrer S1 : il ne répond à rien. Côté utilisateurs, aucun souci signalé.",
        ],
        'en': [
            "Switch S1 no longer responds to monitoring or to ping, even though every computer "
            "in the department works fine.",
            "S1 can't be managed anymore: it doesn't respond to anything. No issue reported by users, though.",
        ],
    },
    'ospf_network_missing': {
        'fr': [
            "Depuis un des sites, impossible de joindre l'autre site ni Internet, alors que les postes "
            "locaux communiquent normalement entre eux.",
            "Un site semble isolé du reste du réseau depuis la dernière intervention sur un routeur.",
        ],
        'en': [
            "From one of the sites, nothing can be reached outside — not the other site, not the Internet — "
            "even though local computers still talk to each other fine.",
            "One site seems cut off from the rest of the network since the last router change.",
        ],
    },
    'wan_wrong_ip': {
        'fr': [
            "Un site a totalement perdu la liaison avec le reste du réseau depuis ce matin.",
            "Plus aucune communication entre un des sites et les autres sites ou Internet.",
        ],
        'en': [
            "One site has completely lost its link to the rest of the network since this morning.",
            "No communication at all between one of the sites and the other sites or the Internet anymore.",
        ],
    },
    'nat_inside_missing': {
        'fr': [
            "Un des sites n'arrive plus à sortir vers Internet du tout, alors que la communication "
            "entre sites fonctionne toujours.",
            "Les utilisateurs d'un site se plaignent de n'avoir plus aucun accès Internet, mais ils "
            "voient bien les autres sites.",
        ],
        'en': [
            "One of the sites can no longer reach the Internet at all, even though communication "
            "between sites still works.",
            "Users at one site report no Internet access whatsoever, yet they can still reach the other sites fine.",
        ],
    },
    'dhcp_wrong_network': {
        'fr': [
            "Les postes affichent 'Réseau non identifié' et une adresse qui commence par 169.254.",
            "Après le redémarrage général de ce matin, aucun PC n'obtient de réseau.",
        ],
        'en': [
            "The computers show 'Unidentified network' and an address starting with 169.254.",
            "After this morning's general restart, no PC is getting a network address.",
        ],
    },
    'default_route_wrong_nexthop': {
        'fr': [
            "Plus personne n'arrive à sortir sur Internet depuis ce matin, mais les sites communiquent "
            "toujours très bien entre eux.",
            "Internet est totalement coupé pour tout le monde depuis l'intervention sur le routeur de bordure. "
            "Les échanges entre sites, eux, fonctionnent normalement.",
        ],
        'en': [
            "Nobody can reach the Internet anymore since this morning, but the sites still communicate "
            "perfectly fine with each other.",
            "Internet access is completely down for everyone since the edge router was touched. "
            "Traffic between sites, though, still works fine.",
        ],
    },
    'stp_root_priority_missing': {
        'fr': [
            "Depuis la dernière maintenance, le réseau est bizarrement plus lent par moments, comme si "
            "le trafic empruntait un chemin plus long qu'avant.",
            "Rien n'est complètement coupé, mais certains postes mettent plus de temps que d'habitude "
            "à joindre le reste du réseau depuis hier.",
        ],
        'en': [
            "Since the last maintenance, the network is oddly slower at times, as if traffic were taking "
            "a longer path than before.",
            "Nothing is fully down, but some computers take longer than usual to reach the rest of the "
            "network since yesterday.",
        ],
    },
    'nat_outside_missing': {
        'fr': [
            "Plus aucun site n'arrive à sortir sur Internet depuis ce matin, mais les sites communiquent "
            "toujours entre eux sans problème.",
            "Internet est totalement injoignable pour tout le monde depuis l'intervention sur le routeur "
            "de bordure, alors que le reste du réseau interne fonctionne normalement.",
        ],
        'en': [
            "No site can reach the Internet anymore since this morning, but the sites still communicate "
            "with each other without any issue.",
            "The Internet is completely unreachable for everyone since the edge router was touched, "
            "even though the rest of the internal network works fine.",
        ],
    },
    'pat_rule_missing': {
        'fr': [
            "Plus personne n'arrive à sortir sur Internet depuis ce matin, pourtant tout semblait "
            "correctement branché côté routeur de bordure.",
            "Internet ne passe plus du tout pour aucun site depuis la dernière intervention sur le NAT.",
        ],
        'en': [
            "Nobody can reach the Internet anymore since this morning, even though everything seemed "
            "correctly set up on the edge router.",
            "Internet access is completely down for every site since the last change on NAT.",
        ],
    },
    'switch_svi_wrong_ip': {
        'fr': [
            "La supervision n'arrive plus à joindre S1 à son adresse habituelle depuis ce matin, "
            "alors que les utilisateurs du service travaillent normalement.",
            "Impossible d'administrer S1 depuis le poste d'administration : l'adresse attendue ne "
            "répond plus, mais les postes du service communiquent sans souci.",
        ],
        'en': [
            "Monitoring can no longer reach S1 at its usual address since this morning, even though "
            "department users are working normally.",
            "S1 can't be managed from the admin workstation: the expected address doesn't respond, "
            "yet department computers communicate without any issue.",
        ],
    },
    'hostname_wrong': {
        'fr': [
            "L'inventaire réseau ne correspond plus à ce qui s'affiche quand on se connecte en console "
            "sur un des équipements.",
            "Un équipement répond à un nom différent de celui attendu dans la documentation, alors que "
            "tout fonctionne normalement par ailleurs.",
        ],
        'en': [
            "The network inventory no longer matches what shows up when connecting to the console of "
            "one of the devices.",
            "A device answers to a different name than the one expected in the documentation, even "
            "though everything else works normally.",
        ],
    },
    'ospf_wrong_area': {
        'fr': [
            "Un site semble isolé du reste du réseau depuis la dernière intervention sur un routeur, "
            "alors que le lien lui-même répond bien au ping.",
            "Les routes vers un des sites ont disparu depuis hier, sans que personne n'ait touché au "
            "câblage ni à l'adressage IP.",
        ],
        'en': [
            "One site seems cut off from the rest of the network since the last router change, even "
            "though the link itself responds fine to ping.",
            "Routes to one of the sites disappeared since yesterday, without anyone having touched the "
            "cabling or the IP addressing.",
        ],
    },
    'ospf_transit_passive': {
        'fr': [
            "Un site a perdu toutes ses routes vers le reste du réseau depuis ce matin, mais le lien "
            "répond toujours au ping.",
            "Depuis la dernière maintenance, un site ne reçoit plus aucune mise à jour de routage, "
            "alors que la connectivité de base du lien fonctionne.",
        ],
        'en': [
            "One site lost all its routes to the rest of the network since this morning, but the link "
            "still responds to ping.",
            "Since the last maintenance, one site no longer receives any routing updates, even though "
            "basic link connectivity works.",
        ],
    },
    'ospf_timer_mismatch': {
        'fr': [
            "La liaison vers un site se coupe et revient sans arrêt depuis hier, sans qu'aucun câble "
            "n'ait été touché.",
            "Un site perd puis retrouve l'accès au reste du réseau de façon répétée depuis la dernière "
            "intervention sur un routeur.",
        ],
        'en': [
            "The link to one site keeps dropping and coming back since yesterday, without any cable "
            "having been touched.",
            "One site repeatedly loses and regains access to the rest of the network since the last "
            "router change.",
        ],
    },
    'access_wrong_vlan': {
        'fr': [
            "Un poste ne voit plus aucun de ses collègues habituels depuis ce matin, mais le câble "
            "et la carte réseau semblent corrects.",
            "Depuis l'intervention sur le switch hier, un poste s'est retrouvé isolé de son équipe "
            "habituelle sans que rien n'ait changé sur le poste lui-même.",
        ],
        'en': [
            "A computer no longer sees any of its usual coworkers since this morning, but the cable "
            "and network card seem fine.",
            "Since yesterday's work on the switch, one computer ended up isolated from its usual team "
            "even though nothing changed on the computer itself.",
        ],
    },
    'vlan_missing': {
        'fr': [
            "Tous les postes d'un groupe ont perdu la connexion entre eux en même temps depuis la "
            "maintenance d'hier sur le switch.",
            "Plusieurs postes qui communiquaient très bien ensemble ne se voient plus du tout depuis "
            "ce matin.",
        ],
        'en': [
            "All the computers in one group lost connectivity with each other at the same time since "
            "yesterday's switch maintenance.",
            "Several computers that used to communicate fine with each other can't see one another "
            "at all since this morning.",
        ],
    },
    'trunk_access_mode': {
        'fr': [
            "Depuis l'intervention sur le lien entre les 2 switchs, plus personne ne communique avec "
            "l'autre bâtiment.",
            "Les 2 groupes d'utilisateurs qui passent normalement par le même lien entre switchs ne se "
            "joignent plus du tout depuis hier.",
        ],
        'en': [
            "Since the work on the link between the 2 switches, nobody communicates with the other "
            "building anymore.",
            "The 2 user groups that normally share the same link between switches can't reach each "
            "other at all since yesterday.",
        ],
    },
    'trunk_vlan_filtered': {
        'fr': [
            "Un des 2 groupes d'utilisateurs a perdu l'accès à l'autre bâtiment depuis hier, mais "
            "l'autre groupe n'a aucun souci.",
            "Depuis la maintenance sur le lien entre les 2 switchs, un seul des 2 groupes ne passe "
            "plus, l'autre fonctionne normalement.",
        ],
        'en': [
            "One of the 2 user groups lost access to the other building since yesterday, but the "
            "other group has no issue at all.",
            "Since the maintenance on the link between the 2 switches, only one of the 2 groups no "
            "longer gets through, the other works fine.",
        ],
    },
    'dot1q_wrong_vlan': {
        'fr': [
            "Un groupe d'utilisateurs ne joint plus du tout le reste du réseau depuis la dernière "
            "intervention sur le routeur, mais ils se voient très bien entre eux.",
            "Depuis hier, un des 2 groupes ne passe plus vers l'extérieur de son réseau local, "
            "l'autre groupe n'a aucun souci.",
        ],
        'en': [
            "One user group can no longer reach the rest of the network at all since the last router "
            "change, but they can still see each other just fine.",
            "Since yesterday, one of the 2 groups no longer gets out of its local network, the other "
            "group has no issue.",
        ],
    },
    'pc_wrong_dns': {
        'fr': [
            "Depuis ce matin, je n'arrive plus à ouvrir le site de l'intranet par son nom, mais l'accès "
            "aux autres sites fonctionne.",
            "Un poste n'arrive plus à joindre le serveur par son nom depuis hier, alors que tout le "
            "reste du réseau fonctionne normalement pour lui.",
        ],
        'en': [
            "Since this morning I can't open the intranet site by its name anymore, but access to other "
            "sites still works.",
            "One computer can no longer reach the server by name since yesterday, even though the rest "
            "of the network works fine for it.",
        ],
    },
    'subinterface_shutdown': {
        'fr': [
            "Un groupe d'utilisateurs a perdu tout accès au-delà de son propre réseau local depuis "
            "la dernière intervention sur le routeur.",
            "Depuis hier, un des 2 groupes ne joint plus personne en dehors de son équipe directe, "
            "l'autre groupe fonctionne normalement.",
        ],
        'en': [
            "One user group lost all access beyond its own local network since the last router change.",
            "Since yesterday, one of the 2 groups can't reach anyone outside its direct team anymore, "
            "the other group works normally.",
        ],
    },
}


def scenario_paragraphs(reports, lang='fr', seed=None):
    """Un paragraphe par panne, dans la langue demandée (fr/en). Accepte un
    rapport seul ou une liste de rapports."""
    if isinstance(reports, dict):
        reports = [reports]
    rng = random.Random(seed)
    return [rng.choice(SYMPTOMS[r['id']][lang]).format(device=r['device']) for r in reports]


if __name__ == '__main__':
    demo = [{'id': 'router_interface_shutdown', 'device': 'R1'},
            {'id': 'cable_missing', 'device': 'PC2'}]
    for lang in ('fr', 'en'):
        print(f'--- {lang} ---')
        for p in scenario_paragraphs(demo, lang=lang, seed=3):
            print(' ', p)
