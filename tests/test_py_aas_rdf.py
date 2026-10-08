#!/usr/bin/env python

"""Tests for `py_aas_rdf` package."""
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
