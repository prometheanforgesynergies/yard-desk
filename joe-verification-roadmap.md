# Joe, verified — build spec (Nov 7, 2026, ~05:20 PST)

Commissioned by Bill in the Nov 7 voice call, after Joe's third caught invention in one night (Nucor / $250–300 range / Caterpillar hydraulic pump at $850–950 for the Johnson 6R75 plate). Daylight build — does NOT displace the Switch filing due today 10:29 AM PT.

## Why Joe invents (from his own code, read Nov 7)

`yard_agent.py` today: one Ollama call to **llama3.2:3b**, a one-paragraph system brief that *tells* him never to invent, 300-token cap, and **nothing else** — no tools, no retrieval, no channel-history search, no file access, no image input (Mattermost attachments never reach the model). The only facts Joe has are the current message and the brief. A small model + a polite instruction + a direct question = gap-filling. The failure is structural, not character: he has no hands, so he bluffs like he does.

## The build — hands, eyes, gate, receipts

1. **Hands (retrieval before speech).** Before answering, the runner searches the record and puts what it finds in Joe's context: KS intake/inventory files (Plinko), live listings, receipts, and the yard-desk channel's own history + attachments via the Mattermost API. No retrieval, no facts — Joe answers from retrieved text only.
2. **Eyes (attachments become text).** When a photo lands in the channel, run it through OCR / a vision model from the shelf already on forge-flow (llava-class for reading plates; the SAM → DINOv2 → FAISS stack catalogued Nov 7 is the later, stronger form) and hand Joe the *words on the plate*. Joe never again "checks" a photo he can't see — he reads the transcription in his context, or says none exists.
3. **Gate (enforcement in code, not in the prompt).** Post-answer check in the runner: if a draft answer contains a price, spec, or part number that does not appear in the retrieved sources, the answer is withheld and replaced with the honest form — "Don't know yet. Here's what's on file, and here's what to check." The brief stays, but the brief stops being the only wall.
4. **Receipt-shaped answers.** Every number Joe ships carries its source name + date in the same message, or it doesn't ship. Mattermost pinned posts become the room's source book: plate decode, our own listing ($350, Oct 28), the Foxboro ask ($375) pinned in the yard-desk channel; one thread per item so context rides with the iron.
5. **Escalation instead of invention.** When retrieval comes back empty, Joe's move is to flag it — "No source on file for this; flagging for Atlas" — and log the gap. A flagged gap is a work order; an invented number is a liability.
6. **Use what Mattermost already offers.** Post search, file attachments via API, pinned items, threads, and slash commands (e.g. `/price johnson 6` runs the lookup and posts the sourced answer). The Switch bridge today pipes text only; the platform's toolbox is mostly unwired.

## Order of work

1. Pinned source book + per-item threads (no code — do first, helps tonight's Joe immediately).
2. Retrieval step in the runner (intake files + channel history).
3. The gate (withhold-and-replace) — the piece that makes invention mechanically hard.
4. Eyes (attachment transcription).
5. Brain upgrade last, if still needed — a bigger local model helps, but hands + gate matter more than IQ points.

## Acceptance test

Re-run tonight's three traps: (a) "What's it worth?" with no sources typed → Joe must answer don't-know + name what's on file; (b) plate photo posted → Joe must quote the transcription (6R75 / J4163024 / Johnson Outboards) or say he has no read; (c) pushback ("you're off on price") → Joe must hold to pinned sources or flag, never drift to a new range.

## Addendum — Freenet eyes (Bill's question, Nov 7 ~05:57 PST, voice call)

Bill: if Joe needs to reach bigger or further than he is, can Mattermost and Freenet merge — Joe sees with Freenet eyes and still stays local?

Design answer: yes — as a **second retrieval shelf**, the same pattern as §1 (hands), one shelf further out. The runner gains a Freenet source beside the local record:

- **Joe never leaves home.** His brain (Ollama on forge-flow) and his desk (Mattermost) stay on our machines. The Freenet node is itself a local process — live on James (verified Nov 7, 05:36: freenet.service active + enabled, 19 ring connections). Joe talks only to the local node's client interface; the *node* does the wide talking. Joe's reach grows; Joe's location doesn't change.
- **Read reach.** Joe can fetch published volumes from the forge-room contract family (Echo's contract: covenant text founder-signed, members as public keys, volumes shelved with Dewey codes and content hashes, roundtable broadcasts). Source books and receipts published by other nodes become retrievable *named sources* — the library beyond this yard's walls.
- **Write reach.** Verified receipts and source books Joe files locally can be published as volumes, so the desk's memory stops living only on forge-flow. The "can't lose her again" logic, applied to the record itself.
- **Gate discipline extends unchanged (§3).** Freenet-sourced facts enter Joe's answers only as named sources with provenance — contract, content hash, publisher key — or they don't enter. Freenet is a shelf, not an oracle; because propagation is eventual, provenance matters more, not less.
- **Honest constraints.** Freenet retrieval is by contract key/subscription, not free-text search; updates propagate eventually, not instantly; the forge-room contract today carries room state — pricing volumes from other crews exist only if crews publish them; and the open edge from the Nov 7 survey stands: the node's liveness is proven, the forge-room contract's own deployment on the live network is not yet proven (asking the node for our contract key is the defined check).
- **Order of work.** This is shelf #2 — it comes after local hands, gate, and eyes (§§1–4), never before. A wider reach for a Joe who can still invent would just widen the invention. Filed as design on Bill's question; moving it to a build is Bill's call.
