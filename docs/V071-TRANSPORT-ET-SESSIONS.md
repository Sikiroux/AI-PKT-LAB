# v0.71 — Transport technicien et sessions utilisateur séparés

## Défaut corrigé

`technician_model.invalidate` effaçait l'authentification AD du client et fermait sa session distante lors d'un déplacement du portable technicien. La déconnexion VPN faisait de même. Le déplacement du technicien n'est pourtant pas une déconnexion Windows de l'employé. De plus, seules les observations du poste principal étaient effacées : les autres projections conservaient leurs anciennes preuves.

## Comportement

Déplacement et déconnexion VPN invalident les observations réseau et la validation pédagogique du poste principal et de tous les bureaux clients. Le VPN est déconnecté. Les authentifications utilisateur et les sessions distantes ouvertes sont conservées. Les gardes d'accès existantes suspendent les actions en attendant un raccordement, un VPN si nécessaire et de nouvelles preuves réseau valides. Après rétablissement, aucune nouvelle connexion Windows n'est requise uniquement à cause du changement de transport.

Aucun nouveau ping, aucune accélération automatique, aucun allongement de validité. Une déconnexion utilisateur explicite, un changement d'identité ou le redémarrage du logiciel gardent leurs règles existantes. Les anciennes observations conservées dans l'historique ne sont pas des preuves actuelles.

## Recette à effectuer dans Windows / PT9

- Connecter un employé sur un bureau distant, ouvrir une application et noter son poste/compte.
- Déplacer le portable technicien : les actions réseau doivent être suspendues et les fenêtres conservées. Confirmer le nouveau raccordement, puis lancer le contrôle prévu. Le compte employé doit rester connecté.
- En télétravail, déconnecter le VPN : vérifier le refus d'accès réseau et la conservation du compte. Reconnecter le VPN et renouveler les preuves ; reprendre sans nouvelle saisie du mot de passe employé.
- Refaire avec un second bureau client ouvert : aucune preuve de l'ancien trajet ne doit autoriser l'accès.
- Vérifier qu'une vraie déconnexion utilisateur reste une déconnexion, et qu'un compte désactivé ne récupère pas une authentification par ce correctif.

## Validation et limites

Quatre nouveaux tests couvrent conservation des authentifications, invalidation de toutes les projections, reprise après preuve et compatibilité sans annuaire. Suite web complète relancée. Générateur, ateliers et JavaScript inchangés depuis leur recette v0.70 (19/19, 8/8, 37 suites).

Recette réelle PT9 toujours nécessaire. Le bloc stabilité/cohérence reste ouvert : ce correctif ne résout ni tous les délais du pont, ni la modélisation des signalements d'entreprise.
