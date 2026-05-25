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
    YOU MUST call mcp__pipeline__search_codebase for every code unit before
    moving to step 3. Do not skip this step — it is required even when you
    believe no DRY violation exists, because absence must be confirmed by search.

    For each code unit (class, struct, enum, protocol, top-level function)
    in the code-to-review block:
    a) Split its name by camelCase boundaries into component words
       (e.g. UserManager becomes User Manager).
    b) Describe its responsibility in plain words and generate 3 domain-aware
       synonyms per keyword.
    c) Build a search query: name + camelCase words + responsibility keywords +
       synonyms, all space-separated.
    d) Call `mcp__pipeline__search_codebase` with that query NOW. Do not defer.
    e) Skip any result whose path is {file_path} — that is the file being
       written and cannot be a reuse source for itself.
    f) For each remaining match, read its solid-description. If the description
       overlaps in domain, operations, or responsibilities with the code unit
       being reviewed, read the file to inspect its types and method signatures.
       Apply DRY-1 detection criteria based on what you find in the file —
       does it already implement the same logic? Could it be reused instead of
       writing new code? Only skip a match if its description is clearly
       unrelated in domain and purpose.

    You must complete a search call for every unit before proceeding.
  </step>

  <step id="3" name="fix-guidance" required="true">
    YOU MUST call mcp__docs__load_fix_for_violation for every SEVERE violation
    before writing the final JSON. Do not write output until all calls complete.

    For every SEVERE violation found in steps 1 and 2:
    a) Call `mcp__docs__load_fix_for_violation` with its metric_id NOW.
    b) The tool returns fix strategy guidance. Apply it to the specific code.
    c) Write a concrete, code-specific solution into the `fix` field.
    d) Do NOT copy guidance verbatim or write placeholder text.
  </step>
</workflow>

Only after ALL tool calls in steps 2 and 3 are complete, write your final JSON response.
