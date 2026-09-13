#!/usr/bin/env python3
"""Derive semantic demand, dependency reach, and build order for census v4."""

from __future__ import annotations

from collections import defaultdict
from theorem_index import derive_related
from canonical_dependencies import canonical_dependencies

DERIVED_FIELDS = (
    "paper_presence_count",
    "central_claim_paper_count",
    "central_claim_use_count",
    "semantic_rank",
    "supported_claim_paper_count",
    "supported_claim_count",
    "downstream_interface_count",
    "build_order",
)


class MetricsError(ValueError):
    pass


def derive_metrics(data: dict) -> None:
    interfaces = data.get("interfaces", [])
    by_id: dict[str, dict] = {}
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in interfaces:
        interface_id = item.get("interface_id")
        if not isinstance(interface_id, str) or not interface_id or interface_id in by_id:
            raise MetricsError("interface IDs must be nonempty and unique before finalization")
        by_id[interface_id] = item
        groups[item.get("rank_group", "")].append(item)

    for item in interfaces:
        members = item.get("members", [])
        uses = item.get("central_claim_uses", [])
        item["paper_presence_count"] = len({member.get("paper_id") for member in members})
        item["central_claim_paper_count"] = len({use.get("paper_id") for use in uses})
        item["central_claim_use_count"] = len(uses)

    for items in groups.values():
        semantic = sorted(items, key=lambda item: (
            -item["central_claim_paper_count"],
            -item["central_claim_use_count"],
            item.get("name", "").casefold(),
            item["interface_id"],
        ))
        for rank, item in enumerate(semantic, 1):
            item["semantic_rank"] = rank

    try:
        canonical = canonical_dependencies(data)
    except (KeyError, TypeError, ValueError) as error:
        raise MetricsError(str(error)) from error
    for item in interfaces:
        if item.get('dependencies') != canonical[item['interface_id']]:
            raise MetricsError(item['interface_id'] + ': canonical dependencies differ from local source edges; run the finalizer')

    prerequisites: dict[str, set[str]] = {interface_id: set() for interface_id in by_id}
    dependents: dict[str, set[str]] = {interface_id: set() for interface_id in by_id}
    for interface_id, item in by_id.items():
        group = item.get("rank_group")
        for dependency in item.get("dependencies", []):
            prerequisite_id = dependency.get("prerequisite_interface_id")
            if prerequisite_id not in by_id:
                raise MetricsError(f"{interface_id} has unknown prerequisite {prerequisite_id!r}")
            if prerequisite_id == interface_id:
                raise MetricsError(f"{interface_id} cannot depend on itself")
            if by_id[prerequisite_id].get("rank_group") != group:
                raise MetricsError(f"{interface_id} has a cross-group prerequisite")
            prerequisites[interface_id].add(prerequisite_id)
            dependents[prerequisite_id].add(interface_id)

    try:
        related = derive_related(data)
    except (ValueError, KeyError, TypeError) as error:
        raise MetricsError(str(error)) from error

    for interface_id, item in by_id.items():
        downstream: set[str] = set()
        stack = list(dependents[interface_id])
        while stack:
            candidate = stack.pop()
            if candidate in downstream:
                continue
            downstream.add(candidate)
            stack.extend(dependents[candidate])
        records = related[interface_id]
        item["related_theorems"] = records
        item["supported_claim_paper_count"] = len({r["paper_id"] for r in records})
        item["supported_claim_count"] = len(records)
        item["downstream_interface_count"] = len(downstream)

    for group, items in groups.items():
        group_ids = {item["interface_id"] for item in items}
        indegree = {interface_id: len(prerequisites[interface_id]) for interface_id in group_ids}
        available = {interface_id for interface_id, degree in indegree.items() if degree == 0}
        order = 0
        while available:
            chosen = min(available, key=lambda interface_id: (
                -by_id[interface_id]["supported_claim_paper_count"],
                -by_id[interface_id]["supported_claim_count"],
                -by_id[interface_id]["central_claim_paper_count"],
                -by_id[interface_id]["central_claim_use_count"],
                by_id[interface_id]["semantic_rank"],
                by_id[interface_id].get("name", "").casefold(),
                interface_id,
            ))
            available.remove(chosen)
            order += 1
            by_id[chosen]["build_order"] = order
            for dependent in dependents[chosen]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    available.add(dependent)
        if order != len(group_ids):
            raise MetricsError(f"dependency cycle in rank group {group!r}; inspect cross-paper grouping instead of dropping local edges")

    data["interfaces"] = sorted(
        interfaces, key=lambda item: (item.get("rank_group", ""), item["build_order"])
    )
