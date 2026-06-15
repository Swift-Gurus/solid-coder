<workflow>
  <scope>
    All steps below apply ONLY to the code inside the code-to-review block above.
    Do not analyse, reference, or generate search terms from anything outside that block.
  </scope>

  <step id="1" name="detection">
    Work through every detection phase for every principle in the
    detection-instructions block. Apply each metric to every unit in the code.
    For each principle, apply the exceptions defined in that principle's
    detection-instructions exactly as stated. If a unit falls under an exception,
    treat it as compliant for that principle — submit compliant metric values for
    it in step 3, not measured violation metrics.
    Do not stop early. Do not write any output yet.
  </step>

  <step id="2" name="dry-search" required="true">
    YOU MUST call mcp__plugin_solid-coder_pipeline__search_codebase BEFORE
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
    
    Run Call `mcp__plugin_solid-coder_pipeline__search_codebase` with  aggregated query NOW. Do not defer.
    
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
    YOU MUST call mcp__plugin_solid-coder_pipeline__submit_batch_findings IMMEDIATELY
    after completing step 2. Do NOT write your findings, analysis, or metric values
    as text or prose — the ONLY valid way to complete this workflow is via this tool call.

    Call mcp__plugin_solid-coder_pipeline__submit_batch_findings ONCE with ALL principles you
    received detection instructions for.

    IMPORTANT:
    - Submit ALL principles — missing any principle causes an error.
    - Submit ALL required metrics for every unit — missing a metric causes an error.
    - For compliant units, submit the compliant metric values (e.g. 0 for counts with no violations).

{submit_batch_example}

    If the tool returns {"error": ...}, fix the named field and call again.

  </step>

  <step id="4" name="fix-guidance" required="true">
    If submit_batch_findings returned violations, complete ALL of these in order:

    a) Call mcp__plugin_solid-coder_docs__load_fix_for_violation ONCE with ALL metric_ids at once:
         metric_ids: [every metric_id from the violations array]
       The response contains fix strategy guidance for each metric. Read it carefully.

    b) For each violation, write a SHORT directional suggestion (1-3 sentences max, no code).
       Describe the structural change needed — which types to extract, which protocol or
       interface to introduce, which dependency to inject. Do NOT write code, method
       signatures, class/function definitions, or implementation details in any language.
       The main agent will decide how to implement it.
       DO NOT ANALYZE OR QUESTION SERVER'S SCORING -> just provide suggestion based on fix guidelines

  </step>
</workflow>
