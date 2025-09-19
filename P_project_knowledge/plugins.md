# First-Party Plugins

> Core functionality plugins that implement import, export, validation, and standardization capabilities.

## 11) First‑Party Plugins (compose features)

61) **`plugins/atomic_process_engine/plugin.yaml`**  
**Purpose:** Manifest describing engine plugin.  
**Key responsibilities:** Capabilities (import, validate, export), IO policies, entry point.  
**Used by:** Registry, executor.

62) **`plugins/atomic_process_engine/plugin.py`**  
**Purpose:** Orchestrate import→validate→export for a target file.  
**Key responsibilities:** Call parser/validator/exporters; emit artifacts (MD, Draw.io, JSON).  
**Depends on:** APF core, exporters, recovery.

63) **`plugins/step_sequencer/plugin.yaml`**  
**Purpose:** Manifest for sequencing plugin.  
**Key responsibilities:** Declare `seq.insert`, `seq.renumber` capabilities.

64) **`plugins/step_sequencer/plugin.py`**  
**Purpose:** Expose insert/renumber as plugin commands.  
**Key responsibilities:** Apply `ids` rules; produce renumber maps; return diagnostics.

65) **`plugins/process_standardizer/plugin.yaml`**  
**Purpose:** Manifest for prose standardizer.  
**Key responsibilities:** Declare normalization/transformation capabilities.

66) **`plugins/process_standardizer/plugin.py`**  
**Purpose:** Normalize prose, map to canonical actors/actions.  
**Key responsibilities:** Apply `prose_rules.yaml`; output clean YAML.

67) **`plugins/diagram_generator/plugin.yaml`**  
**Purpose:** Manifest for diagram exporter.  
**Key responsibilities:** Diagram capabilities and format options.

68) **`plugins/diagram_generator/plugin.py`**  
**Purpose:** Wrapper over draw.io exporter (and optionally Mermaid).  
**Key responsibilities:** Layout presets; theming; artifact bundling.

69) **`plugins/validation_engine/plugin.yaml`**  
**Purpose:** Manifest for deep validation plugin.  
**Key responsibilities:** Additional semantic/policy checks.

70) **`plugins/validation_engine/plugin.py`**  
**Purpose:** Enforce advanced invariants/policies.  
**Key responsibilities:** Cross‑file references, library conformance, security rules.

71) **`plugins/documentation/plugin.yaml`**  
**Purpose:** Manifest for doc bundler.  
**Key responsibilities:** Declares MD/PDF packaging capability; assets.

72) **`plugins/documentation/plugin.py`**  
**Purpose:** Generate documentation bundles.  
**Key responsibilities:** Collate MD, images, diagrams; TOC; export zip.