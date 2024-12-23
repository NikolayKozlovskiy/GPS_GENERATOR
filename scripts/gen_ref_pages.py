"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

root = Path(__file__).parent.parent
src = root / "gps_synth"

for path in sorted(src.rglob("*.py")):
    print(f"path: {path}")
    module_path = path.relative_to(src).with_suffix("")
    print(f"module_path: {module_path}")
    doc_path = path.relative_to(src).with_suffix(".md")
    print(f"doc_path: {doc_path}")
    full_doc_path = Path("reference", doc_path)
    print(f"full_doc_path: {full_doc_path}")

    parts = tuple(module_path.parts)
    print(f"parts: {parts}")

    if not parts or parts == ("__init__",):
        continue  # Skip if parts is empty or if it's just __init__

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    print(f"new parts: {parts}")
    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
