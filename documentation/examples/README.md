# Exemple avant/après

![Profil source, cible avant transfert et cible après transfert](clone_relief_before_after.png)

Cette démonstration synthétique compare le profil source échantillonné, la cible
plane avant transfert et le résultat après transfert.
Elle utilise les opérateurs Clone Relief dans Blender 4.5.8 : **Intensity 1,0**,
**Relief Gain 1×**, **Pattern Scale 1,0**, **Edge Falloff 0,10** et le mode
unidirectionnel par défaut. La source est un motif sinusoïdal régulier et la
cible comporte 20 736 faces sur une tuile de 30 mm; la source a 5 184 faces.
Le profil est copié à gain 1×, avec un fondu de bord. Ce rendu ne prédit pas le
résultat sur un scan réel.

- [Image PNG](clone_relief_before_after.png)
- [Scène Blender modifiable](clone_relief_before_after.blend)
- Script de génération : [`scripts/create_before_after_example.py`](../../scripts/create_before_after_example.py)

## Essayer les captures dans Blender

La scène s’ouvre sur un maillage de test actif en **Edit Mode**, en sélection de
faces. Ses réglages sont déjà **Intensity 1,0**, **Relief Gain 1×**,
**Pattern Scale 1,0**, **Edge Falloff 0,10** et le mode unidirectionnel.
L’opacité de sélection est réglée à **8 %**.
La source striée est à gauche
(ambre) et la cible plane à droite (vert).
Ces deux zones sont deux îlots du même objet.

1. Place le pointeur sur la source à gauche et appuie sur **L** pour sélectionner
   son îlot connecté. Clique **Capture Source** dans le panneau Clone Relief.
2. Désélectionne avec **Option+A**, place le pointeur sur la cible à droite et
   appuie sur **L**. Clique **Capture Target**.
3. Règle **Intensity** à `1,0`, **Relief Gain** à `1` et **Edge Falloff** à
   `0,10`, puis clique **Preview Effect** et **Apply Relief**.

Après **Capture Target**, tu peux changer les réglages, refaire l’aperçu et
appliquer plusieurs fois. Chaque application repart de la géométrie initiale
capturée et remplace le résultat précédent. Capture une nouvelle cible
uniquement pour changer de zone ou après une modification de topologie.
Le réglage **Opacité sélection** dans le panneau réduit le remplissage orange
des faces sélectionnées dans la vue 3D.

**Apply Relief** modifie la cible du maillage `TEST` sur place. L’objet
`After - transferred relief` est une pièce de présentation générée par le
script, et ne suit pas les applications faites ensuite dans `TEST`. Pour
comparer les pièces de présentation dans la vue 3D, masquer `TEST` et afficher
`Before - smooth target` et `After - transferred relief`; pour manipuler le
maillage de test, faire l’inverse.

Le mode unidirectionnel copie le profil source sans écrêter ses creux, puis le
décale pour que les sommets de la cible ne passent pas sous sa surface. À
intensité 100 % et gain 1×, le profil intérieur est identique à la source à une
translation constante près. Le mode bidirectionnel reste disponible pour
conserver creux et bosses signés. Le fondu à 10 % adoucit seulement la bordure.

La scène de comparaison rendue reste disponible avec **F12**. Le maillage de
test est exclu du rendu pour qu’il ne recouvre pas les trois panneaux.

Pour régénérer la scène et l’image depuis la racine du dépôt :

```bash
"/Applications/Blender.app/Contents/MacOS/Blender" \
  --background --factory-startup \
  --python scripts/create_before_after_example.py
```
