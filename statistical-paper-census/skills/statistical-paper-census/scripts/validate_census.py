#!/usr/bin/env python3
"""Validate a statistical-ranked-interfaces-v4 census."""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from census_metrics import DERIVED_FIELDS, MetricsError, derive_metrics
from publication_contract import publication_errors

SCHEMA = "statistical-ranked-interfaces-v4"
INVENTORY_SCHEMA = "statistical-theorem-inventory-v1"
ROLES = {"definition", "predicate", "structure", "class", "inductive", "theorem",
         "hypothesis", "notation", "local_object"}
RELATIONS = {"exact", "equivalent", "specialization", "composite_contains", "distinct"}
USE_KINDS = {"statement_dependency", "claim_target"}
DEPENDENCY_KINDS = {"definition_body", "theorem_statement"}
FORBIDDEN = {"library_status", "library_audit", "matched_declarations"}


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


# Retired UI captions must not return as supposedly source-specific explanations.
BOILERPLATE_EXPLANATIONS = {
    "this theorem directly uses the api",
    "this theorem uses the api through another definition",
    "this theorem is linked through another definition",
    "this theorem is linked through another definition or assumption",
    "the theorem represented by this api",
    "direct use", "indirect use", "through another definition",
}


def has_boilerplate_explanation(value: str) -> bool:
    # Match complete captions/sentences, including a caption prepended to useful text.
    # This does not certify the mathematical content of other explanations.
    sentences = re.split(r"[.!?]+", value)
    return any(" ".join(sentence.split()).strip(" \"'“”‘’*_ ").casefold() in BOILERPLATE_EXPLANATIONS
               for sentence in sentences)


def valid_evidence(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(record, dict)
        and type(record.get("page")) is int and record["page"] > 0
        and text(record.get("location"))
        for record in value
    )


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [str(error)]
    if not isinstance(data, dict) or data.get("schema_version") not in (SCHEMA, INVENTORY_SCHEMA):
        return [f"schema_version must be {SCHEMA!r}"]
    inventory_only = data["schema_version"] == INVENTORY_SCHEMA
    serialized = json.dumps(data).lower()
    for field in FORBIDDEN:
        if f'"{field}"' in serialized:
            errors.append(f"forbidden Stage-B field: {field}")

    scope = data.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        if scope.get("theorem_scope") != "main_text_only":
            errors.append("scope.theorem_scope must be main_text_only")
        for field in (() if inventory_only else ("source_policy", "normalization_policy", "semantic_ranking_policy", "build_order_policy")):
            if not text(scope.get(field)):
                errors.append(f"scope.{field} required")

    papers = data.get("papers")
    if not isinstance(papers, list) or not papers:
        errors.append("papers must be a nonempty list")
        papers = []
    paper_ids: set[str] = set()
    for index, paper in enumerate(papers):
        where = f"papers[{index}]"
        if not isinstance(paper, dict):
            errors.append(f"{where} must be an object")
            continue
        paper_id = paper.get("paper_id")
        if not text(paper_id) or paper_id in paper_ids:
            errors.append(f"{where}.paper_id invalid or duplicate")
        else:
            paper_ids.add(paper_id)
        if not text(paper.get("title")):
            errors.append(f"{where}.title required")
        if not re.fullmatch(r"[0-9a-f]{64}", str(paper.get("pdf_sha256", ""))):
            errors.append(f"{where}.pdf_sha256 invalid")
        if not isinstance(paper.get("pdf_pages"), int) or paper["pdf_pages"] < 1:
            errors.append(f"{where}.pdf_pages invalid")
        if not text(paper.get("version")):
            errors.append(f"{where}.version required")

    claims = data.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        claims = []
    claims_by_paper = defaultdict(list)
    for claim in claims:
        if isinstance(claim, dict) and isinstance(claim.get("paper_id"), str):
            claims_by_paper[claim["paper_id"]].append(claim)
    claim_papers: dict[str, str] = {}
    source_orders = defaultdict(list)
    for index, claim in enumerate(claims):
        where = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{where} must be an object")
            continue
        claim_id, paper_id = claim.get("claim_id"), claim.get("paper_id")
        if not text(claim_id) or claim_id in claim_papers:
            errors.append(f"{where}.claim_id invalid or duplicate")
        elif paper_id not in paper_ids:
            errors.append(f"{where}.paper_id unknown")
        else:
            claim_papers[claim_id] = paper_id
        for field in ("claim_kind", "label", "statement_original"):
            if not text(claim.get(field)):
                errors.append(f"{where}.{field} required")
        if claim.get("claim_kind") != "theorem":
            errors.append(f"{where}.claim_kind must be theorem")
        order = claim.get("source_order")
        if type(order) is not int or order < 1:
            errors.append(f"{where}.source_order must be a positive integer")
        else:
            source_orders[paper_id].append(order)
        if not valid_evidence(claim.get("evidence")):
            errors.append(f"{where}.evidence invalid")

    for pid, orders in source_orders.items():
        if sorted(orders) != list(range(1, len(orders) + 1)):
            errors.append(f"{pid}: theorem source_order must be unique and contiguous")
    if isinstance(scope, dict) and not inventory_only and scope.get("paper_count") != len(paper_ids):
        errors.append("scope.paper_count mismatch")
    if not errors:
        errors.extend(publication_errors(data, path, inventory_only))
    if inventory_only:
        return errors

    interfaces = data.get("interfaces")
    if not isinstance(interfaces, list):
        errors.append("interfaces must be a list")
        interfaces = []
    by_id: dict[str, dict] = {}
    for index, item in enumerate(interfaces):
        if not isinstance(item, dict):
            errors.append(f"interfaces[{index}] must be an object")
            continue
        interface_id = item.get("interface_id")
        if not text(interface_id) or interface_id in by_id:
            errors.append(f"interfaces[{index}].interface_id invalid or duplicate")
        else:
            by_id[interface_id] = item

    use_ids: set[str] = set()
    dependency_ids: set[str] = set()
    ranks: dict[str, dict[str, list[int]]] = defaultdict(lambda: {"semantic": [], "build": []})
    for index, item in enumerate(interfaces):
        where = f"interfaces[{index}]"
        if not isinstance(item, dict):
            continue
        interface_id = item.get("interface_id")
        group = item.get("rank_group")
        if not text(group):
            errors.append(f"{where}.rank_group required")
        for field in ("semantic_rank", "build_order"):
            value = item.get(field)
            if not isinstance(value, int) or value < 1:
                errors.append(f"{where}.{field} invalid")
            elif text(group):
                ranks[group]["semantic" if field == "semantic_rank" else "build"].append(value)
        for field in ("name", "type_shape", "semantic_boundary"):
            if not text(item.get(field)):
                errors.append(f"{where}.{field} required")
        role = item.get("lean_role")
        if role not in ROLES:
            errors.append(f"{where}.lean_role invalid")
        for legacy in ("rank", "paper_count", "central_use_count"):
            if legacy in item:
                errors.append(f"{where}.{legacy} is forbidden in v4")
        for field in DERIVED_FIELDS:
            if not isinstance(item.get(field), int) or item[field] < 0:
                errors.append(f"{where}.{field} must be a nonnegative integer")

        members = item.get("members")
        if not isinstance(members, list) or not members:
            errors.append(f"{where}.members must be nonempty")
            members = []
        member_papers: set[str] = set()
        for member_index, member in enumerate(members):
            member_where = f"{where}.members[{member_index}]"
            if not isinstance(member, dict):
                errors.append(f"{member_where} must be an object")
                continue
            paper_id = member.get("paper_id")
            if paper_id in paper_ids:
                member_papers.add(paper_id)
            else:
                errors.append(f"{member_where}.paper_id unknown")
            for field in ("local_id", "local_label", "statement_original"):
                if not text(member.get(field)):
                    errors.append(f"{member_where}.{field} required")
            source_kind = member.get("source_kind")
            source_heading = member.get("source_heading")
            if source_kind not in {"definition", "assumption", "condition", "theorem_excerpt", "source_passage"}:
                errors.append(f"{member_where}.source_kind must identify the original source type")
            if not text(source_heading):
                errors.append(f"{member_where}.source_heading required")
            elif source_kind != "definition" and re.match(r"Definition\b", source_heading):
                errors.append(f"{member_where}: non-definition source cannot be headed Definition")
            if re.fullmatch(r"Assumption\s+\d+(?:\.\d+)*", str(member.get("local_label", ""))):
                if source_kind != "assumption" or source_heading != member["local_label"]:
                    errors.append(f"{member_where}: preserve the original Assumption label and number")
            contexts = member.get('naming_context', [])
            if not isinstance(contexts, list) or any(not isinstance(c, dict) or not text(c.get('context_id')) or not text(c.get('text')) or not valid_evidence(c.get('evidence')) for c in contexts):
                errors.append(f'{member_where}: naming_context requires exact source excerpts and evidence')
            elif len({c['context_id'] for c in contexts}) != len(contexts):
                errors.append(f'{member_where}: duplicate naming context ID')
            if member.get("relation") not in RELATIONS:
                errors.append(f"{member_where}.relation invalid")
            if not valid_evidence(member.get("evidence")):
                errors.append(f"{member_where}.evidence invalid")
            if not member.get("highlight_symbols") and not member.get("highlight_phrases"):
                errors.append(f"{member_where}: every original definition requires source highlight annotations")
            for field in ("highlight_symbols", "highlight_phrases"):
                selectors = member.get(field, [])
                sources = [member.get("statement_original", "")] + [
                    c.get("statement_original", "") for c in claims_by_paper[paper_id]]
                if field == "highlight_phrases":
                    sources.append(member.get("local_label", ""))
                if not isinstance(selectors, list) or any(not text(selector) or not any(selector in source for source in sources) for selector in selectors):
                    errors.append(f"{member_where}: {field} must quote this paper's original source text")

        if "source_keywords" not in item:
            errors.append(f"{where}.source_keywords required for publication")
        if not isinstance(item.get("theorem_explanations"), dict):
            errors.append(f"{where} ({interface_id}): theorem_explanations must be an object for publication")
        if "source_keywords" in item:
            keywords = item["source_keywords"]
            local_members = {(m.get("paper_id"), m.get("local_id")): m
                             for m in members if isinstance(m, dict)}
            if not isinstance(keywords, list) or not keywords:
                errors.append(f"{where}.source_keywords must be a nonempty list")
            else:
                labels = []
                for keyword in keywords:
                    if not isinstance(keyword, dict) or not text(keyword.get("source_text")) or not text(keyword.get("label")):
                        errors.append(f"{where}: source keyword excerpt and label required")
                        continue
                    member = local_members.get((keyword.get("paper_id"), keyword.get("local_id")))
                    context_id = keyword.get('context_id')
                    source_text = member.get('statement_original', '') if member else ''
                    if context_id is not None:
                        contexts = member.get('naming_context', []) if member else []
                        context = next((c for c in contexts if isinstance(c, dict) and c.get('context_id') == context_id), None)
                        source_text = context.get('text', '') if context else ''
                    if member is None or keyword["source_text"] not in source_text:
                        errors.append(f"{where}: keyword must quote its identified paper-local definition")
                    if text(keyword.get("label")) and text(keyword.get("source_text")):
                        normalize = lambda v: " ".join(v.split()).casefold().replace("–", "-").replace("−", "-")
                        if keyword.get("kind", "term") == "term" and normalize(keyword["label"]) != normalize(keyword["source_text"]):
                            errors.append(f"{where}: term label must preserve the quoted source wording")
                    kind = keyword.get("kind", "term")
                    if kind not in ("term", "symbol"):
                        errors.append(f"{where}: source keyword kind must be term or symbol")
                    if kind == "term" and keyword["label"] not in labels:
                        labels.append(keyword["label"])
                if not labels or item.get("name") != " · ".join(labels):
                    errors.append(f"{where}: name must use natural-language term labels, keeping symbols in the detail page")

        uses = item.get("central_claim_uses")
        if not isinstance(uses, list):
            errors.append(f"{where}.central_claim_uses must be a list")
            uses = []
        use_papers: set[str] = set()
        for use_index, use in enumerate(uses):
            use_where = f"{where}.central_claim_uses[{use_index}]"
            if not isinstance(use, dict):
                errors.append(f"{use_where} must be an object")
                continue
            use_id, paper_id, claim_id = use.get("use_id"), use.get("paper_id"), use.get("claim_id")
            if not text(use_id) or use_id in use_ids:
                errors.append(f"{use_where}.use_id invalid or duplicate")
            else:
                use_ids.add(use_id)
            if claim_id not in claim_papers:
                errors.append(f"{use_where}.claim_id unknown")
            elif claim_papers[claim_id] != paper_id:
                errors.append(f"{use_where} claim and use paper mismatch")
            if paper_id not in member_papers:
                errors.append(f"{use_where}.paper_id lacks an interface member")
            else:
                use_papers.add(paper_id)
            kind = use.get("use_kind")
            if kind not in USE_KINDS:
                errors.append(f"{use_where}.use_kind invalid")
            if role == "theorem" and kind != "claim_target":
                errors.append(f"{use_where} theorem interfaces require claim_target")
            if role != "theorem" and kind == "claim_target":
                errors.append(f"{use_where} claim_target requires theorem role")
            if not text(use.get("reason")):
                errors.append(f"{use_where}.reason required")
            if not valid_evidence(use.get("evidence")):
                errors.append(f"{use_where}.evidence invalid")

        dependencies = item.get("dependencies")
        if not isinstance(dependencies, list):
            errors.append(f"{where}.dependencies must be a list")
            dependencies = []
        seen_prerequisites: set[str] = set()
        for dependency_index, dependency in enumerate(dependencies):
            dependency_where = f"{where}.dependencies[{dependency_index}]"
            if not isinstance(dependency, dict):
                errors.append(f"{dependency_where} must be an object")
                continue
            dependency_id = dependency.get("dependency_id")
            prerequisite_id = dependency.get("prerequisite_interface_id")
            if not text(dependency_id) or dependency_id in dependency_ids:
                errors.append(f"{dependency_where}.dependency_id invalid or duplicate")
            else:
                dependency_ids.add(dependency_id)
            if prerequisite_id not in by_id:
                errors.append(f"{dependency_where}.prerequisite_interface_id unknown")
            elif prerequisite_id == interface_id:
                errors.append(f"{dependency_where} cannot be self-referential")
            elif by_id[prerequisite_id].get("rank_group") != group:
                errors.append(f"{dependency_where} cannot cross rank groups")
            if prerequisite_id in seen_prerequisites:
                errors.append(f"{dependency_where} duplicates a prerequisite")
            else:
                seen_prerequisites.add(prerequisite_id)
            if dependency.get("dependency_kind") not in DEPENDENCY_KINDS:
                errors.append(f"{dependency_where}.dependency_kind invalid")
            if role == "theorem" and dependency.get("dependency_kind") != "theorem_statement":
                errors.append(f"{dependency_where} theorem interfaces require theorem_statement")
            if role != "theorem" and dependency.get("dependency_kind") == "theorem_statement":
                errors.append(f"{dependency_where} theorem_statement requires theorem role")
            if not text(dependency.get("reason")):
                errors.append(f"{dependency_where}.reason required")
            if not valid_evidence(dependency.get("evidence")):
                errors.append(f"{dependency_where}.evidence invalid")

        if item.get("paper_presence_count") != len(member_papers):
            errors.append(f"{where}.paper_presence_count mismatch")
        if item.get("central_claim_paper_count") != len(use_papers):
            errors.append(f"{where}.central_claim_paper_count mismatch")
        if item.get("central_claim_use_count") != len(uses):
            errors.append(f"{where}.central_claim_use_count mismatch")

    for group, values in ranks.items():
        group_size = len([item for item in interfaces if isinstance(item, dict) and item.get("rank_group") == group])
        expected = list(range(1, group_size + 1))
        if sorted(values["semantic"]) != expected:
            errors.append(f"rank group {group!r} semantic ranks must be unique and contiguous")
        if sorted(values["build"]) != expected:
            errors.append(f"rank group {group!r} build orders must be unique and contiguous")

    if not errors:
        expected = copy.deepcopy(data)
        try:
            derive_metrics(expected)
        except MetricsError as error:
            errors.append(str(error))
        else:
            expected_by_id = {item["interface_id"]: item for item in expected["interfaces"]}
            for interface_id, item in by_id.items():
                notes = item["theorem_explanations"]
                related = {r["claim_id"]: r for r in expected_by_id[interface_id]["related_theorems"]}
                if set(notes) != set(related):
                    errors.append(f"interface {interface_id!r}: theorem_explanations must cover exactly its related theorems")
                else:
                    for cid, note in notes.items():
                        record = related[cid]
                        if not isinstance(note, dict) or not text(note.get("text")):
                            errors.append(f"{interface_id}/{cid}: theorem explanation text required")
                            continue
                        if has_boilerplate_explanation(note["text"]):
                            errors.append(f"{interface_id}/{cid}: retired generic relationship caption; backfill a source-specific explanation")
                        if note.get("paper_id") != record["paper_id"] or note.get("via_local_ids") != record["via_local_ids"]:
                            errors.append(f"{interface_id}/{cid}: explanation must match the same-paper dependency path")
                        if not valid_evidence(note.get("evidence")):
                            errors.append(f"{interface_id}/{cid}: explanation source evidence required")
                        else:
                            paper = next(p for p in papers if p["paper_id"] == record["paper_id"])
                            last_page = paper.get("main_text_last_pdf_page", paper["pdf_pages"])
                            if any(e["page"] > last_page for e in note["evidence"]):
                                errors.append(f"{interface_id}/{cid}: explanation evidence outside main text")
                for field in (*DERIVED_FIELDS, "related_theorems"):
                    if item.get(field) != expected_by_id[interface_id].get(field):
                        errors.append(f"interface {interface_id!r}.{field} does not match derived value")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate(args.path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"{args.path}: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
