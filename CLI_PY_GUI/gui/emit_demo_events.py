
#!/usr/bin/env python3
import json, socket, time, os, sys, random

HOST, PORT = "127.0.0.1", 45455

def send(obj):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    line = (json.dumps(obj) + "\n").encode("utf-8")
    s.sendall(line)
    s.close()

# Load or write a sample plan file
plan = {
  "plan_id": "tsk_demo",
  "branch_base": "main",
  "nodes": [
    {"id":"n1","tool":"aider","goal":"Implement feature","deps":[]},
    {"id":"n2","tool":"claude-cli","goal":"Write tests","deps":["n1"]},
    {"id":"n3","tool":"cursor","goal":"Docs","deps":["n1","n2"]}
  ]
}
os.makedirs(os.path.expanduser("~/.python_cockpit"), exist_ok=True)
with open(os.path.expanduser("~/.python_cockpit/plan.json"), "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=2)

# Trigger plan load and node updates
send({"type":"plan.load"})
time.sleep(0.3)
send({"type":"node.update","node_id":"n1","status":"running"})
time.sleep(0.8)
send({"type":"node.update","node_id":"n1","status":"passed"})
send({"type":"merge.enqueue","branch":"lane/feat-n1","checks":["lint","tests"]})
time.sleep(0.5)
send({"type":"node.update","node_id":"n2","status":"running"})
time.sleep(0.8)
send({"type":"merge.update","branch":"lane/feat-n1","status":"passed","checks":["lint✔","tests✔"]})
send({"type":"merge.dequeue","branch":"lane/feat-n1"})
send({"type":"budget.update","burn": 5.50})
time.sleep(0.5)
send({"type":"node.update","node_id":"n2","status":"passed"})
send({"type":"merge.enqueue","branch":"lane/feat-n2","checks":["lint","tests","security"]})
time.sleep(0.8)
send({"type":"node.update","node_id":"n3","status":"running"})
time.sleep(0.6)
send({"type":"node.update","node_id":"n3","status":"passed"})
send({"type":"merge.update","branch":"lane/feat-n2","status":"failed","checks":["lint✔","tests✖","security✔"]})
