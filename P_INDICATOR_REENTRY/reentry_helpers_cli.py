"""
CLI entrypoints for reentry helpers.

Usage examples:
  python -m reentry_helpers_cli make-key --sig NFP_BREAKOUT --tb FLASH --ob W1 --pb AT_EVENT --gen 1
  python -m reentry_helpers_cli parse-key --key NFP_BREAKOUT~FLASH~W1~AT_EVENT~1
  python -m reentry_helpers_cli validate-key --key CPI_REVERSAL~QUICK~BE~POST_30M~2
  python -m reentry_helpers_cli validate-indicators --records indicator_records.json --schema indicator_record.schema.json
"""
from __future__ import annotations
import argparse, json, sys
from typing import Any

from reentry_helpers.vocab import load_vocab
from reentry_helpers.hybrid_id import compose, parse, validate_key, comment

def _print_json(obj: Any):
    print(json.dumps(obj, indent=2))

def cmd_make_key(args):
    key = compose(args.sig, args.tb, args.ob, args.pb, args.gen)
    print(key)
    if args.comment_prefix:
        print(comment(args.comment_prefix, key))

def cmd_parse_key(args):
    hk = parse(args.key)
    _print_json(hk.__dict__)

def cmd_validate_key(args):
    vocab = load_vocab(args.vocab) if args.vocab else load_vocab()
    errs = validate_key(args.key, vocab)
    if errs:
        print("INVALID")
        for e in errs:
            print(f" - {e}")
        sys.exit(1)
    else:
        print("VALID")

def cmd_validate_indicators(args):
    from reentry_helpers.indicator_validator import validate_file
    valids, invalids = validate_file(args.records, args.schema)
    print(f"Valid: {len(valids)}  Invalid: {len(invalids)}")
    if invalids:
        print("First 5 errors:")
        for bad in invalids[:5]:
            rid = bad["record"].get("Id") or bad["record"].get("id") or bad["record"].get("name")
            print(f"- record: {rid}")
            for e in bad["errors"][:5]:
                print(f"  * {e}")
        sys.exit(1)

def main():
    p = argparse.ArgumentParser(prog="reentry_helpers_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("make-key")
    a.add_argument("--sig", required=True)
    a.add_argument("--tb", required=True)
    a.add_argument("--ob", required=True)
    a.add_argument("--pb", required=True)
    a.add_argument("--gen", required=True, type=int)
    a.add_argument("--comment-prefix")
    a.set_defaults(func=cmd_make_key)

    a = sub.add_parser("parse-key")
    a.add_argument("--key", required=True)
    a.set_defaults(func=cmd_parse_key)

    a = sub.add_parser("validate-key")
    a.add_argument("--key", required=True)
    a.add_argument("--vocab", help="Path to reentry_vocab.json (optional)")
    a.set_defaults(func=cmd_validate_key)

    a = sub.add_parser("validate-indicators")
    a.add_argument("--records", required=True)
    a.add_argument("--schema", required=True)
    a.set_defaults(func=cmd_validate_indicators)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
