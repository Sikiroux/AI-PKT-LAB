"""Catalogue local des environnements : aucun déplacement des anciennes sauvegardes."""
import json
import re
import uuid
from pathlib import Path
from workspace_model import Workspace

class EnvironmentStore:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.index = self.folder / 'environments.json'
        self.data = json.loads(self.index.read_text(encoding='utf-8')) if self.index.exists() else {'active': None, 'items': {}}
        legacy = self.folder / 'session.json'
        if not self.data['items'] and legacy.exists():
            self.data = {'active': 'legacy', 'items': {'legacy': {'path': 'session.json'}}}
            self.save()

    def save(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        temp = self.index.with_suffix('.tmp')
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(self.index)

    def path(self, ident):
        if not isinstance(ident, str) or not re.fullmatch(r'legacy|[a-f0-9]{32}', ident) or ident not in self.data['items']:
            raise ValueError('Environnement inconnu.')
        return self.folder / self.data['items'][ident]['path']

    def allocate(self):
        ident = uuid.uuid4().hex
        return ident, self.folder / 'environments' / ident / 'session.json'

    def register(self, ident, path):
        self.data['items'][ident] = {'path': str(path.relative_to(self.folder))}
        self.activate(ident)

    def activate(self, ident):
        self.path(ident)
        self.data['active'] = ident
        self.save()

    def public(self):
        items = []
        for ident in self.data['items']:
            path = self.path(ident)
            s = json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
            if s:
                items.append(dict(id=ident, company=s['company'], seed=s['seed'], network_file=s.get('network_file'), active=ident == self.data['active']))
        return dict(active=self.data['active'], items=items)
