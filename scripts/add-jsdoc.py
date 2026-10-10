#!/usr/bin/env python3
"""
Add comprehensive JSDoc/TSDoc to all ApexGraphSwarm source files.
Uses a state machine approach to properly identify top-level declarations.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIRS = [
    "apps/web/lib",
    "apps/web/components",
    "apps/web/app",
]

SKIP_FILES = {
    "next-env.d.ts",
    "next.config.ts",
    "playwright.config.ts",
}


def get_file_description(filepath):
    rel_path = filepath.relative_to(PROJECT_ROOT)
    parts = rel_path.parts
    if "lib" in parts:
        lib_idx = parts.index("lib")
        module_name = parts[lib_idx + 1] if lib_idx + 1 < len(parts) else "unknown"
        return "Core library module for " + module_name.replace("-", " ") + " functionality."
    elif "components" in parts:
        comp_name = filepath.stem
        return "React component for " + re.sub(r'([A-Z])', r' \1', comp_name).strip().lower() + "."
    elif "api" in parts:
        api_path = "/".join(parts[parts.index("api") + 1:-1])
        return "API route handler for " + api_path.replace("/", " ") + " endpoints."
    elif "app" in parts:
        page_name = filepath.stem
        return "Next.js page component for " + page_name.replace("-", " ") + "."
    else:
        return "Source module: " + filepath.stem + "."


def parse_params(params_str):
    if not params_str or not params_str.strip():
        return []
    params = []
    depth = 0
    current = ""
    for char in params_str:
        if char in "<([{":
            depth += 1
        elif char in ">)]}":
            depth -= 1
        elif char == "," and depth == 0:
            if current.strip():
                params.append(current.strip())
            current = ""
            continue
        current += char
    if current.strip():
        params.append(current.strip())
    result = []
    for param in params:
        if param.startswith("{") or param.startswith("["):
            name = param.split(":")[0].strip().strip("{}[]")
            type_ = param.split(":")[1].strip() if ":" in param else "unknown"
            result.append((name, type_))
            continue
        if "=" in param:
            param = param.split("=")[0].strip()
        if param.startswith("..."):
            param = param[3:]
        if ":" in param:
            parts = param.split(":", 1)
            name = parts[0].strip().rstrip("?")
            type_ = parts[1].strip()
            result.append((name, type_))
        else:
            result.append((param.strip(), "unknown"))
    return result


def generate_jsdoc(name, kind, params=None, return_type=None, extends=None, indent="", extra_description=None):
    lines = [indent + "/**"]
    if extra_description:
        lines.append(indent + " * " + extra_description)
    else:
        desc = kind.capitalize() + " " + name
        if kind == "function":
            desc = "Function " + name
        elif kind == "class":
            desc = "Class " + name
        elif kind == "interface":
            desc = "Interface " + name
        elif kind == "type":
            desc = "Type " + name
        elif kind == "const":
            desc = "Constant " + name
        lines.append(indent + " * " + desc + ".")
    lines.append(indent + " *")
    if params:
        for param_name, param_type in params:
            if param_type and param_type != "unknown":
                lines.append(indent + " * @param {" + param_type + "} " + param_name + " - Description of " + param_name + ".")
            else:
                lines.append(indent + " * @param " + param_name + " - Description of " + param_name + ".")
    if return_type and return_type.strip() and return_type.strip() != "void":
        lines.append(indent + " * @returns {" + return_type.strip() + "} Description of return value.")
    if extends:
        lines.append(indent + " * @extends " + extends)
    lines.append(indent + " *")
    lines.append(indent + " * @example")
    lines.append(indent + " * ```typescript")
    if kind == "function" and params:
        param_names = [p[0] for p in params]
        lines.append(indent + " * const result = " + name + "(" + ", ".join(["..."] * len(param_names)) + ");")
    elif kind == "class":
        lines.append(indent + " * const instance = new " + name + "();")
    elif kind == "const":
        lines.append(indent + " * import { " + name + " } from './module';")
    else:
        lines.append(indent + " * import { " + name + " } from './module';")
    lines.append(indent + " * ```")
    lines.append(indent + " */")
    return "\n".join(lines)


def has_existing_jsdoc(lines, line_idx):
    """Check if there's already a JSDoc comment ending right before this line."""
    if line_idx == 0:
        return False
    # Look backwards for a */ on its own line or at end of a line
    for i in range(line_idx - 1, max(-1, line_idx - 15), -1):
        stripped = lines[i].strip()
        if stripped == "*/":
            return True
        if stripped.endswith("*/") and not stripped.startswith("/*"):
            return True
        if stripped.startswith("/**"):
            return True
        # If we hit a non-comment line, stop
        if stripped and not stripped.startswith("//") and not stripped.startswith("*") and not stripped.startswith("/*") and not stripped.endswith("*/"):
            break
    return False


def process_file(filepath):
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return content, 0
    lines = content.split("\n")
    new_lines = []
    doc_count = 0
    i = 0
    
    # Track brace depth to know if we're at top level
    # We update this AFTER processing each line
    brace_depth = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        indent = line[:len(line) - len(line.lstrip())]
        
        # Skip empty lines and existing comments
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            new_lines.append(line)
            # Still update brace depth for comment lines
            for char in line:
                if char == '{':
                    brace_depth += 1
                elif char == '}':
                    brace_depth -= 1
            i += 1
            continue
        
        # Only process top-level declarations (brace_depth == 0)
        if brace_depth == 0:
            # Check for file-level JSDoc (first non-import, non-comment, non-empty line)
            if i == 0 or (all(not l.strip() or l.strip().startswith(("import ", "export ", "//", "/*", "*", "from ", "@")) for l in lines[:i])):
                if not stripped.startswith("import ") and not stripped.startswith("export ") and not stripped.startswith("/*") and not stripped.startswith("*/"):
                    # Check if there's already a file-level JSDoc
                    has_file_doc = False
                    for j in range(min(5, len(lines))):
                        if lines[j].strip().startswith("/**"):
                            has_file_doc = True
                            break
                    if not has_file_doc:
                        file_desc = get_file_description(filepath)
                        file_jsdoc = "/**\n * " + file_desc + "\n *\n * @module " + filepath.stem + "\n * @packageDocumentation\n */"
                        new_lines.append(file_jsdoc)
                        doc_count += 1
            
            # 1. Exported async function
            m = re.match(r'^export\s+async\s+function\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                params = parse_params(m.group(2))
                return_type = m.group(3)
                jsdoc = generate_jsdoc(name, "function", params, return_type, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 2. Exported function
            m = re.match(r'^export\s+function\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                params = parse_params(m.group(2))
                return_type = m.group(3)
                jsdoc = generate_jsdoc(name, "function", params, return_type, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 3. Exported const arrow function
            m = re.match(r'^export\s+const\s+(\w+)\s*(?::\s*([^=]+))?=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^{]+))?\s*=>', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                params = parse_params(m.group(3))
                return_type = m.group(4) or m.group(2)
                jsdoc = generate_jsdoc(name, "function", params, return_type, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 4. Exported class
            m = re.match(r'^export\s+class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+(\w+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                extends = m.group(2)
                jsdoc = generate_jsdoc(name, "class", extends=extends, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 5. Exported interface
            m = re.match(r'^export\s+interface\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                extends = m.group(2)
                jsdoc = generate_jsdoc(name, "interface", extends=extends, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 6. Exported type (single line)
            m = re.match(r'^export\s+type\s+(\w+)(?:<[^>]*>)?\s*=\s*([^;]+);', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                jsdoc = generate_jsdoc(name, "type", indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 7. Exported const
            m = re.match(r'^export\s+const\s+(\w+)\s*(?::\s*([^=]+))?\s*=', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                jsdoc = generate_jsdoc(name, "const", indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 8. Non-exported function
            m = re.match(r'^(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                params = parse_params(m.group(2))
                return_type = m.group(3)
                jsdoc = generate_jsdoc(name, "function", params, return_type, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 9. Non-exported class
            m = re.match(r'^class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+(\w+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                extends = m.group(2)
                jsdoc = generate_jsdoc(name, "class", extends=extends, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 10. Non-exported interface
            m = re.match(r'^interface\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                extends = m.group(2)
                jsdoc = generate_jsdoc(name, "interface", extends=extends, indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 11. Non-exported type (single line)
            m = re.match(r'^type\s+(\w+)(?:<[^>]*>)?\s*=\s*([^;]+);', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                jsdoc = generate_jsdoc(name, "type", indent=indent)
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 12. React default export component
            m = re.match(r'^export\s+default\s+function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                name = m.group(1)
                params = parse_params(m.group(2))
                return_type = m.group(3)
                jsdoc = generate_jsdoc(name, "function", params, return_type, indent=indent,
                    extra_description="React component " + name + ".")
                new_lines.append(jsdoc)
                doc_count += 1
            
            # 13. API route handler
            m = re.match(r'^export\s+async\s+function\s+(GET|POST|PUT|DELETE|PATCH)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*\{', line)
            if m and not has_existing_jsdoc(lines, i):
                method = m.group(1)
                params = parse_params(m.group(2))
                return_type = m.group(3)
                jsdoc = generate_jsdoc(method, "function", params, return_type, indent=indent,
                    extra_description="API route handler for " + method + " requests.")
                new_lines.append(jsdoc)
                doc_count += 1
        
        new_lines.append(line)
        
        # Update brace depth AFTER processing the line
        for char in line:
            if char == '{':
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
        
        i += 1
    
    return "\n".join(new_lines), doc_count


def main():
    total_files = 0
    total_docs = 0
    for source_dir in SOURCE_DIRS:
        dir_path = PROJECT_ROOT / source_dir
        if not dir_path.exists():
            continue
        for ext in ["*.ts", "*.tsx"]:
            for filepath in dir_path.rglob(ext):
                if filepath.name in SKIP_FILES:
                    continue
                if "node_modules" in str(filepath) or ".next" in str(filepath) or "dist" in str(filepath):
                    continue
                if ".test." in filepath.name:
                    continue
                new_content, doc_count = process_file(filepath)
                if doc_count > 0:
                    filepath.write_text(new_content, encoding="utf-8")
                    total_files += 1
                    total_docs += doc_count
                    rel_path = filepath.relative_to(PROJECT_ROOT)
                    print("  Documented " + str(rel_path) + " (" + str(doc_count) + " additions)")
    print("\nTotal: " + str(total_docs) + " JSDoc comments added across " + str(total_files) + " files")


if __name__ == "__main__":
    main()
