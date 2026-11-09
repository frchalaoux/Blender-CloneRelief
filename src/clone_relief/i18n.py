"""English and French UI translations selected through Blender preferences."""

import re

import bpy


_FRENCH = {
    "Message line": "Ligne du message",
    "Result line; use the button to copy the full message": "Ligne du résultat ; utilisez le bouton pour copier le message complet",
    "Selection Opacity": "Opacité de sélection",
    "Source Status": "État de la source",
    "Target Status": "État de la cible",
    "Reduces the orange fill of selected faces in the 3D View": "Réduit le remplissage orange des faces sélectionnées dans la vue 3D",
    "Intensity": "Intensité",
    "Scale the transferred source relief amplitude": "Règle l’amplitude du relief transféré depuis la source",
    "Relief Gain": "Gain du relief",
    "Amplify the extracted relief without changing its source pattern": "Amplifie le relief extrait sans modifier le motif source",
    "Pattern Scale": "Échelle du motif",
    "Physical pattern size; 2.0 doubles its wavelength": "Taille physique du motif ; 2,0 double sa longueur d’onde",
    "Edge Falloff": "Atténuation du bord",
    "Fraction of target width used to blend relief at its boundary": "Part de la largeur de la cible utilisée pour atténuer le relief à son bord",
    "Maximum Displacement": "Déplacement maximal",
    "Optional scene-unit limit; zero disables the limit": "Limite facultative en unités de scène ; zéro désactive la limite",
    "Transfer Mode": "Mode de transfert",
    "Move the whole pattern outward or preserve signed peaks and valleys": "Transfère tout le motif vers l’extérieur ou conserve les creux et les bosses signés",
    "Unidirectional (+ normal)": "Unidirectionnel (+ normale)",
    "Only displace outward along target normals": "Déplace uniquement vers l’extérieur, selon les normales de la cible",
    "Bidirectional (± normal)": "Bidirectionnel (± normale)",
    "Keep positive and negative source deviations": "Conserve les écarts positifs et négatifs de la source",
    "Cuts per Edge": "Coupes par arête",
    "Number of equal segments inserted into each selected edge": "Nombre de segments égaux créés sur chaque arête sélectionnée",
    "Maximum Added Faces": "Maximum de faces ajoutées",
    "Safety limit checked against a conservative face-count estimate": "Limite de sécurité comparée à une estimation prudente du nombre de faces",
    "Not captured": "Non capturée",
    "Failed": "Échec",
    "Last Result": "Dernier résultat",
    "Message Line": "Ligne du message",
    "Message Level": "Niveau du message",
    "Info": "Info",
    "Warning": "Avertissement",
    "Error": "Erreur",
    "Copy Full Message": "Copier le message complet",
    "Copy Clone Relief Message": "Copier le message Clone Relief",
    "Settings are not registered": "Les paramètres ne sont pas enregistrés",
    "Select a mesh object": "Sélectionnez un objet maillé",
    "main group": "groupe principal",
    "Active mesh ready": "Maillage actif prêt",
    "Mode: {mode}": "Mode : {mode}",
    "Object": "Objet",
    "Edit Mesh": "Mode Édition",
    "Sculpt": "Sculpture",
    "Weight Paint": "Peinture de poids",
    "Vertex Paint": "Peinture de sommets",
    "Texture Paint": "Peinture de texture",
    "Pose": "Pose",
    "Particle": "Particule",
    "1. Capture one connected source region": "1. Capturer une zone source connexe",
    "Use Solid shading and turn X-Ray off so only visible surfaces are selected.": "Utilisez l’ombrage Solid et désactivez X-Ray pour ne sélectionner que la surface visible.",
    "Source: {status}": "Source : {status}",
    "2. Select a separate target region on the same mesh": "2. Sélectionner une zone cible distincte sur le même maillage",
    "Target: {status}": "Cible : {status}",
    "3. Preview, adjust, then apply": "3. Prévisualiser, régler, puis appliquer",
    "2. Select a separate target region on this same mesh": "2. Sélectionner une zone cible distincte sur ce même maillage",
    "Capture Source": "Capturer la source",
    "Capture Target": "Capturer la cible",
    "Reselect Source": "Resélectionner la source",
    "Reselect Target": "Resélectionner la cible",
    "Preview Effect": "Prévisualiser l’effet",
    "Apply Relief": "Appliquer le relief",
    "M5. Mesh Inspection": "M5. Contrôle du maillage",
    "Check Topology for Printing": "Contrôler la topologie pour l’impression",
    "Locate a Component…": "Localiser une composante…",
    "Compare Target Before and After": "Comparer la cible avant/après",
    "Return to Work Mesh": "Revenir au maillage de travail",
    "Export Active Mesh as STL (mm)…": "Exporter le maillage actif en STL (mm)…",
    "Topology check does not detect self-intersections or internal walls.": "Le contrôle topologique ne détecte pas les auto-intersections ni les parois internes.",
    "Target Subdivision": "Densification de la cible",
    "Adds faces to the captured target region to represent the relief more accurately.": "Ajoute des faces à la zone cible capturée pour mieux représenter le relief.",
    "Diagnose Resolution": "Diagnostiquer la résolution",
    "Subdivide Target…": "Densifier la cible…",
    "Preview Clone Relief": "Prévisualiser Clone Relief",
    "Relief Direction": "Direction du relief",
    "Keep the relief above the target or preserve positive and negative source details": "Maintient le relief au-dessus de la cible ou conserve les détails positifs et négatifs de la source",
    "Estimate coverage and maximum displacement without changing the mesh": "Estime la couverture et le déplacement maximal sans modifier le maillage",
    "Capture Relief Source": "Capturer la source du relief",
    "Store the selected connected face region as the relief source": "Enregistre la zone de faces connexe sélectionnée comme source du relief",
    "Capture Relief Target": "Capturer la cible du relief",
    "Store the selected target region and its starting geometry for repeatable applications": "Enregistre la zone cible sélectionnée et sa géométrie initiale pour permettre plusieurs applications",
    "Reselect Captured Source": "Resélectionner la source capturée",
    "Restore the captured source faces as the current selection": "Rétablit les faces de la source capturée comme sélection actuelle",
    "Reselect Captured Target": "Resélectionner la cible capturée",
    "Restore the captured target faces as the current selection": "Rétablit les faces de la cible capturée comme sélection actuelle",
    "Apply Clone Relief": "Appliquer Clone Relief",
    "Apply or replace the relief using the captured target geometry as the baseline": "Applique ou remplace le relief en repartant de la géométrie cible capturée",
    "Check Mesh for 3D Printing": "Contrôler le maillage pour l’impression 3D",
    "Report disconnected parts, open edges, non-manifold geometry, and degenerate faces": "Signale les morceaux séparés, les bords ouverts, les éléments non-manifold et les faces dégénérées",
    "Locate Mesh Component": "Localiser une composante du maillage",
    "Select one disconnected component by face count and center the 3D view on it": "Sélectionne une composante séparée selon son nombre de faces et centre la vue 3D dessus",
    "Component": "Composante",
    "Remove temporary comparison meshes and restore the working mesh": "Supprime les maillages de comparaison temporaires et rétablit le maillage de travail",
    "Create temporary side-by-side meshes from the captured target baseline and current result": "Crée deux maillages temporaires côte à côte à partir de la cible capturée et du résultat actuel",
    "Export Working Mesh as STL": "Exporter le maillage de travail en STL",
    "Export only the active mesh to STL in millimeters": "Exporte uniquement le maillage actif en STL, en millimètres",
    "Diagnose Target Resolution": "Diagnostiquer la résolution de la cible",
    "Compare source and target edge sizes and estimate useful local subdivision": "Compare la taille des arêtes source et cible et estime la densification locale utile",
    "Subdivide the Captured Target": "Densifier la cible capturée",
    "Add faces locally to the target after checking the estimate": "Ajoute localement des faces à la cible après vérification de l’estimation",
    "Choose a component; the view will frame the selection.": "Choisissez une composante ; la vue cadrera la sélection.",
    "Capture source and target, then reopen this dialog": "Capturez la source et la cible, puis rouvrez cette fenêtre",
    "Source median edge: {value} scene units": "Arête médiane de la source : {value} unités de scène",
    "Target P90 edge: {value} ({ratio}x source)": "Arête P90 de la cible : {value} ({ratio}× la source)",
    "Selected target: {faces} faces on {object}": "Cible sélectionnée : {faces} faces sur {object}",
    "Estimated upper bound: {faces} total faces (+{added})": "Estimation haute : {faces} faces au total (+{added})",
    "Estimate exceeds the added-face limit": "L’estimation dépasse la limite de faces ajoutées",
    "Target is already near source spacing": "L’espacement de la cible est déjà proche de celui de la source",
    "Copy the full latest message to the clipboard": "Copie le dernier message complet dans le presse-papiers",
    "Message copied to the clipboard.": "Message copié dans le presse-papiers.",
    "No components loaded": "Aucune composante chargée",
    "File opened: view prepared in Solid shading, X-Ray off, face selection enabled. Select and capture the source.": "Fichier ouvert : vue préparée en ombrage Solid, X-Ray désactivé et sélection de faces active. Sélectionnez puis capturez la source.",
    "No {role} selection captured in this session.": "Aucune sélection de {role} capturée dans cette session.",
    "Component {index} — {faces} faces": "Composante {index} — {faces} faces",
    "Select and frame {faces} edge-connected faces": "Sélectionner et cadrer {faces} faces reliées par des arêtes",
    "No source selection captured in this session.": "Aucune sélection de source n’a été capturée dans cette session.",
    "No target selection captured in this session.": "Aucune sélection de cible n’a été capturée dans cette session.",
    "Failed: {detail}": "Échec : {detail}",
    "Blender units": "unités Blender",
    "Unidirectional, above the target": "Unidirectionnel, au-dessus de la cible",
    "Bidirectional, peaks and valleys": "Bidirectionnel, creux et bosses",
    "No source captured. Select the source, then click Capture Source.": "Aucune source capturée. Sélectionnez la source, puis cliquez sur Capture Source.",
    "The view was prepared: Solid shading, X-Ray off, face selection enabled. Reselect the surface, then capture again.": "La vue a été préparée : ombrage Solid, X-Ray désactivé et sélection de faces active. Refaites la sélection de surface puis relancez la capture.",
    "The source is preserved, but recapture the target before previewing or applying.": "La source est conservée, mais recapturez la cible avant l’aperçu ou l’application.",
    "Source and target overlap; select distinct faces.": "La source et la cible se chevauchent ; sélectionnez des faces distinctes.",
    "Preview failed. See the details in the Clone Relief panel.": "Échec de l’aperçu. Consultez le détail dans le panneau Clone Relief.",
    "No vertices would move. Check the captures and pattern scale.": "Aucun sommet ne bougerait. Vérifiez les captures et l’échelle du motif.",
    "Very subtle preview: {moved}/{total} vertices; max displacement {magnitude}; mode {direction}. ": "Aperçu très faible : {moved}/{total} sommets ; déplacement max. {magnitude} ; mode {direction}. ",
    "Try Relief Gain ≈ {gain}×. ": "Essayez un gain du relief d’environ {gain}×. ",
    "Even 100× may not be enough; choose a more textured source. ": "Même 100× ne suffira peut-être pas ; choisissez une source plus texturée. ",
    "Subdivide the target if the resolution diagnostic recommends it.": "Densifiez la cible si le diagnostic de résolution le recommande.",
    "Preview: {moved}/{total} vertices would move; max displacement {magnitude}; mode {direction}. The mesh was not changed.": "Aperçu : {moved}/{total} sommets bougeraient ; déplacement max. {magnitude} ; mode {direction}. Le maillage n’a pas été modifié.",
    "Preview complete. See the detailed result in Clone Relief.": "Aperçu terminé. Consultez le détail du résultat dans Clone Relief.",
    "Selection contains {groups} separate face groups ({sizes}). Keep one group connected by edges.": "La sélection contient {groups} groupes de faces séparés ({sizes}). Gardez un seul groupe relié par des arêtes.",
    "No face selected for the {role}.": "Aucune face sélectionnée pour la {role}.",
    "source": "source",
    "target": "cible",
    "The selection contains {groups} separate face groups ({sizes}). Keep one group connected by edges.": "La sélection contient {groups} groupes de faces séparés ({sizes}). Gardez un seul groupe relié par des arêtes.",
    "Captured data belongs to {object}; return to that object": "Les données capturées appartiennent à {object} ; revenez à cet objet",
    "Selected the largest group; ignored {faces} faces in {groups} disconnected groups. Check the selection.": "Groupe principal retenu ; {faces} faces ignorées dans {groups} groupes séparés. Vérifiez la sélection.",
    "No previous source capture is available.": "Aucune ancienne capture source à conserver.",
    "No previous target capture is available.": "Aucune ancienne capture cible à conserver.",
    "Previous source capture kept: {faces} faces / {vertices} vertices.": "Ancienne capture source conservée : {faces} faces / {vertices} sommets.",
    "Previous target capture kept: {faces} faces / {vertices} vertices.": "Ancienne capture cible conservée : {faces} faces / {vertices} sommets.",
    "{faces} faces / {vertices} vertices": "{faces} faces / {vertices} sommets",
    "{faces} faces / {vertices} vertices — Target baseline retained": "{faces} faces / {vertices} sommets — référence de la cible conservée",
    "The previous source capture is preserved.": "L’ancienne capture source est conservée.",
    "The previous target capture is preserved.": "L’ancienne capture cible est conservée.",
    "Source capture failed: {detail} {preserved}": "Échec de la capture source : {detail} {preserved}",
    "Target capture failed: {detail} {preserved}": "Échec de la capture cible : {detail} {preserved}",
    "Capture Source failed. See the details in Clone Relief.": "Échec de Capture Source. Consultez le détail dans Clone Relief.",
    "Capture Target failed. See the details in Clone Relief.": "Échec de Capture Target. Consultez le détail dans Clone Relief.",
    "Source captured: {faces} faces, {vertices} vertices. Recapture the target. {note}": "Source capturée : {faces} faces, {vertices} sommets. Recapturez la cible. {note}",
    "Target captured: {faces} faces, {vertices} vertices. {note}": "Cible capturée : {faces} faces, {vertices} sommets. {note}",
    "{object}: source captured, {status}": "{object} : source capturée, {status}",
    "Capture the source first. Details are in the Clone Relief panel.": "Capturez d’abord la source. Détail dans le panneau Clone Relief.",
    "Target captured. See counts in the Clone Relief panel.": "Cible capturée. Consultez les nombres dans le panneau Clone Relief.",
    "Could not restore source selection: {detail}": "Impossible de rétablir la sélection source : {detail}",
    "Could not restore target selection: {detail}": "Impossible de rétablir la sélection cible : {detail}",
    "Source selection could not be restored. See Clone Relief.": "La sélection source n’a pas pu être rétablie. Consultez Clone Relief.",
    "Target selection could not be restored. See Clone Relief.": "La sélection cible n’a pas pu être rétablie. Consultez Clone Relief.",
    "Source selection restored from its capture. Geometry was not changed.": "Sélection source rétablie depuis sa capture. La géométrie n’a pas été modifiée.",
    "Target selection restored from its capture. Geometry was not changed.": "Sélection cible rétablie depuis sa capture. La géométrie n’a pas été modifiée.",
    "Source selection restored.": "Sélection source rétablie.",
    "Target selection restored.": "Sélection cible rétablie.",
    "Relief was not applied: {detail}": "Relief non appliqué : {detail}",
    "Apply Relief failed. See the details in Clone Relief.": "Échec de Apply Relief. Consultez le détail dans Clone Relief.",
    "No relief was produced. The target was restored from its captured geometry; the capture remains active so you can adjust settings and try again.": "Aucun relief produit. La cible a été rétablie depuis sa géométrie capturée ; la capture reste active pour ajuster les paramètres et réessayer.",
    "Relief applied from the captured target geometry, but it is very subtle: {moved}/{total} vertices; max displacement {magnitude}; mode {direction}. Adjust the settings and apply again; the same captured geometry will be used.": "Relief appliqué depuis la géométrie cible capturée, mais très faible : {moved}/{total} sommets ; déplacement max. {magnitude} ; mode {direction}. Ajustez les paramètres puis réappliquez ; la même géométrie capturée sera utilisée.",
    "Success: relief recalculated from the captured target on {moved}/{total} vertices; max displacement {magnitude}; mode {direction}. Change settings and apply again, or capture another target. Undo reverses the operation.": "Réussite : relief recalculé depuis la cible capturée sur {moved}/{total} sommets ; déplacement max. {magnitude} ; mode {direction}. Changez les paramètres et réappliquez, ou capturez une autre cible. Undo annule l’opération.",
    "Target baseline retained": "Référence de la cible conservée",
    "Apply Relief complete. See the detailed result in Clone Relief.": "Apply Relief terminé. Consultez le détail du résultat dans Clone Relief.",
    "Topology check failed: {detail}": "Échec du contrôle topologique : {detail}",
    "Topology check failed. See the Clone Relief panel.": "Échec du contrôle. Consultez le panneau Clone Relief.",
    "Topology check — {object}: {vertices} vertices, {edges} edges, {faces} faces.": "Contrôle topologique — {object} : {vertices} sommets, {edges} arêtes, {faces} faces.",
    "Edge-connected components: {count} ({sizes} faces).": "Composantes reliées par arêtes : {count} ({sizes} faces).",
    "Open edges: {boundary}; wire edges: {wire}; non-manifold edges: {nonmanifold_edges}; non-manifold vertices: {nonmanifold_vertices}; isolated vertices: {isolated}; degenerate faces: {degenerate}.": "Bords : {boundary} ; arêtes filaires : {wire} ; arêtes non-manifold : {nonmanifold_edges} ; sommets non-manifold : {nonmanifold_vertices} ; sommets isolés : {isolated} ; faces dégénérées : {degenerate}.",
    "Self-intersections and internal surfaces were not checked.": "Les auto-intersections et les surfaces internes ne sont pas contrôlées.",
    "No topology defects detected. ": "Aucun défaut topologique détecté. ",
    "The edge shell is closed; inspect the separate components. ": "La topologie des arêtes est fermée ; examinez les composantes séparées. ",
    "Topology check complete. See the Clone Relief panel.": "Contrôle terminé. Consultez le panneau Clone Relief.",
    "No separate components to locate.": "Aucune composante séparée à localiser.",
    "Could not locate component: {detail}": "Impossible de localiser la composante : {detail}",
    "Could not select component: {detail}": "Impossible de sélectionner la composante : {detail}",
    "The object or its topology changed; run the topology check again.": "L’objet ou sa topologie a changé ; relancez le contrôle topologique.",
    "Run component location again.": "Relancez la localisation des composantes.",
    "Component {index}/{total} selected: {faces} faces. ": "Composante {index}/{total} sélectionnée : {faces} faces. ",
    "The view is framed on the component. ": "La vue est cadrée sur la composante. ",
    "Selection made; frame it if needed. ": "Sélection effectuée ; cadrez-la si nécessaire. ",
    "No geometry was changed.": "Aucune géométrie n’a été modifiée.",
    "Component selected: {faces} faces.": "Composante sélectionnée : {faces} faces.",
    "Capture Target before creating a comparison.": "Capturez la cible avant de créer une comparaison.",
    "Comparison failed: {detail}": "Échec de la comparaison : {detail}",
    "Comparison failed. See the Clone Relief panel.": "Échec de la comparaison. Consultez le panneau Clone Relief.",
    "The previous comparison was cleared. Run the command again to recreate it.": "La comparaison précédente a été effacée. Relancez la commande pour la recréer.",
    "The target still matches its captured baseline; apply relief before comparing.": "La cible correspond encore à sa référence ; appliquez le relief avant de comparer.",
    "No changes to compare.": "Aucun changement à comparer.",
    "Comparison created in the Outliner: Before - captured target and After - current target. {moved}/{total} vertices differ; max difference {magnitude}. These temporary surfaces are open and for inspection only; they are not printable. Run this command again to remove them and return to the working mesh.": "Comparaison créée dans l’Outliner : Before - captured target et After - current target. {moved}/{total} sommets diffèrent ; écart max. {magnitude}. Ces surfaces temporaires sont ouvertes et réservées à l’inspection ; elles ne sont pas imprimables. Relancez cette commande pour les supprimer et revenir au maillage de travail.",
    "Before-and-after comparison created. See Clone Relief for details.": "Comparaison avant/après créée. Consultez le détail dans Clone Relief.",
    "No temporary comparison to clear.": "Aucune comparaison temporaire à effacer.",
    "Comparison cleared; working mesh restored.": "Comparaison effacée ; maillage de travail restauré.",
    "Select the working mesh, not a comparison surface.": "Sélectionnez le maillage de travail, pas une surface de comparaison.",
    "The STL exporter did not finish the export.": "L’exporteur STL n’a pas terminé l’export.",
    "STL export failed: {detail}": "Échec de l’export STL : {detail}",
    "STL export failed. See the Clone Relief panel.": "Échec de l’export STL. Consultez le panneau Clone Relief.",
    "STL export completed in millimeters: {path}": "Export STL terminé en millimètres : {path}",
    "STL export complete. Check the dimensions in your slicer.": "Export STL terminé. Vérifiez les dimensions dans votre trancheur.",
    "Resolution diagnostic failed: {detail}": "Échec du diagnostic de résolution : {detail}",
    "Resolution diagnostic failed. See Clone Relief for details.": "Échec du diagnostic. Consultez le détail dans Clone Relief.",
    "Target is too coarse: target P90 edge {target}, source {source} ({ratio}×). Suggested local subdivision: {cuts} cut(s).": "La cible est trop grossière : arête P90 cible {target}, source {source} ({ratio}×). Densification locale conseillée : {cuts} coupe(s).",
    "Target resolution is sufficient: target P90 edge {target}, source {source} ({ratio}×).": "La résolution de la cible est suffisante : arête P90 cible {target}, source {source} ({ratio}×).",
    "Resolution diagnostic complete. See Clone Relief for details.": "Diagnostic terminé. Consultez le détail dans Clone Relief.",
    "Subdivision failed: {detail}": "Échec de la densification : {detail}",
    "Subdivision failed. See Clone Relief for details.": "Échec de la densification. Consultez le détail dans Clone Relief.",
    "Conservative estimate adds {added} faces; limit is {limit}": "L’estimation prudente ajoute {added} faces ; la limite est {limit}",
    "Subdivision succeeded: {added} faces added. Recapture source and target.": "Densification réussie : {added} faces ajoutées. Recapturez la source et la cible.",
    "Subdivision complete. Recapture source and target; see Clone Relief for details.": "Densification terminée. Recapturez la source et la cible ; consultez le détail dans Clone Relief.",
    "Recapture after subdivision": "Recapturez après la densification",
    "Select a mesh object and enter Edit Mode first": "Sélectionnez un objet maillé et passez d’abord en mode Édition",
    "role must be 'source' or 'target'": "le rôle doit être 'source' ou 'target'",
    "Mesh topology changed after capture; capture source and target again": "La topologie du maillage a changé après la capture ; capturez à nouveau la source et la cible",
    "Captured vertex indices are no longer valid; capture again": "Les indices de sommets capturés ne sont plus valides ; recommencez la capture",
    "Object has a singular transform; apply or correct its scale first": "L’objet a une transformation singulière ; appliquez ou corrigez d’abord son échelle",
    "Coordinate and target vertex counts differ": "Le nombre de coordonnées et de sommets cibles diffère",
    "Capture source and target regions first": "Capturez d’abord les zones source et cible",
    "Captured target has no faces or edges": "La cible capturée ne contient aucune face ni arête",
    "Mesh patch has no measurable nonzero edges": "Le patch du maillage ne contient aucune arête non nulle mesurable",
    "Threshold ratio must be finite and greater than 1": "Le rapport seuil doit être fini et supérieur à 1",
    "Current face count must be nonnegative": "Le nombre actuel de faces doit être positif ou nul",
    "Cuts must be at least one": "Le nombre de coupes doit être au moins égal à un",
    "Affected faces must have at least three sides": "Les faces concernées doivent avoir au moins trois côtés",
    "Affected face count exceeds current face count": "Le nombre de faces concernées dépasse le nombre actuel de faces",
    "Relief coordinate and height counts differ": "Le nombre de coordonnées et de hauteurs du relief diffère",
    "Relief field must contain points and faces": "Le champ de relief doit contenir des points et des faces",
    "Relief coordinates must be 2D points": "Les coordonnées du relief doivent être des points 2D",
    "Relief coordinates must be finite": "Les coordonnées du relief doivent être finies",
    "Relief heights must be finite": "Les hauteurs du relief doivent être finies",
    "Relief faces must contain valid vertex indices": "Les faces du relief doivent contenir des indices de sommets valides",
    "Relief field contains no triangles": "Le champ de relief ne contient aucun triangle",
    "Iterations must be nonnegative": "Le nombre d’itérations doit être positif ou nul",
    "Lambda factor must be in (0, 1]": "Le facteur lambda doit être compris dans (0, 1]",
    "Mu factor must be in [-1, 0)": "Le facteur mu doit être compris dans [-1, 0)",
    "Intensity must be in the interval [0, 1]": "L’intensité doit être comprise dans l’intervalle [0, 1]",
    "Gain must be finite and in the interval (0, 100]": "Le gain doit être fini et compris dans l’intervalle (0, 100]",
    "Scale must be finite and greater than zero": "L’échelle doit être finie et supérieure à zéro",
    "Maximum displacement must be finite and nonnegative": "Le déplacement maximal doit être fini et positif ou nul",
    "Direction must be 'OUTWARD' or 'BIDIRECTIONAL'": "Le mode doit être 'OUTWARD' ou 'BIDIRECTIONAL'",
    "{label} has zero or invalid length": "{label} a une longueur nulle ou invalide",
    "Mesh patch must contain at least one vertex": "Le patch du maillage doit contenir au moins un sommet",
    "Mesh patch must contain at least one face": "Le patch du maillage doit contenir au moins une face",
    "Vertices must contain three finite coordinates": "Les sommets doivent contenir trois coordonnées finies",
    "Faces must contain at least three indices": "Les faces doivent contenir au moins trois indices",
    "Faces must reference at least three distinct vertices": "Les faces doivent référencer au moins trois sommets distincts",
    "Face index is outside the vertex array": "L’indice de face se trouve en dehors du tableau de sommets",
    "Width fraction must be in the interval (0, 1]": "La fraction de largeur doit être comprise dans l’intervalle (0, 1]",
    "Target patch has zero area": "Le patch cible a une aire nulle",
    "Transfer and locally refine geometric microrelief": "Transfère et affine localement le microrélief géométrique",
}

_FRENCH.update(
    {
        "mesh patch has no measurable nonzero edges": _FRENCH["Mesh patch has no measurable nonzero edges"],
        "threshold_ratio must be finite and greater than 1": _FRENCH["Threshold ratio must be finite and greater than 1"],
        "current_face_count must be nonnegative": _FRENCH["Current face count must be nonnegative"],
        "cuts must be at least one": _FRENCH["Cuts must be at least one"],
        "affected faces must have at least three sides": _FRENCH["Affected faces must have at least three sides"],
        "affected face count exceeds current face count": _FRENCH["Affected face count exceeds current face count"],
        "relief coordinate and height counts differ": _FRENCH["Relief coordinate and height counts differ"],
        "relief field must contain points and faces": _FRENCH["Relief field must contain points and faces"],
        "relief coordinates must be 2D points": _FRENCH["Relief coordinates must be 2D points"],
        "relief coordinates must be finite": _FRENCH["Relief coordinates must be finite"],
        "relief heights must be finite": _FRENCH["Relief heights must be finite"],
        "relief faces must contain valid vertex indices": _FRENCH["Relief faces must contain valid vertex indices"],
        "relief field contains no triangles": _FRENCH["Relief field contains no triangles"],
        "iterations must be nonnegative": _FRENCH["Iterations must be nonnegative"],
        "lambda_factor must be in (0, 1]": _FRENCH["Lambda factor must be in (0, 1]"],
        "mu_factor must be in [-1, 0)": _FRENCH["Mu factor must be in [-1, 0)"],
        "intensity must be in the interval [0, 1]": _FRENCH["Intensity must be in the interval [0, 1]"],
        "gain must be finite and in the interval (0, 100]": _FRENCH["Gain must be finite and in the interval (0, 100]"],
        "scale must be finite and greater than zero": _FRENCH["Scale must be finite and greater than zero"],
        "max_displacement must be finite and nonnegative": _FRENCH["Maximum displacement must be finite and nonnegative"],
        "direction must be 'OUTWARD' or 'BIDIRECTIONAL'": _FRENCH["Direction must be 'OUTWARD' or 'BIDIRECTIONAL'"],
        "mesh patch must contain at least one vertex": _FRENCH["Mesh patch must contain at least one vertex"],
        "mesh patch must contain at least one face": _FRENCH["Mesh patch must contain at least one face"],
        "vertices must contain three finite coordinates": _FRENCH["Vertices must contain three finite coordinates"],
        "faces must contain at least three indices": _FRENCH["Faces must contain at least three indices"],
        "faces must reference at least three distinct vertices": _FRENCH["Faces must reference at least three distinct vertices"],
        "face index is outside the vertex array": _FRENCH["Face index is outside the vertex array"],
        "width_fraction must be in the interval (0, 1]": _FRENCH["Width fraction must be in the interval (0, 1]"],
        "target patch has zero area": _FRENCH["Target patch has zero area"],
    }
)


_TRANSLATIONS = {
    "fr_FR": {("*", original): translated for original, translated in _FRENCH.items()},
}
_REGISTERED = False
_MODULE_NAME = __package__


def translate(message: str) -> str:
    """Translate one message using Blender's current interface language."""
    suffix = " has zero or invalid length"
    if message.endswith(suffix):
        template = bpy.app.translations.pgettext_iface("{label} has zero or invalid length")
        return template.format(label=message.removesuffix(suffix))
    return bpy.app.translations.pgettext_iface(message)


def format_message(template: str, /, **values: object) -> str:
    """Translate an English template, then interpolate its dynamic values."""
    return translate(template).format(**values)


def format_status(status: str) -> str:
    """Render a stored English status in Blender's current interface language."""
    if status in {"Not captured", "Recapture after subdivision"}:
        return translate(status)

    match = re.fullmatch(r"(\d+) faces / (\d+) vertices(?: \((main group)\))?", status)
    if match:
        rendered = format_message(
            "{faces} faces / {vertices} vertices",
            faces=match.group(1),
            vertices=match.group(2),
        )
        if match.group(3):
            rendered += f" ({translate('main group')})"
        return rendered

    match = re.fullmatch(r"(\d+) faces / (\d+) vertices — Target baseline retained", status)
    if match:
        return format_message(
            "{faces} faces / {vertices} vertices — Target baseline retained",
            faces=match.group(1),
            vertices=match.group(2),
        )

    match = re.fullmatch(r"Failed: (.*)", status)
    if match:
        return format_message("Failed: {detail}", detail=translate(match.group(1)))

    for role in ("source", "target"):
        match = re.fullmatch(
            rf"Previous {role} capture kept: (\d+) faces / (\d+) vertices\.", status
        )
        if match:
            return format_message(
                f"Previous {role} capture kept: {{faces}} faces / {{vertices}} vertices.",
                faces=match.group(1),
                vertices=match.group(2),
            )

    return translate(status)


def register() -> None:
    """Register Clone Relief translations with Blender."""
    global _REGISTERED
    if _REGISTERED:
        return
    bpy.app.translations.register(_MODULE_NAME, _TRANSLATIONS)
    _REGISTERED = True


def unregister() -> None:
    """Remove Clone Relief translations from Blender."""
    global _REGISTERED
    if not _REGISTERED:
        return
    bpy.app.translations.unregister(_MODULE_NAME)
    _REGISTERED = False
