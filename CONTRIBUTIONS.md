# Contributions and Acknowledgments

We thank **Matt Abate** for identifying and reporting these issues on **November 18, 2026**:

- **ComboState progression:** the 1.5× boost expiry reset the consecutive-clear counter, preventing a perfect four-clear streak from reaching the 2.0× tier.
- **MPVE retries:** duplicate detection returned the existing failed job for an identical request, preventing the failed render from being retried.

The reports were addressed in [the main-branch fix (`d39eb5a`)](https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill/commit/d39eb5aa81b8d75c46e387506798474e8fd2cc55) and [the MPVE-branch fix (`38aefd7`)](https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill/commit/38aefd729338d6f8b66939aa568b37fbb6a2f0ba).
