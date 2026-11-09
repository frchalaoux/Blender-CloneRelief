# Qualification pour l’impression 3D

[English translation](PRINT_QUALIFICATION.en.md)

## Portée

La qualification porte sur un résultat précis, pour un modèle, une imprimante,
un matériau et un profil de trancheur identifiés. Elle ne certifie ni tous les
maillages ni toutes les configurations. Un rapport sans défaut détecté par
Clone Relief n’est pas une garantie d’imprimabilité.

La première qualification visée est le flux de travail appliqué à une copie du
scan Pika de la courge. Le fichier original doit rester intact. Le transfert de
relief, la comparaison avant/après et l’export STL de ce résultat ne sont pas
encore validés de bout en bout.

## Étapes et preuves requises

### 1. Résultat géométrique dans Blender

- Travailler sur une copie sauvegardée et identifier l’objet final dans
  l’Outliner.
- Comparer visuellement la cible avant et après, puis contrôler la continuité
  du raccord et la silhouette générale sous plusieurs angles.
- Exécuter l’audit M5 après la dernière modification. Noter ses compteurs et
  examiner les composantes restantes. Cet audit rapide de Clone Relief ne
  remplace pas une analyse de fabricabilité.
- Utiliser l’extension Blender officielle
  [3D Print Toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/)
  pour ses contrôles **Solid**, **Intersections**, **Degenerate**,
  **Thickness**, **Shells**, **Edge Sharp** et **Overhang**. Elle est annoncée
  compatible avec Blender 4.2 et versions ultérieures.
- Examiner les résultats signalés et choisir un seuil d’épaisseur compatible
  avec la buse, le matériau, le profil et l’usage prévu. Un contrôle logiciel
  n’établit pas à lui seul qu’une paroi est adaptée à la pièce réelle.
- Vérifier que le relief ajouté ne crée ni paroi mince ni cavité non souhaitée.

### 2. Export et trancheur

- Exporter uniquement l’objet final sélectionné, après avoir effacé les objets
  temporaires de comparaison.
- Importer le STL dans le trancheur choisi et vérifier ses dimensions en
  millimètres, son orientation, son nombre de coques et les alertes de
  réparation.
- Examiner l’aperçu couche par couche, en particulier le raccord, les détails
  transférés, les parois minces, les surplombs et les supports.
- Enregistrer le nom et la version du trancheur, le profil machine, le
  matériau, la hauteur de couche et les autres réglages pertinents.

Le STL ne contient pas d’unité explicite. Les dimensions affichées après
import sont donc un contrôle obligatoire, même si l’export Blender annonce une
conversion en millimètres.

### 3. Impression réelle

- Imprimer une pièce représentative avec la machine, le matériau et le profil
  enregistrés à l’étape précédente.
- Contrôler les dimensions, l’intégrité du raccord, la présence du relief et
  l’absence de défaut empêchant l’usage prévu.
- Consigner les écarts et défauts observés. Une modification du maillage, du
  matériau, de la machine ou du profil invalide cette preuve et demande une
  nouvelle vérification adaptée.

## État pour le scan Pika

| Contrôle | État |
| --- | --- |
| Une composante fermée, sans arête ouverte, filaire ou non-manifold détectée | Réalisé après suppression des deux composantes internes |
| 3D Print Toolbox : non-manifold / mauvaise continuité / coques | 0 / 0 / 1 lors du relevé du 7 novembre 2026 |
| 3D Print Toolbox : intersections et faces de surface quasi nulle | 349 faces signalées / 3 faces signalées; à examiner visuellement |
| 3D Print Toolbox : faces minces | 5 651 avec seuil de 1 mm; seuil à confronter au procédé et à l’usage |
| 3D Print Toolbox : non-planaires / arêtes vives / surplombs | 563 à 5° / 310 à 160° / 50 498 à 45° dans l’orientation courante; à examiner |
| Comparaison visuelle du transfert sur la courge | À faire |
| Vérification visuelle des intersections et surfaces internes | À faire |
| Contrôle de l’épaisseur adaptée au procédé et à l’usage | À faire |
| Export STL du seul objet final et vérification des dimensions importées | À faire |
| Aperçu des couches dans un trancheur identifié | À faire |
| Impression représentative et inspection du résultat | À faire |

Les validations manuelles doivent être consignées avec la date, les versions
de Blender et du trancheur, l’identifiant du fichier de travail, l’objet
exporté, la machine, le matériau et le profil. Ne pas publier le scan ni les
captures contenant des données privées sans vérifier leur autorisation.

Le 3D Print Toolbox aide à analyser et corriger le maillage dans Blender. Il ne
remplace pas l’import dans le trancheur, l’inspection de l’aperçu couche par
couche ni un essai d’impression.

Les nombres ci-dessus sont les résultats des contrôles de l’extension, pas des
défauts confirmés un par un. Le seuil de surplomb est relatif à l’orientation
courante de l’objet; les faces signalées doivent être examinées dans la vue 3D
et les réglages doivent correspondre au procédé visé.

L’utilisateur indique que certains groupes signalés ont été créés par
inadvertance pendant l’utilisation d’outils de sculpture. Deux groupes ont
maintenant été identifiés comme présentant une intersection visible, mais leur
origine sculpturale n’est pas établie. Ne pas traiter les 349 faces comme un
ensemble à supprimer.

Inspection des deux groupes montrés : le groupe de 45 faces et celui de 21
faces sont associés par 53 paires de faces qui se chevauchent dans le contrôle
BVH du Toolbox; 48 paires ne partagent aucun sommet topologique (5 en partagent
un, aucune n’en partage deux). Cela confirme un chevauchement géométrique entre
ces deux zones selon le contrôle, même si la ligne d’intersection est difficile
à voir dans la vue dense. Après isolement de leur voisinage, l’utilisateur
confirme qu’une intersection nette est visible. Cela valide visuellement ces
deux alertes, sans identifier à elle seule la correction à faire. Ne pas
supprimer ces faces directement; elles sont reliées au maillage principal.

Pour comparer à l’original, un extrait temporaire de 11 809 faces a été
affiché au même emplacement, d’abord au premier plan puis avec sa profondeur
réelle. L’utilisateur la voit derrière la copie depuis un premier angle, puis
devant après une rotation de 25°. Pour départager cette impression visuelle,
un contrôle BVH lecture seule a comparé toute la copie (303 981 faces) à
l’extrait original (11 809 faces) avec epsilon 1e-5 en coordonnées locales :
aucune paire de triangles ne se chevauche. Le changement apparent avant/arrière
est donc dépendant de la projection et ne signifie pas que ces deux surfaces
se croisent. Il ne remet pas en cause le chevauchement établi entre les groupes
orange eux-mêmes et ne suffit pas à déterminer quelle surface conserver.

La comparaison de ces deux groupes à l’original donne une distance médiane
centre de face → surface originale d’environ 8,32 mm pour chacun. Les faces
non signalées voisines dans leurs emprises sont à une distance médiane
d’environ 8,12 mm. L’écart indique que toute cette région est éloignée de
l’original; il ne permet pas d’attribuer la déformation aux seuls groupes
orange ni de décider quelle face retoucher.

Un contrôle comparatif en lecture seule avec l’original caché `BUTTERNUT_010`
(même matrice monde que la copie) renforce cette piste sans la prouver : la
distance des centres des 349 faces signalées au point le plus proche sur
l’original a une médiane de 2,84 mm et un 90e percentile de 8,32 mm. Sur un
échantillon régulier de 2 000 faces non signalées, ces valeurs sont 0 mm et
4,00 mm. La méthode compare des centres de faces à une surface de référence,
pas des sommets correspondants; les maillages ont aussi des résolutions
différentes. Elle sert à prioriser l’inspection, pas à décider seule d’une
suppression.

## Réparation du STL par Formware

Le 7 novembre 2026, l’utilisateur a soumis `BUTTERNUT_010.001.stl` à Formware
Online STL Repair. L’analyse avant réparation a rapporté 911 arêtes nues,
253 trous plans, 0 trou non-plan, 257 arêtes non-manifold, 446 normales
inversées, 436 faces dupliquées, 752 faces dégénérées et 0 coque disjointe.
La réparation s’est terminée. Les comptes rapportés sont passés de 157 729 à
163 899 sommets (+6 170) et de 315 452 à 332 822 triangles (+17 370).

Ces diagnostics concernent le STL soumis; le rapport transmis ne donne pas de
nouvelle analyse des défauts résiduels après réparation. La hausse du nombre de
triangles montre une reconstruction géométrique importante. Le STL réparé doit
être comparé à la copie Blender (silhouette, dimensions et détails), puis
réanalysé et vérifié dans le trancheur avant toute impression.

### Fichier réparé reçu et importé dans Blender

Le fichier fourni `Analyse Butternut M6 010.001.stl` est un STL binaire de
332 822 triangles. Son import temporaire dans Blender 4.5.8 à l’échelle 0,001
donne des dimensions de 103,851 × 238,163 × 111,197 mm, quasi identiques à
celles de `BUTTERNUT_010.001` (103,851 × 238,163 × 111,198 mm). Sur 5 000
sommets échantillonnés dans chaque sens, la distance au plus proche de l’autre
surface a une médiane de 0 mm, un P90 de 0,0038 mm et un maximum de 0,0087 mm.
Il s’agit d’une comparaison échantillonnée de surface, pas d’une correspondance
sommet à sommet; la géométrie externe semble donc pratiquement inchangée.

Le contrôle de l’objet importé dans Blender rapporte encore 363 arêtes liées à
une seule face, 1 496 arêtes liées à plus de deux faces et 3 382 faces d’aire
nulle. Une lecture directe des facettes du STL binaire trouve également 2 648
triangles d’aire exactement nulle. L’import Blender produit 330 614 triangles,
différents des 332 822 facettes du fichier; ces diagnostics sont donc consignés
comme résultats de l’import Blender, sans les confondre avec le décompte brut
Formware. Le STL réparé n’est pas encore qualifié : réanalyser le fichier dans
le trancheur visé et inspecter son aperçu couche par couche.

## Critère de conclusion

On pourra dire que le flux a été qualifié pour ce cas précis lorsque les trois
étapes ont été réalisées sans défaut bloquant et que leurs preuves sont
consignées. Cela ne permet pas d’affirmer que Clone Relief garantit à lui seul
qu’un autre maillage soit imprimable.
