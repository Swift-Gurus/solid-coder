After completing all steps, return your final output as raw JSON with no commentary.

If submit_batch_findings returned violations and you completed step 4:
  Return the {"complete": true, "violations_with_fixes": [...]} result from the
  final submit_fix call. Pass it through as-is.

If there were no violations (submit_batch_findings returned {"violations": []}):
  Return: {"violations": []}

Do NOT add markdown, commentary, or extra text — return only the raw JSON.
