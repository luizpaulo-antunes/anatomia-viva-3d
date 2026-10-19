#!/usr/bin/env python3
"""Generate the checked-in BodyParts3D muscle manifest from upstream metadata.

The source files are distributed by the BodyParts3D v3 STL mirror.  Keeping the
result as a small Python module lets the application work offline while this
script records exactly how the list was selected.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict, deque
from pathlib import Path


CONNECTIVE_TISSUE_WORDS = (
    "aponeurosis",
    "fascia",
    "iliotibial tract",
    "ligament",
    "linea alba",
    "retinaculum",
    "tendon",
    "tendinous",
)

# Exact anatomical translations for names that are not assembled from a
# part/head/belly prefix below.  The English FMA term is also retained in the
# generated catalog, so no source terminology is lost.
PT = {
    "abductor digiti minimi of foot": "abdutor do dedo mínimo do pé",
    "abductor digiti minimi of hand": "abdutor do dedo mínimo da mão",
    "abductor hallucis": "abdutor do hálux",
    "abductor pollicis brevis": "abdutor curto do polegar",
    "abductor pollicis longus": "abdutor longo do polegar",
    "adductor brevis": "adutor curto",
    "adductor longus": "adutor longo",
    "adductor magnus": "adutor magno",
    "adductor minimus": "adutor mínimo",
    "adductor hallucis": "adutor do hálux",
    "adductor pollicis": "adutor do polegar",
    "anconeus": "ancôneo",
    "brachialis": "braquial",
    "brachioradialis": "braquiorradial",
    "buccinator": "bucinador",
    "cervical rotator": "rotador cervical",
    "coccygeus": "coccígeo",
    "coracobrachialis": "coracobraquial",
    "corrugator supercilii": "corrugador do supercílio",
    "depressor anguli oris": "depressor do ângulo da boca",
    "depressor labii inferioris": "depressor do lábio inferior",
    "depressor septi nasi": "depressor do septo nasal",
    "deltoid": "deltoide",
    "diaphragm": "diafragma",
    "digastric": "digástrico",
    "extensor carpi radialis brevis": "extensor radial curto do carpo",
    "extensor carpi radialis longus": "extensor radial longo do carpo",
    "extensor carpi ulnaris": "extensor ulnar do carpo",
    "extensor digiti minimi": "extensor do dedo mínimo",
    "extensor digitorum": "extensor dos dedos",
    "extensor digitorum brevis": "extensor curto dos dedos",
    "extensor digitorum longus": "extensor longo dos dedos",
    "extensor hallucis brevis": "extensor curto do hálux",
    "extensor hallucis longus": "extensor longo do hálux",
    "extensor indicis": "extensor do indicador",
    "extensor pollicis brevis": "extensor curto do polegar",
    "extensor pollicis longus": "extensor longo do polegar",
    "external anal sphincter": "esfíncter externo do ânus",
    "external intercostal muscle": "músculos intercostais externos",
    "external oblique": "oblíquo externo do abdome",
    "fibularis brevis": "fibular curto",
    "fibularis longus": "fibular longo",
    "fibularis tertius": "fibular terceiro",
    "flexor accessorius": "quadrado plantar (flexor acessório)",
    "flexor carpi radialis": "flexor radial do carpo",
    "flexor carpi ulnaris": "flexor ulnar do carpo",
    "flexor digiti minimi brevis of foot": "flexor curto do dedo mínimo do pé",
    "flexor digiti minimi brevis of hand": "flexor curto do dedo mínimo da mão",
    "flexor digitorum brevis": "flexor curto dos dedos",
    "flexor digitorum longus": "flexor longo dos dedos",
    "flexor digitorum profundus": "flexor profundo dos dedos",
    "flexor digitorum superficialis": "flexor superficial dos dedos",
    "flexor hallucis brevis": "flexor curto do hálux",
    "flexor hallucis longus": "flexor longo do hálux",
    "flexor pollicis brevis": "flexor curto do polegar",
    "flexor pollicis longus": "flexor longo do polegar",
    "frontalis": "frontal",
    "gastrocnemius": "gastrocnêmio",
    "gemellus inferior": "gêmeo inferior",
    "gemellus superior": "gêmeo superior",
    "geniohyoid": "gênio-hióideo",
    "gluteus maximus": "glúteo máximo",
    "gluteus medius": "glúteo médio",
    "gluteus minimus": "glúteo mínimo",
    "gracilis": "grácil",
    "iliacus": "ilíaco",
    "iliococcygeus": "iliococcígeo",
    "iliocostalis cervicis": "iliocostal cervical",
    "iliocostalis lumborum": "iliocostal lombar",
    "iliocostalis thoracis": "iliocostal torácico",
    "infraspinatus muscle": "infraespinal",
    "innermost intercostal muscle": "músculos intercostais íntimos",
    "internal intercostal muscle": "músculos intercostais internos",
    "internal oblique": "oblíquo interno do abdome",
    "lateral pterygoid": "pterigóideo lateral",
    "latissimus dorsi": "latíssimo do dorso",
    "levator anguli oris": "levantador do ângulo da boca",
    "levator labii superioris": "levantador do lábio superior",
    "levator labii superioris alaeque nasi": "levantador do lábio superior e da asa do nariz",
    "levator scapulae": "levantador da escápula",
    "longissimus capitis": "longuíssimo da cabeça",
    "longissimus cervicis": "longuíssimo cervical",
    "longissimus thoracis": "longuíssimo torácico",
    "longus capitis": "longo da cabeça",
    "longus colli": "longo do pescoço",
    "lumbar rotator": "rotador lombar",
    "masseter": "masseter",
    "medial pterygoid": "pterigóideo medial",
    "mentalis": "mentual",
    "multifidus": "multífido",
    "mylohyoid": "milo-hióideo",
    "nasalis": "nasal",
    "obliquus capitis inferior": "oblíquo inferior da cabeça",
    "obliquus capitis superior": "oblíquo superior da cabeça",
    "obturator externus": "obturador externo",
    "obturator internus": "obturador interno",
    "occipitalis": "occipital",
    "omohyoid": "omo-hióideo",
    "opponens digiti minimi of foot": "oponente do dedo mínimo do pé",
    "opponens digiti minimi of hand": "oponente do dedo mínimo da mão",
    "opponens pollicis": "oponente do polegar",
    "orbicularis oculi": "orbicular do olho",
    "orbicularis oris": "orbicular da boca",
    "palmaris longus": "palmar longo",
    "pectineus": "pectíneo",
    "pectoralis major": "peitoral maior",
    "pectoralis minor": "peitoral menor",
    "piriformis": "piriforme",
    "plantaris": "plantar",
    "platysma": "platisma",
    "popliteus": "poplíteo",
    "procerus": "prócero",
    "pronator quadratus": "pronador quadrado",
    "pronator teres": "pronador redondo",
    "psoas major": "psoas maior",
    "pubococcygeus": "pubococcígeo",
    "puborectalis": "puborretal",
    "pyramidalis": "piramidal",
    "quadratus femoris": "quadrado femoral",
    "quadratus lumborum": "quadrado lombar",
    "rectus abdominis": "reto do abdome",
    "rectus capitis anterior": "reto anterior da cabeça",
    "rectus capitis lateralis": "reto lateral da cabeça",
    "rectus capitis posterior major": "reto posterior maior da cabeça",
    "rectus capitis posterior minor": "reto posterior menor da cabeça",
    "rectus femoris": "reto femoral",
    "rhomboid major": "romboide maior",
    "rhomboid minor": "romboide menor",
    "risorius": "risório",
    "sartorius": "sartório",
    "scalenus anterior": "escaleno anterior",
    "scalenus medius": "escaleno médio",
    "scalenus posterior": "escaleno posterior",
    "semimembranosus": "semimembranáceo",
    "semispinalis capitis": "semiespinal da cabeça",
    "semispinalis cervicis": "semiespinal cervical",
    "semispinalis thoracis": "semiespinal torácico",
    "semitendinosus": "semitendíneo",
    "serratus anterior": "serrátil anterior",
    "serratus posterior inferior": "serrátil posterior inferior",
    "serratus posterior superior": "serrátil posterior superior",
    "soleus": "sóleo",
    "spinalis cervicis": "espinal cervical",
    "spinalis thoracis": "espinal torácico",
    "splenius capitis": "esplênio da cabeça",
    "splenius cervicis": "esplênio cervical",
    "sternocleidomastoid": "esternocleidomastóideo",
    "sternohyoid": "esterno-hióideo",
    "sternothyroid": "esternotireóideo",
    "stylohyoid": "estilo-hióideo",
    "subclavius": "subclávio",
    "subscapularis": "subescapular",
    "supinator": "supinador",
    "supraspinatus": "supraespinal",
    "temporalis": "temporal",
    "temporoparietalis": "temporoparietal",
    "tensor fasciae latae": "tensor da fáscia lata",
    "teres major": "redondo maior",
    "teres minor": "redondo menor",
    "thoracic rotator": "rotador torácico",
    "thyrohyoid": "tireo-hióideo",
    "tibialis anterior": "tibial anterior",
    "tibialis posterior": "tibial posterior",
    "trapezius": "trapézio",
    "transversus abdominis": "transverso do abdome",
    "transversus thoracis": "transverso do tórax",
    "triceps brachii": "tríceps braquial",
    "biceps brachii": "bíceps braquial",
    "biceps femoris": "bíceps femoral",
    "vastus intermedius": "vasto intermédio",
    "vastus lateralis": "vasto lateral",
    "vastus medialis": "vasto medial",
    "zygomaticus major": "zigomático maior",
    "zygomaticus minor": "zigomático menor",
}

PART_ADJECTIVES = {
    "abdominal": "abdominal",
    "acromial": "acromial",
    "ascending": "ascendente",
    "clavicular": "clavicular",
    "deep": "profunda",
    "descending": "descendente",
    "inferior oblique": "oblíqua inferior",
    "orbital": "orbital",
    "palpebral": "palpebral",
    "spinal": "espinal",
    "sternocostal": "esternocostal",
    "superficial": "superficial",
    "superior oblique": "oblíqua superior",
    "transverse": "transversa",
    "vertical intermediate": "vertical intermédia",
}
HEAD_ADJECTIVES = {
    "deep": "profunda",
    "humeral": "umeral",
    "humeroulnar": "umeroulnar",
    "lateral": "lateral",
    "long": "longa",
    "lower": "inferior",
    "medial": "medial",
    "oblique": "oblíqua",
    "radial": "radial",
    "short": "curta",
    "superficial": "superficial",
    "transverse": "transversa",
    "ulnar": "ulnar",
    "upper": "superior",
}
ORDINALS = {"first": "primeiro", "second": "segundo", "third": "terceiro", "fourth": "quarto"}


def translated_base(name: str) -> str:
    if name in PT:
        return PT[name]
    match = re.fullmatch(r"(.+) interossei of (hand|foot)", name)
    if match:
        kind = {"dorsal": "interósseos dorsais", "palmar": "interósseos palmares", "plantar": "interósseos plantares"}[match.group(1)]
        return f"{kind} da {'mão' if match.group(2) == 'hand' else 'pé'}"
    if name == "lumbricals of hand":
        return "lumbricais da mão"
    if name.startswith("interspinales "):
        return "interespinais " + {"cervicis": "cervicais", "lumborum": "lombares", "thoracis": "torácicos"}[name.split()[-1]]
    if name == "anterior cervical intertransversarii":
        return "intertransversários cervicais anteriores"
    if name == "posterior cervical intertransversarii":
        return "intertransversários cervicais posteriores"
    if name == "lateral lumbar intertransversarius muscles":
        return "intertransversários lombares laterais"
    if name == "medial lumbar intertransversarius muscles":
        return "intertransversários lombares mediais"
    if name == "levatores costarum breves":
        return "levantadores curtos das costelas"
    if name == "levatores costarum longi":
        return "levantadores longos das costelas"
    raise KeyError(f"Tradução ausente: {name}")


def translate_name(source: str) -> tuple[str, str | None]:
    side: str | None = None
    if re.search(r"\bright\b", source):
        side = "direito"
    elif re.search(r"\bleft\b", source):
        side = "esquerdo"
    base = re.sub(r"\b(right|left)\b", "", source.lower())
    base = re.sub(r"\s+", " ", base).strip()

    match = re.fullmatch(r"(.+) part of (.+)", base)
    if match and match.group(1) in PART_ADJECTIVES:
        translated = f"porção {PART_ADJECTIVES[match.group(1)]} do {translated_base(match.group(2))}"
    else:
        match = re.fullmatch(r"(.+) head of (.+)", base)
        if match and match.group(1) in HEAD_ADJECTIVES:
            translated = f"cabeça {HEAD_ADJECTIVES[match.group(1)]} do {translated_base(match.group(2))}"
        else:
            match = re.fullmatch(r"(anterior|posterior) belly of (.+)", base)
            if match:
                adjective = "anterior" if match.group(1) == "anterior" else "posterior"
                translated = f"ventre {adjective} do {translated_base(match.group(2))}"
            else:
                match = re.fullmatch(r"(first|second|third|fourth) (lumbrical|plantar interosseous) of foot", base)
                if match:
                    muscle = "lumbrical" if match.group(2) == "lumbrical" else "interósseo plantar"
                    translated = f"{ORDINALS[match.group(1)]} {muscle} do pé"
                elif base.startswith("set of "):
                    translated = "conjunto dos " + translated_base(base.removeprefix("set of "))
                else:
                    translated = translated_base(base)

    if side:
        translated += f" — lado {side}"
    return translated[0].upper() + translated[1:], side


def region_for(name: str, ancestors: set[str]) -> str:
    lowered = name.lower()
    normalized = re.sub(r"\b(right|left)\b", "", lowered)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if "FMA71287" in ancestors:
        return "Cabeça"
    if "FMA71290" in ancestors:
        return "Pescoço"
    if "FMA71291" in ancestors:
        return "Dorso"
    if "FMA71293" in ancestors:
        return "Tórax"
    if "FMA86917" in ancestors or "FMA71295" in ancestors:
        return "Abdome, pelve e períneo"
    if "FMA9621" in ancestors:
        if any(word in normalized for word in (
            "carpi", "digitorum", "indicis", "pronator", "supinator", "brachioradialis",
            "pollicis longus", "extensor pollicis",
        )):
            return "Antebraço"
        if any(word in normalized for word in ("pollic", "of hand", "lumbrical", "palmar interosse")):
            return "Mão"
        return "Ombro e braço"
    if "FMA9622" in ancestors:
        if any(word in normalized for word in (
            "tibialis", "fibularis", "gastrocnemius", "soleus", "plantaris", "popliteus",
            "digitorum longus", "hallucis longus",
        )):
            return "Perna"
        if any(word in normalized for word in ("of foot", "halluc", "lumbrical", "interosse", "flexor accessorius")):
            return "Pé"
        return "Quadril e coxa"
    return "Outros músculos"


def read_names(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as file:
        rows = csv.reader(file, delimiter="\t")
        next(rows)
        return {row[0]: row[1] for row in rows if len(row) >= 2}


def read_relations(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    children: dict[str, set[str]] = defaultdict(set)
    parents: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8") as file:
        rows = csv.reader(file, delimiter="\t")
        next(rows)
        for row in rows:
            if len(row) >= 4:
                children[row[0]].add(row[2])
                parents[row[2]].add(row[0])
    return children, parents


def closure(start: str, graph: dict[str, set[str]]) -> set[str]:
    found: set[str] = set()
    queue = deque([start])
    while queue:
        item = queue.popleft()
        if item in found:
            continue
        found.add(item)
        queue.extend(graph[item])
    return found


def generate(parts: Path, relations: Path, tree_file: Path, output: Path) -> int:
    names = read_names(parts)
    children, parents = read_relations(relations)
    tree = json.loads(tree_file.read_text(encoding="utf-8"))["tree"]
    stl_ids = {
        Path(item["path"]).stem
        for item in tree
        if item["path"].startswith("assets/BodyParts3D_data/stl/")
        and item["path"].endswith(".stl")
    }
    muscular = closure("FMA72954", children)
    identifiers = sorted(
        (
            item
            for item in muscular & stl_ids
            if not any(word in names[item].lower() for word in CONNECTIVE_TISSUE_WORDS)
        ),
        key=lambda item: (region_for(names[item], closure(item, parents)), names[item], item),
    )

    rows = []
    for fma_id in identifiers:
        name_pt, _side = translate_name(names[fma_id])
        rows.append(
            (
                "muscle_" + re.sub(r"[^a-z0-9]+", "_", fma_id.lower()).strip("_"),
                name_pt,
                names[fma_id],
                region_for(names[fma_id], closure(fma_id, parents)),
                fma_id,
            )
        )

    lines = [
        '"""Generated BodyParts3D/FMA muscle mesh catalog; do not edit by hand."""',
        "",
        "# (application id, Portuguese name, FMA/international name, region, mesh id)",
        "MUSCLE_MESHES: tuple[tuple[str, str, str, str, str], ...] = (",
    ]
    lines.extend(f"    {row!r}," for row in rows)
    lines.extend((")", ""))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parts", type=Path)
    parser.add_argument("relations", type=Path)
    parser.add_argument("tree", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    count = generate(args.parts, args.relations, args.tree, args.output)
    print(f"{count} malhas musculares gravadas em {args.output}")


if __name__ == "__main__":
    main()
