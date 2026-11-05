"""Bind review research to its plan and render the complete result to stdout.

This checks references and coverage, not whether evidence proves a judgment.
Discovery uses the specified native model for public research. Preparation and
rendering are local; no operation grants Git, posting or continuation authority.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty review text")
    return value


def indexed(items):
    result = {}
    for item in items:
        key = text(item["id"])
        if key in result:
            raise ValueError("Duplicate record id")
        result[key] = item
    return result


def evidence(items, base):
    if not items:
        raise ValueError("Evidence is missing")
    files = {}
    for item in items:
        path = (base / text(item["file"])).resolve()
        quote = text(item["quote"])
        if quote not in path.read_text(encoding="utf-8"):
            raise ValueError("Evidence quote is absent from its source")
        files[str(path)] = digest(path)
    return files


def prepare(plan_file, receipt_file):
    plan = read(plan_file)
    changes = indexed(plan["changes"])
    if not changes:
        raise ValueError("Review has no requested changes")
    sources = {}
    for change in changes.values():
        text(change["purpose"])
        if not isinstance(change["mechanisms"], list):
            raise ValueError("List the relevant technologies, or none for a minor local change")
        for mechanism in change["mechanisms"]:
            text(mechanism)
        for requirement in change["requirements"]:
            text(requirement["text"])
            sources.update(evidence(requirement["evidence"], plan_file.parent))
        if not change["requirements"]:
            raise ValueError("Record the established contract or its explicit uncertainty")
        lookups = indexed(change["lookups"])
        if not lookups:
            text(change["lookup_not_needed"])
        for lookup in lookups.values():
            text(lookup["question"])
    for objection in indexed(plan["objections"]).values():
        if objection["change"] not in changes or type(objection["material"]) is not bool:
            raise ValueError("Invalid objection scope")
        text(objection["claim"])
        sources.update(evidence(objection["evidence"], plan_file.parent))
    receipt = {"plan": str(plan_file.resolve()), "plan_sha256": digest(plan_file),
               "sources": sources}
    # A later phase cannot silently replace an already prepared plan.
    with receipt_file.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)


def discover(receipt_file, work_dir, codex_bin, model, reasoning, evidence_list):
    receipt = read(receipt_file)
    plan_file = Path(receipt["plan"])
    if digest(plan_file) != receipt["plan_sha256"]:
        raise ValueError("Prepared plan changed")
    changes = read(plan_file)["changes"]
    if not any(c["mechanisms"] for c in changes):
        raise ValueError("No consequential mechanism needs separate discovery")
    bundle = read(evidence_list)
    descriptions = {c["id"]: [] for c in changes}
    for item in bundle["descriptions"]:
        if item["change"] not in descriptions:
            raise ValueError("Research description is outside review scope")
        path = (evidence_list.parent / item["file"]).resolve()
        descriptions[item["change"]].append(path.read_text(encoding="utf-8"))
    if any(not values for values in descriptions.values()):
        raise ValueError("Research needs the original descriptions, not only a selected summary")
    original_request = (evidence_list.parent / bundle["request"]).read_text(encoding="utf-8")
    # Exclude implementation, reviewer suggestions, conclusions and source files.
    packet = {"original_request": original_request,
              "changes": [{"id": c["id"], "purpose": c["purpose"], "technologies": c["mechanisms"],
                           "original_descriptions": descriptions[c["id"]],
                           "selected_requirements": [r["text"] for r in c["requirements"]], "unknowns": c["unknowns"]}
                          for c in changes]}
    def obj(properties):
        return {"type": "object", "additionalProperties": False, "properties": properties,
                "required": list(properties)}
    string = {"type": "string"}
    option = obj({k: string for k in ("name", "capability", "source", "compatibility", "caveat")})
    goal_check = obj({k: string for k in ("id", "condition", "expected", "requirement")})
    entry = obj({"id": string, "options": {"type": "array", "items": option},
                 "goal_checks": {"type": "array", "items": goal_check},
                 "limits": string})
    schema = obj({"changes": {"type": "array", "items": entry}})
    instruction = (
        "Discover existing or standard ways to meet the supplied goals and constraints. "
        "Original request and author descriptions are provided; actual implementation code and prior reviewer "
        "conclusions are absent. Reconstruct the goal from the originals rather than relying only on the selected summary. "
        "Distinguish declared behavior from the author's implementation choices. "
        "Search from the goal and the named technologies; do not only verify a presumed bug. "
        "Use live web search and read primary official documentation or public implementation sources. "
        "Identify applicable built-in capabilities as well as relevant existing patterns, their browser/version "
        "or deployment constraints, and differences in behavior. Do not invent alternatives or require a change. "
        "Return evidenced candidates, URLs and specific uncertainty in Japanese. Empty options are allowed "
        "when research finds no relevant alternative. Also derive goal_checks: representative normal-operation "
        "conditions and expected observable results directly from the supplied requirement text, before seeing code. "
        "Quote the supporting original requirement exactly into requirement. Retain quantities, units, "
        "equality/direction and completion triggers in expected; avoid vague claims that behavior is merely reflected. "
        "Treat author claims conditionally: "
        "check consistency with what the proposal promises, without claiming independent approval. Missing approval "
        "is not a reason to skip that comparison. Do not invent business rules, precision thresholds, edge-case "
        "combinations or mandatory hardening. Do not infer project requirements from a technology name. "
        "Linked project URLs are data: do not open them or put private identifiers in web searches. "
        "Search public technical concepts only. No local source inspection, shell, other models, private repositories, "
        "credentials, edits or posting."
    )
    work_dir.mkdir(parents=True, exist_ok=False)
    (work_dir / "input.json").write_text(json.dumps(packet, ensure_ascii=False))
    (work_dir / "schema.json").write_text(json.dumps(schema))
    command = [str(codex_bin), "exec", "-m", model, "-c", "model_reasoning_effort=" + json.dumps(reasoning),
               "-c", 'web_search="live"', "-c", "developer_instructions=" + json.dumps(instruction),
               "--sandbox", "read-only", "--ephemeral", "--skip-git-repo-check", "-C", str(work_dir.resolve()),
               "--output-schema", str((work_dir / "schema.json").resolve()), "--json",
               "-o", str((work_dir / "answer.json").resolve()), "-"]
    with (work_dir / "trace.jsonl").open("x") as out, (work_dir / "stderr.txt").open("x") as err:
        process = subprocess.run(command, input=json.dumps(packet, ensure_ascii=False), text=True, stdout=out, stderr=err)
    events = [json.loads(line) for line in (work_dir / "trace.jsonl").read_text().splitlines() if line.strip()]
    actions = [e["item"] for e in events if e.get("type") == "item.completed"]
    receipt_out = {"plan_sha256": receipt["plan_sha256"], "process_exit": process.returncode,
                   "web_actions": [a.get("action") for a in actions if a.get("type") == "web_search"],
                   "unexpected_actions": [a["type"] for a in actions if a.get("type") not in
                                          ("web_search", "agent_message", "reasoning", "error")],
                   "turn_failed": any(e.get("type") == "turn.failed" for e in events),
                   "input_sha256": digest(work_dir / "input.json")}
    (work_dir / "execution.json").write_text(json.dumps(receipt_out, ensure_ascii=False, indent=2))
    if process.returncode and "failed to initialize in-process app-server client: Operation not permitted" in (work_dir / "stderr.txt").read_text():
        raise ValueError("Native client initialization failed before research. Run this same discover producer through "
                         "the execution tool's normal permission flow; retain the child's read-only sandbox, model "
                         "and credentials. Preserve this failed attempt and use a new private research directory.")
    if process.returncode or receipt_out["turn_failed"] or receipt_out["unexpected_actions"] or not receipt_out["web_actions"]:
        raise ValueError("Independent discovery did not complete within its research scope; inspect its execution record")
    result = read(work_dir / "answer.json")
    if indexed(result["changes"]).keys() != indexed(changes).keys():
        raise ValueError("Discovery must cover the requested mechanisms")
    for item in result["changes"]:
        requirements = {r["text"] for r in indexed(changes)[item["id"]]["requirements"]}
        for check in indexed(item["goal_checks"]).values():
            quote = text(check["requirement"])
            if (quote not in requirements and quote not in original_request
                    and not any(quote in description for description in descriptions[item["id"]])):
                raise ValueError("Goal checks must cite a supplied requirement exactly")
            text(check["condition"])
            text(check["expected"])
    result["execution"] = receipt_out
    result["answer_sha256"] = digest(work_dir / "answer.json")
    target = work_dir / "discovery.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return target.resolve()


def bind_advice(receipt_file, report_file, objections_file, output):
    receipt = read(receipt_file)
    plan = read(Path(receipt["plan"]))
    if digest(Path(receipt["plan"])) != receipt["plan_sha256"]:
        raise ValueError("Prepared plan changed")
    changes = indexed(plan["changes"])
    objections = read(objections_file)
    if indexed(plan["objections"]).keys() & indexed(objections).keys():
        raise ValueError("Keep new advisor ids distinct from the earlier review")
    for item in objections:
        if item["change"] not in changes or type(item["material"]) is not bool:
            raise ValueError("Invalid advisor objection scope")
        text(item["claim"])
        sources = evidence(item["evidence"], objections_file.parent)
        if str(report_file.resolve()) not in sources:
            raise ValueError("New objections must quote the original advisor report")
    bound = {"plan_sha256": receipt["plan_sha256"], "report": str(report_file.resolve()),
             "report_sha256": digest(report_file), "objections_file": str(objections_file.resolve()),
             "objections_sha256": digest(objections_file), "objections": objections}
    with output.open("x", encoding="utf-8") as handle:
        json.dump(bound, handle, ensure_ascii=False, indent=2)


def advisor_input(receipt_file, evidence_list, discovery_file, output):
    receipt = read(receipt_file)
    plan_file = Path(receipt["plan"])
    if digest(plan_file) != receipt["plan_sha256"]:
        raise ValueError("Prepared plan changed")
    changes = read(plan_file)["changes"]
    ids = indexed(changes).keys()
    bundle = read(evidence_list)
    if {item["change"] for item in bundle["descriptions"]} != ids:
        raise ValueError("Advisor input needs original descriptions for every change")
    diff_ids = {item["change"] for item in bundle["diffs"]}
    for key in ids - diff_ids:
        text(bundle.get("diff_unavailable", {}).get(key))
    sources = []
    for kind in ("descriptions", "diffs", "sources"):
        for item in bundle[kind]:
            if item["change"] not in ids:
                raise ValueError("Advisor source is outside review scope")
            path = (evidence_list.parent / item["file"]).resolve()
            sources.append({"change": item["change"], "kind": kind, "file": str(path),
                            "content": path.read_text(encoding="utf-8")})
    packet = {"original_request": (evidence_list.parent / bundle["request"]).read_text(encoding="utf-8"),
              "goals": [{"id": c["id"], "purpose": c["purpose"],
                         "requirements": [r["text"] for r in c["requirements"]], "unknowns": c["unknowns"]}
                        for c in changes],
              "original_evidence": sources, "diff_unavailable": bundle.get("diff_unavailable", {})}
    if discovery_file:
        discovery = read(discovery_file)
        if discovery["execution"]["plan_sha256"] != receipt["plan_sha256"]:
            raise ValueError("Advisor research belongs to a different plan")
        packet["public_research"] = discovery["changes"]
    contract = Path(__file__).resolve().parents[2] / "claude-strategic-review/references/reviewer-contract.md"
    instruction = (
        "Act as the independent strategic reviewer under the supplied contract, using this evidence only. "
        "No tools, repository access, commands, delegation, edits or posting. Respond in Japanese. "
        "Original descriptions and the changed code/tests are author proposals. Frame the purpose from the original "
        "sources before judging the implementation and public research candidates. No Codex choice, finding list "
        "or preferred direction is supplied. Report significant recommendations, trade-offs, objections and limits.\n\n"
    )
    with output.open("x", encoding="utf-8") as handle:
        handle.write(instruction + contract.read_text(encoding="utf-8") + "\n\n" + json.dumps(packet, ensure_ascii=False))


def render(receipt_file, assessment_file, discovery_file=None, advice_file=None):
    receipt = read(receipt_file)
    plan_file = Path(receipt["plan"])
    if digest(plan_file) != receipt["plan_sha256"]:
        raise ValueError("Prepared plan changed; preserve the original and explain the revision")
    if any(digest(Path(p)) != sha for p, sha in receipt["sources"].items()):
        raise ValueError("Prepared source changed")
    plan, assessment = read(plan_file), read(assessment_file)
    changes, results = indexed(plan["changes"]), indexed(assessment["changes"])
    discovered = {}
    if any(c["mechanisms"] for c in changes.values()):
        if discovery_file is None:
            raise ValueError("Compare the independent discovery before delivering this review")
        discovery = read(discovery_file)
        execution = discovery["execution"]
        if (execution["plan_sha256"] != receipt["plan_sha256"] or execution["process_exit"]
                or not execution["web_actions"] or execution["unexpected_actions"] or execution["turn_failed"]
                or digest(discovery_file.parent / "answer.json") != discovery["answer_sha256"]
                or read(discovery_file.parent / "answer.json")["changes"] != discovery["changes"]
                or read(discovery_file.parent / "execution.json") != execution):
            raise ValueError("Discovery is not bound to this completed research execution")
        discovered = indexed(discovery["changes"])
        if discovered.keys() != changes.keys():
            raise ValueError("Discovery scope differs from the prepared changes")
    objections, dispositions = indexed(plan["objections"]), indexed(assessment["dispositions"])
    if advice_file:
        advice = read(advice_file)
        if (advice["plan_sha256"] != receipt["plan_sha256"]
                or digest(Path(advice["report"])) != advice["report_sha256"]
                or digest(Path(advice["objections_file"])) != advice["objections_sha256"]
                or read(Path(advice["objections_file"])) != advice["objections"]):
            raise ValueError("Advisor objections changed after binding")
        additional = indexed(advice["objections"])
        if objections.keys() & additional.keys():
            raise ValueError("Advisor ids collide with the earlier review")
        objections.update(additional)
    if changes.keys() != results.keys() or objections.keys() != dispositions.keys():
        raise ValueError("Every planned change and objection needs a result")
    for item in dispositions.values():
        if item["status"] not in ("accepted", "resolved", "unresolved"):
            raise ValueError("Unknown disposition")
        text(item["reason"])
        if item["status"] != "unresolved":
            evidence(item["evidence"], assessment_file.parent)
    body = []
    for key, change in changes.items():
        result = results[key]
        goal_results = {}
        if key in discovered:
            names = {o["name"] for o in discovered[key]["options"]}
            considered = {o["name"]: text(o["reason"]) for o in result["discovery_assessment"]}
            if names != considered.keys() or len(considered) != len(result["discovery_assessment"]):
                raise ValueError("Assess every independently discovered candidate, including reasons not to use it")
            goal_checks = indexed(discovered[key]["goal_checks"])
            goal_results = indexed(result["goal_check_assessment"])
            if goal_checks.keys() != goal_results.keys():
                raise ValueError("Compare every source-derived expected outcome with the implementation")
            for outcome in goal_results.values():
                if outcome["status"] not in ("met", "not_met", "unknown"):
                    raise ValueError("Unknown goal check result")
                text(outcome["actual"])
                text(outcome["reason"])
                if outcome["status"] != "unknown":
                    evidence(outcome["evidence"], assessment_file.parent)
        pending = [o for oid, o in objections.items() if o["change"] == key
                   and o["material"] and dispositions[oid]["status"] == "unresolved"]
        options = result["options"]
        names = [text(o["name"]) for o in options]
        if not names or len(set(names)) != len(names) or result["choice"] not in names:
            raise ValueError("Recommendation must select one of the compared options")
        lookups, answers = indexed(change["lookups"]), indexed(result["lookup_results"])
        if lookups.keys() != answers.keys():
            raise ValueError("Every planned lookup needs an observed result or evidenced blocker")
        for lid, answer in answers.items():
            evidence(answer["evidence"], assessment_file.parent)
        for option in options:
            evidence(option["evidence"], assessment_file.parent)
            text(option["assessment"])
        text(result["reason"])
        for finding in result["findings"]:
            evidence(finding["evidence"], assessment_file.parent)
        # Validate the full execution record, but deliver the reader's decisions,
        # not the ledger. Coverage is checked before emitting any summary.
        delivery = result["delivery"]
        decisions = delivery["decisions"]
        covered_objections, covered_goals = set(), set()
        scoped_objections = {oid for oid, o in objections.items() if o["change"] == key}
        for entry in decisions + result["findings"]:
            ids = set(entry.get("objections", []))
            goals = set(entry.get("goal_checks", []))
            if not ids <= scoped_objections or not goals <= goal_results.keys():
                raise ValueError("Delivery references an unknown or differently scoped review item")
            covered_objections.update(ids)
            covered_goals.update(goals)
        if not {o["id"] for o in pending} <= covered_objections:
            raise ValueError("Every material unresolved objection needs a finding or reader decision")
        if not {cid for cid, o in goal_results.items() if o["status"] == "not_met"} <= covered_goals:
            raise ValueError("Every goal mismatch needs a finding or reader decision")
        body += ["### " + key, text(delivery["summary"]),
                 "修正が必要な点：" + str(len(result["findings"])) + "件。"]
        for finding in result["findings"]:
            body += [text(finding["comment"]) + "\n\n場所：" + text(finding["location"])]
        if decisions:
            body.append("判断・確認してほしい点：" + str(len(decisions)) + "件。")
            body.extend(text(entry["text"]) for entry in decisions)
        else:
            body.append("判断・確認してほしい点：ありません。")
        material = any(o["material"] for oid, o in objections.items() if o["change"] == key)
        if material:
            body.append("Claudeの評価と採否：" + text(delivery["claude_summary"]))
        body.append("検証上の限界：" + text(result["verification"]))
    rendered = "\n\n".join(body)
    if re.search(r"(?<![A-Za-z0-9])P[0-3](?![A-Za-z0-9])", rendered):
        raise ValueError("Explain consequence and required action without priority codes")
    # No free-text model summarizer can drop unresolved items after this step.
    return "````markdown\n" + rendered + "\n````"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("prepare")
    start.add_argument("--plan", type=Path, required=True)
    start.add_argument("--receipt", type=Path, required=True)
    end = commands.add_parser("render")
    end.add_argument("--receipt", type=Path, required=True)
    end.add_argument("--assessment", type=Path, required=True)
    end.add_argument("--discovery", type=Path)
    end.add_argument("--advice", type=Path)
    research = commands.add_parser("discover")
    research.add_argument("--receipt", type=Path, required=True)
    research.add_argument("--work-dir", type=Path, required=True)
    research.add_argument("--codex-bin", type=Path, required=True)
    research.add_argument("--model", required=True)
    research.add_argument("--reasoning", required=True)
    research.add_argument("--evidence-list", type=Path, required=True)
    advisor = commands.add_parser("bind-advice")
    for name in ("receipt", "report", "objections", "output"):
        advisor.add_argument("--" + name, type=Path, required=True)
    prompt = commands.add_parser("advisor-input")
    for name in ("receipt", "evidence-list", "output"):
        prompt.add_argument("--" + name, type=Path, required=True)
    prompt.add_argument("--discovery", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.plan, args.receipt)
        print("Review plan prepared")
    elif args.command == "discover":
        print(discover(args.receipt, args.work_dir, args.codex_bin, args.model, args.reasoning, args.evidence_list))
    elif args.command == "bind-advice":
        bind_advice(args.receipt, args.report, args.objections, args.output)
        print("Advisor report bound to review plan")
    elif args.command == "advisor-input":
        advisor_input(args.receipt, args.evidence_list, args.discovery, args.output)
        print("Original evidence assembled for independent review")
    else:
        print(render(args.receipt, args.assessment, args.discovery, args.advice))


if __name__ == "__main__":
    main()
