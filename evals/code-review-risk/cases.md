# Code-review risk regression cases

These cases are synthetic and contain no historical conversations or organization-specific fixtures. Give the reviewing agent the selected skill and the tasks below, without expected.json or prior conclusions. Judge its actual output against expected.json afterwards. Preserve all attempts; a format check alone does not establish review quality. The cases test judgment with supplied facts, not repository navigation, reproduction execution or long-context performance.

# Review tasks

Review each independent change. State findings, priority/blocking judgment and evidence; distinguish questions and suggestions. These are synthetic systems; use only the supplied facts. Do not assume additional production usage. Numbered lines belong to the post-change code.

## A — workspace reset
The UI lets a user select one of their workspaces and reset that workspace's local layout. The reset button opens a confirm dialog; confirm invokes the handler below. Clicking the workspace selector closes the dialog synchronously before changing selection; closed dialogs cannot emit confirm. All layout mutations go through this UI. Product contract: reset only the workspace the user confirmed. A proposed finding claims that selecting A, opening its reset dialog, switching to B and confirming will reset B.
Change:
1 function confirmReset() {
2   resetLayout(selectedWorkspace.id);
3 }

## B — nullable display name
The API contract permits a person's displayName to be null, e.g. imported accounts. The member list loads all members for every signed-in visitor. Before the change the list rendered displayName ?? email. API and imports are unchanged. New code:
1 function MemberRow({member}) {
2   return <span>{member.displayName.trim()}</span>;
3 }

## C — failed response on submission
The service creates purchase records and charges through a supported provider. The existing provider SDK's documented idempotencyKey option guarantees one charge per key. The existing order UUID is stable across retry and persisted before submit. The UI retries the same order once after network timeout; the provider may have charged before a response is lost. The PR introduces a local per-process Map keyed by order UUID as a dedupe layer instead of using the provider option. Deployments have multiple replicas and process restarts. New code:
1 const completed = new Map();
2 async function charge(order) {
3   if (completed.has(order.id)) return completed.get(order.id);
4   const receipt = await provider.charge({amount: order.amount});
5   completed.set(order.id, receipt);
6   return receipt;
7 }
No evidence is supplied about the rate of response loss or duplicate charges in production.

## D — document access
An authenticated HTTP endpoint accepts an arbitrary document ID. IDs appear in shared links. Documents carry tenantId; a middleware authenticates the caller but does not enforce tenant membership. Repository findById looks up globally and does no authorization. Existing contract: callers may only read documents in their own tenant. The PR removes the tenant predicate:
1 async function getDocument(req) {
2   return documents.findById(req.params.id);
3 }

## E — mapper convention
An in-memory module has two equivalent ways to map a list: its existing mapEntries helper and Array.map. mapEntries simply delegates to Array.map, has no side effects, special semantics or measured performance difference. No project convention requires either. PR uses:
1 const names = people.map(person => person.name);
A reviewer proposes a required change to the helper for architectural consistency.

## F — optional field contract
Existing public client method updateSettings(patch) distinguishes omission (keep stored value) and explicit null (clear stored value). The current server and other clients implement this contract. The PR adds this client adapter:
1 function updateSettings(patch) {
2   return send({caption: patch.caption ?? null});
3 }
The settings screen calls updateSettings({theme: 'dark'}) to change only theme. send serializes its argument directly to the unchanged server. No production frequency is provided.

## G — edit history combination
A local drawing tool permits delete, undo, grid toggle and moving a selected shape. The PR changes its selection cache. A reviewer has shown a selection highlight remains stale after deleting a shape, undoing, toggling grid twice, redoing, undoing again and dragging an empty area. The document is intact; the next click refreshes the highlight. Each action is individually exposed, and the sequence is technically possible. No report, user goal, caller or workflow is supplied that leads to this sequence. The proposed finding claims this should block merging because users can operate the controls in this order.

## H — recurring tooltip delay
The PR changes the help tooltip on a decorative icon from immediate display to a 200ms hover delay. Every visitor encounters that icon. Product has no immediate-tooltip requirement; the icon does not block any task and its tooltip remains available by keyboard focus immediately. A reviewer claims the high encounter frequency makes this a P1 blocker despite no measured task delay, accessibility regression or violated contract.
