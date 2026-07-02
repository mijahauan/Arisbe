-- Strip standalone-doc "chrome" from chapters AT RENDER TIME only, so the book
-- reads as a book while the in-repo sources keep their orientation headers.
-- (Author decision 2026-07-02 — see ALPHA_RELEASE_PLAN.md "Book-voice".)
--
-- What is stripped, and only in the FRONT-MATTER ZONE (blocks before the first
-- level>=2 heading):
--   1. Leading blockquotes that are reader-routing chrome: "What this is.",
--      "Read this first", "New here? …", "Start here".
--   2. Doc-metadata paragraphs: "**Status**: …", "**Date**: …", "**Reviewed**: …"
--      (incl. the middle-dot combined forms).
--   3. Inside surviving front-zone blockquotes: child paragraphs that are pure
--      maintenance dates ("Last consolidated/updated/refreshed: …", "Created
--      2026-…", "Drafted: …", "Read alongside: …"); a blockquote emptied by
--      this is dropped.
-- Date-footer lines ("Last consolidated: …") are stripped anywhere in the doc.
-- Substantive caveat blockquotes (e.g. "Updated 2026-06-08. …the Qt GUI was
-- archived…") are deliberately KEPT — they carry content, not chrome.

local function text_of(el)
  return pandoc.utils.stringify(el)
end

-- chrome blockquote openers (front zone only)
local QUOTE_CHROME = {
  "^What this is", "^Read this first", "^New here%?", "^Start here",
}

-- doc-metadata paragraph openers (front zone only)
local META_FRONT = {
  "^Status[:%s]", "^Date[:%s]", "^Reviewed[:%s]", "^Goal[:%s]", "^Users[:%s]",
}

-- pure maintenance-date lines (stripped anywhere)
local META_DATES = {
  "^Last consolidated", "^Last updated", "^Last refreshed", "^Last revised:",
  "^Created 20%d%d", "^Drafted[:%s]", "^Reorganized[:%s]", "^Read alongside",
}

local function matches_any(s, pats)
  for _, p in ipairs(pats) do
    if s:match(p) then return true end
  end
  return false
end

local function is_date_line(b)
  local s = text_of(b)
  return matches_any(s, META_DATES)
end

-- filter a blockquote's children for maintenance-date paras; nil if emptied
local function scrub_quote(bq)
  local kept = {}
  for _, child in ipairs(bq.content) do
    if not ((child.t == "Para" or child.t == "Plain") and is_date_line(child)) then
      table.insert(kept, child)
    end
  end
  if #kept == 0 then return nil end
  return pandoc.BlockQuote(kept)
end

function Pandoc(doc)
  local out = {}
  local front = true
  for _, b in ipairs(doc.blocks) do
    if front and b.t == "Header" and b.level >= 2 then
      front = false
    end
    local keep = true
    local replacement = b
    if front then
      if b.t == "BlockQuote" then
        if matches_any(text_of(b), QUOTE_CHROME) then
          keep = false
        else
          local scrubbed = scrub_quote(b)
          if scrubbed == nil then keep = false else replacement = scrubbed end
        end
      elseif (b.t == "Para" or b.t == "Plain")
          and (matches_any(text_of(b), META_FRONT) or is_date_line(b)) then
        keep = false
      end
    else
      if (b.t == "Para" or b.t == "Plain") and is_date_line(b) then
        keep = false
      end
    end
    if keep then table.insert(out, replacement) end
  end
  doc.blocks = out
  return doc
end
