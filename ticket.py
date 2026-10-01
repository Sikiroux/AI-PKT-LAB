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
