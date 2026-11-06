# HANDOFF — Blender Clone Relief

- **Projet :** `Blender-CloneRelief`
- **Date :** 6 novembre 2026
- **État :** M0–M4 sont implémentés et testés sur géométrie synthétique; validation sur scan à venir
- **Cible :** Blender **4.5.8** sur **macOS Intel**, utilisation avec **trackpad, sans pavé numérique**
- **Destination :** VSCode + Codex

---

## 1. Objectif et motivation

Créer un outil Python pour Blender appelé **Clone Relief**, capable de **prélever le microrelief géométrique d'une zone saine d'un scan 3D et de le reproduire sur une zone cible sélectionnée**, tout en conservant la courbure générale de cette dernière et en atténuant progressivement l'effet aux frontières.

Le besoin est issu d'un scan de **courge butternut** réalisé avec un **scanner Pika**, traité par **CrealityScan**, puis importé dans Blender. Une région insuffisamment capturée a été automatiquement remplie par CrealityScan au moyen de **grands triangles**, qui donnent une surface artificiellement lisse/plate. Le reste du maillage comporte de nombreux détails organiques à reproduire.

**Priorité :** obtenir de **véritables détails géométriques exportables en STL/3MF** pour l'impression 3D sur une **Bambu Lab P2S**, et non simplement un rendu visuel de type bump/normal map.

**Principe :** modifier les sommets de la zone cible existante, **sans découper un patch pour le souder**, sans superposer de parois, et sans refaire tout le maillage.

## 2. Contexte de la session Blender

### 2.1 Observations établies

- Le scan original de la courge présente plusieurs millions de triangles dans les parties denses.
- La zone reconstruite automatiquement par CrealityScan comporte des triangles beaucoup plus grands et une faible quantité de détail.
- Le pinceau **Grab** fonctionne correctement sur une zone saine du maillage : les opérations de sculpture ne sont pas globalement bloquées.
- **Smooth**, **Inflate/Deflate** et des essais de **Dyntopo** n'ont pas donné un résultat satisfaisant pour reproduire le relief naturel de la courge.
- Paramètres Dyntopo utilisés lors des essais : `Detail Size = 12 px`, `Refine Method = Subdivide Edges`, `Detailing = Relative Detail`.
- Une expérimentation manuelle a consisté à dupliquer des faces saines, séparer le résultat en objet, déplacer/pivoter le patch, puis utiliser **Join** (`Ctrl + J`). Cette dernière opération **réunit les objets sans souder les surfaces**. La méthode par remplacement de faces et raccordement de contours a été jugée insatisfaisante et **est abandonnée comme workflow principal**.
- La **densité de géométrie insuffisante** dans la zone cible reste un enjeu technique à traiter localement.

### 2.2 Conséquences

- Ne pas présenter `Ctrl + J` comme une fusion topologique.
- Ne pas utiliser de *Boolean Union*, *Bridge Edge Loops* ou *Voxel Remesh* global comme mécanisme par défaut.
- Ne pas promettre une reconstruction exacte des détails perdus : l'outil **transfère un motif caractéristique** d'une zone saine, et non les données originales du scan manquant.
- Ne pas confondre **reconstruction de la forme globale** et **transfert des détails haute fréquence**. Les creux/bosses majeurs devront au besoin être corrigés séparément.

## 3. Résultat utilisateur attendu

Dans Blender :

1. Sélectionner un maillage source (la courge de travail).
2. En **Edit Mode**, sélectionner un ensemble de faces saines puis cliquer **Capture Source**.
3. Sélectionner un autre ensemble de faces à traiter, idéalement sur le **même maillage**, puis cliquer **Capture Target**.
4. Régler l'intensité, l'échelle et le fondu de bord.
5. Exécuter **Preview / Apply** pour obtenir un relief géométrique visible, proche de celui de la zone source, mais adapté à la forme locale de la cible.
6. Pouvoir annuler proprement, recommencer et exporter le résultat sans surfaces internes créées par l'outil.

L'interface finale devrait être un panneau **Clone Relief** dans la barre latérale (`N`) de la vue 3D, avec messages d'erreur explicites. **Le premier prototype peut fonctionner sans interface complexe**, via des opérateurs et des propriétés Python.

### 3.1 Valeurs initiales validées

| Réglage | Par défaut | Sens |
|---|---:|---|
| Intensité | **60 %** (`0.60`) | Amplitude relative des déplacements de relief |
| Échelle du motif | **100 %** (`1.00`) | Agrandissement/réduction du motif source |
| Raccord progressif | **25 %** (`0.25`) | Fraction de largeur de la sélection cible servant au fondu |

Prévoir des limites raisonnables et documentées, et éventuellement un réglage supplémentaire **amplitude maximale en unités de scène** pour éviter des déformations excessives.

## 4. Exigences fonctionnelles

**F1 — Capture source.** Mémoriser un ensemble connecté de faces source et la géométrie nécessaire au calcul du relief. Le mécanisme de capture doit rester fiable lorsque l'utilisateur change de sélection; définir clairement si une édition topologique invalide la capture.

**F2 — Capture cible.** Mémoriser une autre sélection de faces sur le même objet dans la V1; refuser ou gérer explicitement tout chevauchement source/cible.

**F3 — Décomposition forme/détails.** Estimer une **surface de référence lissée** sur la source et calculer le **résidu normal** des sommets source par rapport à cette référence. Ce résidu constitue le relief transférable; ne pas transférer la silhouette ou la pente générale de la zone source.

**F4 — Correspondance locale.** Définir une paramétrisation 2D locale (plan tangent ou espace intrinsèque approximatif) de la source et de la cible et un échantillonnage de la carte de relief. Documenter les limites pour les zones très courbes, distordues ou de topologie non disque.

**F5 — Modification cible.** Déplacer les sommets cibles **dans la direction de leurs normales locales** suivant le relief échantillonné, avec facteur d'intensité et fondu de bord. Préserver au maximum la forme générale et la géométrie située hors de la sélection.

**F6 — Fondu.** Construire un masque où le poids vaut zéro sur le bord de la sélection et croît progressivement vers l'intérieur. Préférer une distance **sur le maillage** (approximation géodésique) à une distance euclidienne brute lorsqu'il existe des plis ou replis. Utiliser un profil lisse, par exemple `smoothstep`.

**F7 — Densification locale.** Prévoir une commande explicite et optionnelle pour subdiviser les grands triangles de la cible si l'échantillonnage serait sous-résolu; **ne jamais subdiviser le scan entier par défaut**. Proposer une estimation du nombre de faces final et un plafond de sécurité.

**F8 — Sécurité.** Aucun changement hors sélection, sauf aux bords dans le cadre d'une opération explicitement consentie. Compatible Undo. Ne pas effacer les attributs/UV existants. Prévoir sauvegarde/copie du maillage avant l'opération.

**F9 — Diagnostics.** Fournir des indicateurs utiles : nombre de faces source/cible, densité et taille moyenne des arêtes, amplitude des déplacements, nombre de sommets déplacés, alertes sur les normales, les sélections disjointes et les faces dégénérées.

**F10 — Impression 3D.** La fonction n'est **pas** responsable de réparer toute la topologie du scan, mais ne doit pas introduire de surfaces ouvertes, doubles parois, ou intersections manifestes. Prévoir une étape de contrôle de manifoldness après application.

## 5. Architecture conseillée

```text
Blender-CloneRelief/
├── README.md
├── documentation/
│   ├── HANDOFF.md
│   ├── SPECIFICATIONS.md
│   └── DEVELOPMENT.md
├── pyproject.toml
├── src/
│   └── clone_relief/
│       ├── __init__.py         # entrée de l'add-on / register / unregister
│       ├── relief.py           # extraction, filtres et échantillonnage du relief (sans bpy)
│       ├── geometry.py         # géométrie pure, graphes, masques et interpolation (sans bpy)
│       ├── blender_adapter.py  # conversion BMesh / Mesh vers structures neutres
│       ├── operators.py        # capture source/cible, preview, apply
│       └── ui.py               # panneau N et réglages
├── tests/
│   ├── test_relief.py
│   ├── test_geometry.py
│   ├── test_falloff.py
│   └── test_regressions.py
├── scripts/
│   └── blender_smoke_test.py   # test d'intégration à lancer dans Blender
└── examples/
    └── README.md              # jeu de test synthétique, sans scan privé
```

Les modules `relief.py` et `geometry.py` doivent rester **testables avec pytest sans importer `bpy`**. Toute dépendance à Blender se trouve dans l'adaptateur, les opérateurs et l'UI.

**Python :** toutes les fonctions, variables publiques et structures de données doivent recevoir des **annotations de types**. Utiliser `dataclasses`/`typing` lorsque pertinent. Respecter le Python effectivement livré avec Blender 4.5.8; **ne pas supposer que le Python Homebrew du Mac est celui de Blender**.

## 6. Algorithme V1 proposé (à prototyper et évaluer)

### Étape A — Construire les données locales

- Extraire sommets, faces, normales, adjacences et masques de sélection, sans convertir inutilement tout le scan en structures Python volumineuses.
- Sur la source, calculer un repère tangent cohérent et des coordonnées 2D de travail.
- Construire une surface lissée **de référence**, sans altérer directement le maillage source. Une solution initiale est un lissage laplacien/taubin contrôlé sur une **copie des coordonnées**, avec traitement spécifique des bords. Comparer ensuite avec un ajustement local de surface, si nécessaire.
- Calculer un signal de relief signé, approximativement `h_i = dot(p_i - p_reference_i, n_reference_i)`.
- Retirer la moyenne et, si utile, une tendance basse fréquence pour ne pas transporter les déformations globales.

### Étape B — Échantillonner sur la cible

- Définir un repère local et une projection 2D sur la cible.
- Adapter la texture géométrique à la **taille physique en unités Blender**, pas au nombre de pixels de l'écran.
- Prévoir une orientation initiale stable et un paramètre de rotation du motif si les essais le demandent.
- Interpoler les hauteurs (barycentrique ou autre méthode correctement testée); gérer les échantillons hors de la zone source sans extrapolation incontrôlée.

### Étape C — Appliquer le relief

Pour chaque sommet cible `i` :

```text
p_new[i] = p_original[i]
         + normal[i] * intensity * falloff[i] * sampled_height[i]
```

Le `falloff` varie entre 0 et 1. Il vaut 0 à la frontière et atteint 1 dans l'intérieur, sur une distance dépendant de la largeur de raccord (25 % par défaut). On peut l'obtenir à partir des distances sur le graphe des arêtes jusqu'au bord de la sélection, normalisées par une largeur caractéristique.

**Important :** l'amplitude des hauteurs doit être calibrée en unités de scène. Une valeur de 60 % signifie **0,6 fois l'amplitude extraite**, et non 60 % du diamètre de la courge.

### Étape D — Prévisualisation et application

- Pour une V1 : **Apply** en une opération Undo, avec possibilité de restaurer par Undo / copie de l'objet.
- Pour la V2 : aperçu non destructif, par exemple copie temporaire ou restitution contrôlée des coordonnées d'origine; **ne pas promettre une prévisualisation temps réel sur plusieurs millions de triangles dès la V1**.
- Mesurer le coût de calcul et signaler la densification potentiellement explosive.

### Limites connues de cette approche

- Un motif appliqué sur une zone étendue ou très incurvée pourra se déformer ou s'étirer.
- Si la cible n'a pas suffisamment de sommets, le relief ne sera pas visible malgré un transfert correct : prévoir subdivision **locale** préalable.
- Les détails transférés sont plausibles mais **non fidèles aux détails réels perdus**.
- Le transfert du microrelief ne restaure pas la courbure macroscopique si celle-ci est fausse.
- Les plis, frontières non simples, trous, normales inversées et surfaces qui s'intersectent nécessitent des contrôles spécifiques.

## 7. Exigences de performance

- Le maillage global du scan peut comporter **plusieurs millions de triangles**.
- Travailler sur les seuls sommets/faces des sélections quand c'est possible.
- Éviter de dupliquer plusieurs fois le maillage complet en mémoire.
- Ne pas faire d'opération `O(N_source × N_target)` sans structure spatiale ni borne explicite.
- Prévoir des tests de charge synthétiques progressifs et une option d'annulation utilisateur si Blender le permet.
- Sur le Mac Intel utilisé, mesurer la consommation mémoire et la latence avant de choisir un niveau maximal de densification.

## 8. Tests et critères d'acceptation

### 8.1 Tests unitaires pytest (obligatoires)

1. **Surface plane source sans relief :** hauteur extraite proche de zéro; cible inchangée.
2. **Relief synthétique sinusoïdal :** restitution de fréquence et amplitude dans une tolérance définie.
3. **Intensité :** à `0 %`, aucun déplacement; à `60 %`, déplacements égaux à 0,6 fois ceux obtenus à `100 %` (hors plafonnement).
4. **Échelle :** `100 %` préserve la taille caractéristique des motifs; les autres facteurs modifient la fréquence spatiale conformément à la convention documentée.
5. **Fondu :** poids nul sur les sommets du bord, progressif à l'intérieur, sans discontinuité manifeste.
6. **Sélection :** les sommets hors cible restent bit-à-bit inchangés, lorsque l'opération n'inclut pas de densification.
7. **Cas limites :** sélection vide, une face, éléments disjoints, triangles dégénérés, normales incohérentes, source sans variance, cible sous-échantillonnée.
8. **Non-régression :** les fonctions de calcul ne modifient pas leurs entrées par effet de bord inattendu.

Lancer localement :

```bash
python -m pytest -q
```

### 8.2 Tests d'intégration Blender

- Installer/charger l'add-on sur **Blender 4.5.8**.
- Capturer des sélections source/cible sur un maillage synthétique simple.
- Exécuter `Apply`, puis `Undo`.
- Vérifier que les triangles extérieurs à la cible restent identiques.
- Vérifier l'absence d'erreurs de console ou d'exceptions Python.
- Vérifier l'export STL et la validité du maillage résultant sur un objet fermé de test.

Le script d'intégration peut être lancé avec le binaire Blender, par exemple :

```bash
"/Applications/Blender.app/Contents/MacOS/Blender" --background --factory-startup --python scripts/blender_smoke_test.py
```

**À vérifier sur le poste :** le chemin effectif de l'application Blender 4.5.8.

### 8.3 Validation réelle Pika

- Sur une **copie de la courge**, capturer une zone à microrelief naturel bien numérisé.
- Sélectionner une partie de la grande région triangulée reconstruite.
- Appliquer les valeurs par défaut (60 %, 100 %, 25 %).
- Comparer les vues en lumière rasante, examiner les raccords.
- Mesurer la taille des détails et leur pertinence pour la résolution d'impression choisie.
- Vérifier qu'aucune paroi supplémentaire ni bord ouvert n'a été créé.
- Garder une possibilité de revenir au scan avant modifications.

## 9. UX et macOS

- **Toujours cibler Blender 4.5.8** et vérifier dans la documentation de cette version les API et libellés avant de proposer une navigation UI.
- Les instructions utilisateur doivent fonctionner avec **trackpad** et **sans pavé numérique**.
- Privilégier le panneau `N`, les menus visibles et les boutons d'opérateurs; ne pas reposer uniquement sur `F3` (les touches F peuvent être interceptées par macOS).
- Préciser **Object Mode** ou **Edit Mode** pour chaque étape.
- En cas de doute sur un libellé ou une propriété de l'interface, demander une capture plutôt que d'inventer un chemin.

## 10. Plan de développement pour Codex

### Milestone M0 — Mise en place

- Créer le dépôt/projet VSCode, `pyproject.toml`, structure des modules, README et tests initiaux.
- Vérifier version exacte de Blender 4.5.8 et Python embarqué; documenter environnement macOS.

### Milestone M1 — Prototype mathématique hors Blender

- Implémenter l'extraction du résidu géométrique, l'interpolation spatiale et la fonction de fondu.
- Valider sur jeux de maillages synthétiques avec pytest.
- Générer des métriques et visualisations de test simples si cela aide au diagnostic.

### Milestone M2 — Intégration Blender minimale

- Captures source/cible en Edit Mode.
- Adaptateur BMesh/Mesh.
- Opérateur `Apply` + Undo, erreurs explicites.
- Test d'intégration dans Blender 4.5.8.

### Milestone M3 — Densification locale encadrée

- Comparer le 90e percentile de la taille d’arête cible à la médiane source;
  signaler un manque de résolution au-delà de `1,5×` et recommander un nombre
  de coupes qui ramène l’espacement cible vers la médiane source.
- Exposer `clone_relief.diagnose_resolution` et une subdivision locale
  explicite avec boîte de confirmation, estimation prudente du coût, plafond
  initial de 250 000 faces ajoutées et limite de 8 coupes.
- Subdiviser les arêtes de la cible avec le remplissage en grille BMesh,
  conserver les positions des bords et les captures invalides après changement
  topologique.
- Les tests synthétiques vérifient la recommandation de résolution, l’estimation
  de faces, la préservation des coordonnées de bord et source, et Undo exact.
- Aucune validation de densification n’a été réalisée sur le scan Pika ou un
  maillage de plusieurs millions de faces.

### Milestone M4 — Expérience utilisateur

- Panneau `Clone Relief` dans la barre latérale N, captures source/cible,
  réglages, Apply, diagnostic et subdivision.
- Guide d’installation macOS, capture réelle de l’interface et procédure de
  validation sur une copie de la courge.
- L’aperçu non destructif reste reporté; l’installation depuis Préférences
  n’a pas été testée manuellement.

### Milestone M5 — Fiabilisation impression 3D

- Contrôles de continuité, normals/manifoldness, comparaison avant/après et export test.

**Ordre de priorité :** M1 → M2 sur données synthétiques **avant** de développer une UI sophistiquée ou d'essayer directement sur plusieurs millions de triangles.

## 11. État et limites à ne pas confondre avec des fonctionnalités existantes

Ce document constitue **un cahier des charges et une proposition d'algorithme**. Au 6 novembre 2026 :

- Le noyau M1, les opérateurs M2 et le diagnostic/subdivision M3 sont implémentés. Les 17 tests pytest passent; le smoke test Blender 4.5.8 vérifie capture, diagnostic de résolution, densification d’une région triangulée raccordée, conservation des positions de bord et de la source, ainsi qu’Undo exact.
- Le panneau, les réglages persistants de scène et le guide utilisateur M4
  existent. `scripts/build_addon_zip.py` prépare une archive d’add-on historique;
  son import et son enregistrement ont été vérifiés dans Blender 4.5.8, mais
  l’installation manuelle depuis Préférences reste à vérifier.
- Aucun aperçu non destructif n’est implémenté.
- L'extraction d'un relief depuis une sélection puis son transfert sur une autre **n'est pas une commande native unique** de Blender 4.5.8.
- L'effet obtenu dépendra de la qualité de l'estimation de la forme lissée, de la densité des faces, de l'échelle et de la correspondance spatiale.
- L'outil n'a pas été évalué sur le scan Pika; il ne peut pas encore être qualifié de fiable pour des modèles imprimables.

## 12. Prompt de reprise pour Codex dans VSCode

> Tu travailles sur le projet **Blender-CloneRelief**. Lis `HANDOFF.md`, `SPECIFICATIONS.md`, `DEVELOPMENT.md` et `USER_GUIDE.md`. M0–M4 sont en place. Commence uniquement **M5 — fiabilisation impression 3D** : contrôles de continuité et manifoldness, comparaison avant/après et export test sur géométrie synthétique fermée. Respecte Blender 4.5.8. N’utilise pas le scan original et ne qualifie pas le résultat pour l’impression avant validation séparée sur une copie.

---

**Prochaine action :** commencer M5 avec le prompt de reprise ci-dessous; garder
les vérifications sur des maillages synthétiques fermés avant toute validation
séparée sur une copie du scan Pika.
