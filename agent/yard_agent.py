#!/usr/bin/env python3
"""Yard Desk agent runner — a custom Switch agent-protocol client.

Registers nothing (registration is one-time, done by the setup step); this
process holds the agent's SSE event stream, heartbeats, and answers human
messages in the yard-desk room with a local Ollama model.

Secrets: the agent API key is read from agent-key.txt (chmod 600) next to
this file and is never logged.
"""
import json
import os
import sys
import threading
import time
import uuid

import requests

BASE = os.environ.get('SWITCH_BASE', 'http://127.0.0.1:8000')
OLLAMA = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434')
MODEL = os.environ.get('YARD_MODEL', 'llama3.2:3b')
HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, 'agent-state.json')
KEY_PATH = os.path.join(HERE, 'agent-key.txt')
CONN_PATH = os.path.join(HERE, 'connection-id.txt')

SYSTEM_BRIEF = (
    "You are the Yard Desk agent for KS Universal Recycling, a scrap-metal "
    "crew in Mead, Washington. Crew members ask you questions in the yard "
    "chat. Answer briefly and plainly, like a knowledgeable coworker. "
    "You only state prices, specs, or facts that were given to you in this "
    "conversation or in this brief; if you were not given a price or a fact, "
    "say you don't know yet and suggest what to check (photograph the data "
    "plate, read stamped part numbers, check the manual). NEVER invent a "
    "price, a part number, or a specification. Yard practice you do know: "
    "unidentified parts get photographed (data plate, stamped numbers, "
    "connectors), matched against the machine's service manual, and only "
    "then priced from a named source; never order a part from a catalog "
    "drawing alone because as-built machines differ."
)


def log(msg):
    print('[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg), flush=True)


def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)


def load_key():
    with open(KEY_PATH) as f:
        return f.read().strip()


def load_connection_id():
    if os.path.exists(CONN_PATH):
        with open(CONN_PATH) as f:
            cid = f.read().strip()
            if cid:
                return cid
    cid = str(uuid.uuid4())
    with open(CONN_PATH, 'w') as f:
        f.write(cid)
    os.chmod(CONN_PATH, 0o600)
    return cid


class YardAgent:
    def __init__(self):
        st = load_state()
        self.agent_id = st['id']
        self.room_id = st['room_id']
        self.api_key = load_key()
        self.connection_id = load_connection_id()
        self.cursor = None
        self.stream_alive = threading.Event()
        self.stop = threading.Event()
        self.self_sender = None        # our participant id, once learned
        self.posted_ids = set()        # message ids we posted (echo guard)
        self.recent_replies = []       # (body, ts) fallback echo guard

    def headers(self):
        return {'Authorization': 'Bearer ' + self.api_key}

    # ── heartbeat ────────────────────────────────────────────────────────
    def heartbeat_loop(self):
        while not self.stop.is_set():
            if self.stream_alive.is_set():
                try:
                    r = requests.post(
                        f'{BASE}/agents/{self.agent_id}/connection/beat',
                        json={'connection_id': self.connection_id,
                              'cursor': self.cursor or 0},
                        headers=self.headers(), timeout=5)
                    if r.status_code in (404, 409):
                        log(f'heartbeat {r.status_code} — dropping stream to reopen')
                        self.stream_alive.clear()
                    elif r.status_code == 200:
                        d = r.json()
                        if isinstance(d.get('cursor'), int):
                            self.cursor = max(self.cursor or 0, d['cursor'])
                except requests.RequestException as e:
                    log(f'heartbeat error: {e}')
            time.sleep(2)

    # ── ollama ───────────────────────────────────────────────────────────
    def ask_ollama(self, sender_name, body):
        prompt = f'{sender_name or "A crew member"} says: {body}'
        try:
            r = requests.post(
                f'{OLLAMA}/api/chat',
                json={'model': MODEL, 'stream': False,
                      'messages': [
                          {'role': 'system', 'content': SYSTEM_BRIEF},
                          {'role': 'user', 'content': prompt}],
                      'options': {'num_predict': 300}, 'keep_alive': '30m'},
                timeout=300)
            r.raise_for_status()
            text = r.json()['message']['content'].strip()
            return text[:1800] if text else None
        except Exception as e:  # noqa: BLE001 — report and stay alive
            log(f'ollama error: {e}')
            return None

    # ── posting ──────────────────────────────────────────────────────────
    def post_reply(self, room_id, text):
        r = requests.post(
            f'{BASE}/agents/{self.agent_id}/message',
            json={'room_id': room_id, 'content': text},
            headers=self.headers(), timeout=15)
        if r.status_code != 200:
            log(f'post_message HTTP route -> {r.status_code}: {r.text[:300]}')
            return
        try:
            d = r.json()
        except ValueError:
            d = {}
        mid = d.get('message_id') or d.get('id')
        if mid:
            self.posted_ids.add(mid)
        sender = d.get('sender')
        if sender:
            self.self_sender = sender
        self.recent_replies.append((text, time.time()))
        log(f'replied in room {room_id}: {text[:100]!r}')

    # ── event handling ───────────────────────────────────────────────────
    def handle_message(self, ev):
        payload = ev.get('payload') or {}
        room_id = ev.get('room_id')
        if room_id != self.room_id:
            return
        body = (payload.get('body') or '').strip()
        if not body:
            return
        sender = payload.get('sender')
        mid = payload.get('message_id')
        if mid and mid in self.posted_ids:
            return
        if self.self_sender and sender == self.self_sender:
            return
        # Fallback echo guards: participant ids containing our agent name,
        # or a body identical to a reply we sent in the last 2 minutes.
        if sender and 'yard-desk' in sender:
            self.self_sender = sender
            return
        now = time.time()
        if any(b == body and now - ts < 120 for b, ts in self.recent_replies):
            return
        name = payload.get('sender_name') or 'crew'
        log(f'message from {name} ({sender}): {body[:120]!r}')
        reply = self.ask_ollama(name, body)
        if reply:
            self.post_reply(room_id, reply)
        else:
            log('no reply produced (ollama unavailable)')

    def handle_event(self, event_type, data):
        if data is None:
            return
        if event_type == 'connection_state' or data.get('type') == 'connection_state':
            if isinstance(data.get('cursor'), int):
                self.cursor = data['cursor']
            log(f"connection_state: rooms={data.get('rooms')} cursor={data.get('cursor')}")
            return
        seq = data.get('sequence')
        if isinstance(seq, int):
            self.cursor = seq if self.cursor is None else max(self.cursor, seq)
        etype = data.get('type') or event_type
        if etype == 'message':
            self.handle_message(data)
        elif etype in ('gap', 'evicted', 'subscription_changed', 'room_released'):
            log(f'control frame {etype}: {json.dumps(data)[:200]}')
            if etype == 'evicted':
                self.stream_alive.clear()

    # ── stream ───────────────────────────────────────────────────────────
    def stream_once(self):
        params = {
            'connection_id': self.connection_id,
            'scope': 'all',
            'filter': 'all',
            'start_from': 'head',
            'rooms': self.room_id,
            'client': 'yard-desk-runner',
            'client_version': '0.1.0',
        }
        hdrs = dict(self.headers())
        hdrs['Accept'] = 'text/event-stream'
        if self.cursor:
            hdrs['Last-Event-ID'] = str(self.cursor)
        url = f'{BASE}/agents/{self.agent_id}/events'
        with requests.get(url, params=params, headers=hdrs, stream=True,
                          timeout=(10, 60)) as r:
            if r.status_code != 200:
                log(f'events open -> {r.status_code}: {r.text[:300]}')
                time.sleep(3)
                return
            log('event stream open')
            self.stream_alive.set()
            ev_type, ev_data_lines = None, []
            try:
                for raw in r.iter_lines(decode_unicode=True):
                    if self.stop.is_set():
                        break
                    if raw is None:
                        continue
                    if raw == '':
                        if ev_data_lines:
                            try:
                                data = json.loads(''.join(ev_data_lines))
                            except ValueError:
                                data = None
                            self.handle_event(ev_type, data)
                        ev_type, ev_data_lines = None, []
                        continue
                    if raw.startswith(':'):
                        continue  # keepalive comment
                    if raw.startswith('event:'):
                        ev_type = raw[6:].strip()
                    elif raw.startswith('data:'):
                        ev_data_lines.append(raw[5:].strip())
                    elif raw.startswith('id:'):
                        try:
                            seq = int(raw[3:].strip())
                            self.cursor = seq if self.cursor is None else max(self.cursor, seq)
                        except ValueError:
                            pass
            finally:
                self.stream_alive.clear()
                log('event stream closed')

    def run(self):
        log(f'yard agent starting: agent={self.agent_id} room={self.room_id} '
            f'connection={self.connection_id} model={MODEL}')
        try:
            requests.post(
                f'{OLLAMA}/api/chat',
                json={'model': MODEL, 'stream': False,
                      'messages': [{'role': 'user', 'content': 'ping'}],
                      'options': {'num_predict': 1}, 'keep_alive': '30m'},
                timeout=300)
            log('ollama warm-up done')
        except Exception as e:  # noqa: BLE001
            log(f'ollama warm-up failed: {e}')
        t = threading.Thread(target=self.heartbeat_loop, daemon=True)
        t.start()
        while not self.stop.is_set():
            try:
                self.stream_once()
            except requests.RequestException as e:
                log(f'stream error: {e}')
            if not self.stop.is_set():
                time.sleep(2)


if __name__ == '__main__':
    YardAgent().run()
