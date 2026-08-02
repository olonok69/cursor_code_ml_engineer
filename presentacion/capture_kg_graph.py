#!/usr/bin/env python3
"""
Captura el grafo de conocimiento de tickets (docs/knowledge-graph/output/graph.html,
un vis-network interactivo) como PNG para la slide de la Parte 3.

    pip install playwright   # + navegador chromium disponible
    python capture_kg_graph.py    # -> kg_graph.png

Espera a que la física de vis-network se estabilice antes de disparar.
Requiere red para el CDN de vis-network (unpkg) la primera vez.
"""
import os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "..", "docs", "knowledge-graph", "output", "graph.html")
OUT = os.path.join(HERE, "kg_graph.png")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1760, "height": 990}, device_scale_factor=2)
    page.goto("file://" + os.path.abspath(HTML))
    page.wait_for_function("typeof vis !== 'undefined'", timeout=30000)
    # dejar que la física se asiente y el fit() inicial ocurra
    page.wait_for_timeout(25000)
    page.screenshot(path=OUT)
    browser.close()
print(f"OK -> {OUT}")
