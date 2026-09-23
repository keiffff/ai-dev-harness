#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function usage() {
  return `Usage:
  JEV_KIT_ROOT=/path/to/jev-kit node evals/permission-review/evaluate.mjs [options]

Options:
  --policy <file>       Baseline harness policy JSON
  --calibration <file>  Calibration fixtures JSON
  --holdout <file>      Holdout fixtures JSON
  --candidate <value>   Candidate as id=policyCompliant,instructionAligned,highRisk
  --help                Show this help
`;
}

function parseArgs(argv) {
  const options = {
    policy: resolve(here, "../../hooks/codex/jev-permission-review-policy.json"),
    calibration: resolve(here, "calibration.json"),
    holdout: resolve(here, "holdout.json"),
    candidates: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--help") return { help: true };
    const value = argv[index + 1];
    if (value === undefined) throw new Error(`${argument} requires a value`);
    if (argument === "--policy") options.policy = resolve(value);
    else if (argument === "--calibration") options.calibration = resolve(value);
    else if (argument === "--holdout") options.holdout = resolve(value);
    else if (argument === "--candidate") options.candidates.push(parseCandidate(value));
    else throw new Error(`unknown argument: ${argument}`);
    index += 1;
  }
  return options;
}

function parseCandidate(value) {
  const [id, rawThresholds] = value.split("=", 2);
  const thresholds = rawThresholds?.split(",").map(Number);
  if (id?.trim() === "" || thresholds?.length !== 3 || thresholds.some((item) => !Number.isFinite(item))) {
    throw new Error(`invalid candidate: ${value}`);
  }
  const [policyCompliant, instructionAligned, highRisk] = thresholds;
  for (const threshold of thresholds) {
    if (threshold < 0 || threshold > 1) throw new Error(`candidate threshold must be between 0 and 1: ${value}`);
  }
  return { id, policy: { policyCompliant, instructionAligned, highRisk } };
}

async function readJson(file) {
  return JSON.parse(await readFile(file, "utf8"));
}

function withStandingPolicy(fixtures, standingPolicy) {
  return fixtures.map((fixture) => ({
    ...fixture,
    request: {
      ...fixture.request,
      context: {
        ...fixture.request.context,
        standingPolicy: fixture.request.context.standingPolicy || standingPolicy,
      },
    },
  }));
}

function comparisonFixtures(results) {
  return results.map((result) => ({
    id: result.id,
    expected: result.expected === "allow",
    observation: {
      scores: result.scores,
      selectedWithoutScores: result.observed === "allow",
    },
  }));
}

function decide(observation, thresholds) {
  if (observation.scores === undefined) return observation.selectedWithoutScores;
  return observation.scores.policyCompliant >= thresholds.policyCompliant
    && observation.scores.instructionAligned >= thresholds.instructionAligned
    && observation.scores.highRisk <= thresholds.highRisk;
}

function summarizeEvaluation(evaluation) {
  return {
    total: evaluation.total,
    selected: evaluation.selected,
    selectionRate: evaluation.selectionRate,
    correct: evaluation.correct,
    accuracy: evaluation.accuracy,
    selectedPrecision: evaluation.selectedPrecision,
    falseAllowFixtureIds: evaluation.falseAllowFixtureIds,
    falseDeferFixtureIds: evaluation.falseDeferFixtureIds,
  };
}

const options = parseArgs(process.argv.slice(2));
if (options.help) {
  process.stdout.write(usage());
  process.exit(0);
}

const jevKitRoot = process.env.JEV_KIT_ROOT;
if (jevKitRoot === undefined || jevKitRoot.trim() === "") {
  throw new Error("JEV_KIT_ROOT must point to a built jev-kit checkout");
}

const [{ JevClient }, agentReview, decisionEval] = await Promise.all([
  import(pathToFileURL(resolve(jevKitRoot, "packages/decision-contract/dist/index.js"))),
  import(pathToFileURL(resolve(jevKitRoot, "packages/agent-review/dist/index.js"))),
  import(pathToFileURL(resolve(jevKitRoot, "packages/decision-eval/dist/index.js"))),
]);

const [config, calibrationDefinitions, holdoutDefinitions] = await Promise.all([
  readJson(options.policy),
  readJson(options.calibration),
  readJson(options.holdout),
]);
const baselinePolicy = agentReview.definePermissionReviewPolicy(config.policy);
const candidateIds = new Set(["current"]);
for (const candidate of options.candidates) {
  if (candidateIds.has(candidate.id)) throw new Error(`duplicate candidate id: ${candidate.id}`);
  candidateIds.add(candidate.id);
}

const client = new JevClient({ defaultModel: config.model });
const calibration = await agentReview.evaluateAgentReviewFixtures({
  client,
  policy: baselinePolicy,
  fixtures: withStandingPolicy(calibrationDefinitions, config.standingPolicy),
});
const holdout = await agentReview.evaluateAgentReviewFixtures({
  client,
  policy: baselinePolicy,
  fixtures: withStandingPolicy(holdoutDefinitions, config.standingPolicy),
});

const comparison = decisionEval.compareDecisionPolicies({
  calibrationFixtures: comparisonFixtures(calibration.results),
  holdoutFixtures: comparisonFixtures(holdout.results),
  candidates: [
    { id: "current", policy: baselinePolicy.thresholds },
    ...options.candidates,
  ],
  decide,
});

process.stdout.write(`${JSON.stringify({
  contract: { id: baselinePolicy.id, version: baselinePolicy.version },
  model: [...calibration.results, ...holdout.results].find((item) => item.model)?.model,
  providerCalls: calibration.providerCalls + holdout.providerCalls,
  usage: {
    inputTokens: calibration.usage.inputTokens + holdout.usage.inputTokens,
    outputTokens: calibration.usage.outputTokens + holdout.usage.outputTokens,
  },
  resultsWithoutScores: {
    calibration: calibration.results
      .filter((item) => item.scores === undefined)
      .map(({ id, expected, observed, reason }) => ({ id, expected, observed, reason })),
    holdout: holdout.results
      .filter((item) => item.scores === undefined)
      .map(({ id, expected, observed, reason }) => ({ id, expected, observed, reason })),
  },
  candidates: comparison.candidates.map((candidate) => ({
    id: candidate.id,
    policy: candidate.policy,
    calibration: summarizeEvaluation(candidate.calibration),
    holdout: summarizeEvaluation(candidate.holdout),
  })),
}, null, 2)}\n`);
