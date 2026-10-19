from anatomia_app.catalog import CATALOG, STRUCTURES, search_structures


def test_structure_ids_are_unique() -> None:
    assert len(CATALOG) == len(STRUCTURES)


def test_all_structures_have_required_content() -> None:
    for structure in STRUCTURES:
        assert structure.id
        assert structure.name
        assert structure.latin_name
        assert structure.system
        assert structure.description
        assert structure.function


def test_search_is_case_insensitive_and_supports_latin() -> None:
    assert [item.id for item in search_structures("CRÂNIO")] == ["cranio"]
    results = search_structures("biceps brachii")
    assert {"biceps_d", "biceps_e"} <= {item.id for item in results}
    assert any(item.id.startswith("muscle_") for item in results)


def test_empty_search_returns_all_structures() -> None:
    assert search_structures("   ") == STRUCTURES


def test_expanded_muscle_catalog_has_study_metadata() -> None:
    muscles = [item for item in STRUCTURES if item.system == "Sistema muscular"]
    primitives = [item for item in muscles if item.id.startswith("muscle_")]
    assert len(primitives) == 422
    assert all(item.region for item in muscles)
    assert all(item.details for item in muscles)
    assert sum(item.region == "Pé" for item in primitives) == 36
    assert {"Cabeça", "Pescoço", "Dorso", "Tórax", "Mão", "Pé"} <= {
        item.region for item in primitives
    }
