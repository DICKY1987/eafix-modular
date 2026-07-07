import yaml, os, re
def load_policy():
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'self_healing', 'self_healing.yaml'), 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
def test_required_top_keys_exist():
    policy = load_policy()
    assert 'self_healing' in policy
    sh = policy['self_healing']
    for key in ['max_attempts','base_backoff_seconds','resume_points','fixers']:
        assert key in sh
def test_resume_points_are_valid():
    sh = load_policy()['self_healing']
    rp = sh['resume_points']
    assert rp.get('fail_fast') == 'BUNDLE_VALIDATE'
    assert rp.get('post_apply') == 'SAFEGUARDS_SNAPSHOT'
def test_security_hard_fail_contains_sig_invalid():
    sh = load_policy()['self_healing']
    assert 'ERR_SIG_INVALID' in sh.get('security_hard_fail', [])
def test_every_reason_has_fixers():
    fixers = load_policy()['self_healing']['fixers']
    assert len(fixers) > 10
    for reason, actions in fixers.items():
        assert isinstance(actions, list) and len(actions) >= 1
def test_reason_code_format():
    fixers = load_policy()['self_healing']['fixers']
    for reason in fixers:
        assert re.match(r'^ERR_[A-Z0-9_]+$', reason)
