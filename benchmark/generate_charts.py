#!/usr/bin/env python3
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_FILE = BASE_DIR / "benchmark" / "results" / "20260405-054915" / "results.json"
ASSETS_DIR = BASE_DIR / "assets" / "benchmarks"

# Ensure output directory exists
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Load data
with open(RESULTS_FILE) as f:
    data = json.load(f)

# Framework metadata & styling
STYLE = {
    "aquilia": {
        "name": "Aquilia",
        "color1": "#0ea5e9",
        "color2": "#38bdf8",
        "text": "#38bdf8"
    },
    "fastapi": {
        "name": "FastAPI",
        "color1": "#059669",
        "color2": "#34d399",
        "text": "#34d399"
    },
    "flask": {
        "name": "Flask",
        "color1": "#475569",
        "color2": "#64748b",
        "text": "#94a3b8"
    }
}

def generate_svg_bar_chart(title, subtitle, filename, items, unit=""):
    """
    Generates a beautiful standalone vertical bar chart SVG.
    items: list of dicts: {"key": "aquilia", "value": 0.4787, "label": "0.48 s"}
    """
    width = 500
    height = 320
    padding_top = 70
    padding_bottom = 50
    padding_left = 80
    padding_right = 40

    chart_width = width - padding_left - padding_right
    chart_height = height - padding_top - padding_bottom

    max_val = max(item["value"] for item in items) * 1.15
    if max_val == 0:
        max_val = 1.0

    svg = []
    # SVG Header
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">')

    # Style definitions
    svg.append("""  <style>
    .bg { fill: #0b0f19; rx: 12px; }
    .title { font-family: system-ui, -apple-system, sans-serif; font-size: 16px; font-weight: 700; fill: #f8fafc; }
    .subtitle { font-family: system-ui, -apple-system, sans-serif; font-size: 12px; font-weight: 500; fill: #94a3b8; }
    .axis-label { font-family: system-ui, -apple-system, sans-serif; font-size: 11px; fill: #94a3b8; }
    .bar-value { font-family: system-ui, -apple-system, sans-serif; font-size: 12px; font-weight: 600; }
    .grid-line { stroke: #1e293b; stroke-width: 1; stroke-dasharray: 4 4; }
    .axis-line { stroke: #334155; stroke-width: 1.5; }
  </style>""")

    # Gradients
    svg.append("  <defs>")
    for k, v in STYLE.items():
        svg.append(f"""    <linearGradient id="grad-{k}" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="{v['color1']}" />
      <stop offset="100%" stop-color="{v['color2']}" />
    </linearGradient>""")
    svg.append("  </defs>")

    # Background
    svg.append(f'  <rect width="{width}" height="{height}" class="bg" />')

    # Title & Subtitle
    svg.append(f'  <text x="24" y="32" class="title">{title}</text>')
    svg.append(f'  <text x="24" y="50" class="subtitle">{subtitle}</text>')

    # Grid lines & Y axis ticks
    ticks = 4
    for i in range(ticks + 1):
        val = (max_val / ticks) * i
        y = padding_top + chart_height - (val / max_val * chart_height)
        val_str = f"{val:.2f}" if val < 1.0 else f"{int(val):,}"
        svg.append(f'  <line x1="{padding_left}" y1="{y}" x2="{width - padding_right}" y2="{y}" class="grid-line" />')
        svg.append(f'  <text x="{padding_left - 10}" y="{y + 4}" text-anchor="end" class="axis-label">{val_str}{unit}</text>')

    # Draw bars
    num_items = len(items)
    bar_gap = 25
    total_gaps_width = bar_gap * (num_items - 1)
    bar_width = (chart_width - total_gaps_width) / num_items

    for idx, item in enumerate(items):
        key = item["key"]
        val = item["value"]
        label_text = item["label"]
        st = STYLE.get(key, STYLE["flask"])

        x = padding_left + idx * (bar_width + bar_gap)
        bar_h = (val / max_val * chart_height) if val > 0 else 2
        y = padding_top + chart_height - bar_h

        # Draw Bar
        svg.append(f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" fill="url(#grad-{key})" rx="4" />')

        # Draw value label on top of the bar
        svg.append(f'  <text x="{x + bar_width/2}" y="{y - 8}" text-anchor="middle" fill="{st["text"]}" class="bar-value">{label_text}</text>')

        # Draw X axis label
        svg.append(f'  <text x="{x + bar_width/2}" y="{padding_top + chart_height + 20}" text-anchor="middle" class="axis-label" font-weight="600">{st["name"]}</text>')

    # Draw base axis line
    svg.append(f'  <line x1="{padding_left}" y1="{padding_top + chart_height}" x2="{width - padding_right}" y2="{padding_top + chart_height}" class="axis-line" />')

    svg.append("</svg>")

    output_path = ASSETS_DIR / filename
    with open(output_path, "w") as f_out:
        f_out.write("\n".join(svg))
    print(f"Generated {filename}")

def generate_svg_grouped_bar_chart(title, subtitle, filename, categories, datasets, unit=""):
    """
    Generates a beautiful grouped bar chart SVG.
    categories: list of names e.g. ["Simple JSON", "DI Chain", "Dense Route", "Async Sleep"]
    datasets: dict of framework_name -> list of values matching the categories
    """
    width = 720
    height = 360
    padding_top = 70
    padding_bottom = 60
    padding_left = 80
    padding_right = 160 # Extra right padding for legend

    chart_width = width - padding_left - padding_right
    chart_height = height - padding_top - padding_bottom

    # Find max value
    max_val = 0.0
    for values in datasets.values():
        max_val = max(max_val, max(values))
    max_val *= 1.15
    if max_val == 0:
        max_val = 1.0

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">')

    # Style definitions
    svg.append("""  <style>
    .bg { fill: #0b0f19; rx: 12px; }
    .title { font-family: system-ui, -apple-system, sans-serif; font-size: 18px; font-weight: 700; fill: #f8fafc; }
    .subtitle { font-family: system-ui, -apple-system, sans-serif; font-size: 12px; font-weight: 500; fill: #94a3b8; }
    .axis-label { font-family: system-ui, -apple-system, sans-serif; font-size: 11px; fill: #94a3b8; }
    .legend-text { font-family: system-ui, -apple-system, sans-serif; font-size: 12px; font-weight: 600; fill: #e2e8f0; }
    .grid-line { stroke: #1e293b; stroke-width: 1; stroke-dasharray: 4 4; }
    .axis-line { stroke: #334155; stroke-width: 1.5; }
  </style>""")

    # Gradients
    svg.append("  <defs>")
    for k, v in STYLE.items():
        svg.append(f"""    <linearGradient id="grad-{k}" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="{v['color1']}" />
      <stop offset="100%" stop-color="{v['color2']}" />
    </linearGradient>""")
    svg.append("  </defs>")

    # Background
    svg.append(f'  <rect width="{width}" height="{height}" class="bg" />')

    # Title & Subtitle
    svg.append(f'  <text x="24" y="32" class="title">{title}</text>')
    svg.append(f'  <text x="24" y="50" class="subtitle">{subtitle}</text>')

    # Grid lines & Y axis ticks
    ticks = 4
    for i in range(ticks + 1):
        val = (max_val / ticks) * i
        y = padding_top + chart_height - (val / max_val * chart_height)
        val_str = f"{val:.1f}" if val < 10.0 else f"{int(val):,}"
        svg.append(f'  <line x1="{padding_left}" y1="{y}" x2="{width - padding_right}" y2="{y}" class="grid-line" />')
        svg.append(f'  <text x="{padding_left - 10}" y="{y + 4}" text-anchor="end" class="axis-label">{val_str}{unit}</text>')

    # Draw grouped bars
    num_categories = len(categories)
    cat_gap = 35
    total_cat_gaps = cat_gap * (num_categories - 1)
    cat_width = (chart_width - total_cat_gaps) / num_categories

    frameworks = ["aquilia", "fastapi", "flask"]
    num_fw = len(frameworks)
    fw_gap = 2
    fw_width = (cat_width - fw_gap * (num_fw - 1)) / num_fw

    for c_idx, cat in enumerate(categories):
        cx = padding_left + c_idx * (cat_width + cat_gap)

        for f_idx, fw in enumerate(frameworks):
            val = datasets[fw][c_idx]
            if val is None:
                continue

            x = cx + f_idx * (fw_width + fw_gap)
            bar_h = (val / max_val * chart_height) if val > 0 else 2
            y = padding_top + chart_height - bar_h

            # Draw Bar
            svg.append(f'  <rect x="{x}" y="{y}" width="{fw_width}" height="{bar_h}" fill="url(#grad-{fw})" rx="2" />')

        # Draw category label
        svg.append(f'  <text x="{cx + cat_width/2}" y="{padding_top + chart_height + 20}" text-anchor="middle" class="axis-label" font-weight="600">{cat}</text>')

    # Draw base axis line
    svg.append(f'  <line x1="{padding_left}" y1="{padding_top + chart_height}" x2="{width - padding_right}" y2="{padding_top + chart_height}" class="axis-line" />')

    # Legend
    leg_x = width - padding_right + 25
    leg_y = padding_top + 10
    for idx, fw in enumerate(frameworks):
        st = STYLE[fw]
        y = leg_y + idx * 28
        svg.append(f'  <rect x="{leg_x}" y="{y}" width="16" height="16" fill="url(#grad-{fw})" rx="3" />')
        svg.append(f'  <text x="{leg_x + 24}" y="{y + 13}" class="legend-text">{st["name"]}</text>')

    svg.append("</svg>")

    output_path = ASSETS_DIR / filename
    with open(output_path, "w") as f_out:
        f_out.write("\n".join(svg))
    print(f"Generated {filename}")

# 1. Startup Time Chart
startup_items = [
    {"key": "aquilia", "value": data["frameworks"]["aquilia"]["startup_seconds"], "label": f"{data['frameworks']['aquilia']['startup_seconds']:.3f} s"},
    {"key": "fastapi", "value": data["frameworks"]["fastapi"]["startup_seconds"], "label": f"{data['frameworks']['fastapi']['startup_seconds']:.3f} s"},
    {"key": "flask", "value": data["frameworks"]["flask"]["startup_seconds"], "label": f"{data['frameworks']['flask']['startup_seconds']:.3f} s"}
]
generate_svg_bar_chart("Application Startup Time", "Lower is better (seconds to HTTP-ready)", "startup_time.svg", startup_items, "s")

# 2. Mean Throughput Chart
mean_throughput_items = [
    {"key": "aquilia", "value": 357.82, "label": "357.8 req/s"},
    {"key": "fastapi", "value": 281.49, "label": "281.5 req/s"},
    {"key": "flask", "value": 157.15, "label": "157.2 req/s"}
]
generate_svg_bar_chart("Mean Throughput across Scenarios", "Higher is better (average requests per second)", "mean_throughput.svg", mean_throughput_items, " r/s")

# 3. Average Peak Memory Usage
avg_peak_memory_items = [
    {"key": "aquilia", "value": 76.19, "label": "76.2 MB"},
    {"key": "fastapi", "value": 88.29, "label": "88.3 MB"},
    {"key": "flask", "value": 52.45, "label": "52.5 MB"}
]
generate_svg_bar_chart("Average Peak Memory Usage", "Lower is better (Peak RSS in Megabytes)", "memory_usage.svg", avg_peak_memory_items, " MB")

# 4. WebSocket Throughput
websocket_items = [
    {"key": "aquilia", "value": data["frameworks"]["aquilia"]["websocket"]["throughput_msgs_per_sec"], "label": f"{data['frameworks']['aquilia']['websocket']['throughput_msgs_per_sec']:.1f} m/s"},
    {"key": "fastapi", "value": data["frameworks"]["fastapi"]["websocket"]["throughput_msgs_per_sec"], "label": f"{data['frameworks']['fastapi']['websocket']['throughput_msgs_per_sec']:.1f} m/s"},
    {"key": "flask", "value": 0, "label": "Unsupported"}
]
generate_svg_bar_chart("WebSocket Msg Throughput", "Higher is better (echo roundtrips/sec)", "websocket_throughput.svg", websocket_items, " m/s")

# 5. Throughput scenario-by-scenario
scenarios_to_plot = ["json_simple", "json_large", "di_chain", "route_dense", "compute_async"]
sc_names = ["Simple JSON", "Large JSON", "DI Chain", "Dense Route", "Async Task"]
datasets_throughput = {
    "aquilia": [data["frameworks"]["aquilia"]["scenarios"][s]["throughput_rps"] for s in scenarios_to_plot],
    "fastapi": [data["frameworks"]["fastapi"]["scenarios"][s]["throughput_rps"] for s in scenarios_to_plot],
    "flask": [data["frameworks"]["flask"]["scenarios"][s]["throughput_rps"] for s in scenarios_to_plot]
}
generate_svg_grouped_bar_chart("Throughput by Workload Scenario", "Higher is better (requests per second)", "scenario_throughput.svg", sc_names, datasets_throughput, " r/s")

# 6. Latency P95 comparison
datasets_latency = {
    "aquilia": [data["frameworks"]["aquilia"]["scenarios"][s]["p95_ms"] for s in scenarios_to_plot],
    "fastapi": [data["frameworks"]["fastapi"]["scenarios"][s]["p95_ms"] for s in scenarios_to_plot],
    "flask": [data["frameworks"]["flask"]["scenarios"][s]["p95_ms"] for s in scenarios_to_plot]
}
generate_svg_grouped_bar_chart("P95 Tail Latency by Workload", "Lower is better (milliseconds)", "latency_comparison.svg", sc_names, datasets_latency, " ms")

print("All charts generated successfully.")
