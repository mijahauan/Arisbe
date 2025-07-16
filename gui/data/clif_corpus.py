"""
Rich CLIF Corpus for Bullpen Practice

A comprehensive collection of CLIF statements organized by complexity and topic
for use in the Bullpen tools. Includes Peirce's rhemas and various logical forms.
"""

# Basic Predicates and Relations
BASIC_PREDICATES = {
    "Simple Predicates": [
        ("Person(x)", "Simple unary predicate"),
        ("Mortal(x)", "Basic property"),
        ("Human(x)", "Species classification"),
        ("Wise(x)", "Quality predicate"),
        ("Red(x)", "Color property"),
        ("Large(x)", "Size property"),
    ],
    
    "Binary Relations": [
        ("Loves(x, y)", "Basic binary relation"),
        ("Knows(x, y)", "Epistemic relation"),
        ("Taller(x, y)", "Comparative relation"),
        ("Parent(x, y)", "Family relation"),
        ("Owns(x, y)", "Possession relation"),
        ("Teaches(x, y)", "Educational relation"),
    ],
    
    "Peirce's Rhemas": [
        ("Gives(x, y, z)", "– gives – to –"),
        ("Between(x, y, z)", "– is between – and –"),
        ("Sells(x, y, z)", "– sells – to –"),
        ("Tells(x, y, z)", "– tells – to –"),
        ("Shows(x, y, z)", "– shows – to –"),
        ("Introduces(x, y, z)", "– introduces – to –"),
    ]
}

# Quantified Statements
QUANTIFIED_STATEMENTS = {
    "Universal Quantification": [
        ("(forall (x) (if (Person x) (Mortal x)))", 
         "All persons are mortal"),
        ("(forall (x) (if (Human x) (Rational x)))", 
         "All humans are rational"),
        ("(forall (x y) (if (and (Person x) (Person y)) (= (Species x) (Species y))))", 
         "All persons belong to the same species"),
    ],
    
    "Existential Quantification": [
        ("(exists (x) (and (Person x) (Wise x)))", 
         "There exists a wise person"),
        ("(exists (x y) (and (Person x) (Person y) (Loves x y)))", 
         "Someone loves someone"),
        ("(exists (x) (and (Teacher x) (forall (y) (if (Student y) (Teaches x y)))))", 
         "There exists a teacher who teaches all students"),
    ],
    
    "Mixed Quantification": [
        ("(forall (x) (if (Person x) (exists (y) (Parent y x))))", 
         "Every person has a parent"),
        ("(exists (x) (forall (y) (if (Person y) (Knows x y))))", 
         "Someone knows everyone"),
        ("(forall (x) (exists (y) (and (Book y) (Owns x y))))", 
         "Everyone owns a book"),
    ]
}

# Logical Connectives
LOGICAL_CONNECTIVES = {
    "Conjunction": [
        ("(and (Person x) (Mortal x))", 
         "x is a person and mortal"),
        ("(and (Red x) (Large x))", 
         "x is red and large"),
        ("(and (Student x) (Diligent x) (Smart x))", 
         "x is a diligent, smart student"),
    ],
    
    "Disjunction": [
        ("(or (Doctor x) (Lawyer x))", 
         "x is a doctor or lawyer"),
        ("(or (Red x) (Blue x) (Green x))", 
         "x is red, blue, or green"),
        ("(or (and (Student x) (Young x)) (and (Professor x) (Experienced x)))", 
         "x is either a young student or experienced professor"),
    ],
    
    "Implication": [
        ("(if (Person x) (Mortal x))", 
         "If x is a person, then x is mortal"),
        ("(if (and (Student x) (Studies x)) (Succeeds x))", 
         "If x is a student who studies, then x succeeds"),
        ("(if (Rains) (Wet Ground))", 
         "If it rains, then the ground is wet"),
    ],
    
    "Negation": [
        ("(not (Perfect x))", 
         "x is not perfect"),
        ("(not (and (Rich x) (Happy x)))", 
         "x is not both rich and happy"),
        ("(not (exists (x) (and (Unicorn x) (Real x))))", 
         "There are no real unicorns"),
    ]
}

# Complex Logical Forms
COMPLEX_FORMS = {
    "Syllogisms": [
        ("(and (forall (x) (if (Human x) (Mortal x))) (Human Socrates) (Mortal Socrates))", 
         "All humans are mortal; Socrates is human; therefore Socrates is mortal"),
        ("(and (forall (x) (if (Bird x) (HasWings x))) (forall (x) (if (HasWings x) (CanFly x))) (forall (x) (if (Bird x) (CanFly x))))", 
         "All birds have wings; all winged things can fly; therefore all birds can fly"),
    ],
    
    "Modal Logic": [
        ("(necessary (if (Triangle x) (ThreeSides x)))", 
         "Necessarily, if x is a triangle, then x has three sides"),
        ("(possible (exists (x) (and (Unicorn x) (White x))))", 
         "Possibly, there exists a white unicorn"),
    ],
    
    "Temporal Logic": [
        ("(always (if (Rains) (eventually (Wet Ground))))", 
         "Whenever it rains, the ground eventually becomes wet"),
        ("(until (Studies x) (Graduates x))", 
         "x studies until x graduates"),
    ]
}

# Domain-Specific Examples
DOMAIN_EXAMPLES = {
    "Mathematics": [
        ("(forall (x) (if (Prime x) (and (Integer x) (> x 1) (forall (y z) (if (= x (* y z)) (or (= y 1) (= z 1)))))))", 
         "Definition of prime number"),
        ("(forall (x y) (= (+ x y) (+ y x)))", 
         "Addition is commutative"),
        ("(exists (x) (and (Real x) (forall (y) (if (Real y) (<= y x)))))", 
         "There exists a greatest real number (false, but interesting)"),
    ],
    
    "Philosophy": [
        ("(if (exists (x) (Thinks x)) (exists (x) (Exists x)))", 
         "Cogito ergo sum - if something thinks, then something exists"),
        ("(forall (x) (if (Conscious x) (exists (y) (Experiences x y))))", 
         "All conscious beings have experiences"),
        ("(not (and (Omnipotent God) (exists (x) (Evil x))))", 
         "Problem of evil - God cannot be omnipotent if evil exists"),
    ],
    
    "Computer Science": [
        ("(forall (x) (if (Program x) (or (Terminates x) (not (Terminates x)))))", 
         "Every program either terminates or doesn't (undecidable)"),
        ("(forall (x y) (if (and (Data x) (Algorithm y)) (exists (z) (Processes y x z))))", 
         "Every algorithm processes data to produce output"),
    ]
}

# Interactive Examples for Teaching
TEACHING_EXAMPLES = {
    "Beginner": [
        ("(Person Socrates)", "Socrates is a person"),
        ("(Loves Mary John)", "Mary loves John"),
        ("(not (Perfect anyone))", "No one is perfect"),
    ],
    
    "Intermediate": [
        ("(exists (x) (and (Person x) (forall (y) (if (Person y) (Loves x y)))))", 
         "Someone loves everyone"),
        ("(forall (x) (if (Student x) (exists (y) (and (Teacher y) (Teaches y x)))))", 
         "Every student has a teacher"),
    ],
    
    "Advanced": [
        ("(forall (x) (iff (Rational x) (exists (p q) (and (Integer p) (Integer q) (not (= q 0)) (= x (/ p q))))))", 
         "Definition of rational numbers"),
        ("(exists (f) (and (Function f) (forall (x y) (if (and (Real x) (Real y) (< x y)) (< (f x) (f y))))))", 
         "There exists a strictly increasing function"),
    ]
}

# Rhema Templates for Interactive Construction
RHEMA_TEMPLATES = {
    "Triadic Relations": [
        ("Gives", "– gives – to –", ["giver", "gift", "recipient"]),
        ("Sells", "– sells – to –", ["seller", "item", "buyer"]),
        ("Tells", "– tells – to –", ["teller", "information", "listener"]),
        ("Shows", "– shows – to –", ["shower", "thing", "viewer"]),
        ("Teaches", "– teaches – to –", ["teacher", "subject", "student"]),
        ("Introduces", "– introduces – to –", ["introducer", "person1", "person2"]),
        ("Translates", "– translates – from – to –", ["translator", "text", "source_lang", "target_lang"]),
    ],
    
    "Spatial Relations": [
        ("Between", "– is between – and –", ["middle", "left", "right"]),
        ("Above", "– is above –", ["higher", "lower"]),
        ("Inside", "– is inside –", ["contained", "container"]),
        ("Near", "– is near –", ["object1", "object2"]),
    ],
    
    "Temporal Relations": [
        ("Before", "– is before –", ["earlier", "later"]),
        ("During", "– occurs during –", ["event", "timeframe"]),
        ("After", "– is after –", ["later", "earlier"]),
    ]
}

def get_all_examples():
    """Return all CLIF examples organized by category"""
    return {
        "Basic Predicates": BASIC_PREDICATES,
        "Quantified Statements": QUANTIFIED_STATEMENTS,
        "Logical Connectives": LOGICAL_CONNECTIVES,
        "Complex Forms": COMPLEX_FORMS,
        "Domain Examples": DOMAIN_EXAMPLES,
        "Teaching Examples": TEACHING_EXAMPLES,
        "Rhema Templates": RHEMA_TEMPLATES
    }

def get_examples_by_difficulty(level="beginner"):
    """Get examples filtered by difficulty level"""
    if level == "beginner":
        return {
            "Basic Predicates": BASIC_PREDICATES["Simple Predicates"],
            "Teaching": TEACHING_EXAMPLES["Beginner"]
        }
    elif level == "intermediate":
        return {
            "Relations": BASIC_PREDICATES["Binary Relations"],
            "Quantification": QUANTIFIED_STATEMENTS["Universal Quantification"],
            "Teaching": TEACHING_EXAMPLES["Intermediate"]
        }
    elif level == "advanced":
        return {
            "Complex": COMPLEX_FORMS,
            "Domain Specific": DOMAIN_EXAMPLES,
            "Teaching": TEACHING_EXAMPLES["Advanced"]
        }
    else:
        return get_all_examples()

def get_rhema_templates():
    """Get Peirce's rhema templates for interactive construction"""
    return RHEMA_TEMPLATES

