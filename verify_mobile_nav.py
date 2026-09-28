import asyncio
import os
import sys
from playwright.async_api import async_playwright

VIEWPORTS = [
    # Mobile Portrait & Landscape
    {"name": "360x800_portrait", "width": 360, "height": 800},
    {"name": "800x360_landscape", "width": 800, "height": 360},
    {"name": "390x844_portrait", "width": 390, "height": 844},
    {"name": "844x390_landscape", "width": 844, "height": 390},
    {"name": "393x852_portrait", "width": 393, "height": 852},
    {"name": "852x393_landscape", "width": 852, "height": 393},
    {"name": "412x915_portrait", "width": 412, "height": 915},
    {"name": "915x412_landscape", "width": 915, "height": 412},
    # Tablet & Desktop
    {"name": "768x1024_tablet", "width": 768, "height": 1024},
    {"name": "1400x900_desktop", "width": 1400, "height": 900},
]

INDEX_HTML_PATH = os.path.abspath("index.html")
ARTIFACT_DIR = "/Users/shreyshrivastava/.gemini/antigravity-ide/brain/04bfc650-1642-4677-9b98-e990c40cc7b6"
SCREENSHOT_DIR = os.path.join(ARTIFACT_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def test_viewport(page, vp, url_or_path, is_streamlit=False):
    width = vp["width"]
    height = vp["height"]
    name = vp["name"]
    await page.set_viewport_size({"width": width, "height": height})
    
    if is_streamlit:
        await page.goto("http://localhost:8501", wait_until="domcontentloaded", timeout=30000)
        # Wait for Streamlit iframe
        iframe_element = await page.wait_for_selector("iframe", timeout=20000)
        frame = await iframe_element.content_frame()
        # Give Leaflet / Tailwind 1 second to hydrate
        await page.wait_for_timeout(1500)
        target_doc = frame
    else:
        await page.goto(f"file://{INDEX_HTML_PATH}", wait_until="load")
        target_doc = page

    # Wait for the floating dock to be visible
    dock = await target_doc.wait_for_selector("#floating-dock", timeout=10000)
    
    # Check page horizontal overflow
    overflow_check = await target_doc.evaluate("""() => {
        const docElem = document.documentElement;
        const body = document.body;
        const scrollWidth = Math.max(docElem.scrollWidth, body.scrollWidth);
        const clientWidth = docElem.clientWidth;
        return {
            scrollWidth,
            clientWidth,
            hasHorizontalScroll: scrollWidth > clientWidth,
            viewportWidth: window.innerWidth
        };
    }""")
    
    # Check floating-dock bounding rect
    dock_rect = await dock.bounding_box()
    
    # Check navigation items
    items = ["nav-btn-map", "nav-btn-analytics", "nav-btn-hotspots", "nav-btn-records", "nav-btn-sos"]
    items_status = {}
    for item_id in items:
        el = await target_doc.query_selector(f"#{item_id}")
        if el:
            box = await el.bounding_box()
            items_status[item_id] = {
                "exists": True,
                "box": box,
                "within_viewport": box["x"] >= 0 and (box["x"] + box["width"]) <= (width + 1)
            }
        else:
            items_status[item_id] = {"exists": False}

    # Verify clicking functionality on navigation items
    # Click Analyze
    analyze_btn = await target_doc.query_selector("#nav-btn-analytics")
    if analyze_btn:
        await analyze_btn.click()
    await page.wait_for_timeout(300)
    
    # Check if Analyze is active
    is_analyze_active = await target_doc.evaluate("""() => {
        const btn = document.getElementById('nav-btn-analytics');
        return btn ? btn.classList.contains('active') : false;
    }""")

    # Click Map
    map_btn = await target_doc.query_selector("#nav-btn-map")
    if map_btn:
        await map_btn.click()
    await page.wait_for_timeout(300)
    
    is_map_active = await target_doc.evaluate("""() => {
        const btn = document.getElementById('nav-btn-map');
        return btn ? btn.classList.contains('active') : false;
    }""")

    # Save screenshot for key viewports
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{'streamlit_' if is_streamlit else 'standalone_'}{name}.png")
    await page.screenshot(path=screenshot_path)

    dock_within = (dock_rect["x"] >= 0) and ((dock_rect["x"] + dock_rect["width"]) <= (width + 1))
    
    passed = (
        not overflow_check["hasHorizontalScroll"] and
        dock_within and
        all(st.get("within_viewport", False) for st in items_status.values()) and
        is_map_active
    )
    
    return {
        "viewport": name,
        "width": width,
        "height": height,
        "is_streamlit": is_streamlit,
        "dock_box": dock_rect,
        "dock_within_viewport": dock_within,
        "overflow": overflow_check,
        "items": items_status,
        "interaction_passed": is_map_active,
        "passed": passed,
        "screenshot": screenshot_path
    }

async def run_all_tests():
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    if not os.path.exists(brave_path):
        # Fallback search
        candidate = os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")
        if os.path.exists(candidate):
            brave_path = candidate

    print(f"Using browser at: {brave_path} (exists={os.path.exists(brave_path)})")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=brave_path)
        context = await browser.new_context()
        page = await context.new_page()

        print("=== RUNNING DIRECT STANDALONE VERIFICATION ===")
        results = []
        for vp in VIEWPORTS:
            res = await test_viewport(page, vp, INDEX_HTML_PATH, is_streamlit=False)
            results.append(res)
            status_str = "PASS" if res["passed"] else "FAIL"
            print(f"[{status_str}] {vp['name']} (width: {vp['width']}px): Dock Width={res['dock_box']['width']:.1f}px, X={res['dock_box']['x']:.1f}px, HasScroll={res['overflow']['hasHorizontalScroll']}")

        print("\n=== RUNNING STREAMLIT APP VERIFICATION (http://localhost:8501) ===")
        streamlit_results = []
        for vp in VIEWPORTS:
            res = await test_viewport(page, vp, "http://localhost:8501", is_streamlit=True)
            streamlit_results.append(res)
            status_str = "PASS" if res["passed"] else "FAIL"
            print(f"[{status_str}] Streamlit {vp['name']} (width: {vp['width']}px): Dock Width={res['dock_box']['width']:.1f}px, X={res['dock_box']['x']:.1f}px, HasScroll={res['overflow']['hasHorizontalScroll']}")

        await browser.close()
        
        all_passed = all(r["passed"] for r in results) and all(r["passed"] for r in streamlit_results)
        print(f"\nOVERALL RESULT: {'ALL PASS' if all_passed else 'SOME FAILED'}")
        return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
