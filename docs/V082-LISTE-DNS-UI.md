# v0.82 — Liste des enregistrements DNS

La console technicien ajoute un filtre A/AAAA/CNAME, un compteur affichés/total et un tri naturel par nom puis type. La recherche porte sur nom, type et cible ; elle ignore la casse et les espaces de bord. Recherche et filtre sont conservés lors de l’actualisation et du changement de section, tant que la console reste ouverte.

La sélection utilise le même bouton DOM, pour préserver le double-clic. Une entrée masquée par les filtres n’est plus sélectionnée ; le bouton Propriétés est désactivé sans sélection visible. La recherche préserve les en-têtes sémantiques du tableau. Les messages distinguent une zone vide d’une recherche sans résultat.

Les filtres ne provoquent aucune résolution DNS ni modification. Aucune route, permission ou règle du moteur DNS n’est modifiée. Les fenêtres de propriétés et de création restent celles de la version précédente ; elles ne sont pas annoncées comme refondues.

## Validation

Test dédié : filtres locaux sans requête, sélection stable, sélection masquée retirée, conservation après actualisation, en-têtes et zone vide. Les 42 suites JavaScript passent pour cette version. Le test de console existant est adapté au nouveau libellé de résultat vide.

Le cœur et les ateliers Python ne changent pas : derniers résultats 19/19 et 8/8 en v0.79, non relancés pour cette passe UI. Les tests web Python ne sont pas relancés. Aucun rendu navigateur graphique vérifié ici.

## Recette Chrome

Depuis le bureau technicien, ouvrir DNS puis Enregistrements. Sélectionner une entrée, filtrer pour la masquer : Propriétés doit se désactiver. Actualiser et changer de section : recherche et filtre restent présents. Vérifier la lisibilité dans une fenêtre étroite et le double-clic sur une entrée visible. Les fenêtres de propriétés, la configuration client et la présentation du résultat de résolution restent à améliorer dans de prochaines passes.
