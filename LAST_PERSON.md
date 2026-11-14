# LAST PERSON production branch

This branch adds a separate horror preset and a procedural 2D renderer. It does not change `master`.

## Current test workflow

1. Open the repository's **Actions** tab.
2. Select **LAST PERSON - Render a test Short**.
3. Choose **Run workflow** on branch `last-person-horror`.
4. Keep `last_person_horror` selected. A topic is optional.
5. When the run finishes, download the `last-person-video-...` artifact from that run.

The workflow renders only. It does not upload to YouTube or TikTok.

## Required secret

Add a repository Actions secret named `GROQ_API_KEY` under **Settings → Secrets and variables → Actions**. The value is your own Groq API key. Do not put the key in a source file, commit, issue, or chat.

The LAST PERSON preset does not use `DEAPI_TOKEN`. Edge TTS and the procedural stickman renderer do not require paid image generation.

## Current limitations

- The artwork is original procedural stickman animation with simple movement and scene changes. It is a lightweight first version, not studio-grade frame-by-frame character animation.
- Ambient horror audio is generated procedurally. Dedicated Foley effects and richer character-specific actions are future improvements.
- Each generated narration is checked against the 60–90 second target. If the voice duration falls outside that range, the run stops instead of exporting a wrongly sized Short.
- TikTok posting is intentionally not automated. Review the MP4 and post it manually to both platforms.
- Free provider quotas and GitHub Actions limits can change. This setup aims to avoid paid image-generation services, but cannot promise unlimited free generation.
