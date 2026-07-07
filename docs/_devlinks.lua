-- Rewrite links to docs that are NOT book chapters (dev / design-of-record /
-- archive docs, and repo-root files like CLAUDE.md) to their GitHub source URL,
-- so the rendered book/help has no dead internal links. Links between book
-- chapters are left relative for Quarto to resolve to .html.
--
-- Keep BOOK in sync with the chapter list in _quarto.yml (top-level docs only).

local GH = "https://github.com/mijahauan/Arisbe/blob/main/"

local BOOK = {
  VISION_AND_SCOPE = true,
  LINEAR_GRAPHICAL_CORRESPONDENCE = true,
  CHAIN_OF_SEMIOSIS = true,
  MANIFEST_AND_MEANING = true,
  FIDELITY_A_PLAIN_ACCOUNT = true,
  FIDELITY_AND_DEPARTURES = true,
  FIDELITY_ENDOPOREUTIC_CHECK = true,
  ADVERSARIAL_EXAMINATION = true,
  LEVEL_ZERO_AND_THE_REGISTERS = true,
  MODALITY_WITHOUT_GAMMA = true,
  GAMMA_DEMONSTRATIONS = true,
  FIELD_GUIDE_AND_DRAGONS = true,
  GETTING_STARTED = true,
  ARISBE_FOR_SCHOLARS = true,
  ARISBE_IN_PRACTICE = true,
  ENDOPOREUTIC_GAME_GUIDE = true,
  EXEMPLARS = true,
  EXTERNAL_SOURCES_AND_IMPORT = true,
  FREEFORM_COMPOSITION_AND_LEARNING = true,
  TROUBLESHOOTING = true,
  FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION = true,
  NL_TO_LOGIC = true,
  arisbe_triad_architecture = true,
  UNIVERSE_OF_DISCOURSE_ARCHITECTURE = true,
  DAG_HISTORY_ARCHITECTURE = true,
  EXACT_CORRESPONDENCE = true,
  DOMAIN_ORACLE_AND_M = true,
  GENERATION_AND_TESTING = true,
  CAPABILITY_MAP = true,
  IMPORT_EXPORT_FORMATS = true,
  CHAPTER18_FOPL_TRANSLATION_DOCUMENTATION = true,
  GLOSSARY = true,
  CONTRIBUTION_AND_PRIOR_ART = true,
  ARISBE_CORE_API_REFERENCE = true,
}

function Link(el)
  local t = el.target
  if t == nil or t == "" then return el end
  if t:match("^%a[%w+.-]*://") then return el end   -- external URL
  if t:match("^#") then return el end                -- in-page anchor
  if t:match("^mailto:") then return el end

  -- separate path from any #anchor
  local path = t:match("^([^#]*)") or t

  -- repo-root links: ../CLAUDE.md, ../AGENTS.md, ../src/..., ../tests/...
  local up = path:match("^%.%./(.+)$")
  if up then
    el.target = GH .. up
    return el
  end

  -- a markdown doc under docs/
  local mdpath = path:match("^(.+)%.md$")
  if mdpath then
    -- a top-level book chapter: leave relative for Quarto to resolve
    if (not mdpath:find("/")) and BOOK[mdpath] then return el end
    -- otherwise it is a dev / archive doc not in the book: point at GitHub
    el.target = GH .. "docs/" .. path
    return el
  end

  return el
end
