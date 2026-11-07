# Spécifications — Clone Relief

- **Version :** 0.1 — mise à jour fonctionnelle du 7 novembre 2026
- **État :** spécification de référence; M0–M4 réalisés, validation sur scan à venir
- **Source de cadrage :** [`HANDOFF.md`](HANDOFF.md)
- **Projet :** add-on Python pour Blender 4.5.8, macOS Intel

Ce document transforme le handoff en exigences produit et critères de validation. Les 22 tests pytest et le smoke test synthétique M2–M4 passent dans Blender 4.5.8. La méthode actuelle copie le profil complet relatif au plan moyen de la source; elle reste à valider visuellement sur une copie du scan Pika.

## 1. Objectif

Clone Relief doit copier le profil de surface d’une zone saine d’un scan 3D vers une zone cible du même maillage. En mode unidirectionnel, il translate le profil entier vers l’extérieur sans écrêter ses creux; un fondu facultatif atténue le déplacement près des limites.

Le résultat doit être porté par la géométrie exportée (STL/3MF), et non par une texture ou un effet de rendu. L’outil modifie les sommets de la cible existante : il ne crée pas de patch superposé et ne remplace pas les faces par un morceau de surface soudé.

### Hors périmètre

- Reconstituer les détails réels qui n’ont pas été capturés par le scanner.
- Corriger automatiquement la courbure ou la silhouette macroscopique de la zone.
- Réparer globalement la topologie ou garantir à lui seul la fabricabilité du scan.
- Subdiviser automatiquement l’ensemble du maillage.
- Fournir dès la première version un aperçu temps réel sur plusieurs millions de triangles.

## 2. Environnement et usage

- Version cible : **Blender 4.5.8**.
- Poste cible : **macOS Intel**, utilisation au trackpad, sans pavé numérique.
- Maillages visés : scans pouvant atteindre plusieurs millions de triangles.
- Cas de référence : scan d’une courge butternut capturé avec un scanner Pika, dont une zone a été remplie par de grands triangles dans CrealityScan.
- Les instructions utilisateur devront préciser le mode Blender concerné et ne pas dépendre uniquement de raccourcis F ni du pavé numérique.

## 3. Parcours utilisateur attendu

1. L’utilisateur sélectionne l’objet maillé à traiter.
2. En Edit Mode, il sélectionne des faces saines et lance **Capture Source**.
3. Il sélectionne les faces cibles sur le même objet et lance **Capture Target**.
4. Il prévisualise le nombre de sommets concernés et l’amplitude maximale sans modifier le maillage.
5. Il règle l’intensité, le gain d’amplitude, l’échelle du motif et le fondu de bord.
6. Il applique le transfert en une opération annulable et peut restaurer l’état précédent avec Undo.
7. Il inspecte le résultat et peut exporter le maillage. Une commande optionnelle peut densifier localement une cible trop peu détaillée.

L’interface actuelle est le panneau **Clone Relief** dans la barre latérale N de la vue 3D.

## 4. Réglages

| Réglage | Valeur initiale | Définition |
|---|---:|---|
| Intensité | 1,00 (100 %) | Copie intégrale du profil source. Une valeur plus faible réduit l’écart au profil copié. |
| Gain | 1,00× | Multiplicateur séparé de l’intensité; les valeurs supérieures à 1 exagèrent le profil. |
| Échelle du motif | 1,00 (100 %) | Échelle physique du motif transféré. La convention doit être documentée et vérifiée par test. |
| Largeur du fondu | 0,25 (25 %) | Fraction de la largeur caractéristique de la sélection cible utilisée pour le raccord. |
| Amplitude maximale | facultative | Plafond en unités de scène pour limiter les déplacements excessifs. |

Les plages autorisées devront être bornées et documentées. Le plafonnement éventuel ne doit pas rendre ambiguë la relation entre intensité et déplacement.

## 5. Exigences fonctionnelles

### Capture et état des sélections

- **F-01 — Capture source :** mémoriser un morceau de faces reliées par des arêtes communes, ainsi que leur géométrie utile et les données nécessaires au calcul du relief. Si la sélection contient plusieurs morceaux et que le plus grand compte au moins deux fois plus de faces que les autres réunis, capturer le plus grand, écarter les autres de la sélection visible et signaler leur compte. Sinon, refuser la capture. La capture doit survivre aux changements de sélection.
- **F-02 — Validité de capture :** détecter ou invalider une capture si la topologie de l’objet change après capture. Le comportement doit être explicite pour l’utilisateur.
- **F-03 — Capture cible :** mémoriser une sélection cible distincte sur le même objet pour la V1.
- **F-04 — Sélections incompatibles :** refuser ou traiter explicitement une source vide, une cible vide, des groupes disjoints sans groupe dominant et un chevauchement source/cible.

### Extraction et transfert du relief

- **F-05 — Profil de surface :** extraire la surface supérieure complète par rapport au plan moyen de la source, afin que le profil copié conserve ses bosses et ses creux. À intensité 100 %, gain 1× et échelle 1×, le profil intérieur de la cible doit correspondre au profil source, à une translation constante près en mode unidirectionnel.
- **F-06 — Repères locaux :** construire une paramétrisation 2D locale pour la source et la cible, puis échantillonner le relief source dans le repère cible. Signaler les limites pour les fortes courbures, distorsions, plis et topologies non assimilables à un disque.
- **F-07 — Échelle physique :** interpréter l’échelle selon les unités physiques de Blender, et non selon les pixels de l’écran.
- **F-08 — Interpolation :** interpoler les hauteurs de façon stable, par exemple par coordonnées barycentriques. Les points hors de la source ne doivent pas produire d’extrapolation incontrôlée.
- **F-09 — Déplacement :** par défaut, transférer le profil en mode unidirectionnel : soustraire son minimum pour que le profil copié soit non négatif, puis déplacer les sommets cibles uniquement dans le sens positif de leurs normales locales. Cette translation ne doit ni écrêter les creux ni changer la forme du profil. Le mode bidirectionnel conserve le profil signé autour du plan moyen. Appliquer intensité, gain et fondu; les sommets hors cible restent inchangés.
- **F-10 — Fondu :** le poids est nul sur le bord de la sélection et augmente sans rupture vers l’intérieur, par exemple avec `smoothstep`. Préférer une distance sur le graphe du maillage à une distance euclidienne lorsque la forme comporte des plis ou replis.

### Densité et sécurité

- **F-11 — Densification locale :** proposer une subdivision locale explicite lorsque la cible est trop grossière pour représenter le motif. Ne jamais densifier globalement par défaut. Estimer le nombre de faces et appliquer un plafond de sécurité avant exécution.
- **F-12 — Undo et sauvegarde :** l’application doit constituer une seule opération Undo. Prévoir une copie ou un mécanisme de restauration du maillage avant modification.
- **F-13 — Préservation :** ne pas supprimer les attributs ou UV existants. Ne pas modifier la géométrie extérieure à la cible, à l’exception d’un éventuel raccord explicitement inclus dans l’opération.
- **F-14 — Topologie :** le transfert ne doit pas créer de patch superposé, de double paroi ni de surface interne. Il ne doit pas ouvrir de bord qui était fermé avant l’opération.
- **F-15 — Diagnostics :** présenter des informations ou alertes utiles : nombres de faces source/cible, taille ou densité des arêtes, amplitude des déplacements, nombre de sommets déplacés, normales incohérentes, sélections disjointes et faces dégénérées.
- **F-16 — Impression 3D :** proposer un contrôle de manifoldness après application, sans prétendre réparer les défauts préexistants du scan.
- **F-17 — Aperçu et résultat :** fournir une estimation sans mutation du nombre de sommets à déplacer et du déplacement maximal. Après Apply, annoncer le nombre réellement déplacé, l’amplitude maximale, l’état Undo et signaler explicitement un résultat nul ou inférieur au seuil visuel documenté.
- **F-18 — Gain contrôlé :** conserver l’intensité comme fraction entre 0 et 1 du profil copié et offrir séparément un gain multiplicatif borné à 100× pour rendre visible une source de faible amplitude. L’aperçu doit suggérer un gain lorsque le déplacement estimé est trop faible.
- **F-19 — Sélection visible :** refuser la capture en Wireframe ou avec X-Ray actif et expliquer que ces modes peuvent inclure l’arrière du maillage.
- **F-20 — Messages copiables :** afficher le détail des messages sur plusieurs lignes dans le panneau; permettre de sélectionner/copier les lignes et de copier le message complet en une action.

#### Décision de départ pour M3

Le diagnostic compare le 90e percentile des longueurs d’arêtes de la cible à
la médiane de la source. Il signale une cible grossière au-delà de `1,5×` et
recommande assez de coupes uniformes pour ramener ce percentile vers la taille
médiane source. La boîte de confirmation expose le nombre de coupes et une
borne haute prudente du nombre de faces ajoutées, plafonnée par défaut à
250 000 faces et 8 coupes. Ces valeurs initiales devront être ajustées avec
des mesures sur maillages de test plus grands.

La subdivision est limitée aux arêtes des faces cible. Les faces voisines qui
partagent ces arêtes peuvent être subdivisées pour garder la surface connectée;
les coordonnées des bords restent inchangées. Toute modification de topologie
invalide les captures source et cible.

## 6. Exigences de qualité et de performance

- **Q-01 — Modules calculatoires :** les calculs de géométrie et de relief ne dépendent pas de `bpy` et sont testables avec pytest.
- **Q-02 — Annotations :** annoter les fonctions, variables publiques et structures de données Python. Utiliser `dataclasses` et `typing` lorsque cela clarifie les interfaces.
- **Q-03 — Version Python :** rester compatible avec le Python livré dans Blender 4.5.8; ne pas supposer que le Python Homebrew est utilisé par Blender.
- **Q-04 — Mémoire :** traiter les seules sélections lorsque possible et éviter les copies répétées du maillage complet.
- **Q-05 — Complexité :** ne pas effectuer de recherche quadratique source × cible sans structure spatiale ni borne explicitement contrôlée.
- **Q-06 — Réactivité :** mesurer temps de calcul et consommation mémoire sur le Mac cible avant de fixer les plafonds de densification. Prévoir une annulation utilisateur si l’API Blender le permet.
- **Q-07 — Entrées :** les fonctions de calcul ne modifient pas leurs entrées de manière inattendue.

## 7. Architecture de référence

```text
src/clone_relief/
├── __init__.py         # enregistrement de l’add-on
├── relief.py           # extraction, filtrage et échantillonnage du relief, sans bpy
├── geometry.py         # géométrie, graphes, masques et interpolation, sans bpy
├── blender_adapter.py  # conversion BMesh/Mesh vers structures neutres
├── operators.py        # captures, Apply et commandes
└── ui.py               # panneau et réglages
```

Les tests unitaires se trouvent sous `tests/`; le smoke test Blender sous `scripts/`. Cette architecture est une cible de conception, à adapter si le prototype montre qu’une structure plus simple suffit.

## 8. Critères d’acceptation

Les critères suivants s’appliquent au calcul et à l’intégration. Les tolérances numériques doivent être définies à partir des jeux synthétiques et consignées avec les tests.

1. Une source plane sans relief produit une hauteur proche de zéro et ne déplace pas la cible.
2. Un relief sinusoïdal synthétique conserve une fréquence et une amplitude dans les tolérances définies.
3. Le mode unidirectionnel par défaut ne déplace aucun sommet cible dans le sens négatif de sa normale; le mode bidirectionnel conserve des déplacements positifs et négatifs.
4. En mode unidirectionnel, intensité 100 %, gain 1× et échelle 1×, le profil cible intérieur correspond au profil source à une translation constante près; aucun creux n’est écrêté.
5. Une intensité de 0 % ne déplace aucun sommet; 60 % produit 0,6 fois le déplacement de 100 %, hors plafonnement.
6. L’échelle à 100 % conserve la taille caractéristique du motif; les autres valeurs suivent la convention documentée.
7. Le poids de fondu est nul au bord et progresse vers l’intérieur sans discontinuité manifeste.
8. Sans densification, tous les sommets hors cible restent bit-à-bit inchangés.
9. Les cas vides, une seule face, sélections disjointes, triangles dégénérés, normales incohérentes, source sans variance et cible sous-échantillonnée sont gérés explicitement.
10. Undo restaure les coordonnées d’origine; l’opération n’altère pas les entrées de calcul.
11. Dans Blender 4.5.8, les captures et Apply fonctionnent sur un maillage synthétique; Undo restaure le résultat et la console ne signale pas d’exception.
12. Un export STL de contrôle sur un objet fermé ne contient pas de défaut de manifoldness introduit par l’outil.
13. Sur une copie du scan Pika, le profil source est reconnaissable sur la cible, le raccord est acceptable et aucune paroi supplémentaire ni ouverture n’est créée.

Le dernier critère est une validation empirique sur données réelles; il ne peut pas être remplacé par les tests synthétiques.

## 9. Plan de réalisation

1. **M0 — Mise en place :** structure du projet, configuration Python, documentation de l’environnement Blender/macOS.
2. **M1 — Prototype mathématique :** extraction du profil, interpolation, fondu et jeux synthétiques; valider avant l’interface et avant les scans volumineux.
3. **M2 — Intégration Blender :** captures en Edit Mode, adaptateur, Apply + Undo et smoke test dans Blender 4.5.8.
4. **M3 — Densification locale :** diagnostic de résolution, estimation de coût, subdivision locale encadrée.
5. **M4 — UX :** panneau N, réglages, diagnostics et documentation d’utilisation sur macOS.
6. **M5 — Impression 3D :** contrôles de continuité, manifoldness, comparaison avant/après et export de contrôle.

## 10. Décisions à valider pendant le prototypage

- Méthode d’estimation du plan moyen, correspondance des profils et traitement des bords.
- Méthode de projection locale 2D et comportement sur les surfaces fortement courbes.
- Convention exacte de l’échelle du motif et méthode d’orientation initiale.
- Comportement lorsque des points cibles sortent du domaine source.
- Mesure de largeur caractéristique pour le fondu et sa correspondance avec 25 %.
- Tolérances numériques, plafond de déplacement et plafond de densification.
- Niveau de préservation requis pour les attributs Blender lors d’une éventuelle subdivision locale.

## 11. Stratégie de validation

- Tests pytest des modules purs : géométrie plane, sinusoïde, intensité, échelle, fondu, sélections et cas limites.
- Smoke test d’intégration avec le binaire Blender 4.5.8 réellement installé; le chemin de l’application reste à confirmer sur le poste.
- Validation sur une copie du scan Pika seulement après les tests synthétiques et l’intégration minimale.
- Ne pas qualifier l’outil de fiable pour l’impression avant inspection du maillage résultant et export de contrôle.

Les commandes proposées dans le handoff sont `python -m pytest -q` et, pour l’intégration, le lancement de Blender en arrière-plan avec `scripts/blender_smoke_test.py`. Elles devront être ajustées à l’environnement effectivement installé.
