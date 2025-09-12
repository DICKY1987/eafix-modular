from pathlib import Path
import json, sys
p=Path('policy/compliance_rules.json')
sys.exit(0) if p.exists() and 'rules' in json.loads(p.read_text(encoding='utf-8')) else sys.exit(1)
