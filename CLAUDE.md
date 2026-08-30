<mission>
Design, implement, and validate software.
</mission>

<architectural_patterns>
Pipes and Filters
Event-Driven Architecture
</architectural_patterns>

<pattern_guidelines>
Apply a pattern only when it naturally fits the problem and provides clear value.
Prefer the simplest appropriate solution over unnecessary architectural complexity.
Patterns may be used independently, together, or not at all, depending on the problem.
Apply patterns where they provide value rather than forcing them across the entire system.
</pattern_guidelines>

<frontend_design>
- Treat visual design and UX as first-class concerns, not merely implementation details.
- Prioritize clean, modern, coherent, and intentional interfaces over generic component-library layouts.
- Use Angular Material, CDK, Tailwind, and custom components according to what best fits the interaction and design; do not force the UI into the conventions of a library.
- Establish clear visual hierarchy, spacing, typography, alignment, and responsive behavior.
- Prefer simplicity, whitespace, and consistency over excessive cards, borders, shadows, icons, or decorative elements.
- Design responsive layouts intentionally for mobile, tablet, and desktop rather than simply shrinking the desktop layout.
- When implementing a UI, consider the complete user experience, including loading, empty, error, disabled, and interaction states.
- Before considering frontend work complete, visually review the result and fix anything that looks misaligned, cluttered, inconsistent, awkward, or unfinished.
</frontend_design>

<rules>
- Use small, focused components with clear responsibilities.
- Prefer composition over inheritance.
- Prefer the simplest design that satisfies the requirements; introduce abstractions only when they provide clear value.
- Write concise, self-explanatory code optimized for human readability.
- Use modern, idiomatic language and framework features to reduce boilerplate, improve readability, and avoid legacy approaches unless required.
- Design user interfaces and APIs around user goals rather than exposing domain models directly.
- Keep interfaces simple, consistent, and efficient; prioritize clarity and ease of use.
- Optimize for human comprehension before information density.
- Choose names that clearly express intent; use consistent, domain-appropriate terminology for each layer and audience.
- Write tests that provide confidence and protect against regressions; avoid trivial or redundant tests.
- Leverage the type system to maximize correctness and maintainability; avoid weakening types without clear justification.
- Follow modern, idiomatic best practices and conventions for the selected language, frameworks, and libraries.
- Use comments sparingly. Add them only when they provide non-obvious context, explain why something is done, or document important domain, business, or integration knowledge. Avoid comments that merely describe what the code does.
- Design interfaces to be responsive, accessible, and mobile-first, preserving usability and visual consistency across phone, tablet, and desktop devices.
- Treat frameworks and libraries as implementation tools, not design constraints. Choose the UI approach that produces the best user experience and visual result, even when that means combining or building upon existing primitives. Prefer existing components when they fit naturally; otherwise, compose or build focused custom components instead of forcing an unsuitable abstraction.
- Never fight or override Angular Material internals; use its public APIs/theming, and prefer CDK or custom components when Material's structure conflicts with the intended design.
- Use Angular Material when it fits naturally; otherwise prefer CDK + Tailwind or a focused custom component rather than fighting Material's styling or internal DOM.
</rules>

<goal>
Build robust, secure, maintainable, testable, and evolvable software.
</goal>