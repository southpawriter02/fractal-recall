#!/usr/bin/env python3
"""
Fix D22 notebook: align install cell with D21 and fix map_frontmatter.

Two issues:
1. Install cell missing 6 packages that D21 includes
2. map_frontmatter looks for 'type'/'name' but corpus uses 'entity_type'/'title'
"""
import json
import sys

NOTEBOOK = "D22-single-layer.ipynb"

with open(NOTEBOOK, "r") as f:
    nb = json.load(f)

fixes_applied = []

for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])

    # Fix 1: Install cell - align with D21
    if "packages = [" in src and "chromadb" in src and "subprocess" in src:
        cell["source"] = [
            '#!/usr/bin/env python3\n',
            '"""\n',
            'D-22: Install Dependencies\n',
            '\n',
            'Installs the same packages as D-21, ensuring compatibility with:\n',
            '- ChromaDB (vector storage)\n',
            '- sentence-transformers (embedding models)\n',
            '- FlagEmbedding (BGE-M3 model loader)\n',
            '- scipy (statistical testing)\n',
            '- pandas (data wrangling)\n',
            '- matplotlib/seaborn (visualization)\n',
            '"""\n',
            '\n',
            'import subprocess\n',
            'import sys\n',
            '\n',
            'packages = [\n',
            '    "sentence-transformers>=3.0.0",      # Primary embedding model loader (v2-moe, v1.5)\n',
            '    "chromadb>=1.0.0",                   # Vector database for retrieval evaluation\n',
            '    "pyyaml>=6.0",                       # YAML parsing for corpus frontmatter\n',
            '    "numpy>=1.24.0",                     # Numerical operations for embeddings\n',
            '    "scipy>=1.10.0",                     # Scientific computing for distance metrics\n',
            '    "scikit-learn>=1.3.0",               # Metrics (precision, recall, NDCG) and clustering\n',
            '    "matplotlib>=3.7.0",                 # Plotting evaluation results\n',
            '    "seaborn>=0.12.0",                   # Statistical visualization\n',
            '    "umap-learn>=0.5.0",                 # Dimensionality reduction for embedding visualization\n',
            '    "pandas>=2.0.0",                     # Data frames for results aggregation\n',
            '    "tqdm>=4.65.0",                      # Progress bars for corpus loading\n',
            '    "transformers>=4.30.0",              # Tokenizer utilities and model infrastructure\n',
            '    "FlagEmbedding>=1.2.0",              # BGE-m3 model loader (alternative to sentence-transformers)\n',
            ']\n',
            '\n',
            'for package in packages:\n',
            '    print(f"Installing {package}...")\n',
            '    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])\n',
            '\n',
            'print("\\u2713 All dependencies installed successfully.")\n',
        ]
        cell["outputs"] = []
        fixes_applied.append(f"Cell {i}: Install cell aligned with D21 (added 6 missing packages)")

    # Fix 2: map_frontmatter - replace with D21-style field alias mapping
    if "def map_frontmatter" in src and "Frontmatter missing required field" in src:
        cell["source"] = [
            '#!/usr/bin/env python3\n',
            '"""\n',
            'D-22: Field Mapping & Normalization\n',
            '\n',
            'Normalizes YAML frontmatter into a consistent metadata dictionary.\n',
            '\n',
            'This is aligned with D-21 Cell 05. It uses a FIELD_MAP to normalize\n',
            'varying frontmatter key names (e.g., entity_type -> type, title -> name)\n',
            'to canonical internal names.\n',
            '\n',
            'Reference: D-21 Cell 05; D-20 (corpus schema)\n',
            '"""\n',
            '\n',
            '# Field Map: canonical key -> list of possible raw frontmatter key names\n',
            'FIELD_MAP: Dict[str, List[str]] = {\n',
            '    "type":              ["type", "entity_type", "document_type", "doc_type", "category"],\n',
            '    "name":              ["name", "entity_name", "title", "subject"],\n',
            '    "canon":             ["canon", "canon_status", "canonical", "is_canonical"],\n',
            '    "authority_layer":   ["authority_layer", "authority", "authority_level"],\n',
            '    "era":               ["era", "age", "time_period", "historical_era", "eras"],\n',
            '    "domain_layer":      ["domain_layer", "domain", "lore_category", "source_hierarchy"],\n',
            '    "related_entities":  ["related_entities", "relationships", "relations", "links", "see_also", "cross_references"],\n',
            '    "version":           ["version", "doc_version", "revision"],\n',
            '    "tags":              ["tags", "keywords", "labels"],\n',
            '    "description":       ["description", "summary", "blurb"],\n',
            '}\n',
            '\n',
            '\n',
            'def normalize_canon_status(value) -> str:\n',
            '    """Normalize canon/canonical status to \'true\' or \'false\'."""\n',
            '    if value is None:\n',
            '        return "false"\n',
            '    if isinstance(value, bool):\n',
            '        return "true" if value else "false"\n',
            '    s = str(value).lower().strip()\n',
            '    if s in ("true", "yes", "1", "canonical", "canon", "published", "done"):\n',
            '        return "true"\n',
            '    return "false"\n',
            '\n',
            '\n',
            'def normalize_authority_layer(value) -> str:\n',
            '    """Normalize authority layer to canonical form."""\n',
            '    if value is None:\n',
            '        return "unknown"\n',
            '    s = str(value).lower().strip()\n',
            '    if s in ("primary", "official", "canonical", "1", "l1-mythological"):\n',
            '        return "primary"\n',
            '    if s in ("secondary", "semi-official", "semi-canon", "2", "l2-diagnostic"):\n',
            '        return "secondary"\n',
            '    if s in ("tertiary", "unofficial", "fan", "apocryphal", "3", "l3-technical"):\n',
            '        return "tertiary"\n',
            '    return "unknown"\n',
            '\n',
            '\n',
            'def normalize_entity_type(value) -> str:\n',
            '    """Normalize entity type to canonical form."""\n',
            '    if value is None:\n',
            '        return "unknown"\n',
            '    s = str(value).lower().strip()\n',
            '    type_map = {\n',
            '        "character": "character", "char": "character", "npc": "character", "person": "character",\n',
            '        "faction": "faction", "org": "faction", "organization": "faction", "group": "faction",\n',
            '        "location": "location", "place": "location", "region": "location", "area": "location",\n',
            '        "event": "event", "battle": "event", "war": "event",\n',
            '        "item": "item", "artifact": "item", "object": "item", "weapon": "item",\n',
            '        "concept": "concept", "magic": "concept", "system": "concept",\n',
            '        "timeline": "timeline", "chronology": "timeline",\n',
            '    }\n',
            '    return type_map.get(s, s)  # Return as-is if not in map\n',
            '\n',
            '\n',
            'def map_frontmatter(raw_frontmatter: Dict[str, Any]) -> Dict[str, Any]:\n',
            '    """Normalize YAML frontmatter to canonical metadata format.\n',
            '\n',
            '    Uses FIELD_MAP to resolve varying key names (e.g., entity_type -> type,\n',
            '    title -> name, canon_status -> canon) to canonical internal names.\n',
            '    Missing fields get sensible defaults instead of raising errors.\n',
            '\n',
            '    Args:\n',
            '        raw_frontmatter: Dict parsed from YAML frontmatter block\n',
            '\n',
            '    Returns:\n',
            '        Normalized metadata dict with canonical field names.\n',
            '    """\n',
            '    normalized: Dict[str, Any] = {}\n',
            '    mapped_raw_keys: set = set()\n',
            '\n',
            '    for canonical_key, variations in FIELD_MAP.items():\n',
            '        for variation in variations:\n',
            '            if variation in raw_frontmatter:\n',
            '                raw_value = raw_frontmatter[variation]\n',
            '                mapped_raw_keys.add(variation)\n',
            '\n',
            '                # Apply appropriate normalization\n',
            '                if canonical_key == "canon":\n',
            '                    normalized[canonical_key] = normalize_canon_status(raw_value)\n',
            '                elif canonical_key == "authority_layer":\n',
            '                    normalized[canonical_key] = normalize_authority_layer(raw_value)\n',
            '                elif canonical_key == "type":\n',
            '                    normalized[canonical_key] = normalize_entity_type(raw_value)\n',
            '                elif canonical_key == "related_entities":\n',
            '                    if isinstance(raw_value, str):\n',
            '                        normalized[canonical_key] = [e.strip() for e in raw_value.split(",") if e.strip()]\n',
            '                    elif isinstance(raw_value, list):\n',
            '                        normalized[canonical_key] = [str(e).strip() for e in raw_value if e]\n',
            '                    else:\n',
            '                        normalized[canonical_key] = []\n',
            '                else:\n',
            '                    normalized[canonical_key] = raw_value\n',
            '\n',
            '                break  # Use first matching variation\n',
            '\n',
            '    # Apply defaults for missing fields\n',
            '    normalized.setdefault("type", "unknown")\n',
            '    normalized.setdefault("name", "Untitled")\n',
            '    normalized.setdefault("canon", "true")\n',
            '    normalized.setdefault("authority_layer", "unknown")\n',
            '    normalized.setdefault("domain_layer", "core")\n',
            '    normalized.setdefault("related_entities", [])\n',
            '\n',
            '    return normalized\n',
            '\n',
            '\n',
            '# Test the mapper with a sample matching actual corpus frontmatter\n',
            'sample_frontmatter = {\n',
            '    "title": "Echo-Cant",\n',
            '    "entity_type": "Linguistic Hazard, Phenomenon",\n',
            '    "canon_status": "Draft",\n',
            '    "authority_layer": "L2-Diagnostic",\n',
            '    "source_hierarchy": "000/Codex",\n',
            '    "cross_references": ["Silent Folk", "Echo-Mothers"],\n',
            '}\n',
            '\n',
            'mapped = map_frontmatter(sample_frontmatter)\n',
            'print("\\u2713 Sample frontmatter mapping:")\n',
            'for key, value in mapped.items():\n',
            '    print(f"  {key}: {value}")\n',
        ]
        cell["outputs"] = []
        fixes_applied.append(f"Cell {i}: map_frontmatter replaced with D21-style FIELD_MAP normalization")

    # Fix 3: Summary stats after loading - handle missing keys gracefully
    if 'doc.metadata["type"]' in src and "type_counts" in src:
        src_new = src.replace(
            'doc.metadata["type"]',
            'doc.metadata.get("type", "unknown")'
        ).replace(
            'doc.metadata["canon"]',
            'doc.metadata.get("canon", "true")'
        )
        cell["source"] = [line + "\n" for line in src_new.split("\n")[:-1]]
        if src_new.split("\n")[-1]:
            cell["source"].append(src_new.split("\n")[-1])
        fixes_applied.append(f"Cell {i}: Summary stats use .get() for safe access")

if fixes_applied:
    with open(NOTEBOOK, "w") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
    print(f"Applied {len(fixes_applied)} fixes to {NOTEBOOK}:")
    for fix in fixes_applied:
        print(f"  {fix}")
else:
    print("No fixes applied - patterns not found")
    sys.exit(1)
