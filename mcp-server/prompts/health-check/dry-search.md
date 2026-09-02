  <step id="2" name="dry-search" required="true">
    YOU MUST call mcp__pipeline__search_codebase BEFORE
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

    Call `mcp__pipeline__search_codebase` ONCE with this exact input shape NOW:
      - `query`: the aggregated space-separated query prepared above
      - `output_dir`: `{output_dir}`
    Do not pass the aggregated query as one entry in `tags`. A malformed search
    is rejected and does not satisfy this required step. Do not defer the call.

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
