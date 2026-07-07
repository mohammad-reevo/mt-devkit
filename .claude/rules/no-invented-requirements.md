# No Invented Requirements

## Rule
NEVER invent requirements, implicit behaviors, or "just in case" logic that the user did not ask for. If a design doc or user instruction doesn't specify a behavior, it doesn't exist.

Examples of invented requirements:
- "What if the table is empty? I'll add auto-seeding" — user didn't ask for seeding
- "What if this fails? I'll add a fallback" — user didn't ask for a fallback
- "New orgs won't have config, so I'll populate defaults on first read" — user didn't ask for implicit population
- "This might be needed later, so I'll add it now" — user didn't ask for future-proofing

## What To Do Instead
If you identify a gap (empty table, missing config, edge case), **stop and ask the user**:
- "The table will be empty for new orgs. Should I add seeding during onboarding, or is that out of scope?"
- "If no config exists, should the method return empty or raise?"

The user decides. You implement what was decided. Nothing more.

## Why
Implicit side effects (writes hidden in reads, auto-population, lazy initialization) are the hardest bugs to find. They violate the principle of least surprise and create behavior that no one asked for, no one documented, and no one knows exists until it breaks.
