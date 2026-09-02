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

{dry_search_step}

  <step id="3" name="submit" required="true">
    YOU MUST call mcp__pipeline__submit_batch_findings IMMEDIATELY
    after completing {submission_predecessor}. Do NOT write your findings, analysis, or metric values
    as text or prose — the ONLY valid way to complete this workflow is via this tool call.

    Call mcp__pipeline__submit_batch_findings ONCE with ALL principles you
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

    a) Call mcp__docs__load_fix_for_violation ONCE with ALL metric_ids at once:
         metric_ids: [every metric_id from the violations array]
       The response contains fix strategy guidance for each metric. Read it carefully.

    b) Call mcp__pipeline__submit_fix ONCE with ALL violations:
         output_dir: same output_dir used in step 3
         fixes: one entry per violation with rule_id, file_path, unit_name, and suggested_fix
       For each violation's suggested_fix: write a SHORT directional suggestion (1-3 sentences max, no code).
       Describe the structural change needed — which types to extract, which protocol or
       interface to introduce, which dependency to inject. Do NOT write code, method
       signatures, class/function definitions, or implementation details in any language.
       Base the suggestion on the guidance returned from mcp__docs__load_fix_for_violation.
       DO NOT ANALYZE OR QUESTION SERVER'S SCORING -> just provide suggestion based on fix guidelines

  </step>
</workflow>
