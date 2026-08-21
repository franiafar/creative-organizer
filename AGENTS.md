# Creative Organizer update instructions

For every task in this repository, load and follow `$update-creative-organizer` when it is available. Always read `docs/taxonomy-contract.md` completely before inspecting, changing, testing, documenting, packaging, or releasing the app.

The taxonomy contract is locked by Fran. Do not modify, weaken, reinterpret, bypass, or remove any contract rule unless Fran explicitly authorizes that exact change in the current request. General requests to improve, refactor, fix, update, redesign, optimize, package, or release the app do not authorize contract changes.

If a request conflicts with the contract, stop before editing and ask Fran. When Fran explicitly authorizes a rule change, update implementation, tests, `docs/taxonomy-contract.md`, the installed skill contract, and user-facing examples together.

Run the complete relevant regression suite before claiming completion. Do not publish a release that fails taxonomy tests, preview-without-write verification, second-run idempotency, rollback, undo, bundle build, or signature verification.
