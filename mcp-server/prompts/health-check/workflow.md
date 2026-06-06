<workflow>
  <scope>
    All steps below apply ONLY to the code inside the code-to-review block above.
    Do not analyse, reference, or generate search terms from anything outside that block.
  </scope>

  <step id="1" name="detection">
    Work through every detection phase for every principle in the
    detection-instructions block. Apply each metric to every unit in the code.
    Do not stop early. Do not write any output yet.
  </step>

  <step id="2" name="dry-search" required="true">
    YOU MUST call mcp__pipeline__search_codebase
    moving to step 3. Do not skip this step — it is required even when you
    believe no DRY violation exists, because absence must be confirmed by search.

    a) For each code unit (class, struct, enum, protocol, top-level function)
    in the code-to-review block to prepare a query:
     - [] Split its name by camelCase boundaries into component words
       (e.g. UserManager becomes User Manager).
     - [] Describe its responsibility in plain words and generate 3 domain-aware
       synonyms per keyword.
     - [] Build a search query: name + camelCase words + responsibility keywords +
       synonyms, all space-separated.
    
    Run Call `mcp__pipeline__search_codebase` with  aggregated query NOW. Do not defer.
    
    b) Skip any result whose path is {file_path} — that is the file being
       written and cannot be a reuse source for itself.
    c) For each remaining match, read its solid-description. If the description
       overlaps in domain, operations, or responsibilities with the code unit
       being reviewed, read the file to inspect its types and method signatures.
       Apply DRY-1 detection criteria based on what you find in the file —
       does it already implement the same logic? Could it be reused instead of
       writing new code? Only skip a match if its description is clearly
       unrelated in domain and purpose.

  </step>

  <step id="3" name="submit" required="true">
    Call mcp__pipeline__submit_batch_findings ONCE with ALL principles you
    received detection instructions for.

    IMPORTANT:
    - Submit ALL principles — missing any principle causes an error.
    - Submit ALL required metrics for every unit — missing a metric causes an error.
    - For compliant units, submit the compliant metric values (e.g. 0 for counts with no violations).

    EXCEPTION RULES — apply these during detection; submit compliant values when they match:

    ISP SCOPE: include ONLY units with unit_kind "protocol" or "interface".
      Omit every class, struct, enum, extension, and function from ISP entirely.

    SRP FACADE EXCEPTION: if a unit has ALL of the following — all dependencies are
      protocol-typed (no concrete types in init), all methods are pure delegation (no
      logic or transformation, each method calls exactly one injected dep), no internal
      construction (no `X()` calls in methods) — submit cohesion_groups=1 and
      stakeholder_count=1. This is the Facade/Coordinator exception; it is COMPLIANT
      regardless of the measured group count.

    LSP EXCEPTION — CRITICAL: the server scores the number you SUBMIT, not your analysis.
      If you identify LSP exceptions during detection, you MUST submit type_checks=0 — NOT
      the raw measured count. Submitting type_checks=1 causes a SEVERE score even if you
      note "exception applies" in the suggestion. The fix is to submit 0.
      Submit type_checks=0 when ALL isinstance/type checks in a unit fall into exempt categories:
      - input validation at a method boundary (isinstance(x, list/dict/str/int) to guard an arg)
      - except ConcreteExceptionType clauses in try/except for error recovery
      - checking types of values from external libraries or JSON (not developer-owned hierarchies)
      Only submit type_checks > 0 for: isinstance(obj, AbstractBase) where the RESULT selects
      different subtype-specific behavior — that is the actual LSP violation pattern.

    OCP EXCEPTION — standard library types (Path, json, shutil, re, copy) used directly
      are helpers, not sealed variation points. Do NOT flag them as sealed_variation_points.

{submit_batch_example}

    If the tool returns {"error": ...}, fix the named field and call again.

  </step>

  <step id="4" name="fix-submission" required="true">
    If submit_batch_findings returned violations, complete ALL of these in order:

    a) Call mcp__docs__load_fix_for_violation ONCE with ALL metric_ids at once:
         metric_ids: [every metric_id from the violations array]
       The response contains fix strategy guidance for each metric. Read it carefully.

    b) For each violation, write a SHORT directional suggestion (1-3 sentences max, no code).
       Describe the structural change needed — which types to extract, which protocol or
       interface to introduce, which dependency to inject. Do NOT write code, method
       signatures, class/function definitions, or implementation details in any language.
       The main agent will decide how to implement it.
       DO NOT ANALYZE OR QUESTION SERVER'S SCORING -> just provide suggestion based on fix guidelines


    c) Call mcp__pipeline__submit_fix ONCE with output_dir and a fixes array covering
       every violation:
         output_dir: the output_dir value from the submit_batch_findings response
         fixes: [
           { "metric_id": "...", "file_path": "...", "unit_name": "...", "suggested_fix": "..." },
           ... one entry per violation ...
         ]

       If submit_fix returns {"error": ...}, fix the named field and retry.
       submit_fix returns {"complete": true, "violations_with_fixes": [...]} on success.
  </step>
</workflow>
