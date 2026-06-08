# Arisbe in Practice

## How Knowing, Making, and Contesting Build Understanding

Arisbe provides three complementary ways of working with knowledge,
modelled on how reasoning actually happens in the world:

- **Organon** — the library. Browse, study, and compare what is already known.
- **Ergasterion** — the workshop. Build new claims, descriptions, and ideas.
- **Agon** — the arena. Test a new claim against established knowledge to
  discover what it means.

These three activities form a cycle. You study what you know (Organon), craft
something new (Ergasterion), test it (Agon), and the result flows back into
what you know. This document walks through practical scenarios that show
how the cycle works — in language meant for anyone, not just logicians.

This is the narrative on-ramp; the formal account of the testing step (the
Endoporeutic Game — its rules, its outcome taxonomy, and the Peircean theory of
inquiry behind it) is in [ENDOPOREUTIC_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md).
Each scenario below is a concrete instance of one of that guide's outcome cases;
the guide's Part II gives the scenario-by-scenario mapping.

One rule keeps the cycle honest: work in the workshop never lands directly in
the library. A graph reaches the trusted record (the corpus) only by being
*tested through Agon*, or as a presentation-only restyling of something already
trusted. Until then, a workshop draft lives in a private scratch space. So
where a scenario below says a new claim "becomes part of what she knows," read
it as: the claim was made in the workshop and then earned its place by being
contested.

---

## Scenario 1: What You Already Knew

### The veterinarian's reasoning

Dr. Melo runs a small animal clinic. Over the years she has built up a body
of knowledge about animal biology:

> Every mammal is warm-blooded.
> Every warm-blooded animal needs temperature regulation when under anaesthesia.
> Dogs are mammals.

A client brings in a dog named Biscuit for surgery. Dr. Melo needs to confirm
that she should prepare temperature regulation equipment.

**Organon** — Dr. Melo reviews her knowledge base. She can see the three
assertions laid out, browse their relationships, and confirm they are current
and agreed-upon.

**Ergasterion** — She constructs a new claim: "Biscuit needs temperature
regulation during surgery." This is her *proposal* — a sentence she believes
follows from what she knows, but has not yet formally verified.

**Agon** — She puts the proposal to the test. The game is framed as a
question: "Given everything Dr. Melo knows, does it follow that Biscuit
needs temperature regulation?"

The game proceeds by unwrapping the claim from the outside in:

1. Biscuit is a dog. Does the knowledge base confirm this? *Yes* — the
   client brought a dog.
2. Dogs are mammals. Does the knowledge base confirm this? *Yes* — it's
   one of the established facts.
3. Mammals are warm-blooded. Confirmed.
4. Warm-blooded animals need temperature regulation under anaesthesia.
   Confirmed.

Every link in the chain checks out. The claim is a **theorem** — it was
already implicit in what Dr. Melo knew. The game merely made it explicit.

**The result flows back**: The conclusion "Biscuit needs temperature
regulation" can now be added to the record for this patient — a new explicit
fact derived from established knowledge.

### What this illustrates

This is *deduction* — drawing out what is already contained in what you know.
The Agon did not tell Dr. Melo anything surprising; it confirmed that her
reasoning was sound. In formal terms, this is the simplest kind of game:
the Proposer wins because every piece of the claim maps onto something in
the established knowledge.

---

## Scenario 2: Something Genuinely New

### The birdwatcher's discovery

Tomás keeps a careful log of birds in his local wetland reserve. His
knowledge base records dozens of species with their characteristics:

> Herons are wading birds.
> Wading birds have long legs.
> Kingfishers are diving birds.
> Diving birds nest near riverbanks.

One morning he spots a bird he has never recorded: it has bright blue plumage,
a long bill, and it dives into the water from an overhanging branch.

**Organon** — Tomás searches his knowledge base. No existing entry matches
this combination of traits. He finds partial matches — kingfishers dive,
herons have long bills — but nothing that captures the whole bird.

**Ergasterion** — He constructs a description: "There exists a bird in the
reserve that is blue, has a long bill, and dives from branches." He also
drafts a tentative identification: "This bird is an Azure Kingfisher."

**Agon** — He tests his proposal against the knowledge base. The game
unwraps it:

1. "There exists a bird in the reserve with these traits." The knowledge
   base says nothing about this — it neither confirms nor denies it.
2. "This bird is an Azure Kingfisher." The knowledge base has no entry
   for Azure Kingfishers.

The game reaches a **stalemate** — not because anything is wrong, but
because the proposal is *independent* of the existing knowledge. It doesn't
contradict anything; it simply goes beyond what is currently recorded.

**The game produces an interpretation**: Since the claim is compatible
with everything known, and Tomás has direct observational evidence (he
saw the bird), he accepts it as a **new fact**.
The knowledge base grows: it now includes the Azure Kingfisher, its traits,
and the observation date.

**The result flows back**: Future queries — "What diving birds live in the
reserve?" — will now include the Azure Kingfisher.

### What this illustrates

This is *empirical enlargement* — adding genuinely new knowledge that could
not have been derived from what was already known. The Agon's role here was
not to prove or refute but to *sort* the proposal: it confirmed that the new
claim is consistent with existing knowledge and independent of it, which is
exactly the condition under which a new fact can be accepted.

---

## Scenario 3: A Contradiction That Teaches

### The gardener's surprise

A community garden has a shared knowledge base of growing wisdom:

> Tomatoes require full sun.
> The north bed is in full shade.

From these two facts, everyone has accepted as given:

> Tomatoes cannot grow in the north bed.

One season, a new member, Priya, plants cherry tomatoes in the north bed
using reflective mulch. To everyone's surprise, the plants fruit
abundantly. Priya proposes: "Tomatoes can grow in the north bed."

**Organon** — The group reviews their knowledge base and sees the existing
assertions. The derivation "tomatoes cannot grow in the north bed" is
indeed what follows from the current knowledge.

**Ergasterion** — Priya constructs her claim formally: "Cherry tomatoes
grew in the north bed (this season, with reflective mulch)."

**Agon** — The claim is tested against the knowledge base. The game finds
a problem:

1. "Tomatoes grew in the north bed." But the knowledge base says tomatoes
   require full sun, the north bed has full shade, and therefore tomatoes
   cannot grow there.

The claim **contradicts** the established knowledge. This is a *refutation*
of the proposal — or is it?

**But the game's interpretive function goes deeper than a simple
verdict**: A contradiction does not necessarily mean the proposal is wrong.
It means the proposal and the established knowledge cannot both be true
as stated. There are several possibilities:

- **Reject the proposal**: Perhaps the cherry tomatoes were not really
  thriving, or the north bed got more light than thought.
- **Revise the knowledge base**: Perhaps "tomatoes require full sun" is too
  strong. A more accurate rule might be: "Tomatoes require adequate light,
  which can be supplemented by reflection."
- **Hold both as a hypothesis pending investigation**: Perhaps keep the old
  rule for now but mark Priya's observation as a data point that warrants
  further study.

The group discusses and decides: the evidence is real (the tomatoes are
right there). They revise their knowledge: "Tomatoes require adequate
light" replaces "Tomatoes require full sun," and "Reflective mulch can
supplement light in shaded beds" is added as a new fact.

**The result flows back**: The knowledge base is now more accurate. Future
planting decisions can take reflective mulch into account.

### What this illustrates

This is *knowledge revision* — the most powerful and most difficult outcome
of the game. The Agon did not simply accept or reject; it identified a
genuine conflict and facilitated a resolution that improved the group's
understanding of the world. The old rule was not "wrong" — it
was *incomplete*. The game process exposed the incompleteness and guided
the revision.

---

## Scenario 4: Building an Argument

### The town planner's case

Keiko is a town planner who wants to persuade the council to build a park
in a disused lot. She needs to make an argument — a chain of reasoning
from premises the council already accepts to a conclusion they have not
yet considered.

**Organon** — Keiko reviews the council's established positions:

> Green spaces reduce local air temperature.
> Reduced air temperature lowers energy costs for adjacent buildings.
> Lower energy costs increase property values.
> The disused lot on Elm Street is surrounded by residential buildings.
> The disused lot currently generates no revenue and incurs maintenance costs.

**Ergasterion** — Keiko constructs her argument in steps:

1. A park on Elm Street would be a green space.
2. Therefore it would reduce local air temperature (from established knowledge).
3. Therefore it would lower energy costs for the surrounding homes.
4. Therefore it would increase property values.
5. Increased property values generate higher tax revenue.
6. Higher tax revenue exceeds the current maintenance costs.

Her conclusion: "Building a park on the Elm Street lot is a net financial
benefit to the municipality."

**Agon** — The argument is tested against the council's established knowledge.
The game unwraps each step:

- Steps 1–4 check out: each follows from premises the council has already
  accepted.
- Step 5 introduces a new claim: "increased property values generate higher
  tax revenue." The council's knowledge base does not contain this.
- Step 6 introduces another new claim: the revenue *exceeds* the costs.
  This is a quantitative assertion the knowledge base cannot verify.

**The game yields a mixed interpretation**:

- The first part of the argument is a **theorem** — it follows deductively
  from what the council already accepts.
- Step 5 is a **reasonable extension** — it is widely accepted economic
  knowledge that the council could agree to add.
- Step 6 is an **open conjecture** — it requires empirical data (actual
  cost and revenue projections) that the game cannot supply.

**The result flows back**: Keiko now knows exactly where her argument is
strong and where it needs more work. She can strengthen step 6 with actual
financial projections and re-test. The council can accept the logical
structure of the argument while requesting evidence for the quantitative
claim.

### What this illustrates

Real arguments are rarely pure deductions. They typically contain a
deductive core (steps that follow from agreed premises), some extensions
(new facts or widely accepted claims that need to be explicitly agreed upon),
and some conjectures (claims that require external evidence). The Agon
*sorts* the argument — it tells you which parts are logically certain,
which parts are plausible but need agreement, and which parts are genuinely
open questions. This is far more useful than a simple "valid" or "invalid."

---

## Scenario 5: A Course of Study

### Learning zoology through inquiry

A student, Amara, is learning basic zoology. Her teacher uses Arisbe as a
teaching tool. Rather than lecturing, the teacher guides Amara through a
series of investigations that build her knowledge step by step.

**Week 1 — Establishing the ground**

The teacher provides an initial knowledge base (a small domain model):

> Mammals are warm-blooded.
> Reptiles are cold-blooded.
> Warm-blooded animals regulate their own body temperature.
> Cold-blooded animals rely on external heat sources.

Amara studies these in the Organon. She can browse the relationships, see
how "warm-blooded" connects to "regulate body temperature," and get a
feel for the structure.

**Week 2 — First discovery**

The teacher asks: "Whales live in cold ocean water. Can they regulate their
body temperature?" Amara is not sure. She constructs the question in the
Ergasterion:

> Whales are mammals.
> Therefore, whales are warm-blooded.
> Therefore, whales regulate their own body temperature.

She tests this in the Agon. The first step — "whales are mammals" — is not
in her current knowledge base. It's a **new fact** that she and the teacher
agree to accept (the teacher confirms it from biological authority). Once
accepted, the rest follows as a theorem.

*Amara has learned something*: she now knows that whales can regulate their
body temperature, and she understands *why* — because they are mammals
and mammals are warm-blooded. The knowledge is not memorized; it is
*understood* through the logical structure.

**Week 3 — A surprise**

The teacher asks: "Are all sea creatures cold-blooded?" Amara's first
instinct is "no — we just established that whales are warm-blooded and
they live in the sea." She constructs the counter-claim in the Ergasterion
and tests it. The Agon confirms: the claim "all sea creatures are
cold-blooded" **contradicts** her knowledge base, because it conflicts
with "whales are warm-blooded."

*Amara has learned to reason by contradiction*: she can refute a false
generalization by producing a counterexample from her own knowledge.

**Week 4 — An open question**

The teacher introduces: "Some fish can regulate their body temperature
partially." This contradicts the simple rule that reptiles and fish are
cold-blooded. Testing it in the Agon produces a contradiction with the
existing knowledge.

But instead of rejecting the claim, the teacher and Amara discuss it.
The game presents the options: reject the claim, revise the knowledge
base, or hold it as a hypothesis. Amara decides to **revise**:
"Most fish are cold-blooded, but some species (like tuna) can partially
regulate body temperature." Her knowledge base becomes more nuanced.

*Amara has learned that knowledge evolves*: what seemed like a simple
rule had exceptions, and discovering those exceptions made her understanding
richer, not weaker.

### What this illustrates

Education is not the transfer of facts from teacher to student. It is the
guided construction of understanding through a cycle of proposing, testing,
and revising. The Organon provides the library; the Ergasterion provides
the workshop where the student articulates their thinking; the Agon
provides the arena where that thinking is tested against reality. Each
cycle — each "inning" — leaves the student with a richer, more accurate
knowledge base and, more importantly, with the experience of having
*reasoned* their way to that knowledge.

---

## Scenario 6: Bridging Two Bodies of Knowledge

### Connecting ecology and economics

A research group has two separate knowledge bases:

- **Ecology**: "Wetlands filter pollutants. Filtered water supports
  fisheries. Healthy fisheries sustain coastal communities."
- **Economics**: "Coastal communities generate tourism revenue. Tourism
  revenue funds infrastructure. Infrastructure supports population growth."

Each domain is well-developed internally, but they have never been formally
connected. A researcher, Kwame, wants to explore whether "preserving
wetlands supports population growth" — a claim that spans both domains.

**Organon** — Kwame studies both knowledge bases side by side. He identifies
the linking concept: "coastal communities" appears in both.

**Ergasterion** — He constructs a bridging argument:

> Wetlands filter pollutants (ecology).
> Filtered water supports fisheries (ecology).
> Healthy fisheries sustain coastal communities (ecology).
> Coastal communities generate tourism revenue (economics).
> Tourism revenue funds infrastructure (economics).
> Infrastructure supports population growth (economics).
> Therefore: preserving wetlands supports population growth.

**Agon** — The argument is tested. Each step is a theorem within its
respective domain. The critical link — "healthy fisheries sustain coastal
communities" chaining into "coastal communities generate tourism revenue"
— holds because the two domains share the concept of "coastal communities."

The game confirms: the conclusion follows from the combined knowledge of
both domains. It is a **theorem of the merged model**.

**The result flows back**: The two knowledge bases are now connected through
an explicit chain of reasoning. This connection can be recorded in the
Organon and used as the basis for further inquiry — for example, "If
wetlands are drained, what happens to population growth?"

### What this illustrates

Knowledge does not live in isolation. The Organon's ability to connect
multiple knowledge bases, combined with the Ergasterion's ability to
construct bridging arguments, and the Agon's ability to verify them,
enables the growth of understanding *across* domains. This is how
interdisciplinary insight works: not by blurring boundaries, but by
finding the precise logical links between well-understood domains.

---

## The Cycle of Inquiry

Every scenario above follows the same pattern:

1. **Know** (Organon) — Study what is established. Understand the current
   state of knowledge.
2. **Make** (Ergasterion) — Construct a new claim, question, or argument.
   Articulate what you think might be true.
3. **Contest** (Agon) — Test the new claim against established knowledge.
   Discover whether it follows, contradicts, extends, or opens new questions.
4. **Integrate** — Based on the outcome, update the knowledge base: add
   the new fact, revise an old rule, flag a hypothesis for further study,
   or record a refutation for future reference.

This is Peirce's vision of logic as a **living practice** — not a static
catalogue of truths, but an ongoing process of inquiry in which knowledge
grows, corrects itself, and deepens through the disciplined interplay of
assertion, challenge, and resolution.

The participants need not be logicians. The underlying formal machinery
(the graph structures, the transformation rules, the game protocol) handles
the rigour. What the participants need is clarity about what they know,
honesty about what they claim, and willingness to revise when the evidence
demands it. These are not technical skills. They are the habits of good
reasoning that Peirce spent his life trying to understand and cultivate.
