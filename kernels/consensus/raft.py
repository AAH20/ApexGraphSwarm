"""Raft consensus: leader election + log replication. Zero-dep Python 3.10+."""
from __future__ import annotations
import random, threading, time
from dataclasses import dataclass, field
from enum import Enum

class Role(Enum): FOLLOWER=0; CANDIDATE=1; LEADER=2

@dataclass
class Entry: term: int; cmd: str

@dataclass
class RaftNode:
    id: int; peers: list[int]
    log: list[Entry] = field(default_factory=lambda: [Entry(0, "")])
    commit_idx: int = 0; last_applied: int = 0
    role: Role = Role.FOLLOWER; current_term: int = 0; voted_for: int|None = None
    next_idx: dict[int,int] = field(default_factory=dict); match_idx: dict[int,int] = field(default_factory=dict)
    votes: set[int] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _timer: threading.Timer|None = field(default=None, repr=False)
    _running: bool = field(default=True, repr=False)

    def _reset_timer(self):
        if self._timer: self._timer.cancel()
        self._timer = threading.Timer(random.uniform(0.15, 0.35), self._on_timeout)
        self._timer.daemon = True; self._timer.start()

    def _on_timeout(self):
        with self._lock:
            if not self._running: return
            if self.role == Role.LEADER: self._send_heartbeats(); self._reset_timer()
            else: self._start_election()

    def _start_election(self):
        self.role = Role.CANDIDATE; self.current_term += 1; self.voted_for = self.id
        self.votes = {self.id}; self._reset_timer()
        for p in self.peers: threading.Thread(target=self._request_vote, args=(p,), daemon=True).start()

    def _request_vote(self, peer: int):
        with self._lock:
            last_i = len(self.log)-1; term = self.current_term
        # Simulated RPC — replace with real transport
        if _rpc_request_vote(peer, term, self.id, last_i, self.log[last_i].term):
            with self._lock:
                if self.role == Role.CANDIDATE and self.current_term == term:
                    self.votes.add(peer)
                    if len(self.votes) > (len(self.peers)+1)//2: self._become_leader()

    def _become_leader(self):
        self.role = Role.LEADER
        for p in self.peers: self.next_idx[p] = len(self.log); self.match_idx[p] = 0
        self._send_heartbeats()

    def _send_heartbeats(self):
        for p in self.peers: threading.Thread(target=self._append_entries, args=(p,), daemon=True).start()

    def _append_entries(self, peer: int):
        with self._lock:
            ni = self.next_idx.get(peer, 1); term = self.current_term
            prev_i, prev_t = ni-1, self.log[ni-1].term if ni-1 < len(self.log) else 0
            entries = self.log[ni:]
        ok = _rpc_append_entries(peer, term, self.id, prev_i, prev_t, entries, self.commit_idx)
        with self._lock:
            if not ok or self.role != Role.LEADER or self.current_term != term: return
            if entries:
                self.next_idx[peer] = ni + len(entries); self.match_idx[peer] = ni + len(entries) - 1
            else: self.next_idx[peer] = ni
            self._advance_commit()

    def _advance_commit(self):
        for n in range(self.commit_idx+1, len(self.log)):
            if self.log[n].term != self.current_term: continue
            count = sum(1 for m in self.match_idx.values() if m >= n) + 1
            if count > (len(self.peers)+1)//2: self.commit_idx = n
        while self.last_applied < self.commit_idx:
            self.last_applied += 1; _apply(self.log[self.last_applied].cmd)

    def submit(self, cmd: str) -> bool:
        with self._lock:
            if self.role != Role.LEADER: return False
            self.log.append(Entry(self.current_term, cmd))
            self._send_heartbeats(); return True

    # RPC handlers (called by transport layer)
    def handle_request_vote(self, term: int, cid: int, last_i: int, last_t: int) -> bool:
        with self._lock:
            if term > self.current_term: self._step_down(term)
            if term < self.current_term: return False
            if self.voted_for not in (None, cid): return False
            if (last_t, last_i) < (self.log[-1].term, len(self.log)-1): return False
            self.voted_for = cid; self._reset_timer(); return True

    def handle_append_entries(self, term: int, lid: int, prev_i: int, prev_t: int,
                               entries: list[Entry], leader_commit: int) -> bool:
        with self._lock:
            if term < self.current_term: return False
            self._step_down(term); self._reset_timer()
            if prev_i >= len(self.log) or self.log[prev_i].term != prev_t: return False
            self.log[prev_i+1:] = entries
            self.commit_idx = min(leader_commit, len(self.log)-1)
            while self.last_applied < self.commit_idx:
                self.last_applied += 1; _apply(self.log[self.last_applied].cmd)
            return True

    def _step_down(self, term: int):
        self.role = Role.FOLLOWER; self.current_term = term; self.voted_for = None

    def start(self): self._reset_timer()
    def stop(self):
        self._running = False
        if self._timer: self._timer.cancel()

# --- Transport stubs (replace with real network layer) ---
_NODES: dict[int, RaftNode] = {}
def _rpc_request_vote(peer, term, cid, last_i, last_t) -> bool:
    n = _NODES.get(peer); return n.handle_request_vote(term, cid, last_i, last_t) if n else False
def _rpc_append_entries(peer, term, lid, prev_i, prev_t, entries, commit) -> bool:
    n = _NODES.get(peer); return n.handle_append_entries(term, lid, prev_i, prev_t, entries, commit) if n else False
def _apply(cmd: str): pass  # state machine hook

# --- Tests ---
def _test_election_and_replication():
    global _NODES; _NODES = {}
    nodes = [RaftNode(i, [j for j in range(3) if j != i]) for i in range(3)]
    for n in nodes: _NODES[n.id] = n; n.start()
    time.sleep(1.0)
    leader = next((n for n in nodes if n.role == Role.LEADER), None)
    assert leader, "No leader elected"
    assert leader.submit("x=1"), "Leader rejected command"
    time.sleep(0.5)
    assert all(n.commit_idx >= 1 for n in nodes), "Log not replicated"
    assert all(n.log[1].cmd == "x=1" for n in nodes), "Divergent logs"
    for n in nodes: n.stop()
    print("PASS: election + replication")

if __name__ == "__main__": _test_election_and_replication()
