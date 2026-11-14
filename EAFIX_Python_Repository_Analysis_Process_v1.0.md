# Python Repository Analysis Process

| Field | Value |
|---|---|
| Document ID | `PY-REPO-ANALYSIS-001` |
| Version | `1.0.0` |
| Status | Proposed technical process |
| Scope | Static analysis of Python `.py` files in one repository |
| Required output | Exactly one consolidated JSON document |
| Analysis mode | Read-only, offline-capable, non-executing |
| Primary graph analyzer | Enola |
| Independent import analyzer | Grimp |
| Supplemental parser | CPython `ast` standard library |
| Output validation | `jsonschema` |

## 1. Normative requirements

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

1. The process MUST analyze the repository working-tree snapshot supplied as input.
2. The process MUST inventory every in-scope `.py` file, including files in archive, legacy, deprecated, test, and backup directories unless explicitly excluded by the run configuration.
3. The process MUST NOT execute, import, install, initialize, or test repository application code.
4. The process MUST NOT modify source files, repository configuration, Git metadata, or canonical registries.
5. The process MUST record parse failures, skipped files, unresolved references, and tool coverage gaps. Absence of a relationship MUST NOT be interpreted as proof that no relationship exists.
6. The process MUST distinguish direct evidence from inferred or unresolved relationships.
7. Every relationship MUST include source evidence: source file, line, column when available, extraction method, and relationship type.
8. The process MUST preserve repository-relative paths using `/` separators and MUST NOT use absolute machine-specific paths as entity identifiers.
9. The process MUST produce one valid UTF-8 JSON file. It MUST NOT publish JSONL, CSV, HTML, graph image, or separate report files as final outputs.
10. Intermediate tool artifacts MUST be created in a temporary analysis workspace and removed after successful publication, unless a diagnostic-retention option is explicitly enabled.
11. The final JSON MUST be validated against the schema defined in this document before it is atomically published.
12. Output ordering MUST be deterministic. Arrays MUST be sorted by stable identifiers or their documented sort keys.

## 2. Analysis objective

Produce a repository-wide, evidence-backed model of Python source structure and statically detectable relationships.

### 2.1 Required discoveries

- Python file inventory and content hashes.
- Python module/package identity and source-root mapping.
- Classes, functions, async functions, methods, and nested definitions.
- Direct imports, relative imports, imported names, aliases, and import locations.
- Internal module import relationships.
- Standard-library and third-party import dependencies where classification is possible.
- Statically resolvable function/method calls as emitted by Enola.
- File-system references that can be extracted from statically identifiable calls and literal or safely folded paths.
- Script/module execution references such as `subprocess`, `runpy`, and shell execution calls.
- Dynamic import references such as `importlib.import_module()` and `__import__()`.
- Entry-point markers, including `if __name__ == "__main__"`.
- Dependency cycles, unresolved imports, unresolved paths, parse errors, and extraction coverage.
- Direct evidence and provenance for every emitted relationship.

### 2.2 Explicit non-goals

- Runtime execution tracing.
- Guaranteed call-graph resolution for reflection, monkey-patching, dependency injection, decorators, dynamic dispatch, or metaprogramming.
- Full interprocedural data-flow analysis.
- Determining business ownership, canonical module ownership, or process-step ownership.
- Declaring a file unused solely because no static inbound edge was found.
- Modifying, moving, renaming, deleting, or repairing repository files.
- Assigning EAFIX module IDs or process-step IDs unless those identifiers are explicitly present in source metadata and are captured as literal references.

## 3. Open-source toolchain

Only the following tools are required by this process.

| Tool | License | Required use | Output consumed |
|---|---|---|---|
| Enola | Apache-2.0 | Primary parsed software graph; module/symbol/import/call facts; architecture findings; extraction receipt | `.enola/facts.jsonl`, `.enola/insights.json`, `.enola/receipt.json`; optional `.enola/flows.json` and `.enola/docs.jsonl` when generated |
| CPython `ast` | Python Software Foundation License; part of Python | Syntax validation; exact source locations; declarations; import statements; selected call-site and file-operation extraction | In-memory normalized records |
| Grimp | BSD-2-Clause | Independent package import graph and import-site details; cross-check of Enola import edges | In-memory `ImportGraph` records |
| `jsonschema` | MIT | Validate final JSON against the output schema | Validation result only |

### 3.1 Tool selection rules

1. Enola is the primary broad graph source. Its Python extractor is documented to emit module/symbol facts, imports, and statically resolvable call/instantiation edges. Its parser does not execute repository code. Python-specific framework extraction is limited to documented framework patterns; do not assume universal framework coverage.
2. CPython `ast` is the source-location and supplemental-reference source. It is not a replacement call-graph engine.
3. Grimp is an independent import-graph cross-check for importable Python packages. It is not a whole-repository analyzer for standalone scripts, and its results MUST NOT replace the repository-wide AST inventory.
4. `jsonschema` validates the final output structure. It does not validate the semantic correctness of every detected relationship.
5. NetworkX, Semgrep, Ruff, Pylint, LibCST, and SciTools Understand are not required in this baseline process. They MAY be added only through a separately versioned process revision with a stated analytical purpose.

### 3.2 Version control

- Pin exact versions of Enola, Grimp, `jsonschema`, and the Python interpreter in the analysis environment.
- Do not use unbounded `latest` versions during repeatable production analysis.
- Record the actual version of every tool in `analysis.toolchain` on every run.
- Record the Python runtime version and the Python grammar version used by `ast.parse`.
- Record the Enola extractor names and Enola snapshot format version from `receipt.json`.
- Revalidate this process whenever a major tool version or Enola snapshot format changes.

### 3.3 Reference documentation

- Enola graph model: <https://enola.tech/docs/graph>
- Enola language coverage: <https://enola.tech/docs/language-coverage>
- Enola workflow and snapshot generation: <https://enola.tech/docs/workflows>
- Enola source license: <https://github.com/enola-labs/enola/blob/main/LICENSE>
- Grimp documentation: <https://grimp.readthedocs.io/en/latest/>
- Grimp source license: <https://github.com/python-grimp/grimp/blob/main/LICENSE>
- Python AST documentation: <https://docs.python.org/3/library/ast.html>
- JSON Schema specification: <https://json-schema.org/specification>
- `jsonschema` Python implementation: <https://github.com/python-jsonschema/jsonschema>

## 4. Execution architecture

```text
Repository working tree
        |
        v
Read-only snapshot + Git metadata capture
        |
        v
Python file inventory + SHA-256 hashes + source-root discovery
        |
        +-----------------------+
        |                       |
        v                       v
Enola graph generation     CPython AST extraction
        |                       |
        v                       v
Enola facts/insights/       declarations/imports/calls/
receipt                     file operations/dynamic loads
        |                       |
        +-----------+-----------+
                    |
                    v
              Grimp import graph
                    |
                    v
       Import edge cross-validation
                    |
                    v
       Relationship normalization/deduplication
                    |
                    v
     Graph metrics + coverage + unresolved records
                    |
                    v
        One consolidated JSON object
                    |
                    v
        JSON Schema validation
                    |
                    v
       Atomic publication of one JSON file
```

### 4.1 Required components

The execution wrapper is a minimal orchestration/normalization adapter. It MUST only:

- invoke the listed tools;
- enumerate and hash files;
- normalize documented tool output;
- extract supplemental AST facts using explicitly defined rules;
- reconcile duplicate evidence;
- calculate deterministic graph summaries;
- validate and write the final JSON.

The wrapper MUST NOT become a new general-purpose static-analysis framework or attempt broad semantic inference that duplicates Enola or Grimp.

### 4.2 Command-line contract

The wrapper SHOULD expose this interface:

```text
python analyze_python_repository.py \
  --repo <repository-root> \
  --output <absolute-or-relative-output-file.json> \
  [--exclude <glob>]... \
  [--include-hidden] \
  [--retain-intermediates]
```

Required arguments:

- `--repo`: path to the repository working tree.
- `--output`: destination for the single final JSON file.

Optional arguments:

- `--exclude`: additional repository-relative glob exclusions. Every exclusion MUST be recorded in output.
- `--include-hidden`: include hidden directories other than `.git` and explicitly excluded tool/cache directories.
- `--retain-intermediates`: retain the temporary Enola workspace for diagnostics; default is false. The final result remains one JSON file.

The output file MUST NOT be placed inside a scanned source directory unless explicitly excluded from inventory before the scan.

## 5. Scope and file discovery

### 5.1 Default file inclusion

Include all regular files matching `*.py` under the repository root, regardless of whether they are in:

- application/source directories;
- tests and fixtures;
- scripts and tools;
- archive/legacy/deprecated directories;
- backup or migration directories;
- examples and documentation support directories.

Do not exclude legacy or archived Python files by name alone. Those files may reveal imports, process branches, or historical relationships.

### 5.2 Default exclusions

Exclude only tool/environment artifacts by default:

```text
.git/**
.venv/**
venv/**
__pycache__/**
.pytest_cache/**
.mypy_cache/**
.ruff_cache/**
.tox/**
.nox/**
.build/**
build/**
dist/**
```

Do not blanket-exclude directories named `archive`, `legacy`, `old`, `deprecated`, `backup`, `test`, `tests`, `examples`, or `scripts`.

The exclusion list MUST be configurable. Every excluded path pattern and the number of matching files MUST be recorded in `scope.exclusions`.

### 5.3 Discovery algorithm

1. Canonicalize the repository root using an absolute normalized path.
2. Reject a nonexistent root or a path that is not a directory.
3. Enumerate regular files recursively without following directory symlinks.
4. Include `.py` files; do not silently omit files because they are untracked or not importable.
5. Normalize each relative path to POSIX `/` separators.
6. Reject paths that resolve outside the repository root.
7. Sort the resulting file list lexicographically by normalized relative path.
8. Compute SHA-256, byte size, and modification time for each in-scope file.
9. Record symlinks separately as skipped entries; do not follow them.
10. Detect file changes during analysis by recomputing hashes before publication. If a source file changed between inventory and finalization, mark the run `inconsistent_snapshot` and do not report a complete result.

### 5.4 Git metadata

Capture, when Git is available:

- repository remote URL with credentials stripped;
- `HEAD` commit hash;
- current branch name;
- tracked/untracked/modified state;
- whether submodules are present;
- submodule commit IDs when obtainable without initializing them.

Do not include access tokens, credential-bearing URLs, local username paths, or other secrets. If Git metadata cannot be obtained, record `git.available = false`; do not fail the static analysis.

## 6. Python source-root and module mapping

### 6.1 Configuration sources

Inspect configuration as data only. Do not execute `setup.py` or build backends.

Read, when present:

- `pyproject.toml`;
- `setup.cfg`;
- `setup.py` as text/AST only, without execution;
- `tox.ini`;
- `pytest.ini`;
- `requirements*.txt`;
- `Pipfile` and `Pipfile.lock`;
- `poetry.lock`, `uv.lock`, or other recognized lockfiles;
- `__init__.py` files.

### 6.2 Source-root precedence

Resolve candidate import roots using this precedence:

1. Explicit source-root configuration supplied to the run.
2. Static package-dir declarations in `pyproject.toml` or `setup.cfg`.
3. Recognized `src/` layout.
4. Repository-root package layout.
5. Remaining directories containing Python package files, marked `inferred`.

Record the source-root path and the basis for each mapping.

### 6.3 Module identity rules

- `package/__init__.py` maps to module `package`.
- `package/submodule.py` maps to `package.submodule`.
- `package/subpackage/__init__.py` maps to `package.subpackage`.
- Directories without `__init__.py` MAY be treated as namespace-package portions only when the source-root layout supports that interpretation; otherwise mark the module name unresolved.
- Standalone scripts at a source root receive a module identity derived from their filename without `.py` and `module_kind = "script_or_top_level_module"`.
- If two files map to the same module name under different source roots, preserve both candidates and mark the mapping `ambiguous`; do not select one silently.

### 6.4 Module-resolution categories

Use these categories:

- `internal_resolved`: maps to exactly one in-repository Python file.
- `internal_ambiguous`: multiple in-repository candidate files.
- `stdlib`: top-level import name is in the interpreter's `sys.stdlib_module_names` set.
- `third_party_declared`: external import is declared in project dependency metadata or lockfiles.
- `external_unclassified`: external import not classified by available metadata.
- `unresolved`: import target cannot be mapped with available static evidence.

Do not import third-party modules to classify them.

## 7. Enola primary graph extraction

### 7.1 Workspace isolation

1. Create a unique temporary workspace outside the repository.
2. Copy the repository working-tree contents into the workspace, preserving relative paths and file bytes.
3. Apply the same explicit exclusion rules to the copied tree.
4. Preserve the repository's source files; do not copy credentials, `.git` contents, virtual environments, or cache directories.
5. Capture Git metadata separately before creating the copy.
6. Run Enola only against the temporary copy.

### 7.2 Execution

From the temporary repository root, execute:

```text
enola --version
enola --generate
enola --explain .
```

The analysis wrapper MUST capture exit codes and standard output/error. It MUST NOT treat a successful process exit as proof of complete Python extraction.

### 7.3 Required Enola artifacts

Read these artifacts when generated:

| Artifact | Use |
|---|---|
| `.enola/facts.jsonl` | Primary facts and directed relations |
| `.enola/insights.json` | Architecture findings and evidence |
| `.enola/receipt.json` | Enola version, snapshot metadata, active extractors, parse/extraction coverage |
| `.enola/flows.json` | Optional entry/flow information, if present in the installed Enola version |
| `.enola/docs.jsonl` | Optional documented-symbol associations, if present |

`facts.jsonl` is an intermediate file. It MUST be parsed line by line and normalized into the final JSON array structures. It MUST NOT be published as the final output.

### 7.4 Enola acceptance checks

- Confirm the Python extractor is listed as active in the receipt or equivalent extraction metadata.
- Confirm Python file/fact counts are non-zero when the inventory contains Python files expected to be analyzed.
- Confirm declarations and import relationships are present for a known test fixture.
- Record missing extractors, unsupported files, parse failures, unresolved relationships, and coverage values.
- If Python extraction is absent or all Python files are skipped, set `analysis.status = "partial"` or `"failed"` according to the failure scope; never report `complete`.

### 7.5 Facts consumed

Normalize, when present:

- `module` facts;
- `symbol` facts (functions, methods, classes, constants, and other supported symbol kinds);
- `dependency` facts;
- `route` facts only when the repository framework is explicitly supported by the installed Enola extractor;
- `storage` facts only when supported by the installed framework extractor;
- relation edges such as `declares`, `imports`, `calls`, `implements`, `instantiates`, and other explicitly documented relation types.

Preserve unknown Enola fact kinds and relation kinds under `tool_evidence.enola.raw_kind` / `raw_relation`, or retain their raw record in a bounded extension field. Do not discard unknown additive fields.

## 8. CPython AST extraction

### 8.1 Parse each file

For each inventoried `.py` file:

1. Read bytes.
2. Decode using Python source encoding rules (`tokenize.detect_encoding`).
3. Parse with `ast.parse(source, filename=relative_path, type_comments=True)`.
4. Record parser runtime version and feature-version options.
5. On `SyntaxError`, record exception type, message, line, offset, and text range when available; continue with remaining files.
6. Do not execute the AST or compile it into runnable bytecode.

### 8.2 Declarations

Extract these `ast` node types:

- `ast.Module`;
- `ast.ClassDef`;
- `ast.FunctionDef`;
- `ast.AsyncFunctionDef`;
- nested functions and classes;
- decorated definitions;
- module-level assignments when they define a statically resolvable path/config constant.

For each symbol record:

- stable `symbol_id`;
- `file_id`;
- `name`;
- `qualified_name`;
- `kind` (`class`, `function`, `async_function`, `method`, `async_method`, `nested_function`, `nested_class`, `constant`, `module`);
- `parent_symbol_id`, nullable;
- `lineno`, `end_lineno`, `col_offset`, `end_col_offset`;
- decorator expressions as bounded source strings;
- base-class expressions for classes;
- argument names and parameter categories for functions, excluding runtime values/default object representations;
- `is_async`, `is_generator`, and `is_entrypoint` where statically determinable.

Do not infer method ownership solely from a function name. A function is a method only when it is syntactically nested directly in a class body.

### 8.3 Imports

Extract:

- `ast.Import`;
- `ast.ImportFrom`;
- import aliases;
- relative import level;
- module string;
- imported symbol/name list;
- line/column and exact import statement text.

For each import, calculate:

- importer file/module;
- requested module name;
- resolved in-repository file/module, if unique;
- external classification where available;
- candidate paths for ambiguous resolution;
- resolution status;
- corroboration status from Enola and Grimp.

For `from package import item`, distinguish the imported base module from a possible child module. Resolve `item` to a file only when an in-repository submodule path or other unambiguous evidence exists. Otherwise preserve it as an imported symbol/name and leave `target_file_id` null.

### 8.4 Calls

Extract `ast.Call` nodes and record:

- caller symbol, when contained in a known function/method; otherwise module scope;
- call expression (for example `service.execute`, `Path.read_text`, `run_task`);
- line/column;
- positional argument expression summaries;
- keyword argument names and safe literal summaries;
- Enola-resolved target symbol, if any;
- static target resolution status.

AST name matching alone MUST NOT establish a cross-file call edge. A call edge is `resolved` only when Enola or a deterministic symbol-resolution rule links the call target to one unique in-repository symbol. Otherwise emit an unresolved call-site record with `target_expression`.

### 8.5 File-system and data-file operations

Recognize a versioned API catalog. At minimum, include these call families:

| Operation | APIs/patterns | Relationship type |
|---|---|---|
| Open/read/write | `open`, `io.open`, `Path.open`, `Path.read_text`, `Path.read_bytes`, `Path.write_text`, `Path.write_bytes` | `reads_file`, `writes_file`, `opens_file` |
| Filesystem metadata/listing | `Path.exists`, `Path.is_file`, `Path.is_dir`, `Path.glob`, `Path.rglob`, `os.listdir`, `os.scandir`, `glob.glob`, `glob.iglob` | `checks_file`, `lists_files`, `searches_files` |
| File operations | `shutil.copy`, `copy2`, `copyfile`, `move`, `rmtree`, `os.remove`, `os.unlink`, `Path.unlink`, `Path.rename`, `Path.replace`, `Path.mkdir`, `os.makedirs` | `copies_file`, `moves_file`, `deletes_file`, `creates_directory`, `renames_file` |
| Data readers/writers | common `pandas.read_*`, `DataFrame.to_*`, `csv.reader`, `csv.writer`, `json.load`, `json.dump`, `pickle.load`, `pickle.dump`, `yaml.safe_load`, `yaml.safe_dump`, `configparser.read`, `sqlite3.connect` | `reads_data_file`, `writes_data_file`, `loads_configuration`, `connects_database` |
| Archive operations | `zipfile.ZipFile`, `tarfile.open`, archive extract/create methods | `reads_archive`, `writes_archive`, `extracts_archive` |

For each matched operation record:

- API expression;
- operation category;
- enclosing symbol;
- line/column;
- path argument index or keyword;
- statically evaluated path, if any;
- original path expression;
- path resolution status;
- repository file ID, if the path resolves uniquely inside the repository;
- file target classification (`repository_file`, `external_path`, `dynamic_path`, `unknown`).

For stream-based APIs such as `json.load(file_obj)`, `json.dump(data, file_obj)`, `csv.reader(file_obj)`, `csv.writer(file_obj)`, and `pickle.load(file_obj)`, track only simple file-handle bindings within the same lexical scope:

- `with open(path) as handle:` binds `handle` to the statically evaluated path for the body of that `with` block.
- `handle = open(path)` binds `handle` to the path for the remainder of the same lexical scope until reassigned.
- `json.load(handle)` and equivalent APIs inherit the handle's path only when exactly one unambiguous binding exists.
- Do not carry handle bindings across function boundaries, closures, unknown calls, or complex control-flow merges.
- When the binding is ambiguous or escapes the supported scope, preserve the operation and mark the target unresolved.

The API catalog MUST be stored as a versioned constant in the adapter and its version MUST appear in `analysis.extractor_ruleset_version`.

### 8.6 Safe static path evaluation

Only perform bounded static evaluation. Allowed expressions:

- string constants;
- bytes constants decoded safely when they represent a path;
- names bound to module-level or local immutable string constants where the binding is unambiguous;
- string concatenation of constant operands;
- f-strings whose interpolated expressions are all statically known constants;
- `Path("literal")`;
- `os.path.join()` when every path argument is a known constant;
- `Path("literal").joinpath("literal", ...)` when every argument is a known constant.

Do not evaluate:

- function calls other than the explicitly permitted pure path constructors above;
- environment variables;
- arbitrary attributes;
- comprehensions;
- conditional expressions unless both branches resolve to the same literal value;
- user-defined methods or properties.

If the expression is only partly resolvable, record the literal template and mark it `partially_resolved` or `unresolved`. Do not guess runtime values.

### 8.7 Dynamic imports and execution

Recognize and record:

- `importlib.import_module(...)`;
- `__import__(...)`;
- `runpy.run_module(...)`;
- `runpy.run_path(...)`;
- `subprocess.run`, `subprocess.call`, `subprocess.Popen`, `subprocess.check_call`, `subprocess.check_output`;
- `os.system`, `os.popen`, and platform-specific shell launch wrappers when syntactically identifiable;
- `exec()` and `eval()` as dynamic-code indicators.

Record the literal or expression arguments and line locations. Resolve to a repository file only when the module/path is statically known and maps to one file. Do not execute commands or imports.

### 8.8 Entry points

Detect:

- `if __name__ == "__main__"` blocks;
- `__main__.py` modules;
- statically declared console-script entry points from `pyproject.toml` or `setup.cfg`;
- module-level command registration patterns only when explicitly supported by a deterministic rule.

Mark source of evidence as `ast_main_guard`, `file_name_main`, or `project_metadata`. Do not infer entrypoint status merely because a file contains a `main()` function.

## 9. Grimp independent import analysis

### 9.1 Package selection

1. Use the source-root and module map from Section 6.
2. Identify top-level regular packages and namespace-package portions.
3. Add source roots to the isolated analyzer process's `PYTHONPATH`.
4. Do not install the repository project or its dependencies.
5. Invoke Grimp only for package roots Grimp can identify as importable.
6. Record standalone scripts and unrecognized package roots as `not_applicable`; AST and Enola still analyze those files.

### 9.2 Execution requirements

Use the Grimp API in an isolated subprocess with caching disabled:

```python
import grimp

graph = grimp.build_graph(
    "top_level_package",
    include_external_packages=True,
    cache_dir=None,
)
```

For each internal import edge, retrieve import-site details through Grimp's documented graph API, including importer, imported module, line number, and import line contents where available.

### 9.3 Reconciliation

For each package import edge:

- match to an AST import by normalized importer module, imported module, and source line;
- match to an Enola dependency fact by source module/file and target module;
- set `corroborated_by` to the tools that independently report it;
- retain unmatched Grimp edges as `grimp_only` evidence;
- retain AST/Enola edges absent from Grimp as `not_seen_by_grimp` with a reason such as standalone script, unresolved package root, conditional/dynamic import, or coverage gap;
- never delete an edge solely because another tool did not report it.

Grimp's external package graph is a module-level classification aid. Do not recursively analyze the internal dependencies of third-party packages.

## 10. Relationship normalization

### 10.1 Entity identifiers

Use deterministic, human-readable identifiers. Do not allocate sequential numeric IDs.

- File: `file:<repository-relative-path>`
- Module: `module:<module-qualified-name>`; append `@<relative-path>` if module identity is ambiguous.
- Symbol: `symbol:<relative-path>::<qualified-name>@<line>`
- External package: `package:<top-level-package-name>`
- Unknown call target: no target entity ID; preserve `target_expression`.

All path IDs MUST use repository-relative POSIX paths.

### 10.2 Relationship direction

Relationships are directed from the source actor to the referenced/affected target.

| Relationship type | Source | Target |
|---|---|---|
| `imports` | importing module/file | imported module/package |
| `calls` | caller symbol | resolved callee symbol |
| `instantiates` | caller symbol | resolved class symbol |
| `implements` | class symbol | base/interface symbol |
| `reads_file` | source symbol/file | data/config file |
| `writes_file` | source symbol/file | data/output file |
| `opens_file` | source symbol/file | target file/path |
| `lists_files` | source symbol/file | directory/glob target |
| `copies_file` | source symbol/file | destination file/path; retain source path argument too |
| `moves_file` | source symbol/file | destination file/path; retain source path argument too |
| `deletes_file` | source symbol/file | deleted file/path |
| `executes_script` | caller symbol/file | script/module/command target |
| `dynamic_imports` | importer symbol/file | module name or unresolved expression |
| `references_configuration` | source symbol/file | config file/path |
| `connects_database` | source symbol/file | database target or unresolved expression |

### 10.3 Relationship resolution status

Allowed values:

- `resolved`: unique in-repository file/symbol/package target.
- `external`: known standard-library or third-party target outside the repository.
- `partially_resolved`: part of the target/path is known, but final target is not unique.
- `ambiguous`: multiple equally valid repository targets exist.
- `unresolved`: target cannot be established statically.

### 10.4 Evidence strength

Allowed values:

- `direct_ast`: relationship is directly represented by a syntax node and statically known arguments.
- `enola_linked`: Enola produced a resolved graph edge.
- `grimp_import`: Grimp independently produced an import edge and source-site detail.
- `static_constant`: path/module value resolved by the bounded constant evaluator.
- `inferred_path`: target derived by a documented source-root/path mapping rule.
- `unresolved_expression`: expression was detected but target was not resolved.

Do not assign fabricated numeric confidence scores. Preserve tool provenance and resolution status instead.

### 10.5 Evidence object

Each evidence item MUST contain:

```json
{
  "source_file_id": "file:src/example.py",
  "line": 17,
  "column": 4,
  "end_line": 17,
  "extractor": "python_ast",
  "evidence_type": "direct_ast",
  "expression": "Path('settings.yaml').read_text()",
  "source_hash": "<sha256-of-source-file>"
}
```

`column` and `end_line` MAY be null when the producing tool does not provide them. `expression` MUST be length-limited and MUST NOT include secret values. Source snippets MUST be redacted before serialization when they resemble credentials, tokens, private keys, or connection strings.

### 10.6 Deduplication

Deduplicate relationship records by:

```text
(source_entity_id, relationship_type, target_entity_id, normalized_target_expression)
```

Merge evidence arrays; do not collapse distinct call/import locations. Sort evidence by source file, line, column, extractor.

## 11. Graph analysis

Perform the following analyses on the normalized directed graph.

### 11.1 Direct dependencies

- Count direct internal imports by module and file.
- Count external imports by package and classification.
- Calculate in-degree and out-degree for module/file import graph.
- List files with no statically detected inbound relationships as `no_static_inbound_edges`; do not label them unused/orphan.

### 11.2 Transitive dependencies

- Calculate reachable internal modules for each module using directed graph traversal.
- Preserve the direct-edge path for each reported chain.
- Set a documented maximum path length or result cap for large repositories; record when capped.
- Do not materialize an unbounded all-pairs transitive closure.

### 11.3 Cycles

- Record import cycles reported by Grimp and/or Enola.
- Normalize each cycle to a deterministic representation (rotate the cycle so its lexicographically smallest module is first; preserve direction).
- Record the reporting tool(s) and all known import sites for each cycle edge.
- Do not treat a shared dependency or common third-party import as a cycle.

### 11.4 File data-flow candidates

Create candidate file-flow paths only where explicit file-operation edges connect a producer to a consumer of the same resolved repository file.

- `writes_file` → `reads_file` can form a candidate producer-consumer edge.
- Exact normalized file target match is required.
- Dynamic path templates MUST NOT be merged into exact file flows.
- Record `flow_basis = "matching_static_path"`.
- Do not infer temporal order, successful execution, or runtime reachability from static source alone.

### 11.5 Entry-point reachability

- Starting from each statically identified entrypoint, traverse resolved `calls`, `imports`, and `executes_script` edges separately.
- Report reachable files/symbols by edge category.
- Report unresolved outgoing calls/imports as reachability gaps.
- Do not label modules unreachable where entrypoint detection is incomplete.

### 11.6 Enola findings

Normalize findings from `insights.json` without changing their semantics. Preserve finding ID, category, severity/status, confidence if supplied by Enola, message, evidence, and affected entity references. Keep Enola confidence distinct from the process's evidence-strength enum.

## 12. Output JSON contract

### 12.1 Output filename

Default:

```text
python_repository_analysis.json
```

The caller MAY supply a different filename. The file MUST contain one JSON object, not JSON Lines.

### 12.2 Top-level object

The output MUST contain these top-level keys:

```json
{
  "schema_version": "1.0.0",
  "analysis": {},
  "summary": {},
  "scope": {},
  "files": [],
  "modules": [],
  "symbols": [],
  "relationships": [],
  "imports": {},
  "file_operations": [],
  "entrypoints": [],
  "cycles": [],
  "flows": [],
  "findings": [],
  "unresolved_references": [],
  "coverage": {}
}
```

### 12.3 `analysis`

Required fields:

```json
{
  "analysis_id": "sha256:<deterministic-input-and-toolchain-hash>",
  "started_at_utc": "2026-11-13T16:00:00Z",
  "completed_at_utc": "2026-11-13T16:01:00Z",
  "status": "complete",
  "repository": {
    "name": "repository-name",
    "root_label": "repository-root",
    "git": {
      "available": true,
      "commit": "<commit-or-null>",
      "branch": "<branch-or-null>",
      "working_tree_dirty": false,
      "remote_url_redacted": "<url-or-null>"
    }
  },
  "toolchain": {
    "python": "<runtime-version>",
    "enola": "<version>",
    "grimp": "<version>",
    "jsonschema": "<version>",
    "enola_snapshot_format": "<version-or-null>"
  },
  "extractor_ruleset_version": "1.0.0",
  "analysis_mode": "static_non_executing",
  "network_access": "disabled",
  "network_isolation_enforced": true
}
```

`status` values: `complete`, `partial`, `failed`, `inconsistent_snapshot`.

`analysis_id` MUST be derived from sorted in-scope file paths and hashes, tool versions, scope configuration, and ruleset version. Timestamps MUST NOT be included in `analysis_id`.

### 12.4 `summary`

Include integer counts for:

- `python_files_discovered`;
- `python_files_analyzed`;
- `python_files_parse_success`;
- `python_files_parse_failed`;
- `python_files_skipped`;
- `modules_total`;
- `symbols_total`;
- `imports_total`;
- `internal_imports_resolved`;
- `external_imports`;
- `imports_unresolved`;
- `calls_total`;
- `calls_resolved`;
- `calls_unresolved`;
- `file_operations_total`;
- `file_operations_resolved`;
- `file_operations_unresolved`;
- `dynamic_imports_total`;
- `execution_references_total`;
- `cycles_total`;
- `findings_total`;
- `unresolved_references_total`.

All counts MUST be calculated from the final normalized records, not separately guessed from tool console output. `python_files_analyzed` means files for which an AST parse attempt was made; therefore `python_files_analyzed = python_files_parse_success + python_files_parse_failed` and `python_files_discovered = python_files_analyzed + python_files_skipped`.

### 12.5 `files`

One record per discovered `.py` file:

```json
{
  "file_id": "file:src/package/worker.py",
  "path": "src/package/worker.py",
  "sha256": "<hex-sha256>",
  "size_bytes": 1234,
  "module_id": "module:package.worker",
  "module_name": "package.worker",
  "module_kind": "regular_package_module",
  "source_root": "src",
  "parse_status": "success",
  "enola_status": "parsed",
  "grimp_status": "included",
  "is_test_file": false,
  "is_generated_candidate": false,
  "line_count": 87,
  "parse_errors": []
}
```

Allowed `parse_status`: `success`, `failed`, `not_attempted`.

Allowed `enola_status`: `parsed`, `skipped`, `failed`, `not_reported`.

Allowed `grimp_status`: `included`, `not_applicable`, `not_included`, `failed`.

### 12.6 `modules`

One record per unique module mapping or ambiguous candidate:

```json
{
  "module_id": "module:package.worker",
  "name": "package.worker",
  "file_ids": ["file:src/package/worker.py"],
  "source_root": "src",
  "kind": "regular_package_module",
  "resolution_status": "internal_resolved",
  "mapping_basis": ["src_layout", "init_py_chain"]
}
```

### 12.7 `symbols`

One record per extracted declaration:

```json
{
  "symbol_id": "symbol:src/package/worker.py::Worker.run@22",
  "file_id": "file:src/package/worker.py",
  "module_id": "module:package.worker",
  "name": "run",
  "qualified_name": "Worker.run",
  "kind": "method",
  "parent_symbol_id": "symbol:src/package/worker.py::Worker@8",
  "lineno": 22,
  "end_lineno": 39,
  "decorators": [],
  "bases": [],
  "is_async": false,
  "is_generator": false,
  "is_entrypoint": false,
  "evidence_sources": ["python_ast", "enola"]
}
```

### 12.8 `relationships`

One normalized relationship per unique source/type/target/expression combination:

```json
{
  "relationship_id": "rel:<sha256>",
  "source_id": "module:package.worker",
  "target_id": "module:package.config",
  "relationship_type": "imports",
  "resolution_status": "resolved",
  "evidence_strength": "direct_ast",
  "corroborated_by": ["enola", "grimp"],
  "target_expression": "package.config",
  "evidence": []
}
```

`target_id` MUST be null for unresolved targets. `target_expression` MUST preserve the detected unresolved expression.

### 12.9 `imports`

```json
{
  "internal": [],
  "external": [],
  "unresolved": [],
  "by_module": []
}
```

Each import record MUST preserve:

- importer file/module ID;
- import form (`import` or `from`);
- requested module;
- imported names and aliases;
- relative level;
- source line/column;
- resolved target module/file IDs, if any;
- module classification;
- resolution status;
- `corroborated_by`;
- all source evidence.

### 12.10 `file_operations`

One record for each distinct source-level file/data operation call site. Do not merge separate call sites merely because their target paths match.

Required fields:

- operation ID;
- source file/symbol ID;
- operation type;
- API expression;
- target file ID, nullable;
- target path/expression;
- source/destination path expressions for copy/move operations;
- resolution status;
- line/column;
- evidence.

### 12.11 `entrypoints`, `cycles`, `flows`, `findings`

- `entrypoints`: source file/module/symbol, entrypoint type, evidence.
- `cycles`: ordered module IDs, edge import evidence, reporting tool(s).
- `flows`: only explicit candidate flows defined in Section 11.4 or entrypoint reachability paths; include `flow_basis` and evidence for every edge.
- `findings`: normalized Enola insights and process-level quality findings. Process-level findings MUST be distinguished with `finding_source = "analysis_pipeline"`.

### 12.12 `unresolved_references`

Include every unresolved/ambiguous import, call, dynamic import, file path, execution target, source-root mapping, and failed tool link.

Required fields:

```json
{
  "reference_id": "unresolved:<sha256>",
  "source_file_id": "file:src/worker.py",
  "source_symbol_id": null,
  "reference_type": "dynamic_import",
  "target_expression": "importlib.import_module(module_name)",
  "resolution_status": "unresolved",
  "reason_code": "runtime_value_required",
  "line": 41,
  "column": 8,
  "detected_by": ["python_ast"],
  "evidence": []
}
```

Use stable `reason_code` values, including:

- `dynamic_expression`;
- `runtime_value_required`;
- `multiple_candidate_targets`;
- `module_root_unknown`;
- `unsupported_import_form`;
- `syntax_parse_failed`;
- `tool_extractor_gap`;
- `source_path_outside_repository`;
- `third_party_not_declared`;
- `grimp_not_applicable`.

### 12.13 `scope`

Required fields:

```json
{
  "repository_root_label": "repository-root",
  "included_extensions": [".py"],
  "source_roots": [
    {"path": "src", "basis": "src_layout", "module_names": ["package"]}
  ],
  "exclusions": [
    {"pattern": ".venv/**", "reason": "python_environment", "matched_files": 125}
  ],
  "discovered_file_ids": ["file:src/package/worker.py"]
}
```

`source_roots` and `exclusions` MUST preserve the evidence/basis used to determine them. `discovered_file_ids` MUST refer to records in `files`.

### 12.14 `coverage`

Include:
- discovered file count;
- parsed file count;
- parse failure count and paths;
- Enola active extractor list;
- Enola parsed/skipped/failed file counts when available;
- Grimp package roots attempted/succeeded/failed/not applicable;
- imports seen by AST, Enola, and Grimp;
- corroborated import-edge count;
- tool-only edge counts;
- unresolved relationship counts grouped by type and reason code;
- path-operation API catalog version;
- excluded path patterns and excluded file counts;
- analysis completeness notes.

## 13. JSON Schema validation

Use JSON Schema Draft 2020-12 and the open-source `jsonschema` Python package.

Validation requirements:

1. Validate top-level required keys and `schema_version`.
2. Validate enumerated status and relationship values.
3. Validate all required field types.
4. Validate identifiers as non-empty strings.
5. Validate evidence array shape.
6. Validate that all non-null `file_id`, `module_id`, and `symbol_id` references resolve to entities in the same document.
7. Validate that unresolved relationship targets are null and have a `target_expression` or explicit reason.
8. Validate that all file paths are repository-relative and do not contain `..` path traversal segments.
9. Validate deterministic array sorting.
10. Validate uniqueness of file IDs, symbol IDs, module mapping keys, and relationship IDs.
11. Reject NaN, Infinity, non-UTF-8 output, duplicate JSON object keys, and non-JSON values.
12. Reject output if any relationship references a missing entity, except external package IDs explicitly listed in `imports.external`.

The JSON Schema definition MUST be stored inside the orchestration package or embedded in the technical implementation. It MUST be versioned with this process. Schema validation errors MUST be included in the execution log and MUST prevent publication.

## 14. Publication and cleanup

1. Construct the full output object in memory or in a temporary file outside the repository.
2. Sort every list by its documented stable key.
3. Compute summary counts from the normalized data.
4. Validate the output against JSON Schema.
5. Serialize as UTF-8 JSON with deterministic key ordering and a fixed indentation policy.
6. Write to `<output>.tmp` in the destination directory.
7. Flush and close the temporary file.
8. Recheck source-file hashes against the initial inventory.
9. If any hash changed, set `status = "inconsistent_snapshot"`, regenerate from a stable snapshot or terminate without publishing a complete result.
10. Atomically replace the destination file with the validated temporary file.
11. Remove the temporary Enola workspace and transient files unless `--retain-intermediates` was selected.
12. Confirm that exactly one final `.json` output file was created by the process.

## 15. Error handling and exit codes

| Exit code | Status | Condition |
|---:|---|---|
| `0` | `complete` | All in-scope files inventoried; AST completed; Enola Python extractor active; final JSON validated; no source snapshot inconsistency. Unresolved references may exist and are expected to be reported. |
| `1` | `partial` | Some files failed parsing; Enola coverage incomplete; Grimp could not analyze some packages; or some tool extraction failed while a valid partial JSON can still be produced. |
| `2` | `failed` | Invalid repository/output path, required core tool missing, no valid JSON can be constructed, or schema validation fails. |
| `3` | `inconsistent_snapshot` | Source files changed during analysis and a stable snapshot could not be maintained. |

Tool-specific failures:

- Enola failure: continue AST extraction and Grimp where possible; mark Enola coverage failed and final status `partial`.
- Grimp failure: continue Enola and AST; mark Grimp coverage failed and final status `partial`.
- AST parse failure for one file: retain inventory record, add parse error and unresolved references where applicable; continue remaining files.
- JSON Schema failure: do not publish the result file as valid.
- Source hash change: do not report the result as complete.

## 16. Quality gates and acceptance tests

The process MUST pass these tests before repository-wide deployment.

### 16.1 Test fixture

Create a controlled fixture repository containing:

1. A regular package with `__init__.py`.
2. A namespace package without `__init__.py`.
3. A `src/` layout.
4. A top-level standalone script.
5. Absolute imports.
6. Relative imports (`from .x import y`, `from ..x import y`).
7. Aliased imports.
8. `TYPE_CHECKING` guarded imports.
9. A third-party import and a standard-library import.
10. A direct function call and a class instantiation across files.
11. A dynamic `importlib.import_module()` call.
12. A `__main__` guard.
13. `open()` with a literal repository-relative path.
14. `Path.read_text()` and `Path.write_text()`.
15. `pandas.read_csv()` or an equivalent recognized data reader.
16. A generated f-string path containing a runtime variable.
17. `subprocess.run()` invoking a local script.
18. A copy/move/delete operation.
19. A static import cycle.
20. A syntax-invalid Python file.
21. Two ambiguous module candidates in different source roots.
22. A Python file under an `archive/` or `legacy/` directory.

### 16.2 Required assertions

- All included `.py` files appear exactly once in `files`.
- Excluded files are counted and their patterns are recorded.
- Every source file hash matches the original bytes.
- All valid import statements appear in the `imports` records.
- Relative import resolution is correct for the fixture package layout.
- Ambiguous imports are not resolved arbitrarily.
- External imports are classified without importing external packages.
- Enola and Grimp edge corroboration is correct for common package imports.
- AST records literal file operations with correct line numbers.
- Dynamic file paths are marked unresolved or partially resolved, not linked to guessed targets.
- Subprocess and dynamic import references are recorded without execution.
- Cycles preserve direction and edge evidence.
- The syntax-invalid file is retained in inventory with a parse failure.
- Archive/legacy Python files are included unless explicitly excluded.
- No application source code is executed.
- No repository file is modified.
- Final output is one syntactically valid JSON object and passes JSON Schema validation.
- Repeated runs over identical source/tool versions/configuration produce identical semantic content and identical `analysis_id`; timestamps may differ.

### 16.3 Coverage gates

A run MUST NOT be marked `complete` unless:

- `python_files_discovered == python_files_analyzed + python_files_skipped`;
- every discovered file has a `files` record;
- every AST parse attempt has a result status;
- Enola's Python extractor is confirmed active, or the process configuration explicitly permits AST-only mode;
- every detected relationship has evidence;
- all unresolved references are retained;
- JSON Schema validation succeeds;
- the final source-hash consistency check succeeds.

`Grimp` coverage gaps do not by themselves make the entire run incomplete when Enola and AST coverage are valid; they MUST be reported.

## 17. Security and non-execution controls

- Run tools with network access disabled where the environment supports it.
- Do not install the repository's own package or dependency set.
- Do not invoke package build backends, `setup.py`, scripts, tests, application entrypoints, or module imports.
- Do not evaluate repository expressions or execute AST nodes.
- Run Enola and Grimp in a temporary workspace with read-only access to the source snapshot where supported.
- Do not expose tokens, passwords, private keys, or full credential-bearing URLs in evidence strings.
- Apply secret-pattern redaction to source snippets and path/command arguments before final JSON serialization.
- Store only relative paths in identifiers and normal output fields.
- Keep tool versions and analysis settings in the result for auditability.

## 18. Known static-analysis limitations

The result is a static evidence model, not a complete runtime truth model.

| Source pattern | Expected handling |
|---|---|
| `importlib.import_module(variable)` | Dynamic import record; unresolved unless variable resolves to a safe constant |
| `getattr(module, name)` | Record dynamic attribute access only if explicitly supported; otherwise unresolved reference |
| `eval()` / `exec()` | Dynamic-code indicator; do not attempt to interpret executed code |
| Reflection/monkey-patching | Preserve Enola findings and explicit AST evidence; do not invent call edges |
| Dependency injection/service locator | Unresolved unless Enola has a specific supported extractor or direct static binding is proven |
| Runtime-generated paths | Preserve path expression; no guessed file target |
| Environment-variable paths | Record environment variable name where safe; do not read the environment value |
| Runtime plugin discovery | Record import/entrypoint pattern; do not claim all plugins are known |
| Framework route registration | Include only routes emitted by a supported Enola extractor or explicit configured AST rule |
| Generated Python files | Include unless explicitly excluded; mark generated status only with evidence from headers/build metadata |
| C extensions or compiled modules | Report as external/unresolved import target unless repository source mapping exists |
| Conditional imports | Record condition context when practical; do not assume the condition is true |

## 19. Final result definition

A successful run produces exactly one file:

```text
python_repository_analysis.json
```

The file is the authoritative output of this analysis run. It contains:

- repository and toolchain provenance;
- in-scope Python file inventory;
- module and symbol records;
- normalized direct and transitive relationships;
- import graph and independent tool corroboration;
- statically detected file operations and execution references;
- entrypoints, cycles, and candidate file flows;
- Enola findings;
- unresolved and ambiguous references;
- coverage and quality metrics.

The file MUST NOT claim runtime execution order, successful data transfer, business-process ownership, or canonical module ownership unless those facts are independently established by explicit source evidence and represented as such.

## 20. Source references

1. Enola graph facts, relationships, output artifacts, and extraction limits: <https://enola.tech/docs/graph>
2. Enola Python language coverage and required verification of actual extractor coverage: <https://enola.tech/docs/language-coverage>
3. Enola extraction is parser-based and non-executing: <https://enola.tech/docs/how-it-works>
4. Enola command workflow and snapshot generation: <https://enola.tech/docs/workflows>
5. Enola Apache-2.0 license: <https://github.com/enola-labs/enola/blob/main/LICENSE>
6. Grimp directed import graph, import details, external package handling, and namespace package support: <https://grimp.readthedocs.io/en/latest/usage.html>
7. Grimp BSD-2-Clause license: <https://github.com/python-grimp/grimp/blob/main/LICENSE>
8. Python AST parsing and visitor APIs: <https://docs.python.org/3/library/ast.html>
9. JSON Schema specification: <https://json-schema.org/specification>
10. `jsonschema` implementation and MIT license: <https://github.com/python-jsonschema/jsonschema>

---

## Appendix A. Minimum normalized relationship example

```json
{
  "relationship_id": "rel:7f3d...",
  "source_id": "symbol:contracts/models/csv_models.py::ReentryDecision.validate@118",
  "target_id": "module:shared.reentry",
  "relationship_type": "imports",
  "resolution_status": "resolved",
  "evidence_strength": "direct_ast",
  "corroborated_by": ["python_ast"],
  "target_expression": "shared.reentry",
  "evidence": [
    {
      "source_file_id": "file:contracts/models/csv_models.py",
      "line": 118,
      "column": 19,
      "end_line": 118,
      "extractor": "python_ast",
      "evidence_type": "direct_ast",
      "expression": "from shared.reentry import parse",
      "source_hash": "<sha256>"
    }
  ]
}
```

## Appendix B. Minimum execution sequence

```text
1. Validate input paths and tool versions.
2. Capture Git metadata and working-tree state.
3. Create temporary repository snapshot.
4. Inventory all in-scope .py files and compute SHA-256 hashes.
5. Identify Python source roots, packages, namespace portions, and module candidates.
6. Run Enola --generate in the temporary snapshot.
7. Read Enola facts.jsonl, insights.json, and receipt.json.
8. Parse every .py file with CPython ast.parse.
9. Extract declarations, import statements, call sites, file operations, dynamic imports,
   execution references, and entrypoint markers.
10. Run Grimp against every eligible top-level package in an isolated subprocess.
11. Reconcile AST, Enola, and Grimp import relationships.
12. Normalize identifiers, relationship direction, evidence, and resolution status.
13. Deduplicate relationships while preserving all evidence locations.
14. Compute dependencies, cycles, reachability, file-flow candidates, and coverage.
15. Construct the single output JSON object.
16. Validate JSON structure, references, paths, enums, and sorting.
17. Recompute source hashes and confirm snapshot consistency.
18. Atomically publish python_repository_analysis.json.
19. Remove temporary workspace and intermediate artifacts.
20. Return exit code 0, 1, 2, or 3 using Section 15.
```


## Appendix C. JSON Schema Draft 2020-12 validation contract

The following schema is the minimum structural contract for `python_repository_analysis.json`. Implementations MAY add stricter semantic checks, but MUST NOT weaken the required keys, enums, identifier constraints, path constraints, or referential-integrity checks described in Sections 12 and 13.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:eafix:schemas:python-repository-analysis:1.0.0",
  "title": "Python Repository Analysis Result",
  "type": "object",
  "required": [
    "schema_version", "analysis", "summary", "scope", "files", "modules",
    "symbols", "relationships", "imports", "file_operations", "entrypoints",
    "cycles", "flows", "findings", "unresolved_references", "coverage"
  ],
  "properties": {
    "schema_version": {"const": "1.0.0"},
    "analysis": {
      "type": "object",
      "required": ["analysis_id", "started_at_utc", "completed_at_utc", "status", "repository", "toolchain", "extractor_ruleset_version", "analysis_mode", "network_access", "network_isolation_enforced"],
      "properties": {
        "analysis_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        "started_at_utc": {"type": "string", "format": "date-time"},
        "completed_at_utc": {"type": "string", "format": "date-time"},
        "status": {"enum": ["complete", "partial", "failed", "inconsistent_snapshot"]},
        "repository": {
          "type": "object",
          "required": ["name", "root_label", "git"],
          "properties": {
            "name": {"type": "string", "minLength": 1},
            "root_label": {"type": "string", "minLength": 1},
            "git": {
              "type": "object",
              "required": ["available", "commit", "branch", "working_tree_dirty", "remote_url_redacted"],
              "properties": {
                "available": {"type": "boolean"},
                "commit": {"type": ["string", "null"]},
                "branch": {"type": ["string", "null"]},
                "working_tree_dirty": {"type": ["boolean", "null"]},
                "remote_url_redacted": {"type": ["string", "null"]}
              },
              "additionalProperties": true
            }
          },
          "additionalProperties": true
        },
        "toolchain": {
          "type": "object",
          "required": ["python", "enola", "grimp", "jsonschema", "enola_snapshot_format"],
          "properties": {
            "python": {"type": "string"},
            "enola": {"type": ["string", "null"]},
            "grimp": {"type": ["string", "null"]},
            "jsonschema": {"type": ["string", "null"]},
            "enola_snapshot_format": {"type": ["string", "null"]}
          },
          "additionalProperties": true
        },
        "extractor_ruleset_version": {"type": "string"},
        "analysis_mode": {"const": "static_non_executing"},
        "network_access": {"enum": ["disabled", "not_enforced", "not_applicable"]},
        "network_isolation_enforced": {"type": "boolean"}
      },
      "additionalProperties": true
    },
    "summary": {
      "type": "object",
      "required": [
        "python_files_discovered", "python_files_analyzed", "python_files_parse_success",
        "python_files_parse_failed", "python_files_skipped", "modules_total", "symbols_total",
        "imports_total", "internal_imports_resolved", "external_imports", "imports_unresolved",
        "calls_total", "calls_resolved", "calls_unresolved", "file_operations_total",
        "file_operations_resolved", "file_operations_unresolved", "dynamic_imports_total",
        "execution_references_total", "cycles_total", "findings_total", "unresolved_references_total"
      ],
      "properties": {
        "python_files_discovered": {"type": "integer", "minimum": 0},
        "python_files_analyzed": {"type": "integer", "minimum": 0},
        "python_files_parse_success": {"type": "integer", "minimum": 0},
        "python_files_parse_failed": {"type": "integer", "minimum": 0},
        "python_files_skipped": {"type": "integer", "minimum": 0},
        "modules_total": {"type": "integer", "minimum": 0},
        "symbols_total": {"type": "integer", "minimum": 0},
        "imports_total": {"type": "integer", "minimum": 0},
        "internal_imports_resolved": {"type": "integer", "minimum": 0},
        "external_imports": {"type": "integer", "minimum": 0},
        "imports_unresolved": {"type": "integer", "minimum": 0},
        "calls_total": {"type": "integer", "minimum": 0},
        "calls_resolved": {"type": "integer", "minimum": 0},
        "calls_unresolved": {"type": "integer", "minimum": 0},
        "file_operations_total": {"type": "integer", "minimum": 0},
        "file_operations_resolved": {"type": "integer", "minimum": 0},
        "file_operations_unresolved": {"type": "integer", "minimum": 0},
        "dynamic_imports_total": {"type": "integer", "minimum": 0},
        "execution_references_total": {"type": "integer", "minimum": 0},
        "cycles_total": {"type": "integer", "minimum": 0},
        "findings_total": {"type": "integer", "minimum": 0},
        "unresolved_references_total": {"type": "integer", "minimum": 0}
      },
      "additionalProperties": true
    },
    "scope": {
      "type": "object",
      "required": ["repository_root_label", "included_extensions", "source_roots", "exclusions", "discovered_file_ids"],
      "properties": {
        "repository_root_label": {"type": "string"},
        "included_extensions": {"type": "array", "items": {"type": "string"}},
        "source_roots": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["path", "basis", "module_names"],
            "properties": {
              "path": {"type": "string"},
              "basis": {"type": "string"},
              "module_names": {"type": "array", "items": {"type": "string"}}
            },
            "additionalProperties": true
          }
        },
        "exclusions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["pattern", "reason", "matched_files"],
            "properties": {
              "pattern": {"type": "string"},
              "reason": {"type": "string"},
              "matched_files": {"type": "integer", "minimum": 0}
            },
            "additionalProperties": true
          }
        },
        "discovered_file_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": true}
      },
      "additionalProperties": true
    },
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["file_id", "path", "sha256", "size_bytes", "module_name", "module_kind", "parse_status", "enola_status", "grimp_status", "is_test_file", "is_generated_candidate", "line_count", "parse_errors"],
        "properties": {
          "file_id": {"type": "string", "pattern": "^file:"},
          "path": {"type": "string", "minLength": 1, "not": {"pattern": "(^|/)\\.\\.?(/|$)"}},
          "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
          "size_bytes": {"type": "integer", "minimum": 0},
          "module_id": {"type": ["string", "null"]},
          "module_name": {"type": ["string", "null"]},
          "module_kind": {"type": "string"},
          "source_root": {"type": ["string", "null"]},
          "parse_status": {"enum": ["success", "failed", "not_attempted"]},
          "enola_status": {"enum": ["parsed", "skipped", "failed", "not_reported"]},
          "grimp_status": {"enum": ["included", "not_applicable", "not_included", "failed"]},
          "is_test_file": {"type": "boolean"},
          "is_generated_candidate": {"type": "boolean"},
          "line_count": {"type": "integer", "minimum": 0},
          "parse_errors": {"type": "array", "items": {"type": "object"}}
        },
        "additionalProperties": true
      }
    },
    "modules": {"type": "array", "items": {"type": "object", "required": ["module_id", "name", "file_ids", "kind", "resolution_status"], "properties": {"module_id": {"type": "string"}, "name": {"type": "string"}, "file_ids": {"type": "array", "items": {"type": "string"}}, "kind": {"type": "string"}, "resolution_status": {"enum": ["internal_resolved", "internal_ambiguous", "unresolved"]}}, "additionalProperties": true}},
    "symbols": {"type": "array", "items": {"type": "object", "required": ["symbol_id", "file_id", "name", "qualified_name", "kind", "lineno"], "properties": {"symbol_id": {"type": "string", "pattern": "^symbol:"}, "file_id": {"type": "string"}, "module_id": {"type": ["string", "null"]}, "name": {"type": "string"}, "qualified_name": {"type": "string"}, "kind": {"type": "string"}, "parent_symbol_id": {"type": ["string", "null"]}, "lineno": {"type": "integer", "minimum": 1}, "end_lineno": {"type": ["integer", "null"], "minimum": 1}, "is_async": {"type": "boolean"}, "is_generator": {"type": "boolean"}, "is_entrypoint": {"type": "boolean"}}, "additionalProperties": true}},
    "relationships": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["relationship_id", "source_id", "target_id", "relationship_type", "resolution_status", "evidence_strength", "corroborated_by", "evidence"],
        "properties": {
          "relationship_id": {"type": "string", "pattern": "^rel:"},
          "source_id": {"type": "string", "minLength": 1},
          "target_id": {"type": ["string", "null"]},
          "relationship_type": {"type": "string"},
          "resolution_status": {"enum": ["resolved", "external", "partially_resolved", "ambiguous", "unresolved"]},
          "evidence_strength": {"enum": ["direct_ast", "enola_linked", "grimp_import", "static_constant", "inferred_path", "unresolved_expression"]},
          "corroborated_by": {"type": "array", "items": {"type": "string"}, "uniqueItems": true},
          "target_expression": {"type": ["string", "null"]},
          "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}, "minItems": 1}
        },
        "additionalProperties": true
      }
    },
    "imports": {
      "type": "object",
      "required": ["internal", "external", "unresolved", "by_module"],
      "properties": {
        "internal": {"type": "array", "items": {"type": "object"}},
        "external": {"type": "array", "items": {"type": "object"}},
        "unresolved": {"type": "array", "items": {"type": "object"}},
        "by_module": {"type": "array", "items": {"type": "object"}}
      },
      "additionalProperties": true
    },
    "file_operations": {"type": "array", "items": {"type": "object", "required": ["operation_id", "source_file_id", "operation_type", "api_expression", "resolution_status", "line", "evidence"], "properties": {"operation_id": {"type": "string"}, "source_file_id": {"type": "string"}, "source_symbol_id": {"type": ["string", "null"]}, "operation_type": {"type": "string"}, "api_expression": {"type": "string"}, "target_file_id": {"type": ["string", "null"]}, "target_path_expression": {"type": ["string", "null"]}, "resolution_status": {"enum": ["resolved", "external", "partially_resolved", "ambiguous", "unresolved"]}, "line": {"type": "integer", "minimum": 1}, "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}, "minItems": 1}}, "additionalProperties": true}},
    "entrypoints": {"type": "array", "items": {"type": "object", "required": ["source_file_id", "entrypoint_type", "evidence"], "properties": {"source_file_id": {"type": "string"}, "source_symbol_id": {"type": ["string", "null"]}, "entrypoint_type": {"type": "string"}, "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}}}, "additionalProperties": true}},
    "cycles": {"type": "array", "items": {"type": "object", "required": ["module_ids", "reported_by", "edges"], "properties": {"module_ids": {"type": "array", "items": {"type": "string"}, "minItems": 2}, "reported_by": {"type": "array", "items": {"type": "string"}}, "edges": {"type": "array", "items": {"type": "object"}}}, "additionalProperties": true}},
    "flows": {"type": "array", "items": {"type": "object", "required": ["flow_basis", "steps", "evidence"], "properties": {"flow_basis": {"type": "string"}, "steps": {"type": "array", "items": {"type": "object"}}, "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}}}, "additionalProperties": true}},
    "findings": {"type": "array", "items": {"type": "object", "required": ["finding_source", "message"], "properties": {"finding_source": {"enum": ["enola", "analysis_pipeline"]}, "message": {"type": "string"}, "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}}}, "additionalProperties": true}},
    "unresolved_references": {"type": "array", "items": {"type": "object", "required": ["reference_id", "source_file_id", "reference_type", "target_expression", "resolution_status", "reason_code", "detected_by", "evidence"], "properties": {"reference_id": {"type": "string"}, "source_file_id": {"type": "string"}, "source_symbol_id": {"type": ["string", "null"]}, "reference_type": {"type": "string"}, "target_expression": {"type": "string"}, "resolution_status": {"enum": ["partially_resolved", "ambiguous", "unresolved"]}, "reason_code": {"type": "string"}, "line": {"type": ["integer", "null"], "minimum": 1}, "column": {"type": ["integer", "null"], "minimum": 0}, "detected_by": {"type": "array", "items": {"type": "string"}}, "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}}}, "additionalProperties": true}},
    "coverage": {"type": "object", "required": ["files_discovered", "files_parsed", "parse_failures", "enola_active_extractors", "grimp_packages_attempted", "grimp_packages_succeeded", "unresolved_by_type", "exclusions"], "properties": {"files_discovered": {"type": "integer", "minimum": 0}, "files_parsed": {"type": "integer", "minimum": 0}, "parse_failures": {"type": "array", "items": {"type": "string"}}, "enola_active_extractors": {"type": "array", "items": {"type": "string"}}, "grimp_packages_attempted": {"type": "array", "items": {"type": "string"}}, "grimp_packages_succeeded": {"type": "array", "items": {"type": "string"}}, "unresolved_by_type": {"type": "object"}, "exclusions": {"type": "array", "items": {"type": "object"}}, "analysis_completeness_notes": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": true}
  },
  "$defs": {
    "evidence": {
      "type": "object",
      "required": ["source_file_id", "line", "extractor", "evidence_type", "expression", "source_hash"],
      "properties": {
        "source_file_id": {"type": "string"},
        "line": {"type": ["integer", "null"], "minimum": 1},
        "column": {"type": ["integer", "null"], "minimum": 0},
        "end_line": {"type": ["integer", "null"], "minimum": 1},
        "extractor": {"type": "string"},
        "evidence_type": {"enum": ["direct_ast", "enola_linked", "grimp_import", "static_constant", "inferred_path", "unresolved_expression"]},
        "expression": {"type": "string", "maxLength": 500},
        "source_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

### C.1 Semantic validation beyond JSON Schema

JSON Schema cannot conveniently enforce all cross-record constraints. The validator MUST additionally check:

1. `analysis.analysis_id` equals the expected deterministic hash of the run inputs and toolchain.
2. `summary.python_files_discovered == len(files) == len(scope.discovered_file_ids)`.
3. Every `scope.discovered_file_ids` value exists in `files`.
4. Every non-null file/module/symbol reference resolves to exactly one record, except external package IDs explicitly declared in `imports.external`.
5. Every `relationships[].evidence[].source_file_id` and `file_operations[].source_file_id` exists in `files`.
6. Every file SHA-256 matches the hash captured at inventory time and the final consistency check.
7. Every relationship ID is unique and deterministic.
8. Every cycle edge is represented by one or more import relationships.
9. All arrays are sorted using the stable keys defined in this document.
10. No output field contains an absolute host path, credential-bearing URL, or unredacted secret.