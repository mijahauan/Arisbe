# Canonical Examples from Existential Graphs Literature

## Research Sources

### Primary Sources
1. **Peirce's Tutorial on Existential Graphs** (John F. Sowa)
   - URL: https://www.jfsowa.com/pubs/egtut.pdf
   - Contains Peirce's original words and diagrams with commentary
   - 12 hand-written pages with 18 diagrams
   - Presents syntax, rules of inference, and illustrative examples

### Key Findings from Sowa's Tutorial

#### Peirce's Method for Teaching Logic
- Peirce's existential graphs (EGs) are described as "the simplest, most elegant, and easiest-to-learn system of logic ever invented"
- The tutorial contains Peirce's clearest introduction to existential graphs
- Written in 1909, contains his clearest tutorial on existential graphs
- In just 12 hand-written pages with 18 diagrams, presents:
  - The syntax
  - Rules of inference  
  - Illustrative examples for first-order logic with equality

#### Peirce's First Example: "There is a man"
- Represented as: —man
- The line —, called a "line of identity", represents an existential quantifier (∃x)
- The string "man" is the name of a monadic predicate asserted of x
- With the addition of ovals to represent negation, these graphs become sufficiently general to represent full first-order logic with equality

#### Peirce's Experimental Approach
- Peirce experimented with notation in 1882
- Combined the existential quantifier with an implicit conjunction
- His first example —man represents "There is a man"
- The line of identity represents an existential quantifier (∃x)

#### Tutorial Structure
- Section 1: Peirce's method for teaching logic
- Section 2: Reproduces Peirce's presentation of EG syntax with examples
- For each diagram: shows equivalent formula in Peirce-Peano notation and Existential Graph Interchange Format (EGIF)

## Next Steps
- Continue reading through Sowa's tutorial for specific examples
- Access Roberts' comprehensive work on Peirce's existential graphs
- Search for Dau's formal mathematical examples
- Collect Peirce's original syllogism demonstrations



## Peirce's Canonical Examples from Sowa's Tutorial

### Example 1: "There is a man"
- **Existential Graph**: —man
- **Meaning**: "There is a man" 
- **Formal Logic**: ∃x (man(x))
- **Key Elements**:
  - Line of identity (—) represents existential quantifier
  - "man" is monadic predicate asserted of x

### Example 2: "Some man eats a man"
- **Existential Graph**: Shows curved line connecting to "man" and straight line to "eats" and another "man"
- **Meaning**: "Some man eats a man"
- **Structure**: 
  - Two lines of identity (curve on left, straight line on right)
  - Each line corresponds to an existential quantifier
  - Graph represented in Peirce's notation of 1880 to 1885: Σₓ Σᵧ (manₓ • manᵧ • eatsₓᵧ)

### Peirce's Diagrammatic Syntax Principles
- **Simplicity**: "This syntax is so simple that I will describe it. Every word makes an assertion."
- **Line of Identity**: The dash before "man" is the "line of identity"
- **Nested Structure**: Graphs are nested in indented paragraphs
- **Commentary Integration**: All other graphs are part of the commentary

### Peirce's Innovation: Diagrammatic Syntax
- Peirce invented "several different systems of graphs to deal with relations"
- Called one system "the general algebra of relations"
- Another "the algebra of dyadic relations"
- Finally preferred "what I call a diagrammatic syntax"
- Key advantage: "It is a way of setting down on paper any assertion, however intricate"
- Method: "if one so sets down any premises, and then (guided by 3 simple rules) makes erasures and insertions, he will read before his eyes a necessary conclusion from premises"

## Section Structure of Sowa's Tutorial
1. **Section 1**: Peirce's method for teaching logic
2. **Section 2**: Syntax for First-Order Logic with Equality
3. **Section 3**: Peirce's rules of inference and illustrative proofs
4. **Section 4**: Endoporeutic applications
5. **Section 5**: Recommendations for teaching introductory logic courses
6. **Section 6**: Theoretical principles simplified by EGs

## Key Insight: Peirce's Three Simple Rules
- Peirce mentions "3 simple rules" for making "erasures and insertions"
- These rules allow deriving "a necessary conclusion from premises"
- This is the foundation of the transformation system we've implemented


### Example 3: Peano's Reformulation
- **Peirce's Original**: Σₓ Σᵧ (manₓ • manᵧ • eatsₓᵧ)
- **Peano's Symbols**: ∃x∃y(man(x) ∧ man(y) ∧ eat(x,y))
- **EGIF Format**: [*x] [*y] (man ?x) (man ?y) (eats ?x ?y)

### EGIF (Existential Graph Interchange Format) Structure
- **One-to-one mapping** to and from each feature of the graph
- **Two lines of identity** correspond to **five components** called nodes:
  - [*x] [*y] represent the two lines of identity
  - Character strings x and y are called **identifiers**
  - An identifier prefixed with asterisk (*x) is called a **defining label**
  - An identifier prefixed with question mark (?x) is called a **bound label**
- **Coreference**: Defining label and all bound labels with same identifier refer to same individual
- **Implicit conjunction**: No marker for conjunction since there is implicit conjunction of all nodes in same area
- **Constraint**: Defining label must precede all coreference bound labels

### Example 4: Negation - "There is no phoenix"
- **Existential Graph**: —phoenix (with oval/cut around it)
- **Meaning**: "To deny that there is any phoenix, we shade that assertion which we deny as a whole"
- **Figure 1**: Shows the basic negation structure
- **Interpretation**: "It is false that there is a phoenix"

### Example 5: Double Negation
- **Existential Graph**: —phoenix (with double oval/cut around it)  
- **Figure 2**: Shows double negation structure
- **Logical Principle**: Double negation elimination

## Key Technical Insights

### EGIF Technical Specifications
1. **Nodes**: Five components in the EGIF representation
2. **Identifiers**: Character strings (x, y) for variables
3. **Defining Labels**: Prefixed with asterisk (*x)
4. **Bound Labels**: Prefixed with question mark (?x)
5. **Coreference Rule**: Same identifier = same individual
6. **Ordering Constraint**: Defining label precedes bound labels
7. **Implicit Conjunction**: All nodes in same area are conjoined

### Peirce's Negation System
- **Shading/Ovals**: Represent denial/negation
- **Whole Assertion Denial**: "we shade that assertion which we deny as a whole"
- **Visual Principle**: Negation is represented by enclosure (cuts/ovals)

## Research Priority: Find Peirce's Three Simple Rules
- Peirce mentions "3 simple rules" for erasures and insertions
- These are fundamental to the transformation system
- Need to locate these specific rules in the tutorial


### Example 6: Double Negation Interpretation
- **Figure 2**: —phoenix (double oval)
- **Meaning**: "There is something that is not identical with any phoenix"
- **Logical Principle**: Double negation creates existential assertion

### Peirce's Cut System
- **Cut/Sep**: Peirce used unshaded oval enclosure, called a "cut" or sometimes "sep"
- **Function**: Separates sheet of assertion into positive (outer) area and negative (inner) area
- **MS 514**: Added shading to highlight distinction between positive and negative areas
- **Without shaded oval**: Graph —phoenix would assert that there exists a phoenix
- **With cut**: Entire graph is negated, but part of line is outside the negation

### EGIF Representation Table
| Graph | EGIF | Formula |
|-------|------|---------|
| Unshaded | [*x] (phoenix ?x) | ∃x phoenix(x) |
| Figure 1 | ~[[*x] (phoenix ?x)] | ~∃x phoenix(x) |
| Figure 2 | [*x] ~[(phoenix ?x)] | ∃x ~phoenix(x) |

### Example 7: Thunder and Lightning
- **Figure 3**: Shows nested ovals with "thunder" and "lightning"
- **Figure 4**: Shows simpler structure with "thunder" and "lightning"
- **Interpretation**: 
  - Fig. 3 denies fig. 4
  - Fig. 4 asserts "it thunders without lightning"
  - For denial: "shades the unshaded and unshades the shaded"
  - Fig. 3 means: "If it thunders, it lightens"

### Key Technical Principles

#### EGIF Scope Rules
- **Square Brackets**: EGIF for Figure 1 encloses EGIF for unshaded graph in square brackets
- **Tilde Symbol (~)**: Places symbol ~ in front
- **Scope Extension**: Implicit scope extends to end of formula
- **Line Crossing**: When line crosses one or more negations, defining label or corresponding existential quantifier placed in outermost area where any part of line occurs

#### Peirce's Negation Principles
1. **Odd Number of Ovals**: Area is shaded (negative)
2. **Even Number of Ovals**: Area is unshaded (positive) 
3. **Nested Structure**: Any area nested inside odd number of ovals is shaded
4. **Denial Method**: "shades the unshaded and unshades the shaded"

### Logical Relationships
- **Figure 3 → Figure 4**: "If it thunders, it lightens"
- **Denial Transformation**: Systematic method for creating denials
- **Nested Cuts**: Complex logical structures through nested ovals


### Formal Logic Equivalents Table

| Figure | EGIF | Formula |
|--------|------|---------|
| Figure 3 | ~[[*x] (thunder ?x) ~[(lightning ?x)]] | ~∃x(thunder(x) ∧ ~lightning(x)) |
| Figure 4 | [*x] (thunder ?x) ~[(lightning ?x)] | ∃x(thunder(x) ∧ ~lightning(x)) |

### Peirce's Algebraic Notation
- **~∃ equivalent to ∀~**: In algebraic notation, ~∃ is equivalent to ∀~
- **Figure 3 becomes**: ∀x~(thunder(x) ∧ ~lightning(x))
- **By Peirce's definition**: ∀x~(thunder(x) ∧ ~lightning(x))
- **Implication operator**: ~(p ∧ ~q) is equivalent to p ⊃ q
- **Therefore**: Formula for Figure 3 can be rewritten as ∀x(thunder(x) ⊃ lightning(x))
- **Peirce's reading**: "If it thunders, it lightens"
- **Negated area reading**: "For every x, either x does not thunder or x lightens"

### Peirce's Universal Quantifier Notation
- **Symbol Π**: Peirce introduced symbol Π for universal quantifier
- **Symbol ≺**: Used ≺ for implication
- **Reason for not using in EGs**: Did not use them in existential graphs
- **CGIF**: Conceptual Graph Interchange Format uses symbols for those operators
- **EGIF limitation**: Limited to symbols Peirce actually used in existential graphs
- **Graphic notation advantage**: Already more readable than algebraic notation with special symbols

### Key Terminology Definitions

#### Peirce's Technical Terms
1. **Area**: "By an 'area,' then, I mean the whole of any continuous part of the surface on which graphs are scribed that is alike in all parts of it either shaded or unshaded"
2. **Graph**: "By a 'graph' I mean the way in which a given assertion is scribed"
3. **Graph vs Graph Instance**: 
   - **Graph**: General kind, not a single instance
   - **Graph Instance**: Particular instance
   - **Example**: "male" appears twenty or more times on average page
   - **Distinction**: Editor asks for article on "male" - means to count each instance as distinct word
4. **Existential Graph**: "Any expression of an assertion in this particular diagrammatic syntax is an Existential Graph"

### Important Conceptual Distinctions
- **Graph as Type vs Instance**: Critical for rules of inference
- **Diagrammatic Syntax**: Specific to existential graphs
- **Surface Continuity**: Areas defined by continuous shaded/unshaded regions
- **Assertion Expression**: EGs as expressions of assertions in diagrammatic syntax


### Example 8: Complex Identity - Male Human African
- **Graph Structure**: Shows three connected concepts: male, human, African
- **Assertion**: "there is a male," "there is something human," and "there is an African"
- **Syntactic Junction**: Point of teridentity asserts identity of something denoted by all three
- **Coreference Node**: [?x ?y ?z] shows three lines of identity refer to same individual

#### EGIF Representation
```
[*x] (male ?x) [*y] (human ?y) [*z] (African ?z) [?x ?y ?z]
```
**Simplified**:
```
[*x] (male ?x) (human ?x) (African ?x)
```
**Formula**: ∃x(male(x) ∧ human(x) ∧ African(x))

### Peirce's Ligature System
- **Term**: Peirce used "ligature" for connection of two or more lines of identity
- **Representation**: Each ligature can be represented by coreference node in EGIF
- **Simplification**: Coreference nodes can often be simplified or eliminated by renaming labels
- **Analysis**: Dau (2010) analyzed various examples of ligatures in Peirce's writings

### Peirce's Terminology for Graph Components

#### Pegs System
- **Indivisible graphs**: Usually carry "pegs" (places on periphery for denoting)
- **Each peg**: One of the subjects of the graph
- **Thunder example**: Graph like "thunders" is called "medad" (having no peg)
- **Some time**: "some time it thunders" when it would require a peg
- **Peg counting**:
  - 0 pegs: **medad**
  - 1 peg: **monad** 
  - 2 pegs: **dyad**
  - 3 pegs: **triad**

#### Atoms vs Molecules
- **Atoms**: Peirce's indivisible graphs are called atoms
- **Arguments**: Each atom consists of single predicate or relation with associated arguments
- **Logical subjects**: Peirce called these "logical subjects"
- **Medads**: Atoms with no arguments (0-ary predicates)
- **Line of identity**: Represents projection (Peirce's term from Greek ἰόν for not)

### Peirce's Three-Part System
- **Alpha**: Propositional logic (avoids any lines of identity)
- **Beta**: Introduces relations and lines of identity  
- **Gamma**: Introduces modal and higher-order logic
- **MS 514**: Peirce combined Alpha and Beta in unified presentation
- **Pedagogical advantage**: Highly effective for beginners to represent complete logic

### Key Insight: Complete Logic Representation
- **Every indivisible graph instance**: Must be wholly contained in single area
- **Line of identity**: Can cross boundaries between areas


### Example 9: Line of Identity Composition
- **Basic principle**: Line of identity can be regarded as graph composed of any number of dyads "—is—" or as single dyad
- **Constraint**: Must be wholly in one area, but may abut upon another line of identity in another area

#### Man-African Example
- **Original**: man—African
- **Reading**: "There is an African man"
- **Expansion**: Replacing dash with four copies of —is— would break single line into five separate segments:
  ```
  man—is—is—is—is—African
  ```
- **Peirce's reading**: "There is a man that is something that is something that is something African"
- **Quantification**: Each of five segments corresponds to existentially quantified variable
- **Dyad correspondence**: Each instance of dyad —is— corresponds to equal sign between two variables

#### EGIF and Formula
```
[*x] [*y] [*z] [*u] [*v] (man ?x) (is ?x ?y) (is ?y ?z) (is ?z ?u) (is ?u ?v) (African ?v)
∃x∃y∃z∃u∃v (man(x) ∧ x=y ∧ y=z ∧ z=u ∧ u=v ∧ African(v))
```

#### Equality in EGs
- **Representation**: Equality represented by joining lines of identity
- **EGIF join**: Join of two lines shown by coreference node [?x ?y]
- **Correspondence**: Corresponds to x=y
- **Enclosure**: Coreference node may enclose any number of bound labels to show all their lines of identity are joined

#### Simplified Form
```
[*x] [*y] [*z] [*u] [*v] (man ?x) [?x ?y ?z ?u ?v] (African ?v)
```
**Section 3 rules would simplify to**: [*x] (man ?x) (African ?x)

### Example 10: Mortality - "Every man will die"
- **Figure 5**: Shows "man" connected to "will die" with specific cut structure
- **Assertion**: "fig. 5 denies that there is a man that will not die"
- **Meaning**: "it asserts that every man (if there be such an animal) will die"
- **Structure**: Contains two lines of identity

#### Shaded vs Unshaded Areas
- **Peirce's distinction**: Line of identity in shaded area distinct from line in unshaded area
- **EGIF representation**: Defining label *x for part in shaded area, another defining label *y for part in unshaded area
- **Coreference node**: [?x ?y] for connection at boundary
- **Formula**: ~[[*x] (man ?x) ~[[*y] (will_die ?y)]]

#### Blanks in EGIF
- **Peirce's practice**: Sometimes included blanks in lines of identity for relations
- **EGIF handling**: Blanks not permitted, can be replaced by underscore
- **Pure graph notation**: No labels, there is no need for underscore


### Example 10 Continued: Mortality Analysis

#### EGIF Simplification Process
1. **Original EGIF**: ~[[*x] (man ?x) ~[[*y] (will_die ?y)]]
2. **After identifier replacement**: ~[[*x] (man ?x) ~[[?x ?x] (will_die ?x)]]
3. **After redundant copy deletion**: ~[[*x] (man ?x) ~[(will_die ?x)]]
4. **Final formula**: ~∃x(man(x) ∧ ~will_die(x))

#### Logical Transformation
- **Replace ~∃ with ∀~**: Converting body to implication
- **Result**: ∀x(man(x) ⊃ will_die(x))
- **Reading**: "For every x, if x is a man, then x will die"

### Example 11: Disjunctive Reading - Figure 6
- **Figure 6**: Shows "man" connected to "will die" in different configuration
- **Assertion**: [Fig. 5] denies which fig. 6 asserts
- **Fig. 6 meaning**: "there is a man that is something that is something that is not anything that is anything unless it be something that will not die"

#### Identity Continuity Principle
- **Key insight**: "I state the meaning in this way to show how the identity is continuous regardless of shading"
- **Necessity**: "this is necessarily the case"
- **Nature of identity**: "In the nature of identity that is its entire meaning"
- **Shading effect**: "For the shading denies the whole of what is in its area but not each part except disjunctively"

#### Simpler Disjunctive Reading
- **Figure 6**: "There is a man who will not die"
- **Peirce's disjunctive reading**: Graph in shaded area must be viewed as conjunction of two parts
- **Derivation method**: 
  1. Two copies of dyad —is— or coreference [?x ?y] added outside negation
  2. Two more copies inside negation

#### Complex EGIF Before Conversion
```
[*x] [*y] [*z] (man ?x) (is ?x ?y) (is ?y ?z) ~[[*u] [*v] (is ?z ?u) (is ?u ?v) (will_die ?v)]
```

#### De Morgan's Law Application
- **Before**: ∃x∃y∃z(man(x) ∧ x=y ∧ y=z ∧ (~∃u∃v(z=u ∧ u=v) ∧ will_die(v)))
- **After**: ∃x∃y∃z(man(x) ∧ x=y ∧ y=z ∧ (~∃u∃v(z=u ∧ u=v) ∨ ~will_die(z)))
- **Reading**: "There is a man x that is something y that is something z that is not anything u that is anything v, or z is something that will not die"
- **Spatial interpretation**: "Graphs enable the viewer to interpret a spatial configuration in different ways"

### Peirce's EG Syntax Conclusion
- **Two explicit operators**: Line to represent existential quantifier, oval to represent negation
- **Conjunction**: Implicit operator expressed by drawing any two graphs side by side
- **Equality**: Expressed by joining lines of identity
- **All other operators**: Represented by combining these primitives


## Peirce's Logical Operators and Common Patterns

### Three Common Logical Combinations

#### 1. Implication: "If p then q"
- **EG Structure**: p and q in nested ovals
- **EGIF**: ~[(p) ~[(q)]]
- **Formula**: p ⊃ q

#### 2. Disjunction: "p or q"  
- **EG Structure**: p and q in separate ovals within outer oval
- **EGIF**: ~[~[(p)] ~[(q)]]
- **Formula**: p ∨ q

#### 3. Universal Quantification: "Every A is B"
- **EG Structure**: A connected to B in nested ovals
- **EGIF**: ~[[*x] (A ?x) ~[(B ?x)]]
- **Formula**: (∀x)(A(x) ⊃ B(x))

### Key Insights on EG Readability
- **Graphic patterns**: Just as readable as algebraic formulas with special symbols ⊃, ∨, and ∀
- **Explicit nesting**: EG ovals emphasize effect on scope of quantifiers caused by operators ⊃ and ∨
- **Scope difficulty**: This effect difficult to explain to students because algebraic notation makes ∀ and ∧ look symmetrical
- **EGIF and algebraic**: Following are EGIF and algebraic representations
- **Medads**: Note that medads p and q are represented as relations with no bound labels (p) and (q)

### Logical Equivalence Table

| English | EGIF | Formula |
|---------|------|---------|
| If p, then q | ~[(p) ~[(q)]] | p ⊃ q |
| p or q | ~[~[(p)] ~[(q)]] | p ∨ q |
| Every A is B | ~[[*x] (A ?x) ~[(B ?x)]] | (∀x)(A(x) ⊃ B(x)) |

### Example 12: Complex Disjunction - "If p then q or r or s"
- **EG Structure**: Shows p connected to q, r, s in complex nested structure
- **Reading**: "If p then q or r or s"
- **No implicit ordering**: EG has no implicit ordering of subgraphs
- **Linear notation constraint**: Some ordering imposed by any linear notation
- **EGIF representation**: Just one of 24 equivalent permutations
- **Formula**: ~[(p) ~[~[(q)] ~[(r)] ~[(s)]]]

### Boolean Operator Flexibility
- **Same order advantage**: Even when four subgraphs written in same order
- **Multiple readings**: Choice of Boolean operators enables EG to be read in many different ways
- **English sentence**: As an English sentence
- **Algebraic formula**: Or as algebraic formula


### Multiple Reading Examples

#### Three Ways to Read Boolean Combinations
1. **If p, then q or r or s** → p ⊃ (q ∨ r ∨ s)
2. **If p and not q, then r or s** → (p ∧ ~q) ⊃ (r ∨ s)  
3. **If p and not q and not r, then s** → (p ∧ ~q ∧ ~r) ⊃ s

#### Canonical Form Benefits
- **Multiple permutations**: Each formula has more permutations for each choice in mapping EG to EGIF
- **Good candidate**: EGs are good candidate for canonical form that can reduce multiple variations
- **Search reduction**: Useful for reducing amount of search in programs for theorem proving

### Example 13: Existential Statements with Negation
- **Reading clarification**: Sometimes clarify translation of EG to sentence or formula
- **Next three graphs**: Show ways of saying that there exist two things
- **Left graph**: Shaded area negates connection between lines of identity on either side
- **Negation emphasis**: To emphasize what is being negated, graph in middle replaces part of line with dyad —is—
- **Middle reading**: "Therefore, that graph may be read 'There is something x, which is not something y'"
- **Right graph**: "There exist two different things with property P or simply 'There are two Ps'"

### EGIF and Formula Table for Three Graphs

| Graph | EGIF | Formula |
|-------|------|---------|
| Left graph | [*x] [*y] ~[[?x ?y]] | ∃x∃y~(x=y) |
| Middle graph | [*x] [*y] ~[(is ?x ?y)] | ∃x∃y~is(x,y) |
| Right graph | [*x] [*y] (P ?x) (P ?y) ~[is[?x ?y]] | ∃x∃y(P(x) ∧ P(y) ∧ ~is(x,y)) |

### Negated Equality Principle
- **Oval with line through it**: Can be read as negated equality
- **Equivalent to ≠**: Equivalent to symbol ≠ in algebraic notation
- **Readability advantage**: So readable that there is no need for special symbol
- **Nest of two ovals**: Graph on left below denies that there are two Ps
- **Right graph assertion**: Graph on right asserts that there is exactly one P

### Example 14: Exactly One P
- **Left graph structure**: P with nested double ovals and line connections
- **Right graph structure**: P with single oval and line connections  
- **Left meaning**: Denies that there are two Ps
- **Right meaning**: Asserts that there is exactly one P


### Example 14 Continued: Exactly One P Analysis

#### EGIF for "Exactly One P"
```
[*x] (P ?x) ~[[*y] (P ?y) ~[[?x ?y]]]
```

#### Two Translation Approaches
1. **Direct translation**: Use two negations
   - "There is a P, and there is no other P" → ∃x(P(x) ∧ ~∃y(P(y) ∧ x≠y))
2. **Implication reading**: Use double negation as implication
   - "There's a P, and if there's any P, it's the same as the first" → ∃x(P(x) ∧ ∀y(P(y) ⊃ x=y))

### Example 15: Cardinality Expressions - "at least 3", "at most 3", "exactly 3"

#### Three Cardinality Graphs
- **Left graph**: "at least 3" - three lines of identity in circle, three arcs not enclosed in shaded area
- **Middle graph**: "at most 3" - three lines of identity outside shaded area, point in center of shaded area
- **Right graph**: "exactly 3" - conjunction of other two, combination that says there exist exactly three things

#### Technical Structure
- **Left graph**: Three lines of identity consist of three arcs of circle that are not enclosed in any shaded area
- **Labeling**: Each of those three lines may be labeled *x, *y, and *z
- **Continuation**: Continued into adjacent shaded areas
- **Non-coreference**: Show that it is not coreference with its neighboring lines
- **Middle graph**: Three lines of identity outside shaded area
- **Center point**: Point in center of shaded area
- **Teridentity**: Called a teridentity because it has three branches
- **Right graph**: Conjunction of other two

#### Translations to English, EGIF, and Formulas
- **Complex table**: Following table shows translations of above graphs to English, EGIF, and formulas in predicate calculus
- **Multiple approaches**: Various ways to express cardinality constraints


### Cardinality Examples Table

| English | EGIF | Formulas |
|---------|------|----------|
| at least 3 | [*x] [*y] [*z] ~[[?x ?y]] ~[[?y ?z]] ~[[?z ?x]] | ∃x∃y∃z (x≠y ∧ y≠z ∧ z≠x) |
| at most 3 | [*x] [*y] [*z] ~[[*w] ~[[?w ?x]] ~[[?w ?y]] ~[[?w ?z]]] | ∃x∃y∃z ~∃w (w≠x ∧ w≠y ∧ w≠z) |
| exactly 3 | [*x] [*y] [*z] ~[[?x ?y]] ~[[?y ?z]] ~[[?z ?x]] ~[[*w] ~[[?w ?x]] ~[[?w ?y]] ~[[?w ?z]]] | ∃x∃y∃z (x≠y ∧ y≠z ∧ z≠x ∧ ~∃w(w≠x ∧ w≠y ∧ w≠z)) |

### Advanced Cardinality Concepts
- **Implication reading**: Middle graph can be read as implication with disjunctive conclusion
- **"There is an x, a y, and a z, and if there is a w, then either w is x, or w is y, or w is z"**
- **Generalization**: To represent more than three, EGs could be generalized to three dimensions with wires for lines of identity and bubbles for negation
- **Exercise**: Generalize the above EGs to four things
- **Tetrahedron representation**: Represent each thing by vertex of tetrahedron; place small shaded ball for x on each of six edges; place large shaded ball inside tetrahedron; place dot to represent nonexistent fifth thing at center of large ball; connect center dot by four wires to each of vertices; on each of those wires place small unshaded ball

### Linear vs Graphic Notation
- **Linear notation obscurity**: Labels for variables or lines obscure the symmetry
- **Graphic form clarity**: Graphic form shows identity by joining two lines
- **Linear version requirements**: Linear versions require special notations such as x=y or [?x ?y]
- **Pure graphs advantage**: Pure graphs have no labels, no axioms for equality, no rules for substituting values for variables, and no rules for relabeling variables
- **Artifacts of notation**: Those axioms and rules are artifacts of the notation

---

# 🎯 **FOUND: PEIRCE'S RULES OF INFERENCE!**

## 3. Rules of Inference for FOL

### Peirce's Permission-Based System
- **All proofs**: Based on "permissions" or "formal rules... by which one graph may be transformed into another without danger of passing from truth to falsity"
- **No interpretation reference**: Without referring to any interpretation of the graphs (CP 4.423)
- **Three permissions**: Peirce prescribed the permissions as three pairs of rules
- **Insertion vs Erasure**: One states conditions for inserting a graph, other states inverse conditions for erasing a graph
- **Numbering**: Insertion rules numbered 1i, 2i, 3i; inverse erasure rules are 1e, 2e, 3e

### **PEIRCE'S THREE SIMPLE RULES** (Finally Found!)

#### **Rule Overview**
- **Three simple rules**: For modifying premises when they have once been scribed
- **Sound necessary conclusion**: To get any sound necessary conclusion from them
- **Permissible modifications**: "I will now state what modifications are permissible in any graph we may have scribed"

#### **Peirce's Generalization of Natural Deduction**
- **Generalization**: Peirce's rules are generalization and simplification of rules for natural deduction
- **Gentzen discovery**: Which Gentzen (1934) independently discovered many years later
- **Grouped in pairs**: For both Peirce and Gentzen, rules are grouped in pairs
- **Operator insertion**: One inserts an operator, other erases operator
- **Only axiom**: For both, the only axiom is a blank sheet of paper
- **Theorem definition**: Anything that can be proved without any prior assumptions is a theorem
- **Detailed comparison**: Section 6 presents more detailed comparison with Gentzen's method

### **1st Permission: Erasure and Insertion on Areas**
- **Unshaded area**: Any graph-instance on an unshaded area may be erased
- **Shaded area**: On a shaded area that already exists, any graph-instance may be inserted
- **Identity requirement**: Identity on an unshaded area could be replaced or join two on a shaded area


## **PEIRCE'S THREE RULES OF INFERENCE (Complete)**

### **1st Permission: Erasure and Insertion**
- **Unshaded area erasure**: Any graph-instance on an unshaded area may be erased
- **Shaded area insertion**: On a shaded area that already exists, any graph-instance may be inserted
- **Identity operations**: Includes right to cut any line of identity on an unshaded area, and to prolong one or join two on a shaded area
- **Constraint**: The shading itself must not be erased (because it is not a graph-instance)

#### **Soundness Proof Logic**
- **Erasure soundness**: Erasing a graph reduces number of options that might be false; inserting a graph increases the number of options that might be false
- **Rule 1e**: Permits erasures in unshaded (positive) area, cannot make true statement false; therefore, that area must be at least as true as it was before
- **Rule 1i**: Permits insertions in shaded (negative) area, cannot make false statement true; therefore, negation of that false area must be at least as true as it was before
- **Model-theoretic semantics**: Formal proof of soundness requires version of model theory
- **Endoporeutic**: Section 4 uses Peirce's model-theoretic semantics, which he called "endoporeutic" for "outside-in evaluation"

### **Variable and Identity Rules**
- **No named variables**: Since EGs have no named variables, algebraic rules for dealing with variables are replaced by rules for cutting or joining lines of identity
- **Equality correspondence**: Correspond to erasing or inserting an equality or the graph —is—
- **Positive area cutting**: Cutting a line in positive area has effect of existential generalization (new line separated ends represent different existentially quantified variables)
- **Negative area joining**: Joining two lines in negative area has effect of universal instantiation (replaces universally quantified variable with arbitrary term)

### **2nd Permission: Iteration and Deiteration**
- **Iteration**: Any graph-instance may be iterated (i.e. duplicated) in the same area or in any area enclosed within that
- **Condition**: Provided the new lines of identity so introduced have identically the same connexions they had before the iteration
- **Deiteration**: If any graph-instance is already duplicated in the same area or in two areas one of which is included within the other, their connexions being identical, then the inner of the instances (or either of them if they are in the same area) may be erased
- **Rule name**: Called the Rule of Iteration and Deiteration

#### **Detailed Application Rules**
- **Iteration (2i)**: Extends a line from outside inward; any line of identity may be extended in same area or into any enclosed area
- **Deiteration (2e)**: Retracts a line from inside outward; any line of identity that is not attached to anything may be cut, starting from the innermost area in which it occurs
- **Graph copying**: Peirce also said that any graph may be copied into any area within itself; it is permissible to copy a graph and then make a copy of the new graph in some area of the original graph

#### **Soundness of Iteration and Deiteration**
- **Equivalence relations**: They can never change truth value of a graph
- **Copy equivalence**: Copy of a graph p in same area is equivalent to conjunction p∧p; inserting copy of p by Rule 2i or erasing it by 2e cannot change truth value
- **Nested area contribution**: For copy of subgraph into nested area, proof in Section 4 shows that subgraph makes its contribution to truth value of whole graph at its first occurrence
- **Irrelevant copy**: Presence or absence of more deeply nested copy is irrelevant

### **3rd Permission: Double Cut**
- **Ring-shaped area**: Any ring-shaped area which is entirely vacant may be suppressed by extending


### **3rd Permission: Double Cut (Complete)**
- **Ring-shaped area suppression**: Any ring-shaped area which is entirely vacant may be suppressed by extending the areas within and without it so that they form one
- **Vacant ring-shaped area creation**: A vacant ring-shaped area may be created in any area by shading or by obliterating shading so as to separate two parts of any area by the new ring-shaped area

#### **Double Negation Principle**
- **Vacant ring-shaped area**: Corresponds to a double negation: two negations with nothing between them
- **Third permission**: Says that a double negation may be erased (3e) or inserted (3i) around any graph on any area, shaded or unshaded
- **Empty graph**: Note that Peirce considered the empty graph, represented by a blank sheet of paper, as a valid existential graph
- **Double negation around blank**: Therefore, a double negation may be drawn or erased around a blank

#### **Important Qualification for Vacant Ring**
- **Line connectivity constraint**: Ring is considered vacant even if it contains lines of identity, provided that the lines begin outside the ring and continue to the area enclosed by the ring without having any connections to one another or to anything else in the area of the ring
- **Equivalence rules**: Both rules 3e and 3i are equivalence rules, as the method of endoporeutic shows in Section 4

#### **Peirce's Confidence Statement**
- **Three principles sufficiency**: "It is evident that neither of these three principles will ever permit one to assert more than he has already asserted. I will give examples the consideration of which will suffice to convince you of this."

### **Example 16: Boy/Industrious Transformation**
- **Figure 7**: Shows "boy" connected to "industrious" in single oval
- **Figure 8**: Shows "boy" and "industrious" in separate ovals
- **Transformation**: Fig. 7 asserts that some boy is industrious. By 1st permission it can be changed to fig. 8
- **Fig. 8 assertion**: "there is a boy and that there is an industrious person"
- **Identity assertion**: "This was asserted as fig. 7, together with the identity of some case"

#### **Line of Identity Analysis**
- **Simplification effect**: Erasing a graph or subgraph usually simplifies a statement
- **Line erasure effect**: Erasing part of a line of identity replaces one line of identity with two
- **Emphasis technique**: To emphasize what is being erased, the EGIF or formula that corresponds to Figure 7 can be written as if it contained the dyad —is—, the coreference [?x ?y], or the equation x=y

#### **EGIF Transformation Table**
| Stage | EGIF | Formula |
|-------|------|---------|
| Figure 7 | [*x] (boy ?x) (industrious ?y) | ∃x(boy(x) ∧ industrious(x)) |
| Intermediate | [*x] [*y] (boy ?x) (industrious ?y) [?x ?y] | ∃x∃y(boy(x) ∧ industrious(y) ∧ x=y) |
| Figure 8 | [*x] [*y] (boy ?x) (industrious ?y) | ∃x∃y(boy(x) ∧ industrious(y)) |

### **Key Insights from Examples**
- **Identity preservation**: Line of identity maintains logical connection between predicates
- **Transformation flexibility**: Rules allow both simplification and complexification
- **Logical equivalence**: Each transformation preserves truth value
- **Visual clarity**: Graphical representation makes logical structure immediately apparent

