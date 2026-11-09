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

Le 9 novembre, un traceback pendant le dessin du panneau indiquait que l’icône
`MOD_DIFFERENCE` du bouton de comparaison n’existe pas dans Blender 4.5. Cette
erreur interrompait le rendu de la section M5. L’icône a été remplacée par
`MODIFIER`, valide dans Blender 4.5; recharger l’add-on installé pour appliquer
la correction.

Dans le fichier M6 rouvert, l’objet actif est `BUTTERNUT_010.001` en Edit Mode;
le rapport sur cet objet indique une composante. `BUTTERNUT_010` (original)
en a trois et `M6_FORMWARE_REPAIRED_TEMP` en a une. Le contrôle topologique
analyse seulement l’objet actif; le localisateur exige Edit Mode et au moins
deux composantes dans cet objet. Voir la procédure détaillée dans
[`USER_GUIDE.md`](USER_GUIDE.md#procédure-pas-à-pas).

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

M6 réutilise le 3D Print Toolbox pour les analyses géométriques de
fabricabilité, puis qualifie un cas d’impression identifié sans promesse
générale. Le protocole est dans
[`PRINT_QUALIFICATION.md`](PRINT_QUALIFICATION.md). Pour la copie Pika,
comparaison du transfert, contrôles avec le Toolbox, export et dimensions STL
dans le trancheur, aperçu des couches et impression réelle sont encore à faire.

Un nouveau contrôle en lecture seule a été lancé le 7 novembre 2026 sur
`BUTTERNUT_010.001` en Edit Mode. L’audit Clone Relief a compté 157 952
sommets, 462 083 arêtes et 303 981 faces, une composante, et zéro bord ouvert,
arête filaire/non-manifold, sommet isolé/non-manifold ou face dégénérée.
Le 3D Print Toolbox a rapporté 0 arête non-manifold, 0 mauvaise continuité,
1 coque, 349 faces signalées en intersection, 3 faces quasi nulles, 0 arête
nulle, 563 faces non planes, 5 651 faces minces au seuil de 1 mm, 310 arêtes
vives au seuil de 160° et 50 498 surplombs au seuil de 45°.

Les deux groupes de 45 et 21 faces ont été inspectés visuellement et présentent
une intersection nette; les autres résultats d’intersection et les 3 faces
quasi nulles restent à examiner. Les comptes d’épaisseur et de surplomb
dépendent des seuils et de l’orientation courante. Blender indiquait
`bpy.data.is_dirty = true` avant et après le
contrôle. Ne pas supposer que l’état courant est sauvegardé; aucune géométrie
n’a été éditée ni sauvegardée par l’assistant.

L’utilisateur précise que certains des groupes signalés en intersection ont
été créés par inadvertance avec des outils de sculpture. Les deux groupes
inspectés présentent une intersection, mais leur origine sculpturale n’est pas
établie. Ne pas supprimer en bloc les 349 faces : elles appartiennent au
maillage connecté et leur suppression pourrait ouvrir la surface.

Une comparaison spatiale lecture seule avec l’original caché, dont la matrice
monde est identique à celle de la copie, donne une distance médiane centre de
face → surface originale de 2,84 mm pour les 349 faces signalées (P90 8,32 mm).
Sur 2 000 faces non signalées prises à intervalles réguliers, la médiane est
0 mm (P90 4,00 mm). Comme il ne s’agit pas de correspondances sommet à sommet
et que les résolutions diffèrent, cela rend l’hypothèse de zones sculptées
plausible mais ne prouve pas la cause ni la nature de chaque intersection.

Sur les deux zones montrées par l’utilisateur, le contrôle BVH rapporte 53
paires de faces en chevauchement entre le groupe de 45 faces et celui de 21;
48 paires ne partagent aucun sommet, 5 en partagent un. Cette preuve numérique
explique que la traversée soit difficile à discerner dans le maillage dense.
Après isolement temporaire du voisinage, l’utilisateur confirme voir une
intersection nette. Cette validation visuelle concerne les deux groupes
inspectés seulement; ne pas supprimer les faces sélectionnées. La géométrie
n’a pas été modifiée. Le maillage complet est de nouveau visible et les 66
faces des groupes sont seules sélectionnées pour poursuivre l’inspection.
Un extrait temporaire de 11 809 faces de l’original est superposé à sa
position, semi-transparent et sans affichage forcé au premier plan. L’utilisateur
le voit derrière la copie depuis un angle, puis devant après une rotation de
25°. Un contrôle BVH lecture seule entre toute la copie (303 981 faces) et
l’extrait (11 809 faces), epsilon 1e-5 local, ne trouve aucun chevauchement de
triangles. L’ordre avant/arrière perçu dépend donc de la projection; les deux
groupes orange restent, eux, en chevauchement entre eux.

L’utilisateur a soumis `BUTTERNUT_010.001.stl` à Formware Online STL Repair.
L’analyse avant réparation rapporte 911 arêtes nues, 253 trous plans,
0 trou non-plan, 257 arêtes non-manifold, 446 normales inversées, 436 faces
dupliquées, 752 faces dégénérées et aucune coque disjointe. La réparation a
ajouté 6 170 sommets et 17 370 triangles. Le rapport ne donne pas d’analyse des
défauts résiduels après réparation; comparer le STL réparé à la copie Blender,
puis le réanalyser et le vérifier dans le trancheur.

Le STL réparé fourni (`Analyse Butternut M6 010.001.stl`) a été importé
temporairement dans Blender 4.5.8 à l’échelle 0,001. Ses dimensions
(103,851 × 238,163 × 111,197 mm) correspondent à celles du travail. Une
comparaison de 5 000 sommets échantillonnés dans chaque sens donne médiane 0,
P90 0,0038 mm, maximum 0,0087 mm vers l’autre surface. Toutefois l’import
Blender signale encore 363 arêtes à une face, 1 496 arêtes à plus de deux faces
et 3 382 faces d’aire nulle; une lecture directe du binaire trouve 2 648
triangles d’aire exactement nulle. L’import donne 330 614 triangles contre
332 822 facettes dans le STL. Ces comptes restent distincts; ne pas conclure
que la réparation a rendu le maillage manifold. Pas encore d’analyse par le
trancheur ni d’essai d’impression.

La comparaison des groupes 45/21 faces à l’original trouve une distance
médiane centre de face → surface de 8,32 mm pour chacun, contre environ
8,12 mm pour les faces non signalées proches. L’éloignement concerne donc
plus largement la région; ce relevé ne désigne pas les seules faces à corriger.

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

1. Comparer le résultat avant/après sur la copie Pika, puis contrôler
   les faces signalées en intersection et quasi nulles; confronter les 5 651
   faces minces au procédé choisi et interpréter les surplombs selon
   l’orientation d’impression.
2. Exporter le seul objet final en STL et vérifier ses dimensions et son
   aperçu couche par couche dans le trancheur retenu.
3. Consigner puis inspecter une impression représentative selon le protocole
   M6.

Ne pas déclarer le résultat fiable pour l’impression avant cette validation
réelle.
