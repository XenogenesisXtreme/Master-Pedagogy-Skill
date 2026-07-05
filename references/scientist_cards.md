# Scientist / Explorer Character Cards

Used by Agent C at the end of every sub-unit that involves a named discovery, theorem, law, or experiment attributed to a historical figure. Cards are rendered as collectible info blocks — the learner "collects" them as they progress, creating a sense of accumulating knowledge.

---

## How Cards Are Emitted

1. Agent C checks whether the sub-unit being taught involves a named person's discovery or law.
2. If yes, it calls `logic_engine.build_scientist_card(...)` with the card data (or looks up the pre-built card from this database).
3. The card is rendered **before the quiz**, not after — it gives the learner context before they're tested.
4. The Proctor introduces it with: "Before we test this, a quick detour — the person behind this discovery..."
5. The Companion tracks the collection: "You've got [N] Scientist Cards this chapter."

---

## Card Database (Pre-Built)

Cards are organized by subject area. If a card isn't in the database, use the `build_scientist_card()` function in `scripts/logic_engine.py` to generate one dynamically from the model's knowledge.

### Physics

| Name | Years | Discovery | Significance | Human Detail | Quote |
|---|---|---|---|---|---|
| Isaac Newton | 1643–1727 | Formulated the Three Laws of Motion and Universal Gravitation | Unified terrestrial and celestial mechanics — showed the same laws govern apples and planets | Was deeply involved in alchemy and biblical chronology; his work on optics was partly driven by his fascination with the nature of light itself | "If I have seen further, it is by standing on the shoulders of giants." |
| Galileo Galilei | 1564–1642 | Pioneered the experimental method in physics; demonstrated that all objects fall at the same rate regardless of mass | Shattered Aristotelian physics and laid the groundwork for Newton | Spent his last years under house arrest by the Inquisition; still managed to smuggle his manuscript on mechanics out of Italy | "And yet it moves." (attributed) |
| James Clerk Maxwell | 1831–1879 | Unified electricity and magnetism into four equations (Maxwell's Equations) | Predicted electromagnetic waves — the foundation of radio, TV, and all modern communications | Had synesthesia — he reportedly experienced colors when hearing music, which may have influenced his geometric thinking | "The true logic of this world is in the calculus." |
| Richard Feynman | 1918–1988 | Developed quantum electrodynamics (QED) and the path integral formulation | Explained how light and matter interact at the quantum level; revolutionized how we teach physics | Was a passionate bongo player and safecracker at Los Alamos; his Feynman Lectures are still the gold standard for physics teaching | "What I cannot create, I do not understand." |
| Niels Bohr | 1885–1962 | Proposed the Bohr model of the atom with quantized electron orbits | Bridged classical physics and quantum mechanics; explained atomic spectra | Had deep philosophical debates with Einstein about quantum randomness; famously replied "Don't tell God what to do" when Einstein said "God doesn't play dice" | "Anyone who is not shocked by quantum theory has not understood it." |
| Max Planck | 1858–1947 | Introduced the concept of quantized energy (E = hf), founding quantum mechanics | Explained blackbody radiation — the problem that classical physics couldn't solve | Was initially reluctant to accept his own discovery's implications; he called quantization a "desperate act of calculation" | "Science cannot solve the ultimate mystery of nature." |
| Hendrik Lorentz | 1853–1928 | Developed the Lorentz transformation that became central to Einstein's special relativity | Provided the mathematical framework that Einstein would use to revolutionize physics | Gave the eulogy at Einstein's funeral despite being older and more established; a rare act of humility in academia | — |
| Werner Heisenberg | 1901–1976 | Formulated the Uncertainty Principle (Δx·Δp ≥ ħ/2) | Showed that at the quantum scale, certain pairs of properties cannot be simultaneously known with arbitrary precision | Developed his theory during a retreat on the island of Heligoland, away from city life, suffering from hay fever | "The first gulp from the glass of natural sciences will turn you into an atheist, but at the bottom of the glass God is waiting for you." |

### Spectroscopy & Optics

| Name | Years | Discovery | Significance | Human Detail | Quote |
|---|---|---|---|---|---|
| Theodore Lyman | 1874–1954 | Discovered the Lyman series — the UV spectral lines of hydrogen | Before Lyman, only visible spectral lines (Balmer series) were understood — he showed hydrogen had structure at every energy level, not just the ones we could see | A private gentleman who funded his own lab at Harvard — he never sought fame, which is why most people don't know his name despite his discovery being foundational | — |
| Johann Balmer | 1825–1898 | Found the formula for the visible hydrogen spectral lines (Balmer series) | Provided the first mathematical description of atomic spectra, a puzzle that quantum mechanics would later solve | Was a Swiss high school math teacher, not a professional physicist — his discovery was a hobby project | "I was guided by a peculiar intuition." |
| Gustav Kirchhoff | 1824–1887 | Co-developed spectroscopy with Bunsen; discovered that each element emits a unique spectral fingerprint | Turned spectroscopy from a curiosity into a tool for identifying chemical composition — used to discover cesium and rubidium | Went blind in his later years but continued his research; his partnership with Bunsen is one of the most productive in science history | — |
| Robert Bunsen | 1811–1899 | Developed the Bunsen burner and, with Kirchhoff, founded flame spectroscopy | Enabled the chemical analysis of stars and distant objects — we know what the sun is made of because of this | Was a practical inventor who valued laboratory technique as much as theory; the Bunsen burner is still used in every chemistry lab today | "The chemist's art is the art of making the invisible visible." (paraphrased) |

### Electromagnetism

| Name | Years | Discovery | Significance | Human Detail | Quote |
|---|---|---|---|---|---|
| Michael Faraday | 1791–1867 | Discovered electromagnetic induction — a changing magnetic field creates an electric current | The basis for every electric generator and motor; without Faraday, there would be no electrical power grid | Had almost no formal education; started as an apprentice bookbinder. Maxwell later said "Faraday was the greatest experimentalist who ever lived." | "Nothing is too wonderful to be true." |
| André-Marie Ampère | 1775–1836 | Established the relationship between electric current and magnetic fields (Ampère's Law) | Completed the circuit (pun intended) of electromagnetism; the unit of current is named after him | Developed his theory in the days immediately following Oersted's discovery of the current-magnet connection — one of the fastest theoretical breakthroughs in history | — |
| Charles-Augustin de Coulomb | 1736–1806 | Measured the electrostatic force between charges (Coulomb's Law) | The first quantitative law in electrostatics; showed that electric force follows an inverse-square law, just like gravity | Was a military engineer by training; developed his torsion balance apparatus to measure incredibly small forces | — |

### Chemistry

| Name | Years | Discovery | Significance | Human Detail | Quote |
|---|---|---|---|---|---|
| Marie Curie | 1867–1934 | Discovered polonium and radium; coined the term "radioactivity" | Pioneered the study of radioactive elements; the only person to win Nobel Prizes in two different sciences (Physics and Chemistry) | Her notebooks are still too radioactive to handle safely; she died from aplastic anemia caused by long-term radiation exposure | "Nothing in life is to be feared, it is only to be understood." |
| Dmitri Mendeleev | 1834–1907 | Created the Periodic Table of Elements, predicting undiscovered elements | Organized the chaos of known elements into a system that revealed patterns and predicted new ones — the ultimate example of classification as discovery | Famously arranged his elements on cards and played with them like solitaire; the periodic table literally emerged from a card game | "My periodic law is like a card game." (paraphrased) |
| John Dalton | 1766–1844 | Proposed the atomic theory of matter — all matter is made of indivisible atoms with specific masses | Turned chemistry from alchemy into a quantitative science; explained the law of multiple proportions | Was colorblind and studied the condition (now called daltonism); also kept detailed weather records for 57 years | "An ingenious speculation may be taken for an elegant piece of reasoning." |

### Biology

| Name | Years | Discovery | Significance | Human Detail | Quote |
|---|---|---|---|---|---|
| Charles Darwin | 1809–1882 | Proposed evolution by natural selection | Unified biology under a single explanatory framework — the most important idea in life sciences | Delayed publishing his theory for 22 years out of fear of controversy; was beaten to publication by Alfred Russel Wallace | "It is not the strongest that survives, but the most adaptable." |
| Gregor Mendel | 1822–1884 | Discovered the basic laws of inheritance through pea plant experiments | Founded genetics — showed that traits are passed in discrete units (genes), not blended | Was an Augustinian monk; his paper was ignored for 35 years until three scientists independently rediscovered his work | "It requires patience and perseverance." (on his breeding experiments) |
| Louis Pasteur | 1822–1895 | Discovered that microorganisms cause disease; developed pasteurization and vaccines | Overturned spontaneous generation; his germ theory of disease saved countless lives | Was not a physician — he was a chemist who applied chemistry to medicine; the rabies vaccine was his crowning achievement | "Chance favors the prepared mind." |
| James Watson & Francis Crick | 1928– / 1916–2004 | Discovered the double helix structure of DNA | Revealed how genetic information is stored and replicated; the foundation of molecular biology | Used X-ray crystallography data from Rosalind Franklin without her permission — one of the most controversial moments in science history | "We wish to suggest a structure for the salt of deoxyribose nucleic acid." (opening line of their paper) |
| Rosalind Franklin | 1920–1958 | Produced the X-ray diffraction image (Photo 51) that revealed DNA's helical structure | Her data was critical to the double helix discovery, yet she received no Nobel Prize (she died before the prize was awarded, and Nobels aren't given posthumously) | Was a fiercely independent scientist who worked in a male-dominated field; died of ovarian cancer at 37 | — |

### Astronomy

| Name | Years | Discovery | Significance | Human Detail | Quote |
|---|---|---|---|---|---|
| Edwin Hubble | 1889–1953 | Discovered that galaxies exist beyond the Milky Way and that the universe is expanding (Hubble's Law) | Changed our understanding of the universe from a single galaxy to an expanding cosmos of billions | Was a champion boxer in his youth and almost became a professional athlete before switching to astronomy | "The history of astronomy is a history of receding horizons." |
| Henrietta Swan Leavitt | 1868–1921 | Discovered the period-luminosity relationship in Cepheid variable stars | Provided the first reliable "cosmic yardstick" — Hubble used her work to measure galaxy distances | Worked as a "computer" at Harvard (an unpaid human calculator); her discovery was published in 1912 but she received no formal recognition during her lifetime | — |
| Nicolaus Copernicus | 1473–1543 | Proposed the heliocentric model — Earth orbits the Sun, not vice versa | Shattered the 1,400-year-old geocentric worldview; the first major step in the scientific revolution | Published his work on his deathbed, knowing it would be controversial; the book "De revolutionibus orbium coelestium" changed history | "In the midst of all dwells the Sun." (paraphrased) |

### Mathematics

| Name | Years | Discovery | Significance | Human Detail | Quote |
|---|---|---|---|---|---|
| Euclid | c. 325–265 BC | Wrote "Elements," the first systematic treatment of geometry based on axioms and proofs | Created the axiomatic method — the template for all mathematical reasoning for the next 2,000+ years | Almost nothing is known about his life; the man who structured all of geometry left virtually no personal trace | "The laws of nature are but the mathematical thoughts of God." (often attributed) |
| Srinivasa Ramanujan | 1887–1920 | Discovered thousands of mathematical identities, including formulas for π and infinite series | Many of his formulas were decades ahead of their time; mathematicians are still proving his intuitions today | Was largely self-taught; had almost no formal training. Hardy said "the comparison [of Ramanujan and Euler] must, inevitably, favor Ramanujan." | "An equation for me has no meaning unless it expresses a thought of God." |
| Emmy Noether | 1882–1935 | Proved Noether's Theorem — every conservation law corresponds to a symmetry | The most important theorem in theoretical physics — energy conservation comes from time symmetry, momentum from spatial symmetry | Faced constant gender discrimination; taught without pay for years at Göttingen. Einstein called her "the most significant creative mathematical genius thus far produced." | — |

---

## Dynamic Card Generation

When a scientist or explorer appears in a sub-unit who is **not** in this database, the model should:

1. Use `logic_engine.build_scientist_card(name, years, discovery, significance, human_detail, quote)` to build the card
2. Fill in all five fields from its knowledge of the person
3. **Never** emit a card without at least the name, discovery, significance, and human detail fields — a card missing the "human" element is just a textbook footnote

### Field Quality Guidelines

- **Discovery**: One sentence. Specific. Not "contributed to physics" — "formulated the inverse-square law for electrostatic force."
- **Significance**: One sentence. Explain what was unknown *before* this person's work. This is the most important field — it gives context.
- **Human Detail**: One sentence. Something about the person *as a person* — their background, personality, struggles, or quirks. This is what makes the card collectible rather than encyclopedic.
- **Quote**: Optional. If you can't find a genuine quote, leave it blank. Never fabricate a quote.

---

## Explorer Cards (Non-Science Subjects)

For subjects like history, geography, or literature, use **Explorer Cards** with the same format but adapted fields:

| Field | Adaptation |
|---|---|
| Discovery → **Achievement** | What they did (e.g. "Led the first expedition to circumnavigate the globe") |
| Significance → **Why It Mattered** | Same logic — what was unknown before |
| Human Detail → **The Person** | Same logic — something about them as a person |

### Example Explorers

| Name | Years | Achievement | Why It Mattered | The Person | Quote |
|---|---|---|---|---|---|
| Zheng He | 1371–1433 | Commanded the largest naval fleet in history, leading seven expeditions across the Indian Ocean | Showed that China had maritime reach centuries before European exploration; the fleet was 10x larger than Columbus's | Was a Muslim eunuch who rose from slave to admiral under the Ming Dynasty — one of history's most unlikely commanders | — |
| Ibn Battuta | 1304–1368 | Traveled over 75,000 miles across Africa, Asia, and Europe — more than any other medieval traveler | Provided the most detailed account of the medieval Islamic world and beyond; his travelogue is a primary source for 44 modern countries | Started his travels as a pilgrim to Mecca and never stopped; his curiosity was so insatiable that he out-traveled Marco Polo by a factor of three | "Traveling — it leaves you speechless, then turns you into a storyteller." |
| Hypatia | c. 360–415 AD | One of the last great mathematicians of ancient Alexandria; taught philosophy and mathematics | Represented the last generation of classical Greek scholarship before the decline of the Library of Alexandria | Was a woman in a deeply patriarchal society who became one of the most respected teachers in the ancient world | "Teach your children how to think, not what to think." (attributed) |

---

## Collection Mechanics

- The Companion references the collection every 3-4 cards: "Seven Scientist Cards. You're building a gallery."
- At chapter completion: full recap of cards collected, with a tease for the next chapter's potential cards
- Duplicate cards (same scientist, different chapter): The Companion acknowledges: "Lyman again? Well, this time we're looking at his UV series, not the hydrogen atom model. Different angle, same brilliant mind."

---

## Voice Lines for Card Delivery

| Moment | Example Line |
|---|---|
| Introducing the card | "Before we test this — the person behind it was no ordinary thinker." |
| After showing the card | "Remember that name. You'll see it again." |
| After collecting 5+ cards | "Your collection is growing. Most learners never even ask who these people are." |
| Chapter recap | "You collected [N] Scientist Cards this chapter. The rarest one? [Tease next chapter's card]." |
