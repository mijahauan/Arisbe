# Letter draft — John F. Sowa

**Status: internal draft in the author's voice (2026-07-28), built from
[LETTER_SOWA_SKELETON](LETTER_SOWA_SKELETON.md). Not for sending until the
author revises and signs. Salutation and closing left plain for his hand.**

---

Dear Dr. Sowa,

For several years I have worked on an environment for Peirce's existential
graphs. I call it Arisbe, after the house on the Delaware. Before I describe
what it attempts, I owe you an accounting of what in it belongs to you.

Arisbe implements your notations. EGIF serves as its working linear form;
CGIF and CLIF follow ISO/IEC 24707; a four-way round-trip — EGIF, CGIF, CLIF,
and a first-order rendering — runs against some ninety canonical examples in
its corpus. We invented none of these, and the claim we make reaches only
this far: we bound them together, checkably. Even the word "peel," our name
for the semantic evaluation that reads a graph from the outside in, comes
from your 2011 account of the endoporeutic game, where Graphist and Grapheus
take turns peeling off negations. The EG–DRS isomorphism remains yours,
tracing to Kamp; part of our written record exists precisely to keep us from
ever claiming it. One of the three rendering styles the engine draws carries
your name, and your examples sit in the corpus among the exemplars.

The one claim I would most value your judgment on concerns what we call the
correspondence invariant. Every pair the system serves — a graph as drawn, a
graph as written — passes through a runtime check that reads containment,
incidence, and the crossings of each ligature off the drawn shape itself, and
refuses any pair whose two forms fail to denote one object. The picture and
the sentence stand as two projections of a single mathematical structure, and
the system attests this on every request — not once, in a proof appendix, but
each time anyone looks.

As far as we could determine, no tool in the CG or EG lineage has enforced
this. You know that lineage better than anyone alive; you built much of it.
If prior art exists, you would know where it hides — and a counterexample
from you would teach us more than agreement ever could.

Beyond that claim, the game you described now runs. A person can play it
hot-seat in a browser. The machine can also play it autonomously — three
language-model roles arguing under an incorruptible mechanical referee, so
that the model argues and the calculus decides — with the domain model
developing through play against live sources, Wikidata among them. The run
logs sit in the open repository, priors registered before each run, refuted
priors kept on the record beside the held ones.

I would rather have your refutation than your admiration. Four questions,
roughly in rising order of what an answer would cost us:

1. Does the claim above survive your knowledge of the field — or does prior
   art exist that we missed? We searched and found none, which proves only
   the limits of our searching.
2. Where does our CGIF conformance fall short of the ISO text as you read it?
3. Our treatment of your Proposition-typed context node takes the graph-of-a-
   graph as mention, never use — a quotation device, conservative over the
   first-order core. Does that reading sit with your intent?
4. And a steer, if you care to give one: what would make this genuinely
   useful to the CG community you built?

Everything above stands behind links you can walk — the correspondence
contract, the round-trip suites, the intellectual history that places your
work in the lineage it belongs to, and a five-minute path from install to a
drawn, round-tripped graph. A competent refutation from you would count as
the system working, not the system failing. No one has the last word here,
least of all us.

With respect and gratitude,

Michael Hauan
