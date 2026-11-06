# Guide utilisateur — Clone Relief

**Prototype :** version 0.1.0 pour Blender 4.5.8 LTS. L’outil n’a pas encore
été validé sur le scan Pika ni qualifié pour l’impression 3D.

## Installation sur macOS

1. Dans un Terminal, se placer à la racine du dépôt et construire l’archive :

   ```bash
   python3.11 scripts/build_addon_zip.py
   ```

   L’archive est créée dans `dist/blender_clone_relief_0.1.0.zip`.
2. Dans Blender 4.5.8, ouvrir **Blender → Preferences** puis **Get Extensions**.
3. Dans le menu en haut à droite, choisir **Install from Disk…** et ouvrir
   l’archive créée à l’étape 1.
4. Dans les préférences, chercher **Clone Relief** et activer l’add-on.
5. Dans la vue 3D, ouvrir la barre latérale avec **N**, puis choisir l’onglet
   **Clone Relief**.

Blender 4.5 documente l’installation depuis un fichier ZIP, y compris pour les
add-ons historiques, dans le [guide officiel des Add-ons](https://docs.blender.org/manual/en/4.5/editors/preferences/addons.html).

## Capture et transfert

Toutes les captures et l’application du relief se font en **Edit Mode**, sur le
même objet maillé :

1. Sélectionner les faces d’une zone saine, puis cliquer **Capture Source**.
2. Sélectionner les faces de la zone cible, puis cliquer **Capture Target**.
   Les régions source et cible doivent être connectées, distinctes et ne pas se
   chevaucher.
3. Régler les paramètres et cliquer **Apply Relief**. L’opération peut être
   annulée avec Undo.

La barre latérale affiche les comptes de faces et sommets capturés ainsi que le
dernier résultat ou message d’erreur. Un changement de topologie invalide les
captures.

## Réglages

| Réglage | Défaut | Effet |
|---|---:|---|
| Intensity | 0,60 | Applique 60 % de l’amplitude de relief extraite. |
| Pattern Scale | 1,00 | Échelle physique du motif; 2,00 double sa longueur d’onde. |
| Edge Falloff | 0,25 | Largeur relative du fondu depuis le bord cible. |
| Maximum Displacement | 0 | Aucun plafond; une valeur positive limite le déplacement en unités de scène. |

La version actuelle ne propose pas d’aperçu non destructif. **Apply Relief**
modifie les sommets de la cible et reste annulable par Undo.

## Diagnostic et densification locale

Après les captures source et cible, **Diagnose Resolution** compare le 90e
percentile de longueur d’arête cible à la médiane de la source. Au-delà de
`1,5×`, le panneau signale une cible potentiellement trop grossière et propose
un nombre de coupes. Ce seuil est indicatif; il ne garantit pas que le motif
transféré sera correctement échantillonné.

**Subdivide Target…** ouvre une boîte de confirmation avec le nombre de coupes,
une estimation prudente du nombre de faces et le plafond ajouté (250 000 par
défaut). Vérifier l’estimation avant de confirmer. La subdivision conserve les
positions des bords et peut subdiviser les faces voisines qui partagent les
arêtes de la cible. Après l’opération, recapturer source et cible.

## Validation sur une copie de la courge

Ne pas commencer sur l’original. Faire une copie du fichier ou du maillage de
travail, puis :

1. Confirmer les dimensions physiques et l’échelle objet dans Blender.
2. Choisir une zone source saine et une zone cible triangulée sur le même
   objet; éviter les bords ouverts, plis serrés et régions très courbes.
3. Capturer les régions et lancer **Diagnose Resolution**. Consigner les
   valeurs source/cible et l’estimation.
4. Si la cible est sous-échantillonnée, choisir **Subdivide Target…**, vérifier
   le plafond et confirmer sur la copie.
5. Recapturer les deux régions, appliquer les réglages par défaut, puis
   examiner le relief sous lumière rasante.
6. Comparer avant/après, vérifier les bords et la topologie, puis faire un
   export de contrôle STL et l’ouvrir dans Bambu Studio.

Le transfert crée un motif plausible; il ne récupère pas les détails réellement
perdus du scan. Le prototype ne remplace pas une vérification des
auto-intersections, des parois internes, du manifoldness ou de la fabricabilité.

## Image du panneau

Panneau capturé dans Blender 4.5.8 sur macOS :

![Panneau Clone Relief dans la vue 3D](images/clone-relief-panel.png)

La capture montre le panneau en Object Mode; les commandes de capture et
d’application s’activent en Edit Mode.
