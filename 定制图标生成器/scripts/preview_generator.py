#!/usr/bin/env python3
"""
SVG Icon Preview Generator
Generates an HTML preview page for generated icons.
"""

from typing import List, Dict
from pathlib import Path


def generate_preview_html(icons_data: List[Dict], output_path: str = "icon-preview.html") -> str:
    """
    Generate an HTML preview page for the icons.
    
    Args:
        icons_data: List of dicts with keys: filename, svg_content, keyword, style, color, size
        output_path: Path to save the HTML file
    
    Returns:
        Path to the generated HTML file
    """
    
    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SVG Icons Preview</title>
  <style>
    *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
      background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
      min-height: 100vh;
      padding: 40px 20px;
    }}
    
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    
    .header {{
      text-align: center;
      margin-bottom: 40px;
    }}
    
    .header h1 {{
      font-size: 28px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 8px;
    }}
    
    .header p {{
      font-size: 14px;
      color: #64748b;
    }}
    
    .stats {{
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-top: 20px;
    }}
    
    .stat {{
      background: white;
      padding: 12px 20px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    
    .stat-value {{
      font-size: 20px;
      font-weight: 700;
      color: #2563eb;
    }}
    
    .stat-label {{
      font-size: 12px;
      color: #94a3b8;
      margin-top: 2px;
    }}
    
    .icons-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 20px;
    }}
    
    .icon-card {{
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.06);
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    
    .icon-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    }}
    
    .icon-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }}
    
    .icon-name {{
      font-size: 14px;
      font-weight: 600;
      color: #0f172a;
    }}
    
    .icon-badge {{
      font-size: 10px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 20px;
      text-transform: uppercase;
    }}
    
    .badge-linear {{
      background: #eff6ff;
      color: #2563eb;
    }}
    
    .badge-filled {{
      background: #f0fdf4;
      color: #10b981;
    }}
    
    .icon-preview {{
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 16px;
      padding: 24px;
      background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
      border-radius: 12px;
      margin-bottom: 16px;
    }}
    
    .preview-bg {{
      display: flex;
      align-items: center;
      justify-content: center;
      width: 64px;
      height: 64px;
      border-radius: 12px;
    }}
    
    .bg-white {{
      background: white;
      border: 1px solid #e2e8f0;
    }}
    
    .bg-dark {{
      background: #1e293b;
    }}
    
    .bg-blue {{
      background: linear-gradient(135deg, #3b82f6, #2563eb);
    }}
    
    .icon-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}
    
    .meta-tag {{
      font-size: 11px;
      padding: 4px 10px;
      background: #f1f5f9;
      color: #64748b;
      border-radius: 6px;
    }}
    
    .icon-code {{
      background: #0f172a;
      border-radius: 8px;
      padding: 12px;
      overflow-x: auto;
    }}
    
    .icon-code pre {{
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 10px;
      color: #7dd3fc;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-all;
    }}
    
    .download-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-top: 12px;
      padding: 8px 16px;
      background: #2563eb;
      color: white;
      font-size: 12px;
      font-weight: 500;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      text-decoration: none;
      transition: background 0.2s;
    }}
    
    .download-btn:hover {{
      background: #1d4ed8;
    }}
    
    .size-showcase {{
      display: flex;
      align-items: flex-end;
      gap: 12px;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid #e2e8f0;
    }}
    
    .size-item {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }}
    
    .size-item span {{
      font-size: 10px;
      color: #94a3b8;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎨 SVG Icons Preview</h1>
      <p>Generated icons with different styles, colors, and sizes</p>
      <div class="stats">
        <div class="stat">
          <div class="stat-value">{total_icons}</div>
          <div class="stat-label">Total Icons</div>
        </div>
        <div class="stat">
          <div class="stat-value">{unique_keywords}</div>
          <div class="stat-label">Unique Types</div>
        </div>
      </div>
    </div>
    
    <div class="icons-grid">
      {icon_cards}
    </div>
  </div>
  
  <script>
    // Download SVG functionality
    function downloadSVG(filename, content) {{
      const blob = new Blob([content], {{ type: 'image/svg+xml' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}
  </script>
</body>
</html>'''
    
    # Generate icon cards
    icon_cards = []
    keywords = set()
    
    for icon in icons_data:
        keywords.add(icon['keyword'])
        
        # Escape SVG content for display
        svg_escaped = icon['svg_content'].replace('<', '&lt;').replace('>', '&gt;')
        
        card = f'''
      <div class="icon-card">
        <div class="icon-header">
          <span class="icon-name">{icon['keyword'].title()}</span>
          <span class="icon-badge badge-{icon['style']}">{icon['style']}</span>
        </div>
        
        <div class="icon-preview">
          <div class="preview-bg bg-white">
            {icon['svg_content']}
          </div>
          <div class="preview-bg bg-dark">
            {icon['svg_content']}
          </div>
          <div class="preview-bg bg-blue">
            {icon['svg_content']}
          </div>
        </div>
        
        <div class="icon-meta">
          <span class="meta-tag">{icon['size']}×{icon['size']}</span>
          <span class="meta-tag">{icon['color_type']}</span>
          {f'<span class="meta-tag">{icon["color"]}</span>' if icon.get('color') else ''}
        </div>
        
        <div class="icon-code">
          <pre>{svg_escaped}</pre>
        </div>
        
        <button class="download-btn" onclick="downloadSVG('{icon['filename']}', `{icon['svg_content'].replace(chr(96), '\\`')}`)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Download SVG
        </button>
      </div>'''
        
        icon_cards.append(card)
    
    # Fill template
    html_content = html_template.format(
        total_icons=len(icons_data),
        unique_keywords=len(keywords),
        icon_cards=''.join(icon_cards)
    )
    
    # Write to file
    Path(output_path).write_text(html_content, encoding='utf-8')
    
    return output_path


def generate_simple_preview(icons_data: List[Dict]) -> str:
    """Generate a simple HTML preview string (for inline display)."""
    
    html_parts = ['<div style="display:flex;flex-wrap:wrap;gap:16px;padding:20px;">']
    
    for icon in icons_data:
        html_parts.append(f'''
        <div style="background:white;padding:16px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);text-align:center;min-width:100px;">
          <div style="margin-bottom:8px;">{icon['svg_content']}</div>
          <div style="font-size:12px;color:#64748b;">{icon['filename']}</div>
        </div>
        ''')
    
    html_parts.append('</div>')
    
    return ''.join(html_parts)


if __name__ == "__main__":
    # Example usage
    example_icons = [
        {
            'filename': 'settings-filled-24.svg',
            'svg_content': '<svg>...</svg>',
            'keyword': 'settings',
            'style': 'filled',
            'color_type': 'gradient',
            'color': '#ffffff → #2563eb',
            'size': 24
        }
    ]
    
    output = generate_preview_html(example_icons, "example-preview.html")
    print(f"Preview generated: {output}")
