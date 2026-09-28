"""Pre-run server check for the live pilot: build info, n_ctx, template thinking switch
(rendered off and on via /apply-template), and one probe chat with thinking off.
Usage: python check_server.py <port> <out.json>"""
import json
import sys
import urllib.request

port, out = sys.argv[1], sys.argv[2]
root = f"http://127.0.0.1:{port}"


def get(path):
    with urllib.request.urlopen(root + path, timeout=30) as r:
        return json.loads(r.read().decode())


def post(path, body):
    req = urllib.request.Request(root + path, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


props = get("/props")
msgs = [{"role": "system", "content": "You write Rust."}, {"role": "user", "content": "Say hi."}]
off = post("/apply-template", {"messages": msgs, "chat_template_kwargs": {"enable_thinking": False}}).get("prompt", "")
on = post("/apply-template", {"messages": msgs, "chat_template_kwargs": {"enable_thinking": True}}).get("prompt", "")
dflt = post("/apply-template", {"messages": msgs}).get("prompt", "")
probe = post("/v1/chat/completions", {
    "messages": [{"role": "user", "content": "Write a Rust function that adds two i32 values. One ```rust block only."}],
    "temperature": 0.6, "max_tokens": 256, "seed": 1, "chat_template_kwargs": {"enable_thinking": False},
    "presence_penalty": 0.0, "frequency_penalty": 0.0, "repeat_penalty": 1.0,
})
msg = probe["choices"][0]["message"]
dgs = props.get("default_generation_settings", {})
rep = {
    "build_info": props.get("build_info"),
    "model_path": props.get("model_path"),
    "n_ctx": dgs.get("n_ctx"),
    "total_slots": props.get("total_slots"),
    "server_default_params": {k: (dgs.get("params") or {}).get(k) for k in
                              ("temperature", "top_k", "top_p", "min_p", "repeat_penalty", "presence_penalty",
                               "frequency_penalty", "dry_multiplier", "xtc_probability", "typical_p")},
    "template_tail_off": off[-160:],
    "template_tail_on": on[-160:],
    "template_tail_default": dflt[-160:],
    "off_equals_on": off == on,
    "default_equals_off": dflt == off,
    "probe_content_head": (msg.get("content") or "")[:300],
    "probe_reasoning_chars": len(msg.get("reasoning_content") or ""),
    "probe_think_tag_in_content": "<think>" in (msg.get("content") or ""),
    "probe_usage": probe.get("usage"),
    "probe_timings": probe.get("timings"),
}
with open(out, "w", encoding="utf-8") as f:
    json.dump(rep, f, indent=1, ensure_ascii=False)
print(json.dumps(rep, indent=1, ensure_ascii=False))
