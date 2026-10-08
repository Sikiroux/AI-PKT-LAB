"""Formulations publiques reproductibles, sans accès aux causes privées."""
import hashlib
import random

CATALOGUE={
 'printing':(('Impression non retrouvée','Je ne retrouve pas le document que je voulais imprimer.'),('Document à imprimer en attente','Mon impression attendue n’est pas disponible. Peux-tu m’aider ?'),('Besoin d’aide pour imprimer','Je n’arrive pas à obtenir mon document sur l’imprimante du bureau.')),
 'ftp':(('Transfert documentaire à rétablir','Je n’arrive pas à terminer mon transfert avec le dépôt documentaire.'),('Besoin d’aide sur le dépôt FTP','Le transfert de mon document par FTP ne se passe pas comme prévu.'),('Document à transférer en attente','J’ai besoin d’aide pour échanger un fichier avec notre dépôt.')),
 'endpoint':(('Besoin d’assistance sur mon poste','Il me manque un accès ou une application pour travailler sur ce poste.'),('Application ou accès à rétablir','Peux-tu vérifier les outils de mon poste ? Je n’arrive pas à effectuer l’action attendue.'),('Outils du poste indisponibles','J’ai besoin d’aide pour retrouver un outil ou mon accès aux documents sur ce PC.')),
 'peripherals':(('Accessoire du bureau inutilisable','Un accessoire de mon poste ne fonctionne pas comme prévu.'),('Besoin d’aide sur l’équipement local','Je rencontre un problème avec un accessoire externe de mon PC.'),('Équipement du poste à vérifier','Peux-tu contrôler mes accessoires ? Je n’arrive pas à utiliser normalement le poste sur place.')),
 'ad':(('Accès utilisateur aux documents à rétablir','Je n’arrive pas à utiliser mes documents partagés avec mon compte.'),('Besoin d’aide pour accéder aux documents','Mon accès aux documents partagés ne fonctionne pas comme prévu.'),('Accès au dossier de travail perturbé','Peux-tu vérifier mon accès au dossier partagé de l’entreprise ?')),
 'files':(('Documents partagés indisponibles','Je n’arrive pas à utiliser le partage documentaire attendu.'),('Dossier partagé à vérifier','L’accès à mes documents partagés ne fonctionne pas comme prévu.'),('Besoin d’aide sur le partage de fichiers','J’ai besoin d’aide pour reprendre mon travail dans le dossier partagé.')),
 'dns':(('Adresse du partage introuvable','Je ne retrouve pas le service documentaire avec son nom habituel.'),('Accès documentaire par nom perturbé','L’adresse habituelle de mes documents ne me permet plus d’y accéder.'),('Nom du service documentaire à vérifier','Peux-tu m’aider à retrouver mes documents par leur adresse habituelle ?')),
 'deployment':(('Système de formation à préparer','Il faut préparer le système sur le disque d’atelier.'),('Déploiement d’atelier demandé','Peux-tu réaliser le déploiement prévu sur notre poste d’atelier ?'),('Préparer une installation de formation','J’ai besoin d’un système de formation installé dans l’atelier.')),
 'workstation_setup':(('Préparation du poste demandée','J’ai besoin des applications et documents prévus pour mon poste.'),('Poste utilisateur à préparer','Peux-tu préparer les outils demandés sur mon PC ?'),('Outils de travail à mettre en place','Il faut mettre en place les applications et documents demandés sur mon poste.')),
}
URGENCIES=(
 ('routine','Planifiée','faible','Cette demande peut être traitée dans le cadre des préparations habituelles.'),
 ('normal','Travail en attente','moderee','Mon travail sur cette tâche attend ton intervention.'),
 ('urgent','Besoin prioritaire','elevee','Cette tâche est prioritaire pour moi ; je demande un traitement rapide.'),
)

def compose(seed,family,requester,company,station,serial):
    """Le texte ne prétend jamais avoir mesuré une panne ou un impact collectif."""
    if family not in CATALOGUE:raise ValueError('Famille de formulation inconnue.')
    rng=random.Random(hashlib.sha256((str(seed)+':ticket-wording:v1').encode()).hexdigest())
    title,complaint=rng.choice(CATALOGUE[family])
    urgency,label,severity,reason=rng.choice(URGENCIES)
    context=dict(version=1,requester=requester,company=company,station=station,serial=serial,
                 complaint=complaint,reported_scope='one_user',urgency=urgency,urgency_label=label,priority_reason=reason)
    return dict(title=title,description=f'{requester} — {company}\nPoste : {station} ({serial}).\n« {complaint} »\n{reason}',severity=severity,request_context=context)
