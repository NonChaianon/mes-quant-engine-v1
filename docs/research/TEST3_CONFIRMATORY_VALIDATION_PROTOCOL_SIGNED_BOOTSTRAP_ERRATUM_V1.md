# TEST3 CONFIRMATORY VALIDATION PROTOCOL — SIGNED BOOTSTRAP ERRATUM V1

**Label:** `PROPOSED_ERRATUM / NOT_AUTHORITY / NOT_RATIFICATION / DATA_FREE / NO_EXECUTION_AUTHORITY`

## 1. Standing

This is a **proposed** erratum to the non-ratified candidate
`docs/research/TEST3_CONFIRMATORY_VALIDATION_PROTOCOL_PREPARATION_V1.md` ("Protocol V1"). It is not
an Owner authorization, not a ratification, not an activation, and not evidence. It binds nothing
now. It was written data-free: no data, provider, target, evidence, partition, row, runtime artifact
or execution output was read.

## 2. Classification

Protocol V1, as currently written, is classified `PRE_RATIFICATION_NO_GO`.

The sole and complete reason for this classification is **Section 5.5 item 5**, which requires that
for each bootstrap replicate "The denominator and result must be positive and finite." No other
clause of Protocol V1 is cited, faulted, weakened or reopened by this erratum.

## 3. The defect

`D_star[r]` is a **signed** BASE-minus-HAR improvement statistic. Under Section 5.1, `d_i` is
`L_BASE_i - L_HAR_i`, and under Section 5.4 the replicate statistic is the pooled row-weighted
`D_star = sum(S_s for selected s) / sum(n_s for selected s)`. A positive value favours `RVHAR001`; a
negative value favours `RVBASE001`. Nothing in the specification makes the numerator sign-restricted,
and the denominator is a sum of positive integer session row counts.

Requiring **every replicate result** to be positive therefore contradicts the surrounding contract:

- **Section 5.4** requires only that "Every replicate must be finite," and then requires the
  fifth-percentile lower bound over those replicates to be strictly greater than 0. A distribution in
  which every replicate is already positive by construction would make that lower-bound gate
  vacuous, and would make the frozen 2,000-replicate sampling incapable of expressing the
  no-improvement and BASE-favouring outcomes it exists to measure.
- **Section 6** fixes a strict `D > 0` PASS criterion and an asymmetric equality rule in which a mean
  of exactly 0 fails. That criterion presupposes that non-positive aggregate and replicate values are
  representable and scoreable outcomes, not defects.
- **Section 7.2** places scoring in tier 3, reached only after integrity and structural support have
  passed, and classifies a valid scored result that misses a Section 6 criterion as
  `NOT_CONFIRMED_ON_OUTER_VALIDATION_TEST3_TERMINAL`. Treating a legitimately negative or zero
  replicate as an integrity or arithmetic defect would push a real scientific non-confirmation into
  `INVALID_EVIDENCE`, collapsing the non-overlapping trichotomy that Section 7.2 declares exhaustive.
- The **reviewed tooling behaviour is finite-only** and the **golden-fixture replicate behaviour is
  signed**. A positivity precondition on each replicate is inconsistent with the finite-only
  validation surface and with the signed replicate vectors that the frozen golden fixture replays
  bytewise.

The defect is a single over-strong normative word applied to the wrong operand: positivity belongs
to the denominator, not to the signed result.

## 4. Proposed supersession — exactly one normative requirement

This erratum proposes to supersede **only** the following exact normative requirement in Protocol V1
Section 5.5 item 5:

> The denominator and result must be positive and finite.

and to replace it with:

> The denominator must be positive and finite, and each stored `D_star[r]` must be finite with sign
> unconstrained.

Nothing else in item 5 is displaced. The `float64` left folds over `S_s` and `numpy.float64(n_s)`,
the `D_star[r] = numpy.float64(num / den)` materialization, the C-contiguous `numpy.float64`
replicate vector, the index-order and draw-order traversal including repeats, and the single
authoritative `numpy.quantile(D_star, numpy.float64(0.05), method='linear')` call per `L` are
retained unchanged.

## 5. Consequence for terminal classification

Negative, zero and positive **finite** replicates are all valid scored outcomes. A replicate does
**not** become `INVALID_EVIDENCE` solely because of its sign. A nonfinite replicate, a nonpositive or
nonfinite denominator, and every other integrity, domain, ordering, counter, seal or arithmetic
defect remain `INVALID_EVIDENCE` exactly as Protocol V1 Section 7.2 tier 1 requires.

## 6. Everything else unchanged

The following are retained without alteration:

- the **strict primary fifth-percentile one-sided 95 percent lower-bound greater-than-zero PASS
  gate**, with exact equality at 0 failing;
- **no rescue** and **no redraw** — no reseed, no best-of-seeds, and no promotion of the 1-session or
  20-session diagnostics over the primary 5-session result;
- the **fixed frozen seed schedule**, `master_seed = 20260809`, the derived pooled and Validation
  seeds, the `(5, 1, 20)` block order and 2,000 replications each;
- every other clause of Protocol V1, including Sections 0.1 through 0.1.6, 1 through 5.4, the
  remainder of 5.5, and Sections 6 through 9.

## 7. Byte state and budget

No tooling, test, binding or candidate document is modified by this erratum. The tooling script, its
tests, the existing tooling binding artifact and the four candidate documents remain
**byte-identical**. This erratum reopens **no** `check`, `create` or `verify-existing` invocation
budget, requests no rerun of any deterministic mode, and produces no digest, hash or Git object
identifier of any kind.

## 8. Co-ratification requirement

This erratum and Protocol V1 must be **co-ratified as one contract** before either becomes
operative. Protocol V1 must not be ratified alone while Section 5.5 item 5 stands as written, and
this erratum has no meaning apart from Protocol V1. A future ratification, activation, implementation
acceptance or grant must cite and bind both exact byte sets together.

## 9. No authority created

This document creates **no** authority. It is not an implementation, `C0`, `C0V`, activation, permit,
reservation, fit, witness, Validation opening or Final Test action. It grants no data, provider,
target, path or evidence access, no staging, no commit, no push, no merge, and no scientific
authority. It does not ratify itself and does not ratify Protocol V1.

## 10. Scope

One proposed erratum. One classification cause. One superseded normative requirement. One
co-ratification condition. Zero other changes and zero authority.
