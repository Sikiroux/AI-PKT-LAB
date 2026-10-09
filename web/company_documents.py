"""Documentation factuelle du parc représenté, sans observation ni secret."""

def public(state):
    company = str(state.get('company') or 'Entreprise')
    devices = state.get('devices') or {}
    def article(key, title, paragraphs):
        return {'id': 'company-' + key, 'title': title,
                'category': 'Entreprise · ' + company, 'paragraphs': paragraphs}
    resources = []
    for role, device in sorted(devices.items()):
        if not isinstance(device, dict):
            continue
        resources.append(f"{device.get('name') or role} · référence {role} · adresse configurée : {device.get('ip') or 'non renseignée'}")
    domain = (state.get('directory') or {}).get('domain') or {}
    dns_name = domain.get('dns_name') or 'non renseigné'
    documents_name = state.get('documents_dns_name') or 'non renseigné'
    docs = [
        article('resources', 'Ressources de ' + company, [
            'Ce répertoire couvre les appareils représentés dans cet environnement, pas tout le personnel ni tout le réseau d’une entreprise réelle.',
            *resources,
            'Les adresses sont celles du référentiel enregistré. Elles ne prouvent ni la connectivité actuelle, ni la disponibilité d’un service.']),
        article('naming', 'Identifier un appareil et son utilisateur', [
            'Le nom d’un poste identifie un équipement ; son utilisateur affecté peut changer sans renommer le poste.',
            'Pour une intervention, relever le nom et le numéro de série dans Fiches des postes. Vérifier l’utilisateur associé dans le parc ou l’annuaire.',
            'Les anciens environnements peuvent conserver leur préfixe de site. Les nouvelles conventions sont indépendantes du prénom de l’utilisateur.']),
        article('access', 'Repères pour les accès de ' + company, [
            'Domaine de l’annuaire représenté : ' + str(dns_name),
            'Nom documentaire du serveur de fichiers : ' + str(documents_name),
            'Consulter les partages dans l’application Partages pour connaître les ressources et droits administrés. Un ping réussi ne valide pas les droits d’accès aux fichiers.',
            'Les identifiants de formation se consultent dans les outils d’administration autorisés ; aucun mot de passe n’est publié dans ce répertoire.']),
        article('intervention', 'Préparer et documenter une intervention', [
            'Identifier l’entreprise, le demandeur et le poste du ticket avant de prendre la main. Ne pas confondre le portable du technicien avec le poste du demandeur.',
            'Relever le symptôme, le périmètre touché et le résultat des vérifications. Distinguer un contrôle inconnu d’un échec observé.',
            'Après une correction, retester l’action demandée sur le bon poste. Décrire l’intervention dans le ticket avant de demander sa vérification.',
            'Cette procédure est une consigne pédagogique du simulateur, pas une politique interne réelle inventée pour l’entreprise.'])]

    if state.get('staff'):
        import enterprise_staff
        users,known=enterprise_staff.service_users(state,'ftp')
        departments=sorted({p.get('department') for p in state['staff'] if p.get('department') and 'ftp' in p.get('service_dependencies',enterprise_staff.DEFAULT_DEPENDENCIES.get(p.get('department'),[]))})
        docs.append(article('dependencies','Activités et dépendances des services',[
            'Le dépôt FTP sert aux activités des services suivants : '+(', '.join(departments) or 'aucun service renseigné')+'.',
            str(len(users))+' poste(s) représenté(s) utilisent ce dépôt dans leur activité métier.',
            'Cette liste décrit le scénario de cette entreprise simulée. Elle ne constitue pas une règle générale pour toutes les entreprises.',
            'Une dépendance métier ne donne aucun droit technique. Les comptes et permissions FTP restent à vérifier séparément.',
            'L’impact du ticket est une estimation issue de ces dépendances, pas une vérification individuelle de tous les postes.']))
    return docs
