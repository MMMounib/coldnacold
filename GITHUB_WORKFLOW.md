# GitHub / Claude Code workflow

1. Create a GitHub repository.
2. Put this kit at repository root.
3. Commit and push the complete `.claude/` directory and PCF corpus.
4. In Claude Code, work from the repository root.
5. For each new particle, describe the desired effect in natural language.
6. Claude must ask about any critical ambiguity before generating.
7. Keep validated particles in `particles/approved/` and useful references in `.claude/skills/gmod-particles/examples/`.

Do not commit secrets, private server credentials, or unrelated addons.
