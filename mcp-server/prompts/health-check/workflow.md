<workflow>
  <scope>
    All steps below apply ONLY to the code inside the code-to-review block above.
    Do not analyse, reference, or generate search terms from anything outside that block.
  </scope>

  <step id="1" name="detection">
    Work through every detection phase for every principle in the
    detection-instructions block. Apply each metric to every unit in the code.
    Do not stop early.
  </step>

  <step id="2" name="dry-search">
    For each code unit (class, struct, enum, protocol, top-level function)
    in the code-to-review block:
    a) Split its name by camelCase boundaries into component words
       (e.g. UserManager becomes User Manager).
    b) Describe its responsibility in plain words and generate 3 domain-aware
       synonyms per keyword.
    c) Build a search query: name + camelCase words + responsibility keywords +
       synonyms, all space-separated.
    d) Call `mcp__pipeline__search_codebase` with that query.
    e) Skip any result whose path is {file_path} — that is the file being
       written and cannot be a reuse source for itself.
    f) Apply DRY-1 detection criteria to the remaining matches.
  </step>

  <step id="3" name="fix-guidance">
    For every SEVERE violation found:
    a) Call `mcp__docs__load_fix_for_violation` with its metric_id (e.g. metric_id="OCP-1").
    b) The tool returns fix strategy guidance in the `content` field.
    c) Apply that guidance to the specific code being reviewed.
    d) Write a concrete, code-specific solution into the `fix` field.
    e) Do NOT copy the guidance verbatim or write placeholder text.
  </step>
</workflow>

Only after completing all workflow steps, write your final JSON response.
