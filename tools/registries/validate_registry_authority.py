from registry_core import load_all, validate_authority
if __name__ == "__main__":
 _,r=load_all(); e=validate_authority(r); print("\n".join(e)); raise SystemExit(bool(e))
