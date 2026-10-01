"""
ticket.py — Génère un ticket helpdesk à partir du rapport de faults.py

Règle : le ticket décrit ce que l'UTILISATEUR constate, avec ses mots,
jamais la cause technique. Plusieurs formulations par panne, tirées au
hasard, pour ne pas reconnaître la panne à la phrase.
"""

import random
import datetime

USERS = [
    ('Mme Leroy', 'Comptabilité'), ('M. Garnier', 'Ressources humaines'),
    ('Mme Nguyen', 'Accueil'), ('M. Petit', 'Commercial'),
    ('Mme Diallo', 'Direction'), ('M. Moreau', 'Logistique'),
]

# {device} = poste concerné. Formulations d'utilisateur, pas de technicien.
SYMPTOMS = {
    'pc_wrong_gateway': [
        "Depuis ce matin je n'ai plus Internet ni le serveur de fichiers, mais je vois l'imprimante du bureau à côté.",
        "Mon poste ({device}) n'arrive plus à sortir du réseau. Les collègues à côté n'ont aucun souci.",
    ],
    'pc_wrong_ip': [
        "Plus rien ne marche sur mon PC ({device}) : ni Internet, ni les dossiers partagés. Les autres postes vont bien.",
        "Un prestataire est passé hier sur mon poste ({device}) et depuis je n'ai plus de réseau du tout.",
    ],
    'pc_wrong_mask': [
        "C'est bizarre : j'arrive à joindre le poste de mon voisin mais pas Internet ni le reste du réseau ({device}).",
        "Depuis que j'ai 'bidouillé' mes paramètres réseau ({device}), certaines choses marchent et d'autres non.",
    ],
    'pc_power_off': [
        "Le poste {device} ne répond plus du tout, on n'arrive pas à s'y connecter à distance.",
        "Le PC {device} de la salle de réunion ne répond pas au ping de la supervision.",
    ],
    'cable_missing': [
        "Mon ordinateur ({device}) affiche une petite croix rouge sur l'icône réseau. Le ménage est passé hier soir.",
        "Plus de réseau sur {device} depuis qu'on a déplacé les bureaux.",
    ],
    'router_interface_shutdown': [
        "Plus personne n'a accès à Internet dans tout le service, mais on peut encore s'échanger des fichiers entre nous.",
        "Toute l'équipe est coupée de l'extérieur depuis l'intervention de maintenance de cette nuit.",
    ],
    'router_wrong_ip': [
        "Aucun poste du service n'arrive à sortir du réseau local depuis la reconfiguration du routeur.",
        "Tout le monde a perdu Internet d'un coup. Entre nous, on se voit encore.",
    ],
    'dhcp_wrong_default_router': [
        "Les PC ont bien une adresse IP mais aucun n'arrive à joindre l'extérieur.",
        "On a redémarré nos PC ce matin et depuis, plus d'accès en dehors du service.",
    ],
    'switch_no_default_gateway': [
        "La supervision (sur PC-ADMIN, au service informatique) signale S1 injoignable depuis ce matin. "
        "Pourtant, personne dans le service ne se plaint.",
        "Depuis le poste d'administration, impossible de joindre S1 pour la maintenance de ce soir. "
        "Les utilisateurs, eux, travaillent normalement.",
    ],
    'switch_svi_shutdown': [
        "Le switch S1 ne répond plus à la supervision, ni au ping, alors que tous les postes "
        "du service fonctionnent.",
        "Impossible d'administrer S1 : il ne répond à rien. Côté utilisateurs, aucun souci signalé.",
    ],
    'dhcp_wrong_network': [
        "Les postes affichent 'Réseau non identifié' et une adresse qui commence par 169.254.",
        "Après le redémarrage général de ce matin, aucun PC n'obtient de réseau.",
    ],
}

PRIORITY = {1: 'Basse', 2: 'Moyenne', 3: 'Haute', 4: 'Haute', 5: 'Critique'}


def make_ticket(reports, level=1, seed=None):
    """
    Retourne l'énoncé : un ticket par panne, chacun venant d'un utilisateur
    différent (en entreprise, deux pannes = deux personnes qui appellent).
    Accepte un rapport seul ou une liste de rapports.
    """
    if isinstance(reports, dict):
        reports = [reports]
    rng = random.Random(seed)
    users = rng.sample(USERS, k=min(len(reports), len(USERS)))
    now = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    bar = '─' * 64
    blocks = []
    for report, (user, service) in zip(reports, users):
        text = rng.choice(SYMPTOMS[report['id']]).format(device=report['device'])
        blocks.append(f'{bar}\n'
                      f' TICKET #{rng.randint(10000, 99999)}   {now}   Priorité : {PRIORITY.get(level, "Moyenne")}\n'
                      f' Demandeur : {user} ({service})\n'
                      f'{bar}\n'
                      f' « {text} »')
    footer = (f'{bar}\n'
              f' Fichier : {reports[0]["pkt_path"]}\n'
              + (f' {len(reports)} tickets ouverts sur le même réseau.\n' if len(reports) > 1 else '')
              + ' Dépannez dans Packet Tracer, sauvegardez (Ctrl+S), puis validez.\n'
              f'{bar}')
    return '\n'.join(blocks) + '\n' + footer


if __name__ == '__main__':
    demo = [{'id': 'router_interface_shutdown', 'device': 'R1', 'pkt_path': 'lab.pkt'},
            {'id': 'cable_missing', 'device': 'PC2', 'pkt_path': 'lab.pkt'}]
    print(make_ticket(demo, level=3, seed=3))
