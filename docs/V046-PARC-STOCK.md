# v0.46 — Parc représenté et premier cycle de stock

## Où l’ouvrir

Dans le bureau du technicien, ouvrir l’icône **Parc et stock**. La fenêtre présente les appareils du référentiel Packet Tracer et le matériel de réserve administratif. Elle n’ouvre pas un autre fichier réseau.

Le portable de réserve possède un numéro de série déterminé par la seed (`:stock:v1`). Il ne représente pas un second portable du technicien. Une entreprise reprise conserve son stock et son historique ; la seed ne réinitialise pas les remises enregistrées.

## Parcours

1. Lire le parc réseau et ses affectations existantes.
2. Vérifier la préparation du matériel de réserve, puis **Confirmer la préparation vérifiée**.
3. Choisir un employé représenté de cette entreprise et **Enregistrer la remise**.
4. Lors du retour, **Enregistrer la restitution**. Le matériel redevient disponible mais sa préparation doit être vérifiée avant une nouvelle remise.

Ces actions sont administratives : la déclaration de préparation n’installe pas Windows et ne valide pas l’atelier Déploiement. La remise n’ajoute pas un appareil Packet Tracer, ne change pas l’accès distant, ne remplace pas le poste existant de l’employé et n’accorde pas de permissions. Les relations de remise sont stockées par identifiant d’employé, jamais par prénom.

## Données et API

`session.json` contient désormais `inventory`, avec la portée d’environnement, une révision, les articles et leur historique. Ajout compatible : les anciens fichiers reçoivent une réserve au premier enregistrement ; aucun article ancien n’est supprimé. Les observations réseau ne sont pas utilisées pour prouver une remise matérielle.

- `/workspace/inventory/state` : vue du stock et du référentiel commun.
- `/workspace/inventory/operation` : `prepare`, `assign`, `return` ; `item_id` et `expected_revision` requis, `employee_id` requis pour la remise.
- Les routes exigent l’environnement actif et refusent les actions de stock dans le contexte d’un bureau client.
- Le verrou du contrôleur sérialise les opérations. La copie de travail n’est publiée qu’après validation. Une erreur conserve l’article, la révision et l’historique. L’enregistrement suit le mécanisme de sauvegarde existant.

## Limites de cette livraison

Première réserve : un portable. Pas encore d’achat, de livraison, de retrait de stock, d’extension du catalogue, de remplacement de poste connecté ou de lien automatique avec une installation réussie. La création d’un nouvel appareil réseau demande encore une opération explicite dans Packet Tracer. Le personnel non représenté n’est pas encore sélectionnable.

La préparation visuelle existante reste dans l’application Déploiement ; son association à un article précis reste à implémenter. Ces limites évitent de confondre une action de gestion avec une installation réelle.

## Validation

Tests de cycle complet, identité et seed stables, sauvegarde/reprise, refus avant préparation, employé inconnu, révision périmée et consultation sans mutation. Test DOM : sélection de l’employé, révision envoyée, erreur conservant la remise et restitution imposant une nouvelle préparation. Les tests n’attestent ni le rendu visuel natif ni une intervention réelle sur le matériel.
