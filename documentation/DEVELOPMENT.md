# Développement

[English translation](DEVELOPMENT.en.md)

## Environnement de référence

- Blender **4.5.8 LTS** sur macOS Intel.
- Python embarqué dans Blender sur le poste de référence : **3.11.11**.
- Les modules `src/clone_relief/geometry.py` et `relief.py` n’importent pas
  `bpy` et n’ont pas de dépendance externe à l’exécution.
- Les tests pytest sont prévus pour Python 3.11, séparément du Python embarqué
  dans Blender. Ne pas supposer que les deux exécutables sont le même.

## Installer et lancer les tests

Depuis la racine du projet avec Python 3.11 :

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q
```

## Architecture actuelle

- `geometry.py` contient les structures `MeshPatch` et `TangentFrame`, les
  normales, le repère local, le graphe du patch et le masque de fondu.
- `relief.py` extrait le profil complet de la source par rapport à son plan
  moyen, construit un BVH 2D pour l’interpolation barycentrique, puis calcule
  les coordonnées résultantes sans modifier les entrées. Le mode par défaut
  translate le profil entier vers l’extérieur pour que son minimum arrive sur
  la cible; les creux sont conservés et ne passent pas sous celle-ci. À
  intensité 1, gain 1 et échelle 1, le profil intérieur est copié sans changer
  son amplitude. Le mode bidirectionnel conserve le profil signé.
- `density.py` compare les médianes d’arêtes source/cible et estime une borne
  haute du nombre de faces après subdivision locale, sans dépendance à Blender.
- `blender_adapter.py` capture une sélection BMesh connectée, la compacte en
  données neutres avec les coordonnées initiales et valide la topologie au
  moyen d’une empreinte du maillage.
- `operators.py` expose capture, aperçu chiffré sans mutation, Apply, diagnostic
  de résolution et subdivision locale confirmée en Edit Mode. M5 ajoute un
  rapport topologique en lecture seule, une comparaison temporaire de la cible
  capturée avant/après, un export STL limité à l’objet actif, des commandes
  pour rétablir les captures source/cible et un localisateur de composantes
  déconnectées qui cadre la vue; `ui.py` relie ces actions au panneau N. Chaque
  aperçu et Apply repart des coordonnées de la
  cible capturées; répéter Apply remplace donc le résultat précédent au lieu
  de l’empiler. Le panneau règle aussi l’opacité du remplissage de sélection
  orange; cette couleur de thème est restaurée à la désactivation. Le gain
  d’amplitude est distinct de l’intensité 0–1.
- `tests/` vérifie les cas géométriques synthétiques sans Blender.
- `scripts/blender_smoke_test.py` vérifie le parcours Blender avec un objet
  synthétique sans toucher au scan.
- L’aperçu ne dessine pas de surimpression dans la vue 3D : il calcule le nombre
  de sommets qui bougeraient et le déplacement maximal, sans modifier le mesh.

## Diagnostic et densification locale (M3)

- Capturer une source et une cible distinctes sur le même maillage avant le
  diagnostic ou la subdivision.
- La résolution cible est comparée à la médiane des longueurs d’arêtes source.
  Le 90e percentile des arêtes cible déclenche une alerte au-delà de `1,5×`;
  le nombre de coupes recommandé ramène ce percentile à la taille médiane
  source. Ce seuil est un indicateur initial, pas une garantie de fidélité.
- `clone_relief.diagnose_resolution` ne modifie rien. La commande
  `clone_relief.subdivide_target` ouvre une boîte de confirmation indiquant la
  résolution, le nombre de coupes et une borne haute prudente du nombre de
  faces. La limite initiale est de 250 000 faces ajoutées et les coupes sont
  bornées à 8; l’utilisateur peut ajuster la limite dans la boîte.
- La subdivision reprend les arêtes de toutes les faces cible et utilise le
  remplissage en grille de BMesh. Elle conserve les coordonnées des bords,
  tandis que les faces adjacentes partageant un bord cible peuvent être
  subdivisées pour garder le maillage connecté. Les captures sont invalidées
  après le changement topologique; il faut recapturer source et cible.
- Le plafond de coût est une borne estimée, particulièrement prudente pour les
  polygones de plus de trois côtés. La commande n’est pas évaluée sur des scans
  volumineux ni sur le scan Pika.

Le BVH est construit une fois par application, puis réutilisé pour les
échantillons de la cible. Le fondu utilise des distances Dijkstra sur les
arêtes du patch. La largeur de fondu est une fraction de `sqrt(surface_area)`.
Le paramètre d’échelle multiplie la taille physique du motif : `2.0` double sa
longueur d’onde.

## Limites connues

- Le repère initial suit les axes du monde et n’a pas encore de rotation
  réglable.
- Aucun relief n’est extrapolé hors de la couverture 2D de la source.
- Les détails transférés sont un motif plausible, pas les détails originaux
  absents du scan.
- Les mesures préliminaires du scan Pika précèdent le passage à la copie du
  profil complet; elles ne caractérisent pas encore le résultat de
  l’algorithme actuel et devront être refaites lors de la validation sur copie.
- Les zones très courbes ou distordues peuvent mal se projeter dans un repère
  tangent unique.
- Une cible sous-échantillonnée ne peut pas représenter finement le motif; la
  densification locale M3 existe, mais n’a pas encore été éprouvée sur un grand
  scan réel.
- Le noyau n’a pas encore été validé sur la courge scannée ni qualifié pour
  l’impression 3D.
- Le contrôle topologique M5 et le localisateur de composantes ont été utilisés
  sur le scan Pika; après suppression de deux composantes internes, l’audit a
  confirmé un seul groupe sans défaut topologique détecté. La comparaison
  avant/après et l’export STL, notamment ses dimensions dans un trancheur,
  restent à valider. Le contrôle n’analyse ni les auto-intersections ni les
  surfaces internes.
- M6 réutilise le 3D Print Toolbox pour l’analyse géométrique de fabricabilité
  plutôt que de réimplémenter ses contrôles. Clone Relief garde son résumé
  topologique et son localisateur de composantes. Le protocole de qualification
  d’un cas concret (scan Pika, trancheur et impression) est dans
  [Qualification pour l’impression](PRINT_QUALIFICATION.md); ces validations
  restent à effectuer.

## Smoke test Blender

Avec Blender 4.5.8 installé dans `/Applications/Blender.app` :

```bash
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python scripts/blender_smoke_test.py
```

Le script vérifie la capture source/cible, l’invalidation d’une capture après
changement topologique, le déplacement limité à la cible et le retour exact des
coordonnées avec Undo. Il vérifie aussi le diagnostic, le refus d’un coût
au-dessus du plafond, une subdivision triangulée locale raccordée, la
conservation des bords et de la source, puis Undo exact de la topologie. Les
captures résident en mémoire pour la session Blender; elles sont invalidées
quand l’empreinte de topologie change. Cette
empreinte parcourt tout le maillage à chaque capture/apply, ce qui peut coûter
du temps sur des scans de plusieurs millions de faces.

La capture cible conserve sa géométrie de départ tant que l’utilisateur ne
recapture pas une autre zone ou ne change pas la topologie. Le smoke test vérifie
actuellement que le panneau conserve le statut de cette capture après Apply;
les scénarios de réapplication avec plusieurs réglages restent à valider dans
Blender.
