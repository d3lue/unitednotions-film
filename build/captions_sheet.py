"""Writes build/captions.html: a sheet with every picture of the maze and three boxes for each one.

Open the sheet in a browser, fill in what you know, and save. The file it gives you is captions.json.
Put it in this folder and run build.py, or send it to whoever builds the site.
"""
import html
import json
import os

import content

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape


def build(colour, rend, order):
    photos = {p["slug"]: p for p in content.PHOTOS}
    works = {w["slug"]: w["title"] for w in content.WORKS}
    img_dir = "../assets/img/maze/" if os.path.isdir(os.path.join(HERE, "..", "assets", "img", "maze")) else "../site/assets/img/maze/"
    rows = []
    for n, slug in enumerate(order, 1):
        p = photos[slug]
        r = rend[slug]
        w = min(r["widths"], key=lambda x: (abs(x - 480), x))
        work = works.get(p["work"], {"yakumama": "Yakumama", "lab": "The lab"}.get(p["work"], "No work set"))
        rows.append('<li data-slug="%s"><figure style="background:%s"><img src="%s%s-%d.webp" loading="lazy" alt=""></figure>'
                    '<div class="boxes"><p class="n">%d of %d. %s. <span>%s</span></p>'
                    '<label>What the picture shows<textarea data-k="shows" rows="2">%s</textarea></label>'
                    '<label>Who is in it<input data-k="who" type="text" value="%s" placeholder="Names, left to right"></label>'
                    '<label>Where and when<input data-k="where" type="text" value="%s" placeholder="Place, year"></label></div></li>'
                    % (slug, colour[slug]["swatch"], img_dir, slug, w, n, len(order), E(work), slug,
                       E(p["alt"]), E(p.get("who", "")), E(content.WHERE.get(slug, ""))))
    out = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Captions for the maze | United Notions Film</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #000; color: #ebeae6; font: 16px/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif; }
  header { position: sticky; top: 0; z-index: 2; background: #000; border-bottom: 1px solid #fff; padding: 14px 24px; display: flex; flex-wrap: wrap; gap: 12px 24px; align-items: center; }
  h1 { font-size: 22px; margin: 0; color: #fff; letter-spacing: -0.01em; }
  header p { margin: 0; flex: 1 1 320px; font-size: 14px; color: #a6a39c; }
  button { font: inherit; font-size: 14px; letter-spacing: 0.06em; background: #000; color: #fff; border: 1px solid #fff; padding: 10px 16px; cursor: pointer; }
  button:hover, button:focus-visible { background: #fff; color: #000; }
  ol { list-style: none; margin: 0; padding: 0 24px 80px; }
  li { display: grid; grid-template-columns: minmax(0, 360px) minmax(0, 1fr); gap: 24px; padding: 24px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.24); }
  figure { margin: 0; align-self: start; }
  img { display: block; width: 100%; height: auto; }
  .n { margin: 0 0 10px; font-size: 13px; letter-spacing: 0.1em; color: #fff; }
  .n span { color: #a6a39c; }
  label { display: block; font-size: 12.5px; letter-spacing: 0.1em; color: #a6a39c; margin-bottom: 12px; }
  textarea, input { display: block; width: 100%; margin-top: 4px; font: 16px/1.4 "Helvetica Neue", Helvetica, Arial, sans-serif; letter-spacing: 0; background: #000; color: #fff; border: 1px solid rgba(255, 255, 255, 0.5); padding: 9px 10px; border-radius: 0; }
  textarea:focus, input:focus { outline: 2px solid #fff; outline-offset: 1px; }
  .changed textarea.dirty, .changed input.dirty { border-color: #fff; border-width: 2px; padding: 8px 9px; }
  #state { font-size: 13px; color: #fff; min-width: 9em; }
  @media (max-width: 700px) { li { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<header>
  <h1>Captions for the maze</h1>
  <p>Write what only you know: who is in each picture, where it is and when. What you type is kept in this browser as you go. Save the file when you are done.</p>
  <span id="state" role="status"></span>
  <button type="button" id="save">Save captions.json</button>
  <button type="button" id="copy">Copy everything</button>
</header>
<ol id="list">
__ROWS__
</ol>
<script>
(function () {
  var KEY = "unf-captions";
  var saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) {}
  var state = document.getElementById("state");
  var items = Array.prototype.slice.call(document.querySelectorAll("#list li"));
  items.forEach(function (li) {
    var slug = li.getAttribute("data-slug");
    Array.prototype.forEach.call(li.querySelectorAll("[data-k]"), function (box) {
      var k = box.getAttribute("data-k");
      box.setAttribute("data-first", box.value);
      if (saved[slug] && saved[slug][k] !== undefined) { box.value = saved[slug][k]; }
      mark(box, li);
      box.addEventListener("input", function () { mark(box, li); keep(); });
    });
  });
  function mark(box, li) {
    box.classList.toggle("dirty", box.value !== box.getAttribute("data-first"));
    li.classList.toggle("changed", !!li.querySelector(".dirty"));
  }
  function collect(onlyChanged) {
    var out = {};
    items.forEach(function (li) {
      if (onlyChanged && !li.querySelector(".dirty")) { return; }
      var row = {};
      Array.prototype.forEach.call(li.querySelectorAll("[data-k]"), function (box) { row[box.getAttribute("data-k")] = box.value.trim(); });
      out[li.getAttribute("data-slug")] = row;
    });
    return out;
  }
  function keep() {
    try { localStorage.setItem(KEY, JSON.stringify(collect(true))); } catch (e) {}
    state.textContent = document.querySelectorAll("#list li.changed").length + " pictures changed";
  }
  keep();
  document.getElementById("save").addEventListener("click", function () {
    var blob = new Blob([JSON.stringify(collect(false), null, 1)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "captions.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    state.textContent = "Saved to your Downloads folder";
  });
  document.getElementById("copy").addEventListener("click", function () {
    var text = JSON.stringify(collect(true), null, 1);
    function done() { state.textContent = "Copied. Paste it in a message."; }
    if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(text).then(done, function () { state.textContent = "Could not copy. Use Save."; }); }
    else { state.textContent = "Could not copy. Use Save."; }
  });
})();
</script>
</body>
</html>
""".replace("__ROWS__", "\n".join(rows))
    with open(os.path.join(HERE, "captions.html"), "w", encoding="utf-8") as f:
        f.write(out)
