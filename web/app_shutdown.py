"""Arrêt explicite : enregistrer avant de demander la fermeture du serveur."""
def prepare_shutdown(workspace, tickets, stop_event):
    with workspace.lock, tickets.metadata_lock:
        if workspace.workspace.state:workspace.workspace.save()
        tickets.save()
        stop_event.set()
    return {'stopping':True,'message':'Données enregistrées. Le logiciel est arrêté ; tu peux fermer cet onglet.'}
