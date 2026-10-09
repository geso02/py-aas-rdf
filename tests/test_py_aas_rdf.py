#!/usr/bin/env python

"""Tests for `py_aas_rdf` package."""
import pydantic
import pytest
import rdflib

from py_aas_rdf.models.data_specification_iec_61360 import ValueList, ValueReferencePair
from py_aas_rdf.models.key import Key

AAS = "https://admin-shell.io/aas/3/1/"


def test_key_to_rdf():
    payload = Key(**{"type": "AssetAdministrationShell", "value": "example"})
    graph, created_node = payload.to_rdf()
    re_created = Key.from_rdf(graph, created_node)
    assert payload == re_created


def test_value_reference_to_rdf():
    payload = ValueReferencePair(**{
        "value": "something_63781b6f",
        "valueId": {
            "keys": [
                {
                    "type": "GlobalReference",
                    "value": "urn:yet-another-company15:6b346267"
                }
            ],
            "type": "ExternalReference"
        }
    })
    graph, created_node = payload.to_rdf()
    re_created = ValueReferencePair.from_rdf(graph, created_node)
    assert payload == re_created


def test_value_list_to_rdf():
    payload = ValueList(**{
        "valueReferencePairs": [
            {
                "value": "something_63781b6f",
                "valueId": {
                    "keys": [
                        {
                            "type": "GlobalReference",
                            "value": "urn:yet-another-company15:6b346267"
                        }
                    ],
                    "type": "ExternalReference"
                }
            }
        ]
    })
    graph, created_node = payload.to_rdf()
    re_created = ValueList.from_rdf(graph, created_node)
    assert payload == re_created


def _list_fixture():
    # Importing Submodel resolves the SubmodelElementChoice forward references
    # of the container models, exactly as in regular use.
    import py_aas_rdf.models.submodel  # noqa: F401
    from py_aas_rdf.models.submodel_element_collection import SubmodelElementCollection
    from py_aas_rdf.models.submodel_element_list import SubmodelElementList

    return SubmodelElementList, SubmodelElementCollection


def test_submodel_element_list_mints_digit_segment_iris():
    from py_aas_rdf.models.property import Property

    SubmodelElementList, _ = _list_fixture()

    def prop(id_short=None):
        payload = {"modelType": "Property", "valueType": "xs:string", "value": "v"}
        if id_short:
            payload["idShort"] = id_short
        return Property(**payload)

    payload = SubmodelElementList(**{
        "modelType": "SubmodelElementList",
        "idShort": "Lst",
        "typeValueListElement": "Property",
        "value": [prop(), prop("Temp")],
    })
    graph, node = payload.to_rdf(prefix_uri="c3VibW9kZWw/submodel-elements/", base_uri="https://ex.org/")

    items = sorted(str(o) for o in graph.objects(
        node, rdflib.URIRef(AAS + "SubmodelElementList/value")))
    assert items == [
        "https://ex.org/c3VibW9kZWw/submodel-elements/Lst.0",
        "https://ex.org/c3VibW9kZWw/submodel-elements/Lst.1",
    ]


def test_submodel_element_list_accepts_positional_root_prefix():
    """A list as the root of an element event: the index carries the address."""
    from py_aas_rdf.models.property import Property

    SubmodelElementList, _ = _list_fixture()
    graph, node = SubmodelElementList(**{
        "modelType": "SubmodelElementList",
        "idShort": "Lst",
        "typeValueListElement": "Property",
        "value": [{"modelType": "Property", "valueType": "xs:string", "value": "v"}],
    }).to_rdf(
        prefix_uri="c3VibW9kZWw/submodel-elements/Lst.0.",
        base_uri="https://ex.org/",
        positional=True,
    )

    assert str(node) == "https://ex.org/c3VibW9kZWw/submodel-elements/Lst.0"
    assert len(list(graph)) > 0


def test_named_child_of_a_positional_element_keeps_its_id_short_segment():
    from py_aas_rdf.models.property import Property

    graph, node = Property(**{
        "modelType": "Property",
        "idShort": "Value",
        "valueType": "xs:string",
        "value": "v",
    }).to_rdf(prefix_uri="c3VibW9kZWw/submodel-elements/Lst.0.", base_uri="https://ex.org/")

    assert str(node) == "https://ex.org/c3VibW9kZWw/submodel-elements/Lst.0.Value"


# --- unique child IRIs for Entity, AnnotatedRelationshipElement, Operation

SM = "https://ex.org/c3VibW9kZWw/submodel-elements/"


def _prop(id_short, value="v"):
    return {"modelType": "Property", "idShort": id_short, "valueType": "xs:string", "value": value}


def _children(graph, node, predicate):
    return sorted(str(o) for o in graph.objects(node, rdflib.URIRef(AAS + predicate)))


def _models():
    import py_aas_rdf.models.submodel  # noqa: F401
    from py_aas_rdf.models.annotated_relationship_element import AnnotatedRelationshipElement
    from py_aas_rdf.models.entity import Entity
    from py_aas_rdf.models.operation import Operation

    return Entity, AnnotatedRelationshipElement, Operation


def _entity(**kwargs):
    Entity, _, _ = _models()
    return Entity(**{
        "modelType": "Entity",
        "idShort": "Ent",
        "entityType": "SelfManagedEntity",
        "statements": [_prop("Stmt1"), _prop("Stmt2")],
        **kwargs,
    })


def test_entity_root_keeps_statement_triples_and_mints_name_iris():
    graph, node = _entity().to_rdf(prefix_uri="c3VibW9kZWw/submodel-elements/", base_uri="https://ex.org/")

    assert str(node) == SM + "Ent"
    assert _children(graph, node, "Entity/statements") == [SM + "Ent.Stmt1", SM + "Ent.Stmt2"]
    stmt = rdflib.URIRef(SM + "Ent.Stmt2")
    assert (stmt, rdflib.RDF.type, rdflib.URIRef(AAS + "Property")) in graph
    assert (stmt, rdflib.URIRef(AAS + "index"), rdflib.Literal(1)) in graph


def test_entity_as_list_item_hangs_statements_below_its_own_address():
    graph, node = _entity().to_rdf(
        prefix_uri="c3VibW9kZWw/submodel-elements/Lst.0.",
        base_uri="https://ex.org/",
        positional=True,
    )

    assert str(node) == SM + "Lst.0"
    assert _children(graph, node, "Entity/statements") == [SM + "Lst.0.Stmt1", SM + "Lst.0.Stmt2"]


def test_entity_with_specific_asset_ids_at_root_keeps_them():
    graph, node = _entity(specificAssetIds=[{"name": "serial", "value": "42"}]).to_rdf(
        prefix_uri="c3VibW9kZWw/submodel-elements/", base_uri="https://ex.org/")

    assert len(_children(graph, node, "Entity/specificAssetIds")) == 1


def test_annotated_relationship_element_root_keeps_annotation_triples():
    _, Are, _ = _models()
    ref = {"type": "ModelReference", "keys": [{"type": "Submodel", "value": "x"}]}
    element = Are(**{
        "modelType": "AnnotatedRelationshipElement",
        "idShort": "Rel",
        "first": ref,
        "second": ref,
        "annotations": [_prop("Ann1"), _prop("Ann2")],
    })
    graph, node = element.to_rdf(prefix_uri="c3VibW9kZWw/submodel-elements/", base_uri="https://ex.org/")

    assert _children(graph, node, "AnnotatedRelationshipElement/annotations") == [
        SM + "Rel.Ann1", SM + "Rel.Ann2"]
    assert (rdflib.URIRef(SM + "Rel.Ann1"), rdflib.RDF.type, rdflib.URIRef(AAS + "Property")) in graph


def test_annotated_relationship_element_as_list_item():
    _, Are, _ = _models()
    ref = {"type": "ModelReference", "keys": [{"type": "Submodel", "value": "x"}]}
    graph, node = Are(**{
        "modelType": "AnnotatedRelationshipElement",
        "first": ref,
        "second": ref,
        "annotations": [_prop("Ann1")],
    }).to_rdf(prefix_uri="c3VibW9kZWw/submodel-elements/Lst.1.", base_uri="https://ex.org/", positional=True)

    assert str(node) == SM + "Lst.1"
    assert _children(graph, node, "AnnotatedRelationshipElement/annotations") == [SM + "Lst.1.Ann1"]


def test_operation_variable_values_are_addressed_under_the_operation():
    _, _, Operation = _models()
    graph, node = Operation(**{
        "modelType": "Operation",
        "idShort": "Op",
        "inputVariables": [{"value": _prop("InA")}, {"value": _prop("InB")}],
        "outputVariables": [{"value": _prop("Out")}],
        "inoutputVariables": [{"value": _prop("Both")}],
    }).to_rdf(prefix_uri="c3VibW9kZWw/submodel-elements/", base_uri="https://ex.org/")

    values = sorted(str(o) for o in graph.objects(None, rdflib.URIRef(AAS + "OperationVariable/value")))
    assert values == [SM + "Op.Both", SM + "Op.InA", SM + "Op.InB", SM + "Op.Out"]
    assert not any(isinstance(s, rdflib.URIRef) and s.endswith(".None") for s in graph.subjects())
    in_vars = list(graph.objects(node, rdflib.URIRef(AAS + "Operation/inputVariables")))
    assert len(in_vars) == 2
    assert sorted(int(graph.value(v, rdflib.URIRef(AAS + "index"))) for v in in_vars) == [0, 1]


def test_operation_as_list_item_addresses_variables_below_its_position():
    _, _, Operation = _models()
    graph, _ = Operation(**{
        "modelType": "Operation",
        "inputVariables": [{"value": _prop("InA")}],
    }).to_rdf(prefix_uri="c3VibW9kZWw/submodel-elements/Lst.0.", base_uri="https://ex.org/", positional=True)

    values = [str(o) for o in graph.objects(None, rdflib.URIRef(AAS + "OperationVariable/value"))]
    assert values == [SM + "Lst.0.InA"]


def test_from_rdf_restores_list_order_from_aas_index_whatever_the_store_order():
    import random

    from py_aas_rdf.models.submodel import Submodel

    def prop(idx):
        return {"modelType": "Property", "valueType": "xs:int", "value": str(idx)}

    def var(name):
        return {"value": {"modelType": "Property", "idShort": name, "valueType": "xs:int"}}

    submodel = Submodel(
        id="http://t.sm",
        idShort="Order",
        submodelElements=[
            {
                "modelType": "SubmodelElementList",
                "idShort": "Lst",
                "typeValueListElement": "Property",
                "valueTypeListElement": "xs:int",
                "value": [prop(i) for i in (3, 1, 2, 5, 4)],
            },
            {
                "modelType": "Operation",
                "idShort": "Op",
                "inputVariables": [var(n) for n in ("Zed", "Aye", "Mid")],
            },
        ],
    )
    graph, node = submodel.to_rdf(base_uri="https://example.org/", id_strategy="base64-url-encode")
    expected = submodel.model_dump(exclude_none=True, mode="json")
    for seed in range(10):
        triples = list(graph)
        random.Random(seed).shuffle(triples)
        shuffled = rdflib.Graph()
        for triple in triples:
            shuffled.add(triple)
        assert Submodel.from_rdf(shuffled, node).model_dump(exclude_none=True, mode="json") == expected


def test_extension_from_rdf_reads_every_refers_to_in_order():
    from py_aas_rdf.models.extension import Extension

    def ref(value):
        return {"type": "ModelReference", "keys": [{"type": "Submodel", "value": value}]}

    extension = Extension(name="x", refersTo=[ref("c"), ref("a"), ref("b")])
    graph, node = extension.to_rdf()
    restored = Extension.from_rdf(graph, node)
    assert [r.keys[0].value for r in restored.refersTo] == ["c", "a", "b"]


# --- one-character idShorts: spec 3.1 shape without the minimum length


def test_one_character_id_short_is_accepted_and_mints_an_iri():
    from py_aas_rdf.models.property import Property

    graph, node = Property(**_prop("S")).to_rdf(
        prefix_uri="c3VibW9kZWw/submodel-elements/", base_uri="https://ex.org/"
    )

    assert str(node) == "https://ex.org/c3VibW9kZWw/submodel-elements/S"
    assert len(list(graph)) > 0


@pytest.mark.parametrize("id_short", ["1bad", "a-", "", "a b", "9"])
def test_non_conforming_id_shorts_are_still_rejected(id_short):
    from py_aas_rdf.models.property import Property

    with pytest.raises(pydantic.ValidationError):
        Property(**_prop(id_short))


@pytest.mark.parametrize("id_short", ["S", "a-b", "A_", "a-b_c", "a-_"])
def test_conforming_id_shorts_are_accepted(id_short):
    from py_aas_rdf.models.property import Property

    Property(**_prop(id_short))
