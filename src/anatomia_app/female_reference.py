from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyvista as pv

from .atlas import AtlasModel
from .catalog import Structure


REFERENCE_VERSION = "HRA united-female 1.5"
REFERENCE_SOURCE = "https://humanatlas.io/3d-reference-library"
REFERENCE_LICENSE = "CC BY 4.0 — NIH/HuBMAP Human Reference Atlas"
ASSET_PATH = Path(__file__).with_name("data") / "female_reproductive_v1_5.npz"


@dataclass(frozen=True, slots=True)
class FemalePart:
    id: str
    name: str
    latin: str
    system: str
    description: str
    function: str
    components: str
    color: str


PARTS = (
    FemalePart("hra_f_vagina", "Vagina", "Vagina", "Órgãos e vísceras", "Canal fibromuscular que se estende do colo do útero ao vestíbulo da vulva.", "Participa da cópula, permite a eliminação do fluxo menstrual e constitui parte do canal do parto.", "Vagina e junção cervicovaginal", "#c96f91"),
    FemalePart("hra_f_tuba_d", "Tuba uterina direita", "Tuba uterina dextra", "Órgãos e vísceras", "Tubo par que comunica a região periovariana direita com a cavidade uterina.", "Capta o ovócito e é o local mais frequente de fecundação, conduzindo-o em direção ao útero.", "Infundíbulo, fímbrias, ampola e istmo", "#d58aa0"),
    FemalePart("hra_f_tuba_e", "Tuba uterina esquerda", "Tuba uterina sinistra", "Órgãos e vísceras", "Tubo par que comunica a região periovariana esquerda com a cavidade uterina.", "Capta o ovócito e é o local mais frequente de fecundação, conduzindo-o em direção ao útero.", "Infundíbulo, fímbrias, ampola e istmo", "#d58aa0"),
    FemalePart("hra_f_recesso_uterovesical", "Escavação uterovesical", "Excavatio vesicouterina", "Órgãos e vísceras", "Recesso peritoneal situado entre a bexiga urinária e a face anterior do útero.", "Permite o deslizamento relativo entre as vísceras pélvicas adjacentes.", "Reflexão peritoneal uterovesical", "#b895b3"),
    FemalePart("hra_f_lig_redondo_d", "Ligamento redondo do útero direito", "Ligamentum teres uteri dextrum", "Articulações, ligamentos e fáscias", "Cordão fibromuscular que parte do corno uterino direito e segue pelo canal inguinal.", "Auxilia na manutenção da anteversão uterina.", "Ligamento direito", "#75c9bd"),
    FemalePart("hra_f_lig_redondo_e", "Ligamento redondo do útero esquerdo", "Ligamentum teres uteri sinistrum", "Articulações, ligamentos e fáscias", "Cordão fibromuscular que parte do corno uterino esquerdo e segue pelo canal inguinal.", "Auxilia na manutenção da anteversão uterina.", "Ligamento esquerdo", "#75c9bd"),
    FemalePart("hra_f_lig_uterosacrais", "Ligamentos uterossacrais", "Ligamenta sacrouterina", "Articulações, ligamentos e fáscias", "Pares de condensações fasciais entre o colo uterino e a região sacral.", "Contribuem para o suporte posterior do útero e do colo.", "Direito e esquerdo", "#75c9bd"),
    FemalePart("hra_f_lig_cardinais", "Ligamentos cardinais", "Ligamenta cardinalia", "Articulações, ligamentos e fáscias", "Condensações fasciais laterais associadas ao colo do útero e à vagina superior.", "Participam do suporte apical dos órgãos pélvicos.", "Direito e esquerdo", "#75c9bd"),
    FemalePart("hra_f_lig_susp_ovarios", "Ligamentos suspensores dos ovários", "Ligamenta suspensoria ovarii", "Articulações, ligamentos e fáscias", "Pregas peritoneais que ligam os ovários à parede pélvica lateral.", "Sustentam os ovários e conduzem seus principais vasos, nervos e linfáticos.", "Direito e esquerdo", "#75c9bd"),
    FemalePart("hra_f_lig_proprios_ovarios", "Ligamentos próprios dos ovários", "Ligamenta ovarii propria", "Articulações, ligamentos e fáscias", "Cordões fibromusculares entre os ovários e os cornos uterinos.", "Mantêm cada ovário ligado ao útero.", "Direito e esquerdo", "#75c9bd"),
    FemalePart("hra_f_lig_largo", "Ligamento largo do útero", "Ligamentum latum uteri", "Articulações, ligamentos e fáscias", "Dupla lâmina de peritônio que se estende das margens uterinas às paredes laterais da pelve.", "Forma um mesentério para útero, tubas e ovários e serve de trajeto para vasos.", "Mesométrio e pregas peritoneais associadas", "#75c9bd"),
    FemalePart("hra_f_mesossalpinge", "Mesossalpinge", "Mesosalpinx", "Articulações, ligamentos e fáscias", "Porção superior do ligamento largo relacionada às tubas uterinas.", "Sustenta as tubas uterinas e conduz pequenos vasos.", "Direita e esquerda", "#75c9bd"),
    FemalePart("hra_f_mesovario", "Mesovário", "Mesovarium", "Articulações, ligamentos e fáscias", "Curta prega peritoneal que prende a margem anterior do ovário ao ligamento largo.", "Mantém a conexão do ovário com o ligamento largo e permite passagem neurovascular.", "Direito e esquerdo", "#75c9bd"),
    FemalePart("hra_f_ovario_d", "Ovário direito", "Ovarium dextrum", "Órgãos e vísceras", "Gônada feminina direita localizada na pelve lateral.", "Produz ovócitos e secreta hormônios, especialmente estrogênios e progesterona.", "Ovário direito", "#dca05f"),
    FemalePart("hra_f_ovario_e", "Ovário esquerdo", "Ovarium sinistrum", "Órgãos e vísceras", "Gônada feminina esquerda localizada na pelve lateral.", "Produz ovócitos e secreta hormônios, especialmente estrogênios e progesterona.", "Ovário esquerdo", "#dca05f"),
    FemalePart("hra_f_utero", "Útero", "Uterus", "Órgãos e vísceras", "Órgão muscular oco localizado entre a bexiga e o reto, contínuo inferiormente com a vagina.", "Abriga o desenvolvimento embriofetal, participa da menstruação e produz contrações no parto.", "Fundo, corpo, cornos, segmento inferior, paredes, colo e óstios cervicais", "#bb5d78"),
    FemalePart("hra_f_art_uterina_e", "Artéria uterina esquerda", "Arteria uterina sinistra", "Sistema cardiovascular", "Ramo arterial pélvico que alcança o útero pelo lado esquerdo.", "Irriga principalmente útero e colo, com ramos para vagina, tuba e ovário.", "Artéria esquerda", "#d94747"),
    FemalePart("hra_f_art_uterina_d", "Artéria uterina direita", "Arteria uterina dextra", "Sistema cardiovascular", "Ramo arterial pélvico que alcança o útero pelo lado direito.", "Irriga principalmente útero e colo, com ramos para vagina, tuba e ovário.", "Artéria direita", "#d94747"),
    FemalePart("hra_f_veia_uterina_e", "Veia uterina esquerda", "Vena uterina sinistra", "Sistema cardiovascular", "Componente esquerdo do plexo venoso que drena o útero.", "Conduz sangue venoso uterino em direção ao sistema ilíaco interno.", "Veia esquerda", "#497fc1"),
    FemalePart("hra_f_veia_uterina_d", "Veia uterina direita", "Vena uterina dextra", "Sistema cardiovascular", "Componente direito do plexo venoso que drena o útero.", "Conduz sangue venoso uterino em direção ao sistema ilíaco interno.", "Veia direita", "#497fc1"),
)


def _polydata(points: np.ndarray, triangles: np.ndarray) -> pv.PolyData:
    faces = np.empty((len(triangles), 4), dtype=np.int64)
    faces[:, 0] = 3
    faces[:, 1:] = triangles
    return pv.PolyData(points, faces.ravel())


def add_female_reference(atlas: AtlasModel, asset_path: Path = ASSET_PATH) -> AtlasModel:
    """Add the registered HRA female reproductive subset to the shared scene."""
    if not asset_path.is_file():
        return atlas
    meshes = dict(atlas.meshes)
    colors = dict(atlas.colors)
    structures = list(atlas.structures)
    with np.load(asset_path, allow_pickle=False) as data:
        for part in PARTS:
            meshes[part.id] = _polydata(data[f"{part.id}_points"], data[f"{part.id}_faces"])
            colors[part.id] = part.color
            structures.append(
                Structure(
                    part.id,
                    part.name,
                    part.latin,
                    part.system,
                    part.description,
                    part.function,
                    (
                        ("Componentes representados", part.components),
                        ("Região anatômica", "Pelve e períneo"),
                        ("Perfil reprodutivo", "Feminino"),
                        ("Fonte geométrica", REFERENCE_VERSION),
                        ("Licença desta malha", REFERENCE_LICENSE),
                        ("Registro espacial", "Alinhamento pélvico ao atlas principal"),
                    ),
                    "Pelve e períneo",
                    "feminino",
                )
            )
    return AtlasModel(
        meshes=meshes,
        structures=tuple(structures),
        label=f"{atlas.label} + HRA feminino",
        version=f"{atlas.version} / HRA 1.5",
        source=f"{atlas.source}; {REFERENCE_SOURCE}",
        license_name=f"{atlas.license_name}; {REFERENCE_LICENSE}",
        attribution=f"{atlas.attribution}; NIH/HuBMAP Human Reference Atlas",
        revision=f"{atlas.revision}; united-female v1.5",
        coverage_note=(
            f"{atlas.coverage_note} Perfil feminino complementar com {len(PARTS)} "
            "estruturas reprodutivas e pélvicas registradas no mesmo enquadramento."
        ),
        colors=colors,
    )
