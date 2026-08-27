---
name: codex-cdk-design-review
description: Review AWS CDK changes for shared-environment ownership, names, cross-stack dependencies, region, VPC, quotas, and deployment coupling. Do not deploy.
---

# Codex CDK Design Review

Use this skill to review CDK design and CDK diffs before the agent writes or ships infrastructure changes. The goal is not to generate CDK code; it is to catch failures before a change reaches shared or production-like environments.

## Scope

Good cases:
- designing or reviewing AWS CDK stacks, constructs, or stack boundaries
- adding or changing fixed physical names, SSM Parameters, Secrets, Log Groups, IAM Policies, CloudWatch Alarms, buckets, queues, or roles
- moving constructs between stacks
- changing CloudFormation Outputs, Exports, or cross-stack references
- changing ephemeral, preview, shared, production-like, or multi-account environment configuration
- reviewing `cdk synth`, `cdk diff`, cdk-nag, or policy-validation findings
- deciding whether a CDK change is safe for shared environments

Bad cases:
- ordinary application code with no CDK or CloudFormation surface
- raw AWS operations, deploy execution, migration execution, or production remediation
- cost estimation or general AWS architecture brainstorming without a concrete CDK artifact

## Safety Rules

- Do not run `cdk deploy`, `cdk destroy`, `cdk bootstrap`, CloudFormation update/delete commands, migration commands, or raw `aws`.
- If AWS preflight reads are needed, use the repository/user-approved readonly wrapper, such as `$HOME/.local/bin/aws-readonly ...` or the repository-approved AWS readonly wrapper, and only when the user asked for that investigation.
- Treat isolated temporary-environment success as insufficient evidence for shared or production-like environments. Review fixed names, Exports, retained resources, existing shared resources, quotas, regions, and environment-specific config before saying a change is safe.
- Do not add fallbacks from shared or production-like environments to temporary or default environment values. Missing required environment config should fail before deployment.

## Workflow

1. Identify the CDK artifact under review.
   - Artifact examples: CDK diff, stack graph, construct move, new resource, physical-name change, environment config change, SSM/Secret/VPC reference, post-deploy job.
2. Define the contract.
   - The change must deploy safely in shared environments, preserve existing Export consumers, avoid unintended resource replacement, keep one owner per physical resource, and fail fast on missing environment config.
3. Load `references/cdk-review-checklist.md`.
4. Review the artifact against the checklist, prioritizing failures that isolated temporary environments may not expose.
5. Reconcile findings before acting:
   - `blocker`: likely to fail or replace/delete shared infrastructure.
   - `needs decision`: ownership, migration sequence, environment behavior, or compatibility needs human choice.
   - `trade-off`: risk is real but may be intentionally accepted.
   - `noise`: not applicable to this artifact.
6. If the review changes an interface, stack boundary, persisted resource, Export, or shared environment behavior, stop and surface the decision before editing.

## Output

Use this shape:

```md
## CDK Design Review

### 判定
- Block / Needs decision / Looks safe

### Blockers
- <共有環境・本番相当環境・既存stackで失敗し得る具体理由>

### Decisions Needed
- Resource owner:
- Physical name / RETAIN:
- Cross-stack Export:
- Environment config:
- Region / VPC:
- Quota:
- Post-deploy boundary:

### Safe to Proceed Conditions
- cdk synth:
- cdk diff:
- cdk-nag / policy validation:
- readonly preflight:
```

Keep the report focused on reviewer decisions. Do not produce a file-by-file implementation log.
