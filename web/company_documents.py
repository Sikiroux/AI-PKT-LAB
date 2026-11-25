"""Documentation factuelle du parc représenté, sans observation ni secret."""

def public(state):
    company = str(state.get('company') or 'Entreprise')
    devices = state.get('devices') or {}
    def article(key, title, paragraphs):
        return {'id': 'company-' + key, 'title': title,
                'category': 'Entreprise · ' + {'resources':'Parc et serveurs','naming':'Parc et serveurs','access':'Accès','intervention':'Procédures','network':'Réseau','dependencies':'Services','policy-access':'Accès','policy-mail':'Messagerie','onboarding':'Procédures'}.get(key,'Général'), 'paragraphs': paragraphs}
    resources = []
    for role, device in sorted(devices.items()):
        if not isinstance(device, dict):
            continue
        resources.append(f"{device.get('name') or role} · référence {role} · adresse configurée : {device.get('ip') or 'non renseignée'}")
        if device.get('gateway') or device.get('mask') or device.get('vlan') is not None:
            mask=device.get('mask') or ('255.255.255.0' if state.get('staff_size')==30 and device.get('vlan') is not None else 'non renseigné')
            resources.append(f"Configuration de référence de {device.get('name') or role} · masque : {mask} · passerelle : {device.get('gateway') or 'non renseignée'} · VLAN : {device.get('vlan') if device.get('vlan') is not None else 'non renseigné'}")
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
            'Pour les sessions du domaine : Documentation → Identifiants et mots de passe de formation. Pour un compte local : Fiches des postes → sélectionner le poste → Accès locaux → Afficher le mot de passe local. Pour FTP : Documentation → Se connecter au dépôt FTP. Les comptes du domaine, locaux et FTP sont indépendants.']),
        article('intervention', 'Préparer et documenter une intervention', [
            'Identifier l’entreprise, le demandeur et le poste du ticket avant de prendre la main. Ne pas confondre le portable du technicien avec le poste du demandeur.',
            'Relever le symptôme, le périmètre touché et le résultat des vérifications. Distinguer un contrôle inconnu d’un échec observé.',
            'Après une correction, retester l’action demandée sur le bon poste. Décrire l’intervention dans le ticket avant de demander sa vérification.',
            'Cette procédure est une consigne pédagogique du simulateur, pas une politique interne réelle inventée pour l’entreprise.'])]

    if devices:
        infrastructure=[f"{d.get('name') or role} · adresse de référence : {d.get('ip') or 'non renseignée'}" for role,d in sorted(devices.items()) if isinstance(d,dict) and role not in ('client','technician') and not role.startswith('client')]
        docs.append(article('network','Réseau et serveurs de '+company,[
            'Ces repères décrivent le référentiel de cette entreprise. Ils ne constituent pas une observation de Packet Tracer ni un diagnostic du ticket.',
            *infrastructure,
            'Pour une panne d’accès, identifier le poste dans Fiches des postes puis relever sa configuration réelle dans Packet Tracer : Desktop → IP Configuration.',
            'Comparer IP, masque, passerelle et serveur DNS aux références disponibles. Une valeur non renseignée doit être recherchée dans la configuration du réseau ; ne pas la déduire arbitrairement.',
            'Tester un trajet à la fois : poste vers passerelle, puis vers le serveur, puis accès par nom. Noter la source, la cible et le résultat. Un ping réussi ne valide pas les droits applicatifs.',
            'Sur le switch relié au poste : enable, show vlan brief, show interfaces FastEthernet0/X switchport, puis show interfaces trunk pour la liaison entre switches. Remplacer X par le port réellement utilisé.',
            'Si plusieurs personnes sont touchées, chercher leur dépendance commune avant de modifier chaque poste. Consulter Services et événements pour les services simulés, puis retester l’usage demandé.']))

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
    if state.get('corporate'):
        p=state['corporate']['policy']
        docs.extend([
            article('policy-access','Politique des accès de '+company,[
                'Politique du scénario simulé : validation par '+p['approval']+'.',
                'Attribuer uniquement les groupes demandés pour la fonction. Une licence ne donne aucun droit aux dossiers partagés.',
                'Les comptes restent personnels ; le nom du matériel reste indépendant de son utilisateur.']),
            article('policy-mail','Convention de messagerie et licences',[
                'Domaine pédagogique interne : '+p['domain']+'. Aucun message ne sort du simulateur.',
                'Convention recommandée : '+p['naming']+' ; en cas d’homonyme, ajouter un numéro. Adresse lors de la création : identifiant AD en minuscules @ domaine. Renommer un compte ne renomme pas automatiquement sa boîte.',
                'Messagerie et Bureautique : attribuer une place du catalogue, sans dépasser sa capacité.',
                'Les contenus des boîtes sont conservés dans la sauvegarde locale. Politique de scénario : '+str(p['retention_days'])+' jours ; aucune purge automatique implémentée.']),
            article('onboarding','Procédure d’arrivée d’un employé',[
                'Préavis prévu : '+str(p['notice_days'])+' jours. Enregistrer le service, le responsable, la date et les groupes demandés dans Arrivées et services.',
                'Créer le compte dans Annuaire. Effectuer la première connexion et le changement de mot de passe demandé avant l’utilisation des services.',
                'Attribuer les licences, créer la boîte et envoyer le document d’accueil ; tester un échange depuis la boîte.',
                'Préparer le portable de réserve dans l’atelier du Parc, puis enregistrer sa remise à l’arrivant. Cette remise reste administrative et ne crée pas un appareil Packet Tracer.',
                'Le centre de tickets relit les moteurs pour vérifier la demande. Un groupe AD ne prouve pas les droits SMB ; la connexion du nouveau poste reste hors de ce scénario.'])])
    return docs
