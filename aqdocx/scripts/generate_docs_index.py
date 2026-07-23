import os
import re
import json
import glob

def clean_tsx_content(content):
    content = re.sub(r'import\s+.*?\s+from\s+[\'"].*?[\'"]\s*;?', '', content, flags=re.MULTILINE)
    content = re.sub(r'export\s+function\s+\w+\(\)\s*\{[\s\S]*?return\s*\(', '', content, count=1)
    if content.strip().endswith('}'):
        content = re.sub(r'\s*\}\s*$', '', content)
    content = re.sub(r'\{/\*[\s\S]*?\*/\}', '', content)
    content = re.sub(r'<Link\s+[^>]*to="([^"]*)"[^>]*>([\s\S]*?)</Link>', r'\2', content)
    content = re.sub(r'<(?:strong|b|code|em|span)\b[^>]*>([\s\S]*?)</(?:strong|b|code|em|span)>', r'\1', content)
    content = re.sub(r'\s+className=\{[^\}]+\}', '', content)
    content = re.sub(r'\s+className="[^"]*"', '', content)
    content = re.sub(r'\s+style=\{[^\}]+\}', '', content)
    content = re.sub(r'\s+onClick=\{[^\}]+\}', '', content)
    content = re.sub(r'\{isDark\s*\?\s*[\'"][^\'"]*[\'"]\s*:\s*[\'"][^\'"]*[\'"]\}', '', content)
    content = re.sub(r'\{[a-zA-Z0-9_]+\s*\?\s*[\'"][^\'"]*[\'"]\s*:\s*[\'"][^\'"]*[\'"]\}', '', content)
    return content

def extract_code_blocks(content):
    blocks = []
    pattern_attr_backtick = re.findall(r'<CodeBlock\b[^>]*?code=\{\`([\s\S]*?)\`\}', content)
    blocks.extend(pattern_attr_backtick)
    pattern_child_backtick = re.findall(r'<CodeBlock\b[^>]*?>\s*\{\`([\s\S]*?)\`\}\s*</CodeBlock>', content)
    blocks.extend(pattern_child_backtick)
    pattern_attr_double = re.findall(r'<CodeBlock\b[^>]*?code="([^"]*?)"', content)
    blocks.extend(pattern_attr_double)
    
    cleaned_blocks = []
    for b in blocks:
        b_clean = b.replace('\\`', '`').replace('\\$', '$').strip()
        if b_clean:
            cleaned_blocks.append(b_clean)
    return cleaned_blocks

def clean_text_fully(raw_jsx):
    text = clean_tsx_content(raw_jsx)
    text = re.sub(r'<[^>]*>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
    text = re.sub(r'\{`([\s\S]*?)`\}', r'\1', text)
    text = re.sub(r'\{[\s\S]*?\}', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_tsx_into_chunks(filepath, path_url, page_title):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    raw_content = raw_content.replace('${CONSTANTS.DOMAIN}', 'tubox.cloud').replace('${CONSTANTS.BASE_URL}', 'https://tubox.cloud')
    
    code_blocks = extract_code_blocks(raw_content)
    heading_matches = list(re.finditer(r'<(h2|h3)\b[^>]*>([\s\S]*?)</\1>', raw_content))
    
    if not heading_matches:
        cleaned_text = clean_text_fully(raw_content)
        return [{
            "title": page_title,
            "pageTitle": page_title,
            "path": path_url,
            "pagePath": path_url,
            "content": cleaned_text,
            "codeBlocks": code_blocks
        }]
    
    chunks = []
    first_match_start = heading_matches[0].start()
    intro_raw = raw_content[:first_match_start]
    intro_text = clean_text_fully(intro_raw)
    if len(intro_text.strip()) > 30:
        chunks.append({
            "title": page_title,
            "pageTitle": page_title,
            "path": path_url,
            "pagePath": path_url,
            "content": intro_text,
            "codeBlocks": extract_code_blocks(intro_raw)
        })
        
    for i, match in enumerate(heading_matches):
        h_text = clean_text_fully(match.group(2))
        anchor = h_text.lower().replace(' ', '-').replace('&', 'and')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        chunk_path = f"{path_url}#{anchor}" if anchor else path_url
        
        start_idx = match.end()
        end_idx = heading_matches[i+1].start() if i + 1 < len(heading_matches) else len(raw_content)
        
        section_raw = raw_content[start_idx:end_idx]
        section_text = clean_text_fully(section_raw)
        section_code = extract_code_blocks(section_raw)
        
        chunks.append({
            "title": f"{page_title} > {h_text}",
            "pageTitle": page_title,
            "path": chunk_path,
            "pagePath": path_url,
            "content": f"{h_text}\n\n{section_text}",
            "codeBlocks": section_code
        })
        
    return chunks

def parse_local_releases(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    version_matches = list(re.finditer(r'"([0-9]+\.[0-9]+\.[0-9]+)"\s*:\s*\{', content))
    releases_data = []
    
    for i, match in enumerate(version_matches):
        version = match.group(1)
        start_pos = match.end()
        end_pos = version_matches[i+1].start() if i + 1 < len(version_matches) else len(content)
        block_str = content[start_pos:end_pos]
        
        file_matches = re.finditer(r'"([^"]+?\.md)"\s*:\s*`((?:[^`\\]|\\.)*)`', block_str)
        version_files = {}
        for fm in file_matches:
            filename = fm.group(1)
            markdown_content = fm.group(2).replace('\\`', '`').replace('\\$', '$')
            version_files[filename] = markdown_content
            
        releases_data.append({
            "version": version,
            "files": version_files
        })
        
    return releases_data

def chunk_markdown(page_title, path_url, md_content):
    code_blocks = re.findall(r'```(?:python|bash|json|yaml|ts|js)?\s*([\s\S]*?)```', md_content)
    headings = list(re.finditer(r'^(#{1,3})\s+(.*?)$', md_content, flags=re.MULTILINE))
    
    if not headings:
        clean_text = re.sub(r'```[\s\S]*?```', '', md_content)
        clean_text = re.sub(r'#+\s+', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return [{
            "title": page_title,
            "pageTitle": page_title,
            "path": path_url,
            "pagePath": path_url,
            "content": clean_text,
            "codeBlocks": code_blocks
        }]
        
    chunks = []
    first_heading_start = headings[0].start()
    intro_raw = md_content[:first_heading_start]
    intro_text = re.sub(r'```[\s\S]*?```', '', intro_raw)
    intro_text = re.sub(r'\s+', ' ', intro_text).strip()
    if len(intro_text) > 30:
        chunks.append({
            "title": page_title,
            "pageTitle": page_title,
            "path": path_url,
            "pagePath": path_url,
            "content": intro_text,
            "codeBlocks": re.findall(r'```(?:python|bash|json|yaml|ts|js)?\s*([\s\S]*?)```', intro_raw)
        })
        
    for i, h_match in enumerate(headings):
        h_text = h_match.group(2).strip()
        anchor = h_text.lower().replace(' ', '-').replace('&', 'and')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        chunk_path = f"{path_url}#{anchor}" if anchor else path_url
        
        start_idx = h_match.end()
        end_idx = headings[i+1].start() if i + 1 < len(headings) else len(md_content)
        
        section_raw = md_content[start_idx:end_idx]
        section_text = re.sub(r'```[\s\S]*?```', '', section_raw)
        section_text = re.sub(r'\s+', ' ', section_text).strip()
        section_code = re.findall(r'```(?:python|bash|json|yaml|ts|js)?\s*([\s\S]*?)```', section_raw)
        
        if len(section_text) > 20:
            chunks.append({
                "title": f"{page_title} > {h_text}",
                "pageTitle": page_title,
                "path": chunk_path,
                "pagePath": path_url,
                "content": f"{h_text}\n\n{section_text}",
                "codeBlocks": section_code
            })
            
    return chunks

def main():
    print("Starting deep comprehensive documentation indexing...")
    aqdocx_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    aquilia_dir = os.path.dirname(aqdocx_dir)
    
    print(f"aqdocx folder: {aqdocx_dir}")
    print(f"aquilia folder: {aquilia_dir}")
    
    pages_indexed = []
    chunks_indexed = []
    
    # ---------------------------------------------------------
    # 1. Index TSX pages registered in App.tsx
    # ---------------------------------------------------------
    app_tsx_path = os.path.join(aqdocx_dir, "src/App.tsx")
    with open(app_tsx_path, "r", encoding="utf-8") as f:
        app_content = f.read()
        
    imports_map = {}
    import_matches = re.finditer(r'import\s+\{\s*([\s\S]*?)\s*\}\s+from\s+[\'"](.*?)[\'"]', app_content)
    for match in import_matches:
        names_str = match.group(1)
        imp_path = match.group(2)
        if not imp_path.startswith('.'):
            continue
        names = [n.strip() for n in names_str.split(',')]
        for name in names:
            if ' as ' in name:
                orig, alias = re.split(r'\s+as\s+', name)
                imports_map[alias.strip()] = imp_path
            else:
                imports_map[name] = imp_path
                
    docs_routes = []
    docs_block_match = re.search(r'<Route\s+path="\/docs"\s+element={<DocsLayout\s*/>}>\s*([\s\S]*?)</Route>', app_content)
    if docs_block_match:
        routes_content = docs_block_match.group(1)
        route_matches = re.finditer(r'<Route\s+(?:path="([^"]+)"\s+element={<(\w+)\s*/>}|index\s+element={<(\w+)\s*/>})', routes_content)
        for rm in route_matches:
            path_attr = rm.group(1)
            comp_path_match = rm.group(2)
            comp_index_match = rm.group(3)
            comp_name = comp_path_match if comp_path_match else comp_index_match
            url_path = f"/docs/{path_attr}" if path_attr else "/docs"
            docs_routes.append({"component": comp_name, "path": url_path})
            
    print(f"Found {len(docs_routes)} child routes under /docs in App.tsx")
    
    for route in docs_routes:
        comp_name = route["component"]
        url_path = route["path"]
        if comp_name not in imports_map:
            continue
        rel_path = imports_map[comp_name]
        abs_src_path = os.path.normpath(os.path.join(aqdocx_dir, "src", rel_path + ".tsx"))
        if not os.path.exists(abs_src_path):
            abs_src_path = os.path.normpath(os.path.join(aqdocx_dir, "src", rel_path + ".ts"))
            if not os.path.exists(abs_src_path):
                continue
                
        with open(abs_src_path, 'r', encoding='utf-8') as f:
            file_code = f.read()
        file_code = file_code.replace('${CONSTANTS.DOMAIN}', 'tubox.cloud').replace('${CONSTANTS.BASE_URL}', 'https://tubox.cloud')
            
        h1_match = re.search(r'<h1\b[^>]*>([\s\S]*?)</h1>', file_code)
        if h1_match:
            page_title = clean_text_fully(h1_match.group(1))
            page_title = page_title.replace('— Aquilia Documentation', '').strip()
            page_title = re.sub(r'^[^\w\s@#\.\-]+', '', page_title).strip()
        else:
            page_title = url_path.split('/')[-1].replace('-', ' ').title()
            
        if not page_title or len(page_title) < 2:
            page_title = url_path.split('/')[-1].replace('-', ' ').title()
            
        plain_text = clean_text_fully(file_code)
        code_blocks = extract_code_blocks(file_code)
        
        pages_indexed.append({
            "title": page_title,
            "path": url_path,
            "content": file_code,
            "plainText": plain_text,
            "codeBlocks": code_blocks
        })
        
        chunks = split_tsx_into_chunks(abs_src_path, url_path, page_title)
        chunks_indexed.extend(chunks)

    # ---------------------------------------------------------
    # 2. Index Local Releases in localReleases.ts & releases/
    # ---------------------------------------------------------
    releases_path = os.path.join(aqdocx_dir, "src/data/localReleases.ts")
    if os.path.exists(releases_path):
        print("Indexing release notes from localReleases.ts...")
        releases = parse_local_releases(releases_path)
        for rel in releases:
            version = rel["version"]
            for filename, md_content in rel["files"].items():
                base_name = filename.replace('.md', '')
                if base_name == 'README':
                    path_url = f"/releases/{version}"
                    page_title = f"Release {version}"
                else:
                    path_url = f"/releases/{version}/{base_name}"
                    page_title = f"Release {version}: " + base_name.replace('-', ' ').title()
                    
                clean_text = re.sub(r'```[\s\S]*?```', '', md_content)
                clean_text = re.sub(r'#+\s+', '', clean_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                code_blocks = re.findall(r'```(?:python|bash|json|yaml)?\s*([\s\S]*?)```', md_content)
                
                pages_indexed.append({
                    "title": page_title,
                    "path": path_url,
                    "content": md_content,
                    "plainText": clean_text,
                    "codeBlocks": code_blocks
                })
                
                chunks = chunk_markdown(page_title, path_url, md_content)
                chunks_indexed.extend(chunks)

    # ---------------------------------------------------------
    # 3. Index Standalone Pages in aqdocx/src/pages/
    # ---------------------------------------------------------
    other_pages = [
        ("Benchmark.tsx", "/benchmark", "Aquilia Performance & Benchmark"),
        ("Changelogs.tsx", "/changelogs", "Aquilia Changelogs"),
        ("Help.tsx", "/help", "Aquilia Help & Support"),
        ("Community.tsx", "/community", "Aquilia Community"),
        ("Privacy.tsx", "/privacy", "Aquilia Privacy Policy"),
        ("Terms.tsx", "/terms", "Aquilia Terms of Service")
    ]
    for filename, url_path, page_title in other_pages:
        page_file = os.path.join(aqdocx_dir, "src/pages", filename)
        if os.path.exists(page_file):
            with open(page_file, 'r', encoding='utf-8') as f:
                code = f.read()
            code = code.replace('${CONSTANTS.DOMAIN}', 'tubox.cloud').replace('${CONSTANTS.BASE_URL}', 'https://tubox.cloud')
                
            plain_text = clean_text_fully(code)
            code_blocks = extract_code_blocks(code)
            
            pages_indexed.append({
                "title": page_title,
                "path": url_path,
                "content": code,
                "plainText": plain_text,
                "codeBlocks": code_blocks
            })
            
            chunks = split_tsx_into_chunks(page_file, url_path, page_title)
            chunks_indexed.extend(chunks)

    # ---------------------------------------------------------
    # 4. Index API Entities (src/data/docEntities/)
    # ---------------------------------------------------------
    entities_dir = os.path.join(aqdocx_dir, 'src/data/docEntities')
    print("Indexing API entity definitions from docEntities...")
    for p in glob.glob(os.path.join(entities_dir, '*.ts')):
        if p.endswith('index.ts'): continue
        with open(p, 'r', encoding='utf-8') as f:
            code = f.read()
        
        id_matches = re.finditer(r'id:\s*[\'"]([^\'"]+)[\'"][\s\S]*?title:\s*[\'"]([^\'"]+)[\'"][\s\S]*?description:\s*[\'"]([^\'"]+)[\'"](?:[\s\S]*?signature:\s*[\'"]([^\'"]+)[\'"])?(?:[\s\S]*?docsHref:\s*[\'"]([^\'"]+)[\'"])?', code)
        for m in id_matches:
            e_id = m.group(1)
            title = m.group(2)
            desc = m.group(3)
            sig = m.group(4) or ""
            href = m.group(5) or "/docs"
            
            content = f"API Entity: {title} (ID: {e_id})\nDescription: {desc}\nSignature: {sig}"
            chunks_indexed.append({
                "title": f"API Entity: {title}",
                "pageTitle": f"API Entity: {title}",
                "path": f"{href}#entity-{e_id}",
                "pagePath": href,
                "content": content,
                "codeBlocks": [sig] if sig else []
            })

    # ---------------------------------------------------------
    # 5. Index Framework Root Markdown Docs & Guides (Aquilia/docs, GUIDE.md, CHANGELOG.md, etc.)
    # ---------------------------------------------------------
    print("Indexing framework repository markdown documentation & changelogs...")
    root_md_files = [
        os.path.join(aquilia_dir, 'GUIDE.md'),
        os.path.join(aquilia_dir, 'README.md'),
        os.path.join(aquilia_dir, 'CHANGELOG.md'),
        os.path.join(aquilia_dir, 'CHANGES.md'),
        os.path.join(aquilia_dir, 'SECURITY.md'),
        os.path.join(aquilia_dir, 'CONTRIBUTING.md'),
        os.path.join(aquilia_dir, 'RELEASE_NOTES.md')
    ] + glob.glob(os.path.join(aquilia_dir, 'docs/**/*.md'), recursive=True) + glob.glob(os.path.join(aquilia_dir, 'releases/**/*.md'), recursive=True)

    for p in root_md_files:
        if not os.path.exists(p) or 'node_modules' in p or '.venv' in p: continue
        rel_name = os.path.relpath(p, aquilia_dir)
        with open(p, 'r', encoding='utf-8') as f:
            md_text = f.read()
            
        page_title = f"Framework Docs: {rel_name}"
        path_url = f"/docs/framework/{rel_name.replace('/', '-').replace('.md', '')}"
        
        clean_text = re.sub(r'```[\s\S]*?```', '', md_text)
        clean_text = re.sub(r'#+\s+', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        code_blocks = re.findall(r'```(?:python|bash|json|yaml|ts|js)?\s*([\s\S]*?)```', md_text)
        
        pages_indexed.append({
            "title": page_title,
            "path": path_url,
            "content": md_text,
            "plainText": clean_text[:5000],
            "codeBlocks": code_blocks[:10]
        })
        
        chunks = chunk_markdown(page_title, path_url, md_text)
        chunks_indexed.extend(chunks)

    # ---------------------------------------------------------
    # 6. Index Agent Skills (.agents/skills/aquilia-*/SKILL.md)
    # ---------------------------------------------------------
    print("Indexing Aquilia agent skill manuals...")
    skill_files = glob.glob(os.path.join(aquilia_dir, '.agents/skills/aquilia-*/SKILL.md'))
    for p in skill_files:
        skill_name = os.path.basename(os.path.dirname(p))
        with open(p, 'r', encoding='utf-8') as f:
            stext = f.read()
            
        page_title = f"Aquilia Skill Manual: {skill_name}"
        path_url = f"/docs/skills/{skill_name}"
        
        clean_text = re.sub(r'```[\s\S]*?```', '', stext)
        clean_text = re.sub(r'#+\s+', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        code_blocks = re.findall(r'```(?:python|bash|json|yaml)?\s*([\s\S]*?)```', stext)
        
        pages_indexed.append({
            "title": page_title,
            "path": path_url,
            "content": stext,
            "plainText": clean_text[:5000],
            "codeBlocks": code_blocks[:10]
        })
        
        chunks = chunk_markdown(page_title, path_url, stext)
        chunks_indexed.extend(chunks)

    # ---------------------------------------------------------
    # 7. Index Python Source Code Docstrings (aquilia/**/*.py)
    # ---------------------------------------------------------
    print("Indexing Python API source code docstrings...")
    py_files = glob.glob(os.path.join(aquilia_dir, 'aquilia/**/*.py'), recursive=True)
    for p in py_files:
        if '__pycache__' in p or 'tests' in p: continue
        rel_p = os.path.relpath(p, os.path.join(aquilia_dir, 'aquilia'))
        mod_name = rel_p.replace('/', '.').replace('\\', '.').replace('.py', '')
        with open(p, 'r', encoding='utf-8') as f:
            code = f.read()
            
        class_matches = re.finditer(r'class\s+([A-Za-z0-9_]+)\b[^\:]*\:[\s\n]*[\'\"]{3}([\s\S]*?)[\'\"]{3}', code)
        for cm in class_matches:
            cname = cm.group(1)
            doc = cm.group(2).strip()
            if len(doc) > 20:
                chunks_indexed.append({
                    "title": f"Python API: aquilia.{mod_name}.{cname}",
                    "pageTitle": f"Python Source API: {mod_name}",
                    "path": f"/docs/api/{mod_name}#{cname.lower()}",
                    "pagePath": f"/docs/api/{mod_name}",
                    "content": f"Class aquilia.{mod_name}.{cname}\nModule: aquilia.{mod_name}\n\nDocstring:\n{doc}",
                    "codeBlocks": []
                })

    # Save to src/data/docsContent.ts
    output_path = os.path.join(aqdocx_dir, "src/data/docsContent.ts")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// Automatically generated deep documentation index. Do not edit.\n")
        f.write("export interface DocSection {\n")
        f.write("  title: string;\n")
        f.write("  path: string;\n")
        f.write("  content: string;\n")
        f.write("  plainText: string;\n")
        f.write("  codeBlocks: string[];\n")
        f.write("}\n\n")
        
        f.write("export interface DocChunk {\n")
        f.write("  title: string;\n")
        f.write("  pageTitle: string;\n")
        f.write("  path: string;\n")
        f.write("  pagePath: string;\n")
        f.write("  content: string;\n")
        f.write("  codeBlocks: string[];\n")
        f.write("}\n\n")
        
        f.write("export const docsContent: DocSection[] = ")
        f.write(json.dumps(pages_indexed, indent=2))
        f.write(";\n\n")
        
        f.write("export const docsChunks: DocChunk[] = ")
        f.write(json.dumps(chunks_indexed, indent=2))
        f.write(";\n")
        
    json_output_path = os.path.join(aqdocx_dir, "src/data/docsContent.json")
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump({
            "docsContent": pages_indexed,
            "docsChunks": chunks_indexed
        }, f, indent=2)
        
    print(f"Documentation indexing finished! Saved {len(pages_indexed)} pages and {len(chunks_indexed)} chunks to {output_path} and {json_output_path}")

if __name__ == "__main__":
    main()
