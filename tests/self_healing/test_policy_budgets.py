import yaml, os
def load_policy():
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'self_healing', 'self_healing.yaml'), 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
def test_attempt_budget_reasonable():
    sh = load_policy()['self_healing']
    assert 1 <= sh['max_attempts'] <= 10
    assert 1 <= sh['base_backoff_seconds'] <= sh['max_backoff_seconds'] <= 3600
