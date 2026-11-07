# HANDOFF — Blender Clone Relief

- **Date :** 7 novembre 2026
- **Dépôt :** Blender-CloneRelief, branche locale staging
- **Cible :** Blender 4.5.8 LTS sur macOS Intel; usage au trackpad, sans pavé numérique
- **État :** M0–M4 implémentés. Une mise à jour locale conserve la géométrie de départ de la cible pour les Apply répétés, ajoute l’opacité de sélection et réordonne le panneau; cette mise à jour n’a pas encore été validée dans Blender.

## Objectif et décision fonctionnelle actuelle

Clone Relief copie le profil de surface d’une zone source sur une zone cible du
même maillage. En mode **unidirectionnel**, l’outil translate le profil complet
vers l’extérieur afin que son point le plus bas arrive sur la surface cible.
Les creux sont conservés et ne sont pas écrêtés. À intensité 100 %, gain 1× et
échelle 1×, le profil intérieur doit correspondre à la source à une translation
constante près. Le fondu de bord atténue volontairement le raccord.

Cette règle remplace l’ancienne approche qui extrayait seulement un résidu par
rapport à une surface lissée. Le résultat reste un motif transféré; il ne
reconstruit pas les détails absents du scan.

## État du produit

- **M0–M4 :** structure, noyau géométrique, captures source/cible, Apply/Undo,
  diagnostic et densification locale encadrée, panneau N, messages lisibles et
  copiables, guide macOS.
- **Sélection :** Solid, X-Ray désactivé et sélection de faces préparés à
  l’activation et à l’ouverture d’un fichier. Les captures refusent les modes
  susceptibles de sélectionner la face arrière. Les sélections disjointes
  sont signalées; un groupe dominant peut être retenu avec indication des faces
  écartées.
- **Transfert :** extraction du profil complet par rapport au plan moyen; le
  mode unidirectionnel translate tout le profil au-dessus de la cible. Le mode
  bidirectionnel garde les déplacements signés. Le gain est séparé de
  l’intensité. La nouvelle logique locale conserve les coordonnées initiales
  de la cible capturée; changer les réglages puis refaire Apply doit remplacer
  le résultat précédent plutôt que l’empiler.
- **Opacité :** un réglage local du panneau réduit l’alpha du remplissage
  orange de sélection; il doit restaurer le thème initial à la désactivation.
- **Densification :** commande locale confirmée, estimation de coût, plafond
  initial de 250 000 faces ajoutées et limite de 8 coupes. Elle invalide les
  captures. Pas encore éprouvée sur un gros scan réel.
- **Exemple :** documentation/examples/clone_relief_before_after.blend et son
  rendu PNG montrent le profil source échantillonné, la cible plane avant et
  la cible après. Paramètres : intensité 1, gain 1, échelle 1, fondu 0,1.

## État Blender à la reprise

Le dernier état observé dans Blender est le fichier Pika
`/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend`.
`BUTTERNUT_010.001` est la copie de travail active; `BUTTERNUT_010` reste
masqué. Avec la version précédemment installée de l’add-on, une capture source
de 1 542 faces/830 sommets et une cible de 1 268 faces/694 sommets ont été
utilisées. Le dernier Apply a modifié 564 sommets, avec un déplacement maximal
de 0,537 mm (intensité 0,6, gain 1×, échelle 1, fondu 0,25, mode OUTWARD).
Le fichier était marqué modifié et n’était pas enregistré.

Les captures sont en mémoire et ne survivent pas à la réouverture du fichier.
La version précédemment installée invalide aussi la cible après Apply. La mise
à jour locale conserve la géométrie cible capturée pour refaire les aperçus et
remplacer un résultat avec de nouveaux paramètres; elle doit être réinstallée
avant de pouvoir l’utiliser. Vérifier que le maillage est à l’état de départ
avant une réapplication avec cette version.

**Attention :** le pont Blender charge l’add-on depuis
`~/Library/Application Support/Blender/4.5/scripts/addons/clone_relief/`, alors
que le code de référence est dans `src/clone_relief/`. L’archive
`dist/blender_clone_relief_0.1.0.zip` a été reconstruite avec les changements
ci-dessus, mais la session Blender doit désinstaller l’ancienne copie,
redémarrer, puis installer cette archive. Sauvegarder d’abord le fichier Pika
si le résultat courant doit être conservé.

## Scan Pika

Fichier de travail déjà utilisé :
/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend.
L’objet original est BUTTERNUT_010; l’objet de travail est
BUTTERNUT_010.001. Garder l’original intact et travailler sur une copie avant
toute application ou densification. Les mesures de relief et de résolution
faites avec l’ancienne extraction lissée doivent être refaites avec le profil
complet actuel.

## Validations acquises avant la dernière mise à jour

- .venv/bin/python -m pytest -q : **22 tests réussis**.
- Smoke test exécuté avec Blender **4.5.8 LTS** : captures, mode de sélection,
  aperçu sans mutation, Apply/Undo, diagnostic et subdivision locale validés
  sur maillage synthétique.
- scripts/create_before_after_example.py exécuté avec Blender 4.5.8; le
  fichier blend et le PNG ont été régénérés.
- git diff --check sans erreur avant le commit de reprise.

Le changement de référence cible, le réglage d’opacité et l’ordre des contrôles
du panneau n’ont pas encore été testés dans Blender. Les critères correspondants
ont été ajoutés à `SPECIFICATIONS.md`; ne pas présenter cette mise à jour comme
validée avant exécution du smoke test et une vérification visuelle légère.

Ces validations synthétiques ne remplacent pas l’inspection du résultat sur la
courge ni le contrôle de topologie/manifoldness pour impression.

## Prochaine action

1. Sauvegarder ou abandonner explicitement le résultat Pika non enregistré,
   puis installer l’archive reconstruite et redémarrer Blender.
2. Vérifier le réglage Opacité sélection et que le thème revient à sa valeur
   initiale à la désactivation de l’add-on.
3. Sur la copie de travail, capturer source et cible, faire plusieurs aperçus
   puis plusieurs Apply avec des gains différents; confirmer que chaque Apply
   repart de la géométrie initiale capturée, sans empilement. Vérifier Undo.
4. Examiner ensuite le transfert sur le scan en lumière rasante. Ne pas
   déclarer le résultat fiable pour l’impression avant vérification de la
   bordure, des auto-intersections, des surfaces internes et de la fabricabilité.

Ne pas déclarer le résultat fiable pour l’impression avant cette validation
réelle.
