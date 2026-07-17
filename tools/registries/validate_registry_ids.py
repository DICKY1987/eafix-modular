from registry_core import load_all, validate_ids
if __name__ == "__main__":
 _,r=load_all(); e=validate_ids(r); print("\n".join(e)); raise SystemExit(bool(e))
