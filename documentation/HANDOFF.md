# HANDOFF — Blender Clone Relief

- **Date :** 7 novembre 2026
- **Dépôt :** Blender-CloneRelief, branche locale staging
- **Cible :** Blender 4.5.8 LTS sur macOS Intel; usage au trackpad, sans pavé numérique
- **État :** M0–M4 réalisés dans le commit `07e55e6`. M5 est implémenté dans
  le code local : audit topologique en lecture seule, comparaison temporaire de
  la cible et export STL du seul objet actif en millimètres. L’archive doit être
  reconstruite et ces fonctions restent à valider dans Blender avant usage.

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
- **M5 local :** audit topologique sans mutation, comparaison temporaire de la
  cible capturée avant/après Apply et export STL limité à l’objet actif, avec
  conversion `scale_length` vers les millimètres. L’audit n’inspecte pas les
  auto-intersections ni les surfaces internes. Le dossier d’add-on Blender
  installé correspond aux sources locales; le localisateur a été enregistré
  dans la session active et utilisé par l’utilisateur. Le compte rendu du dernier
  opérateur est affiché juste sous Preview/Apply pour rester visible près de
  son action. Deux commandes **Reselect Source/Target** restaurent les faces
  des captures en Edit Mode tant que l’objet et sa topologie correspondent.
  **Localiser une composante…** permet de choisir un groupe par nombre de faces,
  le sélectionne et cadre la vue sans modifier sa géométrie.

## État Blender à la reprise

Le dernier état observé dans Blender est le fichier Pika
`/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend`.
`BUTTERNUT_010.001` est la copie de travail active; `BUTTERNUT_010` reste
masqué. Avec la version précédemment installée de l’add-on, une capture source
de 1 542 faces/830 sommets et une cible de 1 268 faces/694 sommets ont été
utilisées. Le dernier Apply a modifié 564 sommets, avec un déplacement maximal
de 0,537 mm (intensité 0,6, gain 1×, échelle 1, fondu 0,25, mode OUTWARD).
Le fichier était marqué modifié et n’était pas enregistré. Lors de la reprise
M5, le fichier était toujours ouvert en Edit Mode sur `BUTTERNUT_010.001`; le
dernier état M4 affichait une source de 1 572 faces/846 sommets, une cible de
2 758 faces/1 457 sommets, 1 106 sommets déplacés et un maximum de 1,065 mm.
L’opacité était 0,08. Un relevé topologique en lecture seule de la copie
indiquait 165 523 sommets, 484 984 arêtes et 319 251 faces, répartis en trois
composantes de 304 013, 10 562 et 4 676 faces; aucun bord ouvert, filaire,
non-manifold ou dégénéré n’avait été relevé. Ce relevé est un état observé,
pas encore le rapport émis par la nouvelle commande M5.

### État après localisation et suppression — 7 novembre 2026

L’utilisateur a localisé et supprimé les deux composantes internes jugées
inutiles. Lecture seule de Blender après cette opération :
`BUTTERNUT_010.001` est actif en Edit Mode et compte 157 964 sommets, 462 127
arêtes et 304 013 faces, soit le compte de faces de la grande composante
précédente. Le contrôle M5 a ensuite
été relancé et a trouvé une seule composante, zéro bord ouvert, arête filaire,
arête/sommet non-manifold, sommet isolé ou face dégénérée. Au moment de ce
contrôle, Blender indiquait `bpy.data.is_dirty = false`; l’utilisateur confirme
avoir sauvegardé le fichier. L’audit ne vérifie pas
les auto-intersections ni les surfaces internes. La géométrie n’a pas été
modifiée par l’assistant.

Les captures sont en mémoire et ne survivent pas à la réouverture du fichier.
Le code M5 est chargé dans la session courante; le localisateur a servi à
identifier les deux composantes supprimées par l’utilisateur. Les captures
source/cible sont à recapturer si elles ont été perdues lors du rechargement.

**Attention :** le pont Blender charge l’add-on depuis
`~/Library/Application Support/Blender/4.5/scripts/addons/clone_relief/`, alors
que le code de référence est dans `src/clone_relief/`. L’archive
`dist/blender_clone_relief_0.1.0.zip` a été reconstruite et le dossier
d’installation Blender synchronisé. L’utilisateur a sauvegardé le fichier Pika
après le nettoyage.

## Scan Pika

Fichier de travail déjà utilisé :
/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend.
L’objet original est BUTTERNUT_010; l’objet de travail est
BUTTERNUT_010.001. Garder l’original intact et travailler sur une copie avant
toute application ou densification. Les mesures de relief et de résolution
faites avec l’ancienne extraction lissée doivent être refaites avec le profil
complet actuel.

## Validations acquises avant M5

- .venv/bin/python -m pytest -q : **22 tests réussis**.
- Smoke test exécuté avec Blender **4.5.8 LTS** : captures, mode de sélection,
  aperçu sans mutation, Apply/Undo, diagnostic et subdivision locale validés
  sur maillage synthétique.
- scripts/create_before_after_example.py exécuté avec Blender 4.5.8; le
  fichier blend et le PNG ont été régénérés.
- git diff --check sans erreur avant le commit de reprise.

Lors de la session du 7 novembre, les sources installées correspondaient aux
fichiers de référence; la cible capturée était conservée entre les Apply et
l’opacité observée était 0,08. L’audit M5 et le localisateur ont été utilisés
sur la copie Pika; après la suppression des composantes internes, l’audit a
confirmé une composante fermée sans défaut topologique détecté. L’export STL,
la vérification de dimensions et les auto-intersections/surfaces internes
restent à contrôler. Aucun test automatisé n’a été lancé pendant cette reprise.

Ces validations synthétiques ne remplacent pas l’inspection du résultat sur la
courge ni le contrôle de topologie/manifoldness pour impression.

## Prochaine action

1. Vérifier indépendamment auto-intersections et surfaces internes; l’audit ne
   les couvre pas.
2. Si le résultat paraît correct, exporter le seul objet actif en STL et
   vérifier ses dimensions dans Bambu Studio avant toute impression.

Ne pas déclarer le résultat fiable pour l’impression avant cette validation
réelle.
