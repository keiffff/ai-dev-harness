# CDK Review Checklist

Use this reference when reviewing AWS CDK designs or diffs. It is based on failures that often appear only when changes tested in isolated temporary environments reach shared or production-like environments.

## 1. Resource Ownership

Each physical AWS resource must have one owner.

Check:
- Does more than one stack create the same IAM Policy, Log Group, SSM Parameter, CloudWatch Alarm, bucket, queue, role, or shared resource?
- Is this resource temporary-environment-specific, environment-specific, or globally shared?
- If shared, is it created by a dedicated owner stack and referenced elsewhere by ARN, name, or ID?
- Are shared SSM Parameters created by every temporary-environment stack by accident?

Block when:
- two stacks can create the same physical resource name;
- temporary-environment stacks create resources that should be shared;
- ownership is implied by naming instead of encoded in stack structure.

## 2. Physical Names and Retained Resources

Explicit physical names are long-lived deployment contracts.

Check:
- Is a fixed physical name being added or changed?
- Is the fixed name required by AWS, an external integration, or cross-environment reference?
- If the name is environment-specific, does it include the environment identifier?
- Could a resource with `RETAIN` remain after stack deletion and block same-name creation later?
- Does a rename require CloudFormation replacement?

Prefer:
- CDK-generated names unless a physical name is required;
- environment identifiers in names for environment-owned resources;
- a planned import/adoption/deletion path for retained resources.

## 3. Cross-Stack Exports and Construct Moves

Moving a construct between stacks can be a delete in the old stack and a create in the new stack. Export changes are blocked while consumers still import them.

Check:
- Is a construct moved from one stack to another?
- Are CloudFormation Outputs or Export names changed?
- Does any stack still import the old Export?
- Does the change remove an Export in the same deployment that updates its consumers?
- Are Processing Bucket, DB Secret, SQS Queue, or similar shared resources exported from multiple places?

Safe migration shape:
1. Teach consumers the new reference path without deleting the old Export.
2. Deploy consumers so they no longer import the old Export.
3. Remove the old Export or old resource.
4. Move ownership only after references are detached.

Block when:
- Export removal and consumer update happen in one deployment;
- a resource move causes replacement of a shared resource;
- cross-stack dependencies become hard to untangle.

## 4. Dependency Direction and Stack Graph

Stack dependencies should flow in one direction.

Recommended direction:
- foundation: VPC, Security Groups, shared buckets
- data: DB, queues, secrets
- application: Lambda, Step Functions, ECS, application resources
- integration: notifications, monitoring, event wiring

Check:
- Is there a circular dependency between stacks?
- Does a lower-level stack reference an application or integration stack?
- Does a construct cross stage or account boundaries unexpectedly?
- Is a bidirectional relationship better represented through a shared resource or event wiring stack?

Block when:
- two stacks need each other to deploy;
- stage boundaries are crossed through direct construct references;
- shared resources are exported by multiple layers.

## 5. Construct References and Creation Order

String-built names do not always encode CloudFormation dependencies.

Check:
- Is a Log Group, MetricFilter, subscription, permission, or alarm referencing a resource by string name?
- Is the referenced resource CDK-managed or created implicitly by AWS at runtime?
- Does CDK know the dependency through construct attributes?
- Does the change rely on "Lambda creation implies Log Group exists"?

Prefer:
- passing construct attributes rather than rebuilding names as strings;
- explicitly managed Log Groups when they are monitored or filtered;
- explicit dependencies only when construct references cannot express ordering.

Block when:
- a dependent resource can be created before the target exists;
- a Custom Resource or raw string hides required ordering.

## 6. Environment Separation

Success in an isolated temporary environment does not prove shared-environment safety.

Check per environment:
- VPC and Subnets
- Security Groups
- required SSM Parameters
- required Secrets
- shared resources created vs referenced
- enabled features
- region
- physical-name pattern

Block when:
- missing shared or production-like config falls back to temporary/default values;
- a source-control branch name is used as the only environment discriminator;
- temporary, shared, and production-like environments share assumptions that are not true in AWS.

## 7. VPC, Subnet, and Security Group Consistency

IDs can exist but still belong to the wrong network.

Check:
- Do VPC, Subnet, and Security Group values come from one coherent environment config?
- Does every Security Group belong to the expected VPC?
- Do Subnet count and Availability Zone count line up?
- Does an imported VPC construct validate the expected VPC ID?

Block when:
- Security Group and target resource can be in different VPCs;
- VPC/Subnet/SecurityGroup values are read independently without consistency checks.

## 8. Global and Regional Resources

Some resources require a specific region regardless of the application stack region.

Check:
- CloudFront, WAF, ACM certificates, Lambda@Edge, and monitoring resources for region requirements.
- Does a Custom Resource receive the parent stack region by accident?
- Are us-east-1 resources separated from ap-northeast-1 application stacks when required?

Block when:
- a global/edge resource is created in the application stack region without confirming AWS requirements;
- cross-region ownership is hidden inside an application construct.

## 9. Account-Level Quotas and Temporary Environment Multiplication

Temporary environments can multiply resources.

Check:
- Does each temporary environment create resources that could be shared?
- Are AppConfig Deployment Strategies, CloudWatch Logs Resource Policies, IAM policy documents, alarms, queues, buckets, or roles multiplied by temporary environment count?
- Are temporary environment deletion and cleanup paths reliable?
- Are quota limits, policy size limits, and resource count limits considered?

Block when:
- a resource count grows with temporary environment count without a cleanup or sharing strategy;
- service quotas are assumed infinite because one temporary environment deploy succeeded.

## 10. External Resource Preflight

`cdk synth` can succeed while deployment fails because external resources are missing or inaccessible.

Check before shared-environment deployment:
- required SSM Parameters exist;
- required Secrets exist;
- deployment roles have read permissions;
- public AMIs, Lambda Layers, or external ARNs still exist;
- cross-account resources are readable.

Use readonly wrappers for checks. Do not run AWS mutation commands from Codex.

## 11. Post-Deploy Boundaries

CDK success and later job failure should be distinguishable and independently recoverable.

Check:
- Are CDK deploy, migrations, frontend build, Remotion/font/artifact downloads, and external distribution in the same job?
- If a later step fails, are AWS resources already updated?
- Can each step be retried independently and idempotently?
- Do failure notifications identify which phase failed?

Prefer:
- separate retry boundaries for infrastructure, migration, application build, and artifact distribution;
- idempotent post-deploy tasks;
- clear failure classification.

## Quick Review Questions

- Is there exactly one owner for every physical resource?
- Did the change add or modify a fixed physical name?
- Did the change move a construct between stacks?
- Did it change or remove an Export?
- Are dependencies one-directional?
- Are string references hiding creation order?
- Do shared and production-like environments have all required environment config?
- Are Security Groups and targets in the same VPC?
- Are global/edge resources in the required region?
- Does temporary environment count multiply account-level resources?
- Can post-CDK failures be retried without rerunning successful infrastructure updates?
