from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StudyContent:
    """Portuguese study text derived from an anatomical name and system."""

    classification: str
    region: str
    description: str
    function: str


# TA2 is multilingual, but a few Portuguese cells are empty, still contain the
# English source label, or retain a non-Portuguese Latin label.  These overrides
# keep the student-facing interface consistently in Portuguese.  Latin remains
# available separately in Structure.latin_name.
PORTUGUESE_OVERRIDES: dict[str, str] = {
    "????????": "Estrutura não identificada na fonte",
    "?x": "Estrutura não identificada na fonte",
    "Atlas (C1)": "Atlas (C1)",
    "Incus": "Bigorna",
    "Talus": "Tálus",
    "Ulna": "Ulna",
    "Vertebra T10": "Vértebra T10",
    "Vertebra T11": "Vértebra T11",
    "(Opponens digiti minimi muscle of foot)": "Músculo oponente do dedo mínimo do pé",
    "Adductor longus": "Músculo adutor longo",
    "Extensor carpi radialis brevis": "Músculo extensor radial curto do carpo",
    "Extensor carpi radialis longus": "Músculo extensor radial longo do carpo",
    "Extensor digiti minimi": "Músculo extensor do dedo mínimo",
    "Extensor digitorum": "Músculo extensor dos dedos",
    "Extensor digitorum brevis": "Músculo extensor curto dos dedos",
    "Extensor digitorum longus": "Músculo extensor longo dos dedos",
    "Extensor hallucis brevis": "Músculo extensor curto do hálux",
    "Extensor hallucis longus": "Músculo extensor longo do hálux",
    "Extensor indicis": "Músculo extensor do indicador",
    "Extensor pollicis longus": "Músculo extensor longo do polegar",
    "Fascia lata": "Fáscia lata",
    "Flexor carpi radialis": "Músculo flexor radial do carpo",
    "Flexor digitorum brevis": "Músculo flexor curto dos dedos",
    "Flexor digitorum longus": "Músculo flexor longo dos dedos",
    "Flexor hallucis longus": "Músculo flexor longo do hálux",
    "Linea alba": "Linha alba",
    "Psoas major": "Músculo psoas maior",
    "Rotatores": "Músculos rotadores",
    "Semimembranosus bursa": "Bursa do músculo semimembranáceo",
    "Supinator": "Músculo supinador",
    "Cauda equina": "Cauda equina",
    "Chorda tympani": "Corda do tímpano",
    "Culmen": "Cúlmen",
    "Cuneus": "Cúneo",
    "Declive": "Declive do cerebelo",
    "Falx cerebri": "Foice do cérebro",
    "Flocculus": "Flóculo",
    "Fornix": "Fórnice",
    "Globus pallidus": "Globo pálido",
    "Habenula": "Habênula",
    "Nucleus proprius": "Núcleo próprio",
    "Pons": "Ponte",
    "Precuneus": "Pré-cúneo",
    "Putamen": "Putâmen",
    "Retina": "Retina",
    "Stria medullaris thalami": "Estria medular do tálamo",
    "Stria terminalis": "Estria terminal",
    "Tentorium cerebelli": "Tentório do cerebelo",
    "Thalamus": "Tálamo",
    "Ductus deferens": "Ducto deferente",
    "Glans penis": "Glande do pênis",
    "Pleura": "Pleura",
    "Testis": "Testículo",
    "Ureter": "Ureter",
    "Anterior occipital sulcus*": "Sulco occipital anterior",
    "Anterior temporal branch": "Ramo temporal anterior",
    "Artery of central sulcus": "Artéria do sulco central",
    "Artery of precentral sulcus": "Artéria do sulco pré-central",
    "Branch to angular gyrus": "Ramo para o giro angular",
    "Central canal'": "Canal central",
    "Cingulate gyrus (Posteroventral part*)": "Giro do cíngulo — parte posteroventral",
    "Cingulate gyrus and sulcus (Middle anterior part)": "Giro e sulco do cíngulo — parte média anterior",
    "Cingulate gyrus and sulcus (Middle posterior part)": "Giro e sulco do cíngulo — parte média posterior",
    "Cingulate gyrus and sulcus (Posterior dorsal part)": "Giro e sulco do cíngulo — parte posterodorsal",
    "Cingulate sulcus (Marginal part*)": "Sulco do cíngulo — parte marginal",
    "Coracobrachial bursa": "Bursa coracobraquial",
    "Cruciform part of fibrous sheath of digit of hand": "Parte cruciforme da bainha fibrosa do dedo da mão",
    "Distal lateral striate branches": "Ramos estriados laterais distais",
    "Frenula capsulae": "Frênulos da cápsula articular",
    "Inferior occipital gyrus and sulcus*": "Giro e sulco occipitais inferiores",
    "Inferior vein of left ventricle (//Posterior '')": "Veia inferior do ventrículo esquerdo",
    "Insula (Subcentral gyrus and ant. and post. sulci*)": "Ínsula — giro subcentral e sulcos anterior e posterior",
    "Insular branches of middle cerebral artery (M2-segment)": "Ramos insulares da artéria cerebral média — segmento M2",
    "Lat_Fis-ant-Horizont": "Ramo anterior horizontal do sulco lateral",
    "Lat_Fis-ant-Vertical": "Ramo anterior ascendente do sulco lateral",
    "Lat_Fis-post": "Ramo posterior do sulco lateral",
    "Lateral frontobasal artery": "Artéria frontobasal lateral",
    "Lateral occipital gyrus (Middle occipital gyrus*)": "Giro occipital lateral",
    "Lunate sulcus": "Sulco semilunar",
    "Medial occipitotemporal gyrus (Parahippocampal*)": "Giro occipitotemporal medial",
    "Middle cerebral artery (M3 segment)": "Artéria cerebral média — segmento M3",
    "Middle genicular artery": "Artéria genicular média",
    "Node of arch of azygos vein": "Linfonodo do arco da veia ázigos",
    "Node of ligamentum arteriosum": "Linfonodo do ligamento arterioso",
    "Occipitotemporal sulcus (Lateral part*)": "Sulco occipitotemporal — parte lateral",
    "Orbital gyri (Frontomarginal gyrus and sulcus*)": "Giros orbitais — giro e sulco frontomarginais",
    "Orbital part of  inferior frontal gyrus": "Parte orbital do giro frontal inferior",
    "Orbital sulci (H-shaped orbital sulci*)": "Sulcos orbitais em H",
    "Orbital sulci (Lateral Orbital sulcus*)": "Sulco orbital lateral",
    "Paracentral gyrus and sulcus*": "Giro e sulco paracentrais",
    "Posterior lateral nasal branches of sphenopalatine artery.": "Ramos nasais posterolaterais da artéria esfenopalatina",
    "Posterior parietal artery": "Artéria parietal posterior",
    "Posterior temporal branch": "Ramo temporal posterior",
    "Posterior transverse collateral sulcus": "Sulco colateral transverso posterior",
    "Precentral sulcus (inferior part)*": "Sulco pré-central — parte inferior",
    "Precentral sulcus (Superior part)*": "Sulco pré-central — parte superior",
    "Prefrontal artery": "Artéria pré-frontal",
    "Proximal lateral striate branches": "Ramos estriados laterais proximais",
    "Straight gyrus (Gyrus rectus)": "Giro reto",
    "Subcutaneous acromial bursa": "Bursa subcutânea acromial",
    "Subfacial prepatellar bursa": "Bursa pré-patelar subfascial",
    "Sulcus interm_prim-Jensen": "Sulco intermediário de Jensen",
    "Superior temporal gyrus (Lateral part)": "Giro temporal superior — parte lateral",
    "Temporo-occipital branch": "Ramo temporo-occipital",
    "Tendon sheath of extensors carpi radialis": "Bainha dos tendões dos extensores radiais do carpo",
    "Tendon sheath of tibialis anterior": "Bainha do tendão do tibial anterior",
    "Transverse frontopolar gyrus and sulcus*": "Giro e sulco frontopolares transversos",
    "Trochanteric bursa of gluteus medius muscle": "Bursa trocantérica do músculo glúteo médio",
}


def portuguese_name(source_name: str, ta2_name: str | None) -> str:
    """Prefer a reviewed override, then TA2, never an English fallback."""
    if source_name in PORTUGUESE_OVERRIDES:
        return PORTUGUESE_OVERRIDES[source_name]
    if ta2_name and ta2_name.strip():
        return ta2_name.strip()
    return "Estrutura anatômica sem tradução validada"


def _contains(name: str, *terms: str) -> bool:
    return any(term in name for term in terms)


_REGION_TERMS = (
    (
        "Cabeça",
        (
            "brain", "cerebr", "cerebell", "cran", "skull", "facial", "eye",
            "ocular", "orbit", "ear", "tympan", "nasal", "tongue", "tooth",
            "premolar", "mandib", "maxill", "ethmoid", "incus", "malleus",
            "stapes", "cochlea", "vestibule", "parotid", "temporal", "occipital",
            "frontal", "parietal", "meningeal", "trigeminal", "gyrus", "sulcus",
            "lobule", "vermis", "geniculate", "pallid",
        ),
    ),
    (
        "Pescoço",
        ("neck", "cervic", "pharyn", "laryn", "thyroid", "hyoid", "arytenoid", "jugular"),
    ),
    (
        "Tórax",
        (
            "thorac", "rib", "costal", "intercost", "stern", "lung", "bronch",
            "cardiac", "heart", "mediast", "coronary", "ventric",
            "atrioventricular", "pulmonary", "pericard", "azygos", "vena cava",
            "thymus",
        ),
    ),
    (
        "Abdome",
        (
            "abdomin", "gastr", "stomach", "hepatic", "liver", "splen", "pancrea",
            "duoden", "jejun", "ileum", "ileocol", "colic", "colon", "mesenter",
            "caec", "renal", "kidney", "spleen",
        ),
    ),
    (
        "Pelve e períneo",
        (
            "pelvi", "perine", "rect", "anal", "bladder", "prostat", "uter",
            "vagin", "penis", "test", "ovary", "iliac", "inguinal", "obturator",
            "vesical",
        ),
    ),
    (
        "Ombro",
        (
            "scapul", "clavicul", "shoulder", "acrom", "deltoid", "infraspinatus",
            "teres major", "trapezius", "axilla",
        ),
    ),
    (
        "Membro superior",
        (
            "brachi", "humer", "elbow", "forearm", "radial", "ulnar", "carp",
            "hand", "finger", "digit", "pollic", "scapho", "triquetr", "pisotri",
            "interosseous artery", "flexor tendon",
        ),
    ),
    (
        "Membro inferior",
        (
            "femor", "thigh", "hip", "knee", "patell", "tibia", "fibul", "ankle",
            "malleol", "tars", "foot", "toe", "leg", "halluc", "calcane", "cuneo",
            "cuboid", "navicular", "plantar", "poplite", "trochanter", "glute",
            "genicular",
        ),
    ),
    (
        "Dorso e coluna",
        (
            "vertebr", "spinal", "lumbar", "sacral", "sacro-iliac", "coccy", "back",
            "nucleus pulposus",
        ),
    ),
)


def _body_region(name: str, reference: str = "") -> str:
    # Prefer the concise anatomical label.  Definitions often mention several
    # regions (for example, the vena cava drains head, neck and upper limbs), so
    # they are only a fallback and require a word boundary to avoid accidental
    # matches such as "eye" inside "they" or "rib" inside "describe".
    for region, terms in _REGION_TERMS:
        if _contains(name, *terms):
            return region
    nearest: tuple[int, str] | None = None
    for region, terms in _REGION_TERMS:
        for term in terms:
            match = re.search(rf"\b{re.escape(term)}", reference)
            if match is not None and (nearest is None or match.start() < nearest[0]):
                nearest = match.start(), region
    if nearest is not None:
        return nearest[1]
    return "Não especificada"


def _location_phrase(region: str) -> str:
    return {
        "Cabeça": "na cabeça",
        "Pescoço": "no pescoço",
        "Tórax": "no tórax",
        "Abdome": "no abdome",
        "Pelve e períneo": "na pelve e no períneo",
        "Ombro": "no ombro",
        "Membro superior": "no membro superior",
        "Membro inferior": "no membro inferior",
        "Dorso e coluna": "no dorso e na coluna vertebral",
    }.get(region, "em região não especificada pela fonte")


def _muscle_action(name: str) -> str:
    specific_actions = (
        (("biceps brachii",), "Flexiona o cotovelo e realiza supinação do antebraço."),
        (("triceps brachii",), "Estende o cotovelo; a cabeça longa também auxilia a extensão e a adução do ombro."),
        (("deltoid",), "Abduz o braço; suas porções anterior e posterior também participam da flexão, extensão e rotação do ombro."),
        (("pectoralis major",), "Aduz e roda medialmente o braço; a porção clavicular auxilia a flexão do ombro."),
        (("pectoralis minor",), "Estabiliza e traciona a escápula anteriormente e para baixo."),
        (("latissimus dorsi",), "Estende, aduz e roda medialmente o braço."),
        (("trapezius",), "Eleva, retrai, deprime e roda superiormente a escápula, conforme a porção ativada."),
        (("sternocleidomastoid",), "Inclina a cabeça para o mesmo lado, roda-a para o lado oposto e auxilia a flexão cervical."),
        (("masseter",), "Eleva a mandíbula e auxilia sua protrusão durante a mastigação."),
        (("temporalis",), "Eleva a mandíbula; suas fibras posteriores também fazem retrusão."),
        (("rectus abdominis",), "Flexiona o tronco, comprime as vísceras abdominais e auxilia a estabilização da pelve."),
        (("diaphragm",), "É o principal músculo da inspiração e aumenta o volume da cavidade torácica ao contrair."),
        (("gluteus maximus",), "Estende e roda lateralmente a coxa e auxilia a estabilização do quadril e do joelho."),
        (("gluteus medius", "gluteus minimus"), "Abduz e roda medialmente a coxa e mantém a pelve nivelada durante a marcha."),
        (("sartorius",), "Flexiona, abduz e roda lateralmente o quadril e também flexiona o joelho."),
        (("rectus femoris", "vastus lateralis", "vastus medialis", "vastus intermedius"), "Integra o quadríceps e estende o joelho; o reto femoral também flexiona o quadril."),
        (("biceps femoris", "semitendinosus", "semimembranosus"), "Integra os isquiotibiais, estende o quadril e flexiona o joelho."),
        (("gastrocnemius",), "Realiza flexão plantar do tornozelo e auxilia a flexão do joelho."),
        (("soleus",), "Realiza flexão plantar e contribui de modo importante para a manutenção da postura em pé."),
        (("tibialis anterior",), "Dorsiflete e inverte o pé e auxilia a sustentação do arco medial."),
        (("fibularis longus", "fibularis brevis"), "Evertem o pé e auxiliam a flexão plantar e a estabilidade lateral do tornozelo."),
    )
    for terms, action in specific_actions:
        if _contains(name, *terms):
            return action
    actions = (
        (("flexor",), "produz ou auxilia a flexão da articulação relacionada"),
        (("extensor",), "produz ou auxilia a extensão da articulação relacionada"),
        (("abductor",), "afasta o segmento corporal do plano ou eixo de referência"),
        (("adductor",), "aproxima o segmento corporal do plano ou eixo de referência"),
        (("levator",), "eleva a estrutura em que se insere"),
        (("depressor",), "deprime a estrutura em que se insere"),
        (("pronator",), "participa da pronação"),
        (("supinator",), "participa da supinação"),
        (("sphincter",), "fecha ou controla a abertura que circunda"),
        (("dilator",), "aumenta o calibre da abertura relacionada"),
        (("constrictor",), "reduz o calibre da passagem relacionada"),
        (("rotator",), "produz ou auxilia a rotação do segmento relacionado"),
        (("tensor",), "tensiona e estabiliza a estrutura em que se insere"),
        (("opponens",), "produz o movimento de oposição do dedo relacionado"),
    )
    for terms, action in actions:
        if _contains(name, *terms):
            return action.capitalize() + "."
    return "Produz força por contração e participa do movimento ou da estabilização da região indicada pelo nome."


def _nerve_function(name: str) -> str:
    specific_functions = (
        (("olfactory nerve",), "Conduz informações relacionadas ao olfato."),
        (("optic nerve",), "Conduz informações visuais da retina ao encéfalo."),
        (("oculomotor nerve",), "Inerva a maior parte dos músculos extrínsecos do olho e conduz fibras parassimpáticas para a pupila."),
        (("trochlear nerve",), "Fornece inervação motora ao músculo oblíquo superior do olho."),
        (("trigeminal nerve",), "Conduz a sensibilidade principal da face e fornece inervação motora aos músculos da mastigação."),
        (("abducens nerve",), "Fornece inervação motora ao músculo reto lateral e participa da abdução do olho."),
        (("facial nerve",), "Inerva músculos da expressão facial e conduz fibras gustativas e parassimpáticas."),
        (("vestibulocochlear nerve",), "Conduz informações relacionadas à audição e ao equilíbrio."),
        (("glossopharyngeal nerve",), "Conduz sensibilidade e paladar da orofaringe e participa da deglutição e de funções parassimpáticas."),
        (("vagus nerve",), "Fornece inervação parassimpática extensa às vísceras torácicas e abdominais e participa de funções faríngeas e laríngeas."),
        (("accessory nerve",), "Fornece inervação motora principalmente ao esternocleidomastóideo e ao trapézio."),
        (("hypoglossal nerve",), "Fornece inervação motora aos músculos da língua."),
        (("median nerve",), "Inerva a maior parte dos flexores do antebraço, músculos tenares e território sensitivo lateral da mão."),
        (("ulnar nerve",), "Inerva músculos do antebraço e grande parte dos músculos intrínsecos da mão, além de território sensitivo medial da mão."),
        (("radial nerve",), "Inerva músculos extensores do membro superior e conduz sensibilidade de parte de sua face posterior."),
        (("femoral nerve",), "Inerva músculos do compartimento anterior da coxa e conduz sensibilidade da face anterior da coxa e medial da perna."),
        (("sciatic nerve",), "Inerva músculos posteriores da coxa e dá origem às principais vias motoras e sensitivas da perna e do pé."),
        (("tibial nerve",), "Inerva músculos posteriores da perna e planta do pé e conduz sensibilidade plantar."),
        (("common fibular nerve", "common peroneal nerve"), "Distribui fibras para os compartimentos anterior e lateral da perna e para o dorso do pé."),
    )
    for terms, function in specific_functions:
        if _contains(name, *terms):
            return function
    return "Conduz impulsos sensitivos, motores ou autonômicos entre o sistema nervoso central e o território indicado pelo nome."


def build_study_content(
    display_name: str,
    source_name: str,
    system: str,
    source_reference: str = "",
) -> StudyContent:
    """Build concise, wholly Portuguese content for every atlas structure."""
    key = source_name.casefold()
    # Location phrases in the source definition help classify terse labels such
    # as "Declive".  The source prose itself is never displayed.
    region = _body_region(key, source_reference[:800].casefold())
    location = _location_phrase(region)

    if system == "Sistema esquelético":
        is_part = _contains(
            key,
            "process", "surface", "border", "angle", "head of", "neck of",
            "part of", "canal", "foramen", "fossa", "notch", "crest",
        )
        if _contains(key, "cartilage"):
            classification = "Cartilagem"
            description = (
                f"{display_name}: tecido cartilaginoso do sistema esquelético, "
                f"com localização {location}."
            )
            function = "Oferece suporte flexível, mantém a forma regional e pode servir de ponto de fixação para tecidos moles."
        elif _contains(key, "tooth", "premolar", "molar", "incisor", "canine"):
            classification = "Dente"
            description = (
                f"{display_name}: tecido mineralizado da dentição, com localização "
                f"{location}."
            )
            function = "Participa da apreensão ou trituração dos alimentos e auxilia a articulação da fala."
        else:
            classification = "Acidente ou parte óssea" if is_part else "Osso"
            description = (
                f"{display_name}: tecido mineralizado do sistema esquelético, "
                f"com localização {location}. "
                + (
                    "Corresponde a uma parte ou referência morfológica de um osso."
                    if is_part
                    else "Integra o arcabouço rígido do corpo e estabelece relações com articulações e inserções musculares."
                )
            )
            function = "Atua na sustentação e proteção e pode servir de alavanca, superfície articular ou ponto de fixação para tecidos moles."
    elif system == "Articulações, ligamentos e fáscias":
        if _contains(key, "bursa"):
            classification = "Bursa sinovial"
            description = f"{display_name}: tecido revestido por membrana sinovial {location}, situado entre estruturas sujeitas a atrito."
            function = "Reduz o atrito e facilita o deslizamento entre tendões, músculos, ossos ou pele."
        elif _contains(key, "ligament"):
            classification = "Ligamento"
            description = f"{display_name}: tecido conjuntivo resistente {location}, responsável por conectar e orientar estruturas do aparelho locomotor."
            function = "Estabiliza a articulação, limita movimentos excessivos e orienta o movimento fisiológico."
        elif _contains(key, "fascia", "retinaculum", "fibrous sheath", "aponeuros"):
            classification = "Fáscia ou bainha fibrosa"
            description = f"{display_name}: tecido conjuntivo organizado {location}, associado ao revestimento, contenção ou transmissão de forças."
            function = "Reveste e separa estruturas, mantém tendões em posição ou distribui forças mecânicas."
        elif _contains(key, "cartilage", "disc", "meniscus", "labrum"):
            classification = "Cartilagem ou fibrocartilagem"
            description = f"{display_name}: tecido cartilaginoso {location}, relacionado a uma superfície ou cavidade articular."
            function = "Distribui cargas, melhora a congruência articular e reduz o atrito durante o movimento."
        else:
            classification = "Articulação ou componente articular"
            description = f"{display_name}: componente do complexo articular {location}, participante da união entre estruturas do esqueleto."
            function = "Permite e orienta movimento, transmite cargas e contribui para a estabilidade regional."
    elif system == "Sistema muscular":
        if _contains(key, "tendon", "aponeuros"):
            classification = "Tendão ou aponeurose"
            description = f"{display_name}: tecido conjuntivo denso {location}, associado à transmissão da força muscular."
            function = "Transmite ao esqueleto ou a outros tecidos a força produzida pelo músculo."
        elif _contains(key, "fascia", "bursa"):
            classification = "Estrutura associada ao músculo"
            description = f"{display_name}: tecido conjuntivo associado ao sistema muscular {location}."
            function = "Reveste, protege ou facilita o deslizamento das estruturas musculares relacionadas."
        else:
            classification = "Músculo esquelético"
            description = f"{display_name}: tecido muscular estriado esquelético {location}, organizado para produzir força entre seus pontos de fixação."
            function = _muscle_action(key)
    elif system == "Sistema cardiovascular":
        if _contains(key, "artery", "arterial", "aorta"):
            classification = "Artéria ou ramo arterial"
            description = f"{display_name}: estrutura vascular do sistema arterial {location}, com parede adaptada à condução de sangue sob pressão."
            function = "Conduz sangue para o território indicado pelo nome e participa de sua irrigação."
        elif _contains(key, "vein", "venous", "vena", "sinus"):
            classification = "Veia ou tributária venosa"
            description = f"{display_name}: estrutura vascular do sistema venoso {location}, integrante da rede de drenagem sanguínea."
            function = "Drena o território indicado pelo nome e conduz o sangue em direção a vasos venosos de maior calibre e ao coração."
        elif _contains(key, "valve"):
            classification = "Valva cardíaca"
            description = f"{display_name}: tecido valvar do coração que se movimenta conforme as diferenças de pressão."
            function = "Favorece o fluxo sanguíneo em um único sentido e reduz o refluxo entre câmaras ou grandes vasos."
        else:
            classification = "Estrutura cardíaca ou vascular"
            description = f"{display_name}: componente do sistema cardiovascular {location}, participante do circuito de circulação do sangue."
            function = "Contribui para impulsionar, distribuir, receber ou direcionar o sangue, conforme sua posição anatômica."
    elif system == "Sistema linfático":
        if _contains(key, "node"):
            classification = "Linfonodo"
            description = f"{display_name}: tecido linfoide encapsulado {location}, interposto no trajeto dos vasos linfáticos."
            function = "Filtra a linfa e oferece um local para reconhecimento e resposta de células do sistema imune."
        elif _contains(key, "vessel", "duct", "trunk"):
            classification = "Vaso linfático"
            description = f"{display_name}: componente da rede de vasos linfáticos {location}."
            function = "Conduz linfa e contribui para devolver ao sangue líquido e macromoléculas provenientes dos tecidos."
        else:
            classification = "Órgão ou tecido linfoide"
            description = f"{display_name}: componente do sistema linfático e imune {location}."
            function = "Participa da vigilância imunológica, da produção ou maturação de células imunes ou da drenagem linfática."
    elif system == "Sistema nervoso":
        if _contains(key, "nerve", "branch", "ramus", "root"):
            classification = "Nervo, raiz ou ramo nervoso"
            description = f"{display_name}: feixe de fibras do sistema nervoso {location}, associado a trajeto e território próprios."
            function = _nerve_function(key)
        elif _contains(key, "ganglion"):
            classification = "Gânglio nervoso"
            description = f"{display_name}: agrupamento de corpos celulares neuronais fora do sistema nervoso central, com localização {location}."
            function = "Participa do processamento ou retransmissão de sinais sensitivos ou autonômicos."
        elif _contains(key, "plexus"):
            classification = "Plexo nervoso"
            description = f"{display_name}: rede de fibras nervosas interconectadas {location}."
            function = "Redistribui fibras nervosas e forma trajetos destinados a diferentes territórios."
        elif _contains(key, "gyrus", "sulcus", "cortex", "nucleus", "brain", "cerebr", "thalam", "pons", "medulla"):
            classification = "Estrutura do sistema nervoso central"
            description = f"{display_name}: região individualizada do sistema nervoso central, com localização {location}."
            function = "Participa da integração e do processamento neural; a modalidade predominante depende dos circuitos aos quais se conecta."
        elif _contains(key, "tract", "fascicul", "commissure", "radiation", "capsule"):
            classification = "Via nervosa central"
            description = f"{display_name}: conjunto organizado de fibras nervosas no sistema nervoso central."
            function = "Conecta regiões neurais e conduz informação entre os centros indicados por seu trajeto anatômico."
        else:
            classification = "Estrutura do sistema nervoso"
            description = f"{display_name}: componente do sistema nervoso {location}, com relações próprias com vias ou centros neurais."
            function = "Participa da recepção, condução, integração ou resposta a sinais nervosos."
    else:
        organ_functions = (
            (("kidney", "renal"), "Filtra o sangue, regula água e eletrólitos e participa da formação da urina."),
            (("lung",), "Realiza trocas gasosas entre o ar e o sangue."),
            (("liver", "hepatic"), "Participa do metabolismo, da síntese de proteínas plasmáticas, da detoxificação e da produção de bile."),
            (("pancrea",), "Produz secreções digestivas e hormônios relacionados ao controle da glicemia."),
            (("stomach", "gastric"), "Armazena e mistura o alimento e inicia etapas mecânicas e químicas da digestão."),
            (("intestin", "duoden", "jejun", "ileum", "colon"), "Participa da digestão, absorção ou condução do conteúdo intestinal, conforme o segmento."),
            (("bladder",), "Armazena temporariamente a urina e participa de sua eliminação."),
            (("ureter",), "Conduz a urina do rim até a bexiga por movimentos peristálticos."),
            (("testis",), "Produz espermatozoides e hormônios sexuais masculinos."),
            (("prostate",), "Produz parte do líquido seminal e participa do sistema reprodutor masculino."),
        )
        function = "Exerce a função especializada do órgão ou componente visceral indicado pelo nome."
        for terms, candidate in organ_functions:
            if _contains(key, *terms):
                function = candidate
                break
        classification = "Órgão ou componente visceral"
        description = f"{display_name}: estrutura visceral com localização {location}, organização anatômica própria e relações com órgãos, vasos e nervos vizinhos."

    return StudyContent(classification, region, description, function)
