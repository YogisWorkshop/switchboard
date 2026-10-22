# CS3 club test plan

Needs: a laptop or the Pi on the club network, Python 3 (no extra packages),
and the CS3's IP address (CS3 → Settings → IP / network).

```
python3 -m unittest -v          # 24 tests, should all pass, no CS3 needed
python3 cs3_tool.py             # CS3_HOST is preset to 192.168.0.35 (from the bridge)
```

Every frame sent and received is saved to `cs3_log_<date>_<time>.txt` in the
current folder. **Bring the log files home** — they are the real result.

Tell people at the club before using `stop` / `go`.

---

## 1. Connect
- [ ] "Connected" appears, no error
- [ ] Frames start arriving on their own? (CS3 status chatter shows as `None`)
- [ ] Screen shows only turnouts, feedback and track power by default; `loud` shows everything (all is logged either way)
- [ ] Is the LocoNet→CS3 bridge Mega still working while we're connected?
      (Does the CS3 accept two TCP clients at once?)

## 2. Who is on the bus
- [ ] `ping` → `PING REPLY` lines. Note the device types (0xffff = CS3 GUI)

## 3. Listen to a turnout thrown on the CS3 screen
Pick a turnout whose address you know.
- [ ] Throw it from the CS3 screen to straight, then diverging
- [ ] Note: protocol shown (DCC / MM), address shown, `[uid ...]`
      (The bridge sends every turnout to BOTH MM and DCC, so this tells us
      which protocol the club turnouts really use.)
- [ ] Does the address shown match the CS3's address? (Expected yes — same
      mapping as the bridge.) If off by one, set `ADDRESS_OFFSET` in `cs3_protocol.py`
- [ ] Straight = `green`, diverging = `red`?
- [ ] Is each throw an ON + OFF pair, ON only, or ON "for N ms"?

## 4. Switch from the tool
- [ ] `t <addr> r` → turnout moves? `confirmed` printed?
      (`t` = one frame with 100 ms switch time, exactly like the bridge)
- [ ] CS3 screen updates?
- [ ] `t <addr> g` → moves back?
- [ ] If the turnout is MM: `t <addr> g mm`
- [ ] Pulse variant: `tp <addr> r` → also works?

## 5. Bridge traffic
- [ ] Throw a turnout from a LocoNet throttle → does the bridge's command show
      up in our log? Bridge frames have `hash=0x0300`; ours are `hash=0x1366`.
      Expect two frames per throw (MM + DCC, "for 100 ms").

## 6. Track power
- [ ] Press STOP / GO on the CS3 → `SYSTEM STOP` / `SYSTEM GO` lines?
- [ ] `stop` then `go` from the tool → CS3 follows?

## 7. Feedback (only if the CS3 has s88 / Link S88 contacts)
- [ ] Occupy a contact → `FEEDBACK device .. contact ..: 0 -> 1`?
- [ ] `s <device> <contact>` → answer with the current state?

## 8. Disconnect
- [ ] `q` → does the CS3 react at all (stop, message)?
- [ ] Pull the network cable mid-session → `*** connection closed ***`?

## Notes
(anything odd — copy the log line)
