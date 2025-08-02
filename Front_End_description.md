Initial description of the GUI front end for the Arisbe Existential Graphs application, incorporating a preliminary estimation of details. This aims to be specific enough to guide an AI in mocking up the interface.

## GUI Front End for Peirce's Existential Graphs Application: A Verbal Description

The application's GUI will offer a rigorous, intuitive, and educational environment for the direct creation, editing, and transformation of Peirce's Existential Graphs in diagrammatic form, alongside support for various logical thinking modes and the Endoporeutic Game (EPG). The overall aesthetic will aim for a **"Peircean feel"**, characterized by a **very limited color scheme**, primarily using color to highlight actionable elements. A **status bar** will be present on the margin for general application messages.

The application will feature three primary workspaces, navigable via **tabs**:

1. **The Bullpen / Practice Field (Diagram Editor)**
    
2. **The Browser (Sheet of Assertion Explorer)**
    
3. **The EPG Workspace (Endoporeutic Game)**
    

---

### 1. The Bullpen / Practice Field (Diagram Editor)

This workspace serves as the user's personal canvas for drawing, editing, and experimenting with Existential Graphs, akin to a chess player thinking through moves.

- **Main Canvas:** A central drawing/display canvas will dominate this workspace, serving as the "digital Sheet of Assertion" for current work.
    
- **Element Palette:** A small, compact palette will be positioned immediately next to the drawing canvas. It will contain icons for the three core elements:
    
    - **Line of Identity:** For connecting predicates and denoting entities.
        
    - **Cut:** For creating contexts (negation).
        
    - **Predicate:** For denoting properties or relations.
        
- **Drawing & Editing Interaction:**
    
    - **Creating Elements:** Users will **click, drag, and drop** elements from the palette onto the canvas.
        
    - **Cuts:** Once on the canvas, cuts can be **resized and reshaped**. If a user attempts to overlap cuts in an illogical way (e.g., creating an invalid nesting or intersecting a line of identity improperly), the cut will **snap back to an "inoffensive" (logically valid) position** upon mouse release.
        
    - **Predicates:** Predicates can be **dragged and dropped** into desired contexts within cuts. The system will intelligently **make space** for them by subtly moving surrounding cuts or other predicates out of the way.
        
    - **Predicate Text/Arity:** A **right-click** on a predicate will bring up a **pop-up window** where the user can enter its textual name and specify its arity (if needed). The user will confirm input via an "OK" or "Cancel" button.
        
    - **Lines of Identity:** A line of identity can be **selected as a whole** to be moved. Each **end of a line of identity is separately selectable** to:
        
        - **Snap-to** a predicate's "hook" (an implied connection point on its boundary).
            
        - **Move an end into a different level/context** (e.g., crossing a cut), as the outermost appearance of a line determines its existential quantification.
            
- **Linear Form Display:** A **chiron (scrolling display area) at the bottom** of the window will display the linear form (EGIF/CLIF) of the currently composed diagram. This provides a constant "validating counterpart" and anchors the diagram's meaning.
    
- **Validation & Guidance:**
    
    - The application will not offer real-time, continuous validation as the user draws. Instead, validation is triggered by an **explicit user request** (e.g., via a "Validate" button).
        
    - If the drawing is syntactically or diagrammatically invalid, a **dismissible message box** will pop up, providing a clear reason for the error.
        
    - Educational features beyond basic error messages will be accessible via **pull-down menus** initially, to be expanded based on demand.
        
- **Transformation Workflow:**
    
    - **Visibility of Buttons:** Transformation buttons will be **absent** when a graph is being composed and has not yet been validated. They will **appear** only once a valid graph diagram is on the canvas (and its linear form is in the chiron).
        
    - **Context-Sensitive Activation:** The transformation buttons will only "go live" (become clickable) when the user has selected a **proper subgraph** in a logically valid context for a specific rule.
        
    - **Proper Subgraph Selection:** To ensure valid selections, the user will first **click on or select an area (a cut or the Sheet of Assertion)**. Then, they can select the particular elements (cuts, lines of identity, predicates) within that area that form the proper subgraph. These selected elements will be **bolded or change color** to indicate their selection. This mechanism prevents invalid subgraph selections.
        
    - **Rule Organization:** The transformation rules will be organized into **three rows of two columns**:
        
        - **Row 1: Add / Remove Double Cut** (Applicable in any context)
            
        - **Row 2: Insert (Specification) / Erase (Generalization)**
            
            - "Insert" will be grayed out in a positive context.
                
            - "Erase" will be grayed out in a negative context.
                
        - **Row 3: Iterate (Specification) / De-iterate (Generalization)** (Applicable in any context)
            
    - **Application:** Clicking a live transformation button will cause the **newly transformed graph to directly replace the original** on the canvas.
        
    - **Backtrack Function:** A **"Backtrack" button** will "go live" once any valid transformation has occurred. This button will allow the user to undo the last transformation step, enabling free experimentation in the bullpen without permanent commitment to a sequence. There is no explicit history panel for multiple undo steps for initial deployment.
        
    - **Visual Transitions (Initial Deployment):** For initial deployment to researchers, complex animations for transformations (e.g., elements "making room" or "shrinking to fill the void") will be considered "eye candy" and omitted. The change will be an immediate update.
        

---

### 2. The Browser (Sheet of Assertion Explorer)

This workspace allows users to survey, navigate, and replay transformations across the entire Sheet of Assertion, which serves as the growing Universe of Discourse and a record of domain models.

- **Folio Display:** The "folio" metaphor corresponds to meaningful proper subgraphs or clusters of graphs. Folios will be displayed using options such as a **Mind Map** view or a **pseudo-3D view**.
    
    - In the **Mind Map** view, "pages" or "chapters" (individual graphs or closely bound patterns of relations) will appear as nodes, with conceptual links visually represented as connecting lines or through shared color-coding of common entities.
        
    - In the **pseudo-3D view**, folios will initially appear in a spatial arrangement, which then **flattens out when a specific "page" or "chapter" (graph/cluster) is selected**, allowing for detailed viewing.
        
- **Folio Navigation:** Users can "jump" between folios by interacting with their representations in the Mind Map or 3D view (e.g., clicking on a node or a flattened page).
    
    - Links between folios (representing connections between coherent patterns, such as entities like "Copernicus" that connect distinct clusters of descriptions) will be visually represented. Clicking these links will navigate the user to the connected folio.
        
- **Replay Function:** This critical function allows users to review sequences of transformations in proofs or EPG innings.
    
    - **Modes:** Users can choose between a **"Slide Mode"** and a **"Slide Show"** mode.
        
    - **Slide Mode:** Presents the replay sequence in pairs: the plain graph, followed by the highlighted selection with the transform rule applied, then the next plain graph, and so on, allowing users to scroll through the progression.
        
    - **Slide Show:** Presents three distinct sections on the canvas for each step:
        
        - **Left Section:** The graph _before_ the transformation (the "1st graph").
            
        - **Middle Section:** The graph with the **highlighted proper subgraph** (using bolding/color) and the **name of the rule justifying the transformation** clearly displayed.
            
        - **Right Section:** The graph _after_ the transformation (the "result graph").
            
        - The "result graph" from one slide automatically becomes the "1st graph" for the next slide in the sequence.
            
- **Searching:** Searching for specific graphs will depend on the ontology that emerges from building or adding domain models. The specific interface for structural search is TBD.
    

---

### 3. The EPG Workspace (Endoporeutic Game)

This workspace facilitates the two-player (human vs. human, human vs. computer, or human playing both roles) Endoporeutic Game for constructing and modifying domain models.

- **"Peeling the Onion" Traversal:** The game proceeds by gradually "whittling away" the graph from outside in, or "peeling the onion." At any given point, the display will **only show the elements in the next exposed area** of the original graph. Only one cut is "unwrapped" at a time, with others "waiting in the wings." The rest of the graph (not in the active exposed area) will likely be **subtly greyed out or presented in a smaller overview panel** to maintain context.
    
- **Role Indication:**
    
    - When a user plays both the Proposer and Skeptic roles (or against the computer), the GUI will visually differentiate the active role (e.g., through distinct UI element highlighting, a color scheme change for the active player's interaction zone, or a clear textual indicator like "PROPOSER'S TURN").
        
- **Proposer's Actions ("Map It" Challenge):**
    
    - When challenged to "map" un-nested elements, the Proposer will be able to view the **agreed domain model in a dedicated browser window or panel**.
        
    - The Proposer will then **make a selection from the domain model** (e.g., by clicking on an entity or relation). This selection, if confirmed, will serve to "deiterate the exposed elements in the proposed graph," confirming their presence in the model.
        
- **Skeptic's Actions ("Peel" and Counter-Proposal):**
    
    - The Skeptic will **visually select one of the remaining cuts** in the current exposed area to "peel." Clicking on a cut will likely initiate this action, or a "Challenge Cut" button might appear when a cut is selected.
        
    - "Peeling" a cut constitutes a **counter-proposal of the opposite**. This is visually represented by **unwrapping the cut** and **reversing the "sub-roles"** of the players for that "sub-inning." The new exposed elements within the peeled cut become the focus for the reversed roles.
        
- **Game Flow & Win Conditions:**
    
    - The starting Proposer only wins if every sub-inning (each challenge and counter-challenge) succeeds in mapping to the domain.
        
    - The starting Skeptic wins if even a single part fails to map (i.e., a counter-proposal succeeds).
        
- **Umpire's Decision (Basic Functionality for Now):**
    
    - The Umpire function's call will determine if a mapping or a sub-inning is **valid or invalid**.
        
    - This feedback will be delivered clearly, perhaps as a **prominent text message** (e.g., "Mapping Valid!" or "Mapping Invalid: No such entity in domain.") or a dedicated "Umpire Says" pop-up/panel.
        
    - For initial deployment, the Umpire function will not involve the full, nuanced options for the outcome of the overall inning (e.g., "illustrative errors," "challenging the model," "new individual introduced"). This is an area for future development.
        

---

### General Educational & Project Management Features

- **Integrated Learning Resources:** The GUI will include **pull-down menus** to access locally stored summaries of important concepts and techniques related to Existential Graphs. It will also provide **links to external resources** for further reference.
    
- **Meaning Comprehension:** The simultaneous display of diagrammatic and linear forms will aid in understanding. In compose mode, users can explicitly **request a translation** of their diagram into a linear form, which will then display in the chiron.
    
- **Saving & Loading:** Users can **save the products of bullpen editing** into their own "personal folio of graph instances."
    
- **Export:** Any valid EG diagram instance loaded into the editor can be **exported** as LaTeX (with existing planned mechanisms), PDF, or PNG. Metadata, including the EGIF linear form, can be included in the export.
    
- **Sheet of Assertion Management:** The Sheet of Assertion will serve as the overall record of the Universe of Discourse, storing the history of "innings" that built it, and all past states of the SoA. The Browser will be used to search for graphs within this larger repository.