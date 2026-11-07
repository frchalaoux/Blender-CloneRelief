# HANDOFF — Blender Clone Relief

- **Date :** 7 novembre 2026
- **Dépôt :** Blender-CloneRelief, branche locale staging
- **Cible :** Blender 4.5.8 LTS sur macOS Intel; usage au trackpad, sans pavé numérique
- **État :** M0–M4 implémentés; validation sur géométrie synthétique réussie; validation du transfert sur le scan Pika et qualification impression restent à faire

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
  l’intensité.
- **Densification :** commande locale confirmée, estimation de coût, plafond
  initial de 250 000 faces ajoutées et limite de 8 coupes. Elle invalide les
  captures. Pas encore éprouvée sur un gros scan réel.
- **Exemple :** documentation/examples/clone_relief_before_after.blend et son
  rendu PNG montrent le profil source échantillonné, la cible plane avant et
  la cible après. Paramètres : intensité 1, gain 1, échelle 1, fondu 0,1.

## État Blender à la reprise

La scène d’exemple ci-dessus est chargée dans Blender 4.5.8, en Edit Mode, sur
TEST - source striee et cible plane. Les réglages enregistrés sont intensité
1, gain 1, échelle 1, fondu 0,1 et mode OUTWARD. Les captures ne sont pas
conservées à l’ouverture : sélectionner et capturer à nouveau source et cible
avant un essai.

**Attention :** le pont Blender charge l’add-on depuis
~/Library/Application Support/Blender/4.5/scripts/addons/clone_relief/, alors
que le code de référence est dans src/clone_relief/. Cette copie installée
n’a pas été synchronisée avec les dernières modifications de l’algorithme.
Pour tester l’algorithme actuel dans l’interface, reconstruire/réinstaller
l’add-on depuis le dépôt puis redémarrer Blender. La génération de l’exemple et
les smoke tests utilisent bien le code du dépôt.

## Scan Pika

Fichier de travail déjà utilisé :
/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend.
L’objet original est BUTTERNUT_010; l’objet de travail est
BUTTERNUT_010.001. Garder l’original intact et travailler sur une copie avant
toute application ou densification. Les mesures de relief et de résolution
faites avec l’ancienne extraction lissée doivent être refaites avec le profil
complet actuel.

## Validations acquises

- .venv/bin/python -m pytest -q : **22 tests réussis**.
- Smoke test exécuté avec Blender **4.5.8 LTS** : captures, mode de sélection,
  aperçu sans mutation, Apply/Undo, diagnostic et subdivision locale validés
  sur maillage synthétique.
- scripts/create_before_after_example.py exécuté avec Blender 4.5.8; le
  fichier blend et le PNG ont été régénérés.
- git diff --check sans erreur avant le commit de reprise.

Ces validations synthétiques ne remplacent pas l’inspection du résultat sur la
courge ni le contrôle de topologie/manifoldness pour impression.

## Prochaine action

1. Réinstaller depuis le dépôt l’add-on correspondant au code actuel, puis
   redémarrer Blender.
2. Sur une copie du fichier Pika, recapturer une zone source saine et une zone
   cible, puis tester le transfert unidirectionnel à intensité 100 %, gain 1×,
   échelle 1× et fondu réduit.
3. Comparer les creux source/cible en lumière rasante, vérifier la bordure et
   Undo. Si le résultat est plausible, densifier localement seulement si le
   diagnostic le recommande, puis contrôler l’export sur une copie.

Ne pas déclarer le résultat fiable pour l’impression avant cette validation
réelle.
