from __future__ import annotations

from dataclasses import dataclass

from .muscle_data import MUSCLE_MESHES


@dataclass(frozen=True, slots=True)
class Structure:
    id: str
    name: str
    latin_name: str
    system: str
    description: str
    function: str
    details: tuple[tuple[str, str], ...] = ()
    region: str = ""
    anatomical_profile: str = "comum"

    @property
    def search_text(self) -> str:
        aliases = " ".join(value for _label, value in self.details)
        return " ".join(
            (self.name, self.latin_name, self.system, self.region, aliases)
        ).casefold()


def muscle_pair(
    identifier: str,
    name: str,
    latin_name: str,
    region: str,
    description: str,
    function: str,
    origin: str,
    insertion: str,
    innervation: str,
) -> tuple[Structure, Structure]:
    common_details = (
        ("Origem", origin),
        ("Inserção", insertion),
        ("Inervação", innervation),
    )
    return (
        Structure(
            f"{identifier}_d", f"{name} direito", f"Musculus {latin_name} dexter",
            "Sistema muscular", f"{description} no lado direito.", function,
            common_details, region,
        ),
        Structure(
            f"{identifier}_e", f"{name} esquerdo", f"Musculus {latin_name} sinister",
            "Sistema muscular", f"{description} no lado esquerdo.", function,
            common_details, region,
        ),
    )


_BASE_STRUCTURES: tuple[Structure, ...] = (
    Structure(
        "cranio", "Crânio", "Cranium", "Sistema esquelético",
        "Conjunto ósseo que forma a cabeça e protege o encéfalo.",
        "Proteção do encéfalo, sustentação da face e fixação de músculos.",
        (("Região", "Cabeça"),),
    ),
    Structure(
        "coluna", "Coluna vertebral", "Columna vertebralis", "Sistema esquelético",
        "Eixo ósseo segmentado formado pelas vértebras e pelo sacro.",
        "Sustenta o tronco, protege a medula espinal e permite movimento.",
        (("Divisões", "Cervical, torácica, lombar, sacral e coccígea"),),
    ),
    Structure(
        "costelas", "Costelas", "Costae", "Sistema esquelético",
        "Arcos ósseos pares que compõem grande parte da caixa torácica.",
        "Protegem órgãos torácicos e participam da mecânica respiratória.",
        (("Região", "Tórax"),),
    ),
    Structure(
        "esterno", "Esterno", "Sternum", "Sistema esquelético",
        "Osso plano mediano localizado na parede anterior do tórax.",
        "Conecta-se às cartilagens costais e protege estruturas do mediastino.",
        (("Partes", "Manúbrio, corpo e processo xifoide"),),
    ),
    Structure(
        "pelve", "Pelve óssea", "Pelvis ossea", "Sistema esquelético",
        "Anel ósseo formado pelos ossos do quadril, sacro e cóccix.",
        "Transmite o peso ao membro inferior e protege vísceras pélvicas.",
        (("Região", "Cintura pélvica"),),
    ),
    Structure(
        "umero_d", "Úmero direito", "Humerus dexter", "Sistema esquelético",
        "Osso longo do braço direito.", "Conecta a cintura escapular ao antebraço.",
        (("Articulações", "Ombro e cotovelo"),),
    ),
    Structure(
        "umero_e", "Úmero esquerdo", "Humerus sinister", "Sistema esquelético",
        "Osso longo do braço esquerdo.", "Conecta a cintura escapular ao antebraço.",
        (("Articulações", "Ombro e cotovelo"),),
    ),
    Structure(
        "antebraco_d", "Rádio e ulna direitos", "Radius et ulna dextra", "Sistema esquelético",
        "Ossos longos paralelos do antebraço direito.",
        "Participam dos movimentos do cotovelo, punho e pronação-supinação.",
    ),
    Structure(
        "antebraco_e", "Rádio e ulna esquerdos", "Radius et ulna sinistra", "Sistema esquelético",
        "Ossos longos paralelos do antebraço esquerdo.",
        "Participam dos movimentos do cotovelo, punho e pronação-supinação.",
    ),
    Structure(
        "femur_d", "Fêmur direito", "Femur dextrum", "Sistema esquelético",
        "Osso longo da coxa direita e o maior osso do corpo.",
        "Transmite cargas entre quadril e joelho e serve de alavanca muscular.",
        (("Articulações", "Quadril e joelho"),),
    ),
    Structure(
        "femur_e", "Fêmur esquerdo", "Femur sinistrum", "Sistema esquelético",
        "Osso longo da coxa esquerda e o maior osso do corpo.",
        "Transmite cargas entre quadril e joelho e serve de alavanca muscular.",
        (("Articulações", "Quadril e joelho"),),
    ),
    Structure(
        "perna_d", "Tíbia e fíbula direitas", "Tibia et fibula dextra", "Sistema esquelético",
        "Ossos longos da perna direita; a tíbia suporta a maior parte da carga.",
        "Conectam o joelho ao tornozelo e dão inserção a músculos da perna.",
    ),
    Structure(
        "perna_e", "Tíbia e fíbula esquerdas", "Tibia et fibula sinistra", "Sistema esquelético",
        "Ossos longos da perna esquerda; a tíbia suporta a maior parte da carga.",
        "Conectam o joelho ao tornozelo e dão inserção a músculos da perna.",
    ),
    Structure(
        "cintura_escapular_d", "Cintura escapular direita", "Cingulum pectorale dextrum", "Sistema esquelético",
        "Conjunto formado pela clavícula e pela escápula direitas.",
        "Conecta o membro superior ao tronco e oferece ampla base de fixação muscular.",
        (("Componentes", "Clavícula e escápula"),),
    ),
    Structure(
        "cintura_escapular_e", "Cintura escapular esquerda", "Cingulum pectorale sinistrum", "Sistema esquelético",
        "Conjunto formado pela clavícula e pela escápula esquerdas.",
        "Conecta o membro superior ao tronco e oferece ampla base de fixação muscular.",
        (("Componentes", "Clavícula e escápula"),),
    ),
    Structure(
        "mao_d", "Ossos da mão direita", "Ossa manus dextrae", "Sistema esquelético",
        "Conjunto ósseo do carpo, metacarpo e falanges da mão direita.",
        "Sustenta a preensão e os movimentos finos dos dedos e do polegar.",
        (("Componentes", "8 carpais, 5 metacarpais e 14 falanges"),),
    ),
    Structure(
        "mao_e", "Ossos da mão esquerda", "Ossa manus sinistrae", "Sistema esquelético",
        "Conjunto ósseo do carpo, metacarpo e falanges da mão esquerda.",
        "Sustenta a preensão e os movimentos finos dos dedos e do polegar.",
        (("Componentes", "8 carpais, 5 metacarpais e 14 falanges"),),
    ),
    Structure(
        "patela_d", "Patela direita", "Patella dextra", "Sistema esquelético",
        "Osso sesamoide localizado anteriormente ao joelho direito.",
        "Protege a face anterior do joelho e aumenta a eficiência do quadríceps.",
    ),
    Structure(
        "patela_e", "Patela esquerda", "Patella sinistra", "Sistema esquelético",
        "Osso sesamoide localizado anteriormente ao joelho esquerdo.",
        "Protege a face anterior do joelho e aumenta a eficiência do quadríceps.",
    ),
    Structure(
        "pe_d", "Ossos do pé direito", "Ossa pedis dextri", "Sistema esquelético",
        "Conjunto ósseo do tarso, metatarso, falanges e sesamoides do pé direito.",
        "Suporta o peso, forma os arcos do pé e participa da marcha.",
        (("Componentes", "7 tarsais, 5 metatarsais, 14 falanges e sesamoide"),),
    ),
    Structure(
        "pe_e", "Ossos do pé esquerdo", "Ossa pedis sinistri", "Sistema esquelético",
        "Conjunto ósseo do tarso, metatarso, falanges e sesamoides do pé esquerdo.",
        "Suporta o peso, forma os arcos do pé e participa da marcha.",
        (("Componentes", "7 tarsais, 5 metatarsais, 14 falanges e sesamoide"),),
    ),
    Structure(
        "deltoide_d", "Deltoide direito", "Musculus deltoideus dexter", "Sistema muscular",
        "Músculo superficial que recobre o ombro direito.",
        "Principal abdutor do braço; suas porções também auxiliam flexão e extensão.",
        (("Inervação", "Nervo axilar"), ("Inserção", "Tuberosidade deltoidea do úmero")),
        "Membro superior",
    ),
    Structure(
        "deltoide_e", "Deltoide esquerdo", "Musculus deltoideus sinister", "Sistema muscular",
        "Músculo superficial que recobre o ombro esquerdo.",
        "Principal abdutor do braço; suas porções também auxiliam flexão e extensão.",
        (("Inervação", "Nervo axilar"), ("Inserção", "Tuberosidade deltoidea do úmero")),
        "Membro superior",
    ),
    Structure(
        "biceps_d", "Bíceps braquial direito", "Musculus biceps brachii dexter", "Sistema muscular",
        "Músculo anterior do braço direito com cabeças longa e curta.",
        "Flexiona o cotovelo e é potente supinador do antebraço.",
        (("Inervação", "Nervo musculocutâneo"), ("Inserção", "Tuberosidade do rádio")),
        "Membro superior",
    ),
    Structure(
        "biceps_e", "Bíceps braquial esquerdo", "Musculus biceps brachii sinister", "Sistema muscular",
        "Músculo anterior do braço esquerdo com cabeças longa e curta.",
        "Flexiona o cotovelo e é potente supinador do antebraço.",
        (("Inervação", "Nervo musculocutâneo"), ("Inserção", "Tuberosidade do rádio")),
        "Membro superior",
    ),
    Structure(
        "peitoral", "Peitoral maior", "Musculus pectoralis major", "Sistema muscular",
        "Músculo amplo e superficial da parede anterior do tórax.",
        "Aduz e roda medialmente o braço; a porção clavicular auxilia a flexão.",
        (("Inervação", "Nervos peitorais lateral e medial"),),
        "Tórax e abdome",
    ),
    Structure(
        "quadriceps_d", "Quadríceps femoral direito", "Musculus quadriceps femoris dexter", "Sistema muscular",
        "Grupo muscular anterior da coxa direita.",
        "Estende o joelho; o reto femoral também auxilia a flexão do quadril.",
        (("Inervação", "Nervo femoral"), ("Inserção", "Tuberosidade da tíbia via ligamento patelar")),
        "Membro inferior",
    ),
    Structure(
        "quadriceps_e", "Quadríceps femoral esquerdo", "Musculus quadriceps femoris sinister", "Sistema muscular",
        "Grupo muscular anterior da coxa esquerda.",
        "Estende o joelho; o reto femoral também auxilia a flexão do quadril.",
        (("Inervação", "Nervo femoral"), ("Inserção", "Tuberosidade da tíbia via ligamento patelar")),
        "Membro inferior",
    ),
)

STRUCTURES: tuple[Structure, ...] = _BASE_STRUCTURES
STRUCTURES += muscle_pair(
    "masseter", "Masseter", "masseter", "Cabeça e pescoço",
    "Músculo espesso da mastigação situado na face lateral da mandíbula",
    "Eleva a mandíbula; a parte superficial auxilia a protrusão.",
    "Arco zigomático", "Face lateral do ramo e ângulo da mandíbula",
    "Nervo massetérico, ramo do nervo mandibular (V3)",
)
STRUCTURES += muscle_pair(
    "temporal", "Temporal", "temporalis", "Cabeça e pescoço",
    "Músculo em leque que ocupa a fossa temporal",
    "Eleva a mandíbula; suas fibras posteriores fazem retrusão.",
    "Fossa temporal e fáscia temporal", "Processo coronoide e ramo da mandíbula",
    "Nervos temporais profundos, ramos do nervo mandibular (V3)",
)
STRUCTURES += muscle_pair(
    "esternocleidomastoideo", "Esternocleidomastóideo", "sternocleidomastoideus", "Cabeça e pescoço",
    "Músculo superficial anterolateral do pescoço",
    "Bilateralmente flexiona o pescoço; unilateralmente inclina para o mesmo lado e roda para o oposto.",
    "Manúbrio do esterno e terço medial da clavícula",
    "Processo mastoide e metade lateral da linha nucal superior",
    "Nervo acessório (XI) e ramos de C2–C3",
)
STRUCTURES += muscle_pair(
    "trapezio", "Trapézio", "trapezius", "Dorso",
    "Músculo superficial amplo da nuca e do dorso superior",
    "Eleva, retrai, deprime e roda superiormente a escápula conforme a porção ativada.",
    "Occipital, ligamento nucal e processos espinhosos de C7–T12",
    "Terço lateral da clavícula, acrômio e espinha da escápula",
    "Nervo acessório (XI), com propriocepção de C3–C4",
)
STRUCTURES += muscle_pair(
    "latissimo_dorso", "Latíssimo do dorso", "latissimus dorsi", "Dorso",
    "Músculo superficial amplo da região inferior do dorso",
    "Estende, aduz e roda medialmente o braço.",
    "Processos espinhosos de T7–T12, fáscia toracolombar, crista ilíaca e costelas inferiores",
    "Assoalho do sulco intertubercular do úmero", "Nervo toracodorsal",
)
STRUCTURES += muscle_pair(
    "reto_abdominal", "Reto do abdome", "rectus abdominis", "Tórax e abdome",
    "Músculo vertical da parede abdominal anterior",
    "Flexiona o tronco, comprime as vísceras e estabiliza a pelve.",
    "Sínfise e crista púbicas", "Processo xifoide e cartilagens costais da 5ª à 7ª costela",
    "Nervos toracoabdominais (T6–T12)",
)
STRUCTURES += muscle_pair(
    "obliquo_externo", "Oblíquo externo", "obliquus externus abdominis", "Tórax e abdome",
    "Músculo superficial da parede anterolateral do abdome",
    "Comprime o abdome, flexiona o tronco e produz rotação contralateral.",
    "Faces externas das costelas 5–12", "Linha alba, tubérculo púbico e crista ilíaca anterior",
    "Nervos toracoabdominais (T7–T11) e subcostal (T12)",
)
STRUCTURES += muscle_pair(
    "triceps", "Tríceps braquial", "triceps brachii", "Membro superior",
    "Músculo do compartimento posterior do braço, com três cabeças",
    "Principal extensor do cotovelo; a cabeça longa também atua no ombro.",
    "Tubérculo infraglenoidal e face posterior do úmero", "Olécrano da ulna", "Nervo radial",
)
STRUCTURES += muscle_pair(
    "braquial", "Braquial", "brachialis", "Membro superior",
    "Músculo profundo do compartimento anterior do braço",
    "É um dos principais flexores do cotovelo em qualquer posição do antebraço.",
    "Metade distal da face anterior do úmero", "Processo coronoide e tuberosidade da ulna",
    "Nervo musculocutâneo, com contribuição do nervo radial",
)
STRUCTURES += muscle_pair(
    "braquiorradial", "Braquiorradial", "brachioradialis", "Membro superior",
    "Músculo superficial da região lateral do antebraço",
    "Flexiona o cotovelo, sobretudo com o antebraço em posição neutra.",
    "Crista supracondilar lateral do úmero", "Extremidade distal do rádio, próxima ao processo estiloide",
    "Nervo radial",
)
STRUCTURES += muscle_pair(
    "flexor_carpo_radial", "Flexor radial do carpo", "flexor carpi radialis", "Membro superior",
    "Músculo superficial do compartimento anterior do antebraço",
    "Flexiona e abduz radialmente o punho.",
    "Epicôndilo medial do úmero", "Bases do 2º e 3º metacarpais", "Nervo mediano",
)
STRUCTURES += muscle_pair(
    "extensor_carpo_radial_longo", "Extensor radial longo do carpo", "extensor carpi radialis longus", "Membro superior",
    "Músculo do compartimento posterior do antebraço",
    "Estende e abduz radialmente o punho.",
    "Crista supracondilar lateral do úmero", "Base do 2º metacarpal", "Nervo radial",
)
STRUCTURES += muscle_pair(
    "gluteo_maximo", "Glúteo máximo", "gluteus maximus", "Membro inferior",
    "Músculo superficial e volumoso da região glútea",
    "Estende e roda lateralmente a coxa; auxilia a estabilização do quadril e joelho.",
    "Ílio posterior, sacro, cóccix e ligamento sacrotuberal",
    "Trato iliotibial e tuberosidade glútea", "Nervo glúteo inferior",
)
STRUCTURES += muscle_pair(
    "gluteo_medio", "Glúteo médio", "gluteus medius", "Membro inferior",
    "Músculo lateral da região glútea, parcialmente coberto pelo glúteo máximo",
    "Abduz e roda medialmente a coxa; mantém a pelve nivelada durante a marcha.",
    "Face externa do ílio", "Face lateral do trocânter maior do fêmur", "Nervo glúteo superior",
)
STRUCTURES += muscle_pair(
    "sartorio", "Sartório", "sartorius", "Membro inferior",
    "Músculo longo e superficial que cruza obliquamente a coxa",
    "Flexiona, abduz e roda lateralmente o quadril; também flexiona o joelho.",
    "Espinha ilíaca anterossuperior", "Face medial proximal da tíbia, na pata de ganso", "Nervo femoral",
)
STRUCTURES += muscle_pair(
    "adutores", "Grupo adutor da coxa", "adductores femoris", "Membro inferior",
    "Grupo medial formado aqui pelos adutores longo, curto, magno e mínimo",
    "Aduz a coxa; porções específicas auxiliam flexão, extensão ou rotação do quadril.",
    "Púbis e ísquio", "Linha áspera e tubérculo adutor do fêmur",
    "Nervo obturatório; a porção isquiotibial do adutor magno recebe o nervo tibial",
)
STRUCTURES += muscle_pair(
    "isquiotibiais", "Isquiotibiais", "musculi ischiocrurales", "Membro inferior",
    "Grupo posterior da coxa: bíceps femoral, semitendíneo e semimembranáceo",
    "Estende o quadril e flexiona o joelho; participa da rotação da perna.",
    "Tuberosidade isquiática; a cabeça curta do bíceps origina-se na linha áspera",
    "Cabeça da fíbula e faces mediais da tíbia", "Divisões tibial e fibular comum do nervo isquiático",
)
STRUCTURES += muscle_pair(
    "gastrocnemio", "Gastrocnêmio", "gastrocnemius", "Membro inferior",
    "Músculo superficial posterior da perna, com cabeças medial e lateral",
    "Faz flexão plantar do tornozelo e auxilia a flexão do joelho.",
    "Côndilos medial e lateral do fêmur", "Calcâneo por meio do tendão calcâneo", "Nervo tibial",
)
STRUCTURES += muscle_pair(
    "soleo", "Sóleo", "soleus", "Membro inferior",
    "Músculo posterior profundo ao gastrocnêmio",
    "Realiza flexão plantar e é importante para a manutenção da postura em pé.",
    "Cabeça da fíbula e linha do sóleo da tíbia", "Calcâneo por meio do tendão calcâneo", "Nervo tibial",
)
STRUCTURES += muscle_pair(
    "tibial_anterior", "Tibial anterior", "tibialis anterior", "Membro inferior",
    "Músculo superficial do compartimento anterior da perna",
    "Dorsiflete e inverte o pé, além de sustentar o arco medial.",
    "Côndilo lateral e face lateral da tíbia", "Cuneiforme medial e base do 1º metatarsal",
    "Nervo fibular profundo",
)


_REGION_FUNCTIONS = {
    "Cabeça": "Participa da expressão facial, mastigação ou estabilização de estruturas da cabeça, conforme o músculo selecionado.",
    "Pescoço": "Move ou estabiliza a cabeça, o pescoço, o osso hioide ou a laringe, conforme o músculo selecionado.",
    "Dorso": "Move e estabiliza a coluna vertebral, a cabeça ou a cintura escapular, conforme o músculo selecionado.",
    "Tórax": "Participa da respiração ou dos movimentos da cintura escapular e do membro superior.",
    "Abdome, pelve e períneo": "Contribui para o movimento e a estabilização do tronco, da pelve ou do assoalho pélvico.",
    "Ombro e braço": "Move ou estabiliza a cintura escapular, o ombro ou o cotovelo.",
    "Antebraço": "Move ou estabiliza o cotovelo, o antebraço, o punho ou os dedos.",
    "Mão": "Move ou estabiliza o polegar, os dedos e as articulações da mão.",
    "Quadril e coxa": "Move ou estabiliza o quadril, a pelve ou o joelho.",
    "Perna": "Move ou estabiliza o joelho, o tornozelo ou o pé.",
    "Pé": "Move os dedos e contribui para a estabilização dos arcos do pé.",
}


def _bodyparts3d_muscle_structures() -> tuple[Structure, ...]:
    return tuple(
        Structure(
            identifier,
            name_pt,
            international_name,
            "Sistema muscular",
            f"Malha muscular individualizada da região {region.lower()}, identificada pela terminologia FMA.",
            _REGION_FUNCTIONS[region],
            (
                ("Nome internacional", international_name),
                ("Identificador FMA/BodyParts3D", mesh_id),
                ("Cobertura", "Malha primitiva do BodyParts3D 3.0"),
            ),
            region,
        )
        for identifier, name_pt, international_name, region, mesh_id in MUSCLE_MESHES
    )


# The compact procedural demo uses the curated entries above.  The detailed
# BodyParts3D model uses the primitive entries below, avoiding overlapping
# aggregate muscles while keeping every available component selectable.
STRUCTURES += _bodyparts3d_muscle_structures()

CATALOG = {structure.id: structure for structure in STRUCTURES}


def search_structures(query: str) -> tuple[Structure, ...]:
    normalized = query.strip().casefold()
    if not normalized:
        return STRUCTURES
    return tuple(item for item in STRUCTURES if normalized in item.search_text)
