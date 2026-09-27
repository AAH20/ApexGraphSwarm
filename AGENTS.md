# ApexGraphSwarm engineering contract

Keep the Python control plane Python 3.10+ standard-library only. Preserve source provenance and licenses. Use targeted file reads. Run `python3 -m unittest discover tests` and `npm --prefix apps/web test` for changes; run web typecheck/build for frontend changes. Report measured test counts and timings honestly.

300 logical agents is a design and benchmark target, not a claim of 300 simultaneous paid model calls. Separate deterministic fixture benchmarks from live model evaluations. Never fabricate model prices, capability support, benchmark scores, or provider usage. Keep secrets server-side and out of Git, logs, exports and browser bundles. Unknown costs remain unknown. No real provider calls without a configured task and budget.

Jobs, leases and accounting transitions must be transactional and idempotent. Evaluate proposed evolution on held-out tasks before promotion. Preserve local-first operation and explicit adapters. Optional framework/service dependencies stay isolated from the stdlib control plane.
