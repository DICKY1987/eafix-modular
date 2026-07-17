from registry_core import load_all, validate_schemas
if __name__ == "__main__":
 i,r=load_all(); e=validate_schemas(i,r); print("\n".join(e)); raise SystemExit(bool(e))
