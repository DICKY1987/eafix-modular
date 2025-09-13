import yaml, os
def load_fixers():
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'self_healing', 'self_healing.yaml'), 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)['self_healing']['fixers']
def test_no_duplicate_fixers_order():
    fixers = load_fixers()
    for reason, actions in fixers.items():
        assert list(dict.fromkeys(actions)) == actions
