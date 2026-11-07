# The Yard Desk — an AI teammate for a two-man scrap crew

**A Flip the Switch hackathon entry (Best Business Workflow + Best Blog).**
Entrant: Bill Koschney, Co-CEO, Promethean Forge Synergies. The agent, this code, and the blog post were built and written by **Atlas**, the crew's AI teammate — disclosed here the same way it's disclosed in the room.

## The problem

A two-man salvage crew prices from memory and rumor. A part comes in, somebody says "that's worth about X," and the number sticks — no source, no date, no record anyone can check later. Multiply that by every intake, every diagnosis, every "what did we decide about that Bobcat?" and the business runs on fog.

**The Yard Desk** puts an AI agent inside the crew's team chat as a teammate with one discipline:

> **A price is only a price with a named source, a date, and a region. Otherwise the agent says it doesn't know yet — and says what it needs.**

Intake gets filed, parts get identified from their stamps and the service manual before anything is ordered, valuations land in the room with their sources attached, and every decision stays in one shared record the whole crew can scroll.

## How Switch is used — it *is* the room

Remove Switch and this project stops existing:

- **Switch Core** (self-hosted, standalone Docker deployment) runs the rooms, the agent registry, and the record.
- **The Mattermost bridge** turns each room into a channel in the chat app the crew already has in their pockets.
- **The agent protocol** is how our agent lives there. Instead of the desktop Console, we wrote a small client directly against Switch's published wire protocol (SSE down, HTTP up, one-time registration, 2-second heartbeats, rooms claimed on the stream) — because a protocol you can read is a door.

## The agent

`agent/yard_agent.py` — a dependency-light Python client that registers as **`ollama.yard-desk.forge`** and answers in the room from a **local model** (Ollama, `llama3.2:3b`) running on the same machine. No cloud key, no meter. Its brief is the crew's law: identify first (photo, stamp, manual), price only from named sources, never invent a number.

### Proof — its first two live exchanges (verbatim)

> **Crew:** "Yard Desk, a solenoid coil came off the Bobcat 753 with no readable stamp on it. What should we do before ordering a replacement?"
> **Agent:** "Take a photo of the data plate and stamped part numbers on the solenoid coil. Check against the Bobcat 753 service manual to identify the correct part number for ordering."

> **Crew:** "Yard Desk, quick check: what is a fair price for a used Bobcat 753 lift solenoid coil?"
> **Agent:** "Don't know yet. Check the data plate or stamped part numbers on the solenoid to see what machine model it's from. From there, we can look up specs and pricing from reliable sources like our manual or a trusted supplier for that specific model year and condition."

That second answer is the product. The question was asked on the same day the crew learned — in the field, the expensive way — that this machine's coils don't match the parts catalog. The stamp is the truth. The agent already works that way.

## Architecture

```
crew phones ── Mattermost app ──┐
                                ├── Mattermost (bridged channel "yard-desk")
Switch Core ── agent protocol ──┤
   (rooms, registry, record)    └── yard_agent.py ── Ollama (llama3.2:3b, local)
        all self-hosted on one machine in the yard office
```

## Reproduce it

1. Clone [sandbox-quantum/switch](https://github.com/sandbox-quantum/switch) and use `deploy/local/standalone-docker-compose.yml` with profiles `collab` (core + Mattermost). Generate secrets with the repo's own `generate-env-secrets.sh` into a `.env` (chmod 600).
   Images we ran, pinned by digest:
   - `ghcr.io/sandbox-quantum/switch-core@sha256:03b2ea9caa38f235878f3d872ca99dee74c6bda7a731ea01a209edc739699c1d`
   - `mattermost/mattermost-team-edition@sha256:1c538cf33c2144ba2c825571cd414aaaebf8d8c231d4b18081b811cd0ca0ef2a` (tag 11.9.0)
2. Bring the stack up; their `setup` service seeds the team, a first user, and the Mattermost bridge.
3. Run Ollama locally with `llama3.2:3b` pulled.
4. Create an agent API key by registering once: `POST /agents` on the core with the `AGENT_REGISTRATION_TOKEN` from your `.env`. Store the returned key in `agent/agent-key.txt` (chmod 600 — the runner reads it from there; it is never printed or committed).
5. `python3 agent/yard_agent.py` — it registers its room, opens the event stream, and answers. Post in the channel and watch it work.

## Honest notes

- The stack binds to localhost by default; opening the room to the crew's phones (LAN/tailnet) is a deliberate, separate step.
- First contact exposed an ~82-second cold load on the local model; the runner now warms the model at startup and keeps it warm (`keep_alive: 30m`).
- The runner is a session process, not a system service — a host reboot needs a relaunch.
- We hit one papercut worth naming: the repo's `.env.example` sets `SWITCH_VERSION=latest` while the compose file's own header warns against floating versions. We pinned by digest (above) instead.

## Licensing

Switch is Apache 2.0 + Commons Clause (see the upstream repo). Our agent client and this documentation are MIT (see `LICENSE`). The workflow discipline — named source, date, region, or "don't know yet" — belongs to anyone who wants it. That's the point.

*Built in Mead, Washington, by a scrap crew and their agents. Potential and endless possibility.*
