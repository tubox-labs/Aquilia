import os
import re
import json

def clean_tsx_content(content):
    # Remove imports
    content = re.sub(r'import\s+.*?\s+from\s+[\'"].*?[\'"]\s*;?', '', content, flags=re.MULTILINE)
    
    # Remove function declarations and wraps
    content = re.sub(r'export\s+function\s+\w+\(\)\s*\{[\s\S]*?return\s*\(', '', content, count=1)
    
    # Remove ending brace/return code
    if content.strip().endswith('}'):
        # Just strip trailing parts
        content = re.sub(r'\s*\}\s*$', '', content)
    
    # Remove JSX comments
    content = re.sub(r'\{/\*[\s\S]*?\*/\}', '', content)
    
    # Replace inline components with text contents
    # Link to text
    content = re.sub(r'<Link\s+[^>]*to="([^"]*)"[^>]*>([\s\S]*?)</Link>', r'\2', content)
    # strong, b, code, em
    content = re.sub(r'<(?:strong|b|code|em|span)\b[^>]*>([\s\S]*?)</(?:strong|b|code|em|span)>', r'\1', content)
    
    # Strip HTML attributes from tags we want to keep/strip
    content = re.sub(r'\s+className=\{[^\}]+\}', '', content)
    content = re.sub(r'\s+className="[^"]*"', '', content)
    content = re.sub(r'\s+style=\{[^\}]+\}', '', content)
    content = re.sub(r'\s+onClick=\{[^\}]+\}', '', content)
    
    # Strip ternary expressions inside curly braces (e.g. styling or conditional rendering helpers)
    content = re.sub(r'\{isDark\s*\?\s*[\'"][^\'"]*[\'"]\s*:\s*[\'"][^\'"]*[\'"]\}', '', content)
    content = re.sub(r'\{[a-zA-Z0-9_]+\s*\?\s*[\'"][^\'"]*[\'"]\s*:\s*[\'"][^\'"]*[\'"]\}', '', content)
    
    # Clean standard components but leave text
    return content

def extract_code_blocks(content):
    blocks = []
    # 1. Pattern: <CodeBlock language="python" filename="..." code={`...`} />
    # OR <CodeBlock code={`...`} language="..." />
    # Matches backtick strings in code={} attribute
    pattern_attr_backtick = re.findall(r'<CodeBlock\b[^>]*?code=\{\`([\s\S]*?)\`\}', content)
    blocks.extend(pattern_attr_backtick)
    
    # 2. Pattern: <CodeBlock language="python" filename="...">{`...`}</CodeBlock>
    pattern_child_backtick = re.findall(r'<CodeBlock\b[^>]*?>\s*\{\`([\s\S]*?)\`\}\s*</CodeBlock>', content)
    blocks.extend(pattern_child_backtick)
    
    # 3. Pattern: <CodeBlock code="code content" ... />
    pattern_attr_double = re.findall(r'<CodeBlock\b[^>]*?code="([^"]*?)"', content)
    blocks.extend(pattern_attr_double)
    
    # Clean backslash escapes in code blocks (e.g. \` or \$ or \n)
    cleaned_blocks = []
    for b in blocks:
        # replace escaped backticks and dollar signs
        b_clean = b.replace('\\`', '`').replace('\\$', '$').strip()
        cleaned_blocks.append(b_clean)
        
    return cleaned_blocks

def split_tsx_into_chunks(filepath, path_url, page_title):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    
    # Extract code blocks before stripping tags
    code_blocks = extract_code_blocks(raw_content)
    
    # We will search for sections. Let's find h2 and h3 sections in the TSX
    # Pattern: <h2 className=... >System Requirements</h2>
    # OR <h2>System Requirements</h2>
    # Let's extract heading positions and text
    headings = []
    
    # Regex to find headings: <h[23]\b[^>]*>([\s\S]*?)</h[23]>
    heading_matches = list(re.finditer(r'<(h2|h3)\b[^>]*>([\s\S]*?)</\1>', raw_content))
    
    # If no headings, return entire file as one chunk
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
    
    # Let's add the intro section (before the first heading) if it has text
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
        h_type = match.group(1) # h2 or h3
        h_text = clean_text_fully(match.group(2))
        
        # Determine anchor
        anchor = h_text.lower().replace(' ', '-').replace('&', 'and')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        chunk_path = f"{path_url}#{anchor}" if anchor else path_url
        
        # Extract raw text until the next heading or end of file
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

def clean_text_fully(raw_jsx):
    # Apply tsx cleaning
    text = clean_tsx_content(raw_jsx)
    
    # Strip remaining XML/HTML/JSX tags (e.g. <div className="..."> ... </div>)
    text = re.sub(r'<[^>]*>', ' ', text)
    
    # Replace HTML entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
    
    # Strip curly braces expressions
    text = re.sub(r'\{`([\s\S]*?)`\}', r'\1', text)
    text = re.sub(r'\{[\s\S]*?\}', ' ', text)
    
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_local_releases(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Match all versions and their files
    # E.g. "1.3.1": {
    #   "README.md": `...`,
    #   "backends.md": `...`,
    # }
    
    # Find version blocks
    # Version pattern: "1.3.1": {
    version_matches = list(re.finditer(r'"([0-9]+\.[0-9]+\.[0-9]+)"\s*:\s*\{', content))
    
    releases_data = []
    
    for i, match in enumerate(version_matches):
        version = match.group(1)
        start_pos = match.end()
        
        # find end of block (the matching closing brace)
        # For simplicity, we search until the next version match or end of file
        end_pos = version_matches[i+1].start() if i + 1 < len(version_matches) else len(content)
        block_str = content[start_pos:end_pos]
        
        # Now find all files in the block: "filename.md": `markdown`
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

def chunk_markdown(version, filename, md_content):
    # Map to release path
    base_name = filename.replace('.md', '')
    if base_name == 'README':
        path_url = f"/releases/{version}"
        page_title = f"Release {version}"
    else:
        path_url = f"/releases/{version}/{base_name}"
        # Capitalize filename for title
        page_title = f"Release {version}: " + base_name.replace('-', ' ').title()
        
    # Extract code blocks
    code_blocks = re.findall(r'```(?:python|bash|json|yaml)?\s*([\s\S]*?)```', md_content)
    
    # Split by H2 headings only to keep code blocks and avoid python comments matching
    headings = list(re.finditer(r'^(##)\s+(.*?)$', md_content, flags=re.MULTILINE))
    
    if not headings:
        # No headings, return entire file as one chunk
        clean_text = re.sub(r'```[\s\S]*?```', '', md_content) # strip code
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
    
    # Add intro
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
            "codeBlocks": re.findall(r'```(?:python|bash|json|yaml)?\s*([\s\S]*?)```', intro_raw)
        })
        
    for i, h_match in enumerate(headings):
        h_level = len(h_match.group(1))
        h_text = h_match.group(2).strip()
        
        # Determine anchor
        anchor = h_text.lower().replace(' ', '-').replace('&', 'and')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        chunk_path = f"{path_url}#{anchor}" if anchor else path_url
        
        # Section end
        start_idx = h_match.end()
        end_idx = headings[i+1].start() if i + 1 < len(headings) else len(md_content)
        
        section_raw = md_content[start_idx:end_idx]
        section_text = re.sub(r'```[\s\S]*?```', '', section_raw)
        section_text = re.sub(r'\s+', ' ', section_text).strip()
        section_code = re.findall(r'```(?:python|bash|json|yaml)?\s*([\s\S]*?)```', section_raw)
        
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
    print("Starting documentation indexing...")
    aqdocx_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"aqdocx folder: {aqdocx_dir}")
    
    app_tsx_path = os.path.join(aqdocx_dir, "src/App.tsx")
    with open(app_tsx_path, "r", encoding="utf-8") as f:
        app_content = f.read()
        
    # Find all imports mapping component names to paths
    # Handles: import { QuickStartPage } from './pages/docs/getting-started/QuickStart'
    # Handles: import { OverviewPage as ProvidersOverview } from './pages/docs/providers/Overview'
    imports_map = {}
    import_matches = re.finditer(r'import\s+\{\s*([\s\S]*?)\s*\}\s+from\s+[\'"](.*?)[\'"]', app_content)
    for match in import_matches:
        names_str = match.group(1)
        imp_path = match.group(2)
        
        # Normalize path
        if not imp_path.startswith('.'):
            continue
            
        # Parse names (could be multiple, or have aliases)
        names = [n.strip() for n in names_str.split(',')]
        for name in names:
            if ' as ' in name:
                orig, alias = re.split(r'\s+as\s+', name)
                imports_map[alias.strip()] = imp_path
            else:
                imports_map[name] = imp_path
                
    # Find all routes under /docs
    # <Route path="/docs" element={<InstallationPage />} />
    # <Route index element={<IntroductionPage />} />
    docs_routes = []
    # Find the child routes of /docs
    # Let's extract the Route block for path="/docs"
    docs_block_match = re.search(r'<Route\s+path="\/docs"\s+element={<DocsLayout\s*/>}>\s*([\s\S]*?)</Route>', app_content)
    if docs_block_match:
        routes_content = docs_block_match.group(1)
        # Find all routes inside
        route_matches = re.finditer(r'<Route\s+(?:path="([^"]+)"\s+element={<(\w+)\s*/>}|index\s+element={<(\w+)\s*/>})', routes_content)
        for rm in route_matches:
            path_attr = rm.group(1)
            comp_path_match = rm.group(2)
            comp_index_match = rm.group(3)
            
            comp_name = comp_path_match if comp_path_match else comp_index_match
            url_path = f"/docs/{path_attr}" if path_attr else "/docs"
            
            # Map component to url
            docs_routes.append({
                "component": comp_name,
                "path": url_path
            })
            
    print(f"Found {len(docs_routes)} child routes under /docs")
    
    # We will process each route
    pages_indexed = []
    chunks_indexed = []
    
    for route in docs_routes:
        comp_name = route["component"]
        url_path = route["path"]
        
        # Resolve source path
        if comp_name not in imports_map:
            print(f"Warning: Component {comp_name} not found in imports")
            continue
            
        rel_path = imports_map[comp_name]
        # E.g. './pages/docs/getting-started/QuickStart'
        # Convert to absolute path
        abs_src_path = os.path.normpath(os.path.join(aqdocx_dir, "src", rel_path + ".tsx"))
        if not os.path.exists(abs_src_path):
            # Try with other extensions or folders
            abs_src_path = os.path.normpath(os.path.join(aqdocx_dir, "src", rel_path + ".ts"))
            if not os.path.exists(abs_src_path):
                print(f"Warning: File {abs_src_path} does not exist")
                continue
                
        # Get page title: we can use a friendly title based on path, or parse the first h1
        # Let's extract first <h1> tag or use capitalized path
        with open(abs_src_path, 'r', encoding='utf-8') as f:
            file_code = f.read()
            
        h1_match = re.search(r'<(?:h1|span\s+className=[^>]*font-bold[^>]*>)([\s\S]*?)</(?:h1|span)>', file_code)
        if h1_match:
            page_title = clean_text_fully(h1_match.group(1))
            # Strip any gradient tags, extra headers
            page_title = page_title.replace('— Aquilia Documentation', '').strip()
        else:
            # Fallback title from url
            page_title = url_path.split('/')[-1].replace('-', ' ').title()
            
        print(f"Indexing {page_title} ({url_path}) from {os.path.basename(abs_src_path)}")
        
        # 1. Full Page Object (for docsContent)
        full_content = file_code
        plain_text = clean_text_fully(file_code)
        code_blocks = extract_code_blocks(file_code)
        
        pages_indexed.append({
            "title": page_title,
            "path": url_path,
            "content": full_content,
            "plainText": plain_text,
            "codeBlocks": code_blocks
        })
        
        # 2. Chunked sections (for docsChunks)
        chunks = split_tsx_into_chunks(abs_src_path, url_path, page_title)
        chunks_indexed.extend(chunks)
        
    # Index releases from src/data/localReleases.ts
    releases_path = os.path.join(aqdocx_dir, "src/data/localReleases.ts")
    if os.path.exists(releases_path):
        print(f"Indexing release notes from localReleases.ts...")
        releases = parse_local_releases(releases_path)
        for rel in releases:
            version = rel["version"]
            for filename, md_content in rel["files"].items():
                print(f"  Indexing release {version} - {filename}")
                base_name = filename.replace('.md', '')
                if base_name == 'README':
                    path_url = f"/releases/{version}"
                    page_title = f"Release {version}"
                else:
                    path_url = f"/releases/{version}/{base_name}"
                    page_title = f"Release {version}: " + base_name.replace('-', ' ').title()
                    
                # Full page
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
                
                # Chunked
                chunks = chunk_markdown(version, filename, md_content)
                chunks_indexed.extend(chunks)
                
    # Also index other standalone pages in aqdocx/src/pages/
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
            print(f"Indexing other page {page_title} ({url_path})")
            with open(page_file, 'r', encoding='utf-8') as f:
                code = f.read()
                
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

    # Write output to src/data/docsContent.ts
    output_path = os.path.join(aqdocx_dir, "src/data/docsContent.ts")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// Automatically generated documentation index. Do not edit.\n")
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
        
        # Serialize docsContent
        f.write("export const docsContent: DocSection[] = ")
        f.write(json.dumps(pages_indexed, indent=2))
        f.write(";\n\n")
        
        # Serialize docsChunks
        f.write("export const docsChunks: DocChunk[] = ")
        f.write(json.dumps(chunks_indexed, indent=2))
        f.write(";\n")
        
    # Also write a raw JSON file for Python testing/benchmarking
    json_output_path = os.path.join(aqdocx_dir, "src/data/docsContent.json")
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump({
            "docsContent": pages_indexed,
            "docsChunks": chunks_indexed
        }, f, indent=2)
        
    print(f"Documentation indexing finished! Saved {len(pages_indexed)} pages and {len(chunks_indexed)} chunks to {output_path} and {json_output_path}")

if __name__ == "__main__":
    main()
