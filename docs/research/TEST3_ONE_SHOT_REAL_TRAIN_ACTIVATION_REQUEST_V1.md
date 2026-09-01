# Test 3 One-Shot Real TRAIN Activation Request V1

**Status:** `PREPARATION_ONLY_NOT_ACTIVATION / NO_AUTHORITY`

## Purpose

This document describes the later decisions that would be required to create and consume one
Test 3 activation. It does not make those decisions, activate Test 3, establish scientific
readiness, create evidence, reserve authority, expose a protected path, or authorize a fit.

The preparation candidate consists only of the closed activation plan, its local deterministic
generator, synthetic tests, and this request. The plan deliberately omits every implementation
digest and the activation-payload digest, so it cannot be presented to the reviewed loader as an
activation envelope.

## Frozen preparation boundary

The prepared generator has three modes:

- `check` reconstructs the would-be envelope in memory from the reviewed source constants and
  current six implementation files. It requires the activation and every activation-bound
  evidence surface to be absent and writes nothing.
- `create` implements a future create-once, durable publication, but may not be invoked against
  the repository under this preparation authority.
- `verify-existing` is a read-only, non-claiming post-publication verifier. It recomputes the
  complete envelope from the reviewed sources and current bytes and requires byte-exact canonical
  equality. It never invokes the loader, creates a replay claim, returns a capability, or enters a
  runner path.

The generator statically reads the reviewed Python source. It does not import the G3-P or G3-F
runtime modules, invoke the scientific runner, access a provider, or read scientific data.

## Required later causal order

1. This preparation candidate must pass its focused synthetic tests, Ruff, real-repository static
   `check`, machine firewall, and fresh cross-family review.
2. The four preparation files may then be committed and pushed without creating an activation.
3. The Owner separately reviews the exact prepared plan, generator, six-path implementation
   binding process, and all prohibitions.
4. Only a new exact Owner authorization may permit one real-repository `create` invocation. That
   later decision must bind the exact intended repository state and output and must not be inferred
   from this request.
5. After that separately authorized publication, the created envelope must pass the generator's
   read-only, non-claiming `verify-existing` mode. Verification must not invoke the loader, create
   a claim, write any file, or enter the runner.
6. Only a further exact scientific-execution authorization may permit the runner's first
   real-repository loader invocation, activation consumption, replay claim, execution-authority
   reservation, protected source or target access, or the four TRAIN fits.

Each later step is fail-closed and independently authorized. Completion of one step never implies
authority for the next.

## Frozen future names

The preparation plan freezes a single future override and recovery lineage, exactly four ordered
fit permits, one execution-authority reservation name, one terminal name, one G3-F evidence root
and namespace, and the two mechanically derived G3-P request/target witness paths. These are names
only. The G3-P witnesses remain under the reviewed G3-P recovery root and are not relocated into
the G3-F runtime evidence namespace.

## What remains prohibited

This request does not authorize or claim completion of any of the following:

- Decision C or Phase B;
- activation publication or consumption;
- a loader invocation against the real repository;
- an activation replay claim, execution reservation, permit, witness, terminal, or other evidence;
- provider, source-path, target-path, protected-path, or numeric-target access;
- a real fit, bootstrap, Validation, Final Test, Test 3b, Test 4, or any scientific execution;
- OIDC, signing, server, cloud, external service, or release machinery.

The only valid disposition of this document is
`PREPARATION_ONLY_NOT_ACTIVATION / NO_AUTHORITY` until the separate later Owner decisions above are
made in their required order.
