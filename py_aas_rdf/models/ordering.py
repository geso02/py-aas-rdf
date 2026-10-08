"""Read list-valued RDF properties back in their ``aas:index`` order.

RDF is unordered: ``graph.objects`` yields in store order, which differs between
stores and after a serialization round trip. ``to_rdf`` writes ``aas:index`` on
every list item, so ``from_rdf`` sorts by it. Items without an index (a store
that dropped it) sort last, in a stable IRI order.
"""

from __future__ import annotations

import rdflib

from py_aas_rdf.models.aas_namespace import AASNameSpace


def objects_by_index(graph: rdflib.Graph, subject: rdflib.Node, predicate: rdflib.URIRef) -> list[rdflib.Node]:
    """Objects of ``(subject, predicate, ?)`` ordered by their ``aas:index``."""

    def sort_key(node: rdflib.Node) -> tuple[bool, int, str]:
        index = next(graph.objects(subject=node, predicate=AASNameSpace.AAS["index"]), None)
        return (index is None, int(index) if index is not None else 0, str(node))

    return sorted(graph.objects(subject=subject, predicate=predicate), key=sort_key)
