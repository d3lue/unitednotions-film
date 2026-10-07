/* United Notions Film
   The page works without this file. With it:
   1. pictures fade in from their colour when they have loaded
   2. the big lines fill the width exactly, whatever font the device has
   3. the header shows the studio's name once the big name has scrolled away
   4. a line leads through the maze as the page scrolls. Every visitor can leave it and walk their own way:
      click a corridor or a room, or use the arrows. The way they walked is drawn behind them and kept for their next visit.
   5. on a film page, the trailer plays in the page
   6. in a lab note, short videos play when they come into view, and outside videos load when asked
*/
(function () {
  "use strict";
  var doc = document;
  var win = window;
  var reduce = win.matchMedia && win.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function all(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }
  function visible(el) { return el && win.getComputedStyle(el).display !== "none"; }
  var store = {
    get: function (key) { try { return JSON.parse(win.localStorage.getItem(key)); } catch (e) { return null; } },
    set: function (key, value) { try { win.localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private window */ } },
    drop: function (key) { try { win.localStorage.removeItem(key); } catch (e) { /* private window */ } }
  };

  /* 1. pictures. Every picture starts as its own colour. The ones on the first screen
        turn into pictures one after the other, in the order of the palette. */
  var opening = [];
  all(".photo img").forEach(function (img) {
    function show() { img.classList.add("is-in"); }
    function whenLoaded(then) {
      if (img.complete && img.naturalWidth) { then(); } else { img.addEventListener("load", then); img.addEventListener("error", then); }
    }
    if (!reduce && img.getBoundingClientRect().top < win.innerHeight * 1.1 && win.scrollY < 40) {
      opening.push(function (delay) { win.setTimeout(function () { whenLoaded(show); }, delay); });
    } else {
      whenLoaded(show);
    }
  });
  opening.forEach(function (start, i) { start(280 + i * 120); });

  /* 2. lines that fill the width */
  function textWidth(el) {
    var range = doc.createRange();
    range.selectNodeContents(el);
    return range.getBoundingClientRect().width;
  }
  function fit(el, box) {
    el.style.fontSize = "";
    var style = win.getComputedStyle(box);
    var room = box.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    var parts = el.children.length && win.getComputedStyle(el.children[0]).display === "block" ? all(":scope > *", el) : [el];
    var widest = Math.max.apply(null, parts.map(textWidth));
    if (!widest || !room) { return; }
    var ratio = room / widest;
    if (ratio > 0.8 && ratio < 1.25) {
      el.style.fontSize = (parseFloat(win.getComputedStyle(el).fontSize) * ratio * 0.995) + "px";
    }
  }
  function fitAll() {
    all(".room-title h1").forEach(function (el) { fit(el, el.parentNode); });
    all(".room-statement p").forEach(function (el) {
      if (win.getComputedStyle(el).whiteSpace === "nowrap") { fit(el, el.parentNode); } else { el.style.fontSize = ""; }
    });
    all("[data-fit]").forEach(function (el) { fit(el, el.parentNode); });
  }
  fitAll();
  if (doc.fonts && doc.fonts.ready) { doc.fonts.ready.then(fitAll); }

  /* 3. header */
  var header = doc.querySelector("[data-header]");
  var bigName = doc.querySelector(".room-title");
  function headerState() {
    if (!header) { return; }
    var past = bigName ? bigName.getBoundingClientRect().bottom < header.offsetHeight + 8 : win.scrollY > 40;
    header.classList.toggle("is-past", past);
  }

  /* 4. walking the maze */
  var SVG = "http://www.w3.org/2000/svg";
  var mazeEl = doc.getElementById("maze");
  var inner = mazeEl && mazeEl.querySelector(".maze-inner");
  var plan = doc.querySelector(".plan");
  var planLabel = doc.querySelector(".plan-label");
  var pad = doc.querySelector("[data-pad]");
  var tally = doc.querySelector("[data-tally]");
  var againButton = doc.querySelector("[data-again]");
  var followButton = doc.querySelector("[data-follow]");
  var journey = doc.querySelector("[data-journey]");
  var WORDS = {
    walk: (pad && pad.getAttribute("data-t-walk")) || "Scroll to follow the line",
    some: (pad && pad.getAttribute("data-t-some")) || "{n} of {m} works found",
    all: (pad && pad.getAttribute("data-t-all")) || "All {m} works found",
    way: (journey && journey.getAttribute("data-t")) || "Your way through the maze:"
  };
  var WORKS = all(".room-work[data-work]").map(function (el) {
    return { slug: el.getAttribute("data-work"), title: (el.querySelector("h2") || el).textContent.trim(), el: el };
  });
  var found = (store.get("unf-found") || []).filter(function (slug) {
    return WORKS.some(function (w) { return w.slug === slug; });
  });
  var W = null;      // the maze that is on screen now, and where the visitor is in it

  function shape(tag, cls, parent) {
    var el = doc.createElementNS(SVG, tag);
    el.setAttribute("class", cls);
    parent.appendChild(el);
    return el;
  }
  function X(i) { return W.data.n[2 * i] / 4; }
  function Y(i) { return W.data.n[2 * i + 1] / 4; }
  function span(a, b) { return Math.abs(X(a) - X(b)) + Math.abs(Y(a) - Y(b)); }

  function teardown() {
    if (!W) { return; }
    if (W.G && W.G.raf) { win.cancelAnimationFrame(W.G.raf); }
    [W.guideEl, W.trail, W.lit, W.stride, W.handles, W.ring, W.dot, W.planLit].forEach(function (el) { if (el && el.parentNode) { el.parentNode.removeChild(el); } });
    W = null;
  }

  function setup() {
    if (!inner) { return; }
    var svg = all(".lines", inner).filter(visible)[0];
    if (!svg) { teardown(); return; }
    var letter = (svg.getAttribute("class").match(/lines-(\w)/) || [])[1];
    if (W && W.letter === letter) { return; }
    teardown();
    var source = doc.getElementById("walk-" + letter);
    if (!source) { return; }
    var data = JSON.parse(source.textContent);
    var n = data.n.length / 2;
    var adj = [];
    var i;
    for (i = 0; i < n; i++) { adj.push([]); }
    for (i = 0; i < data.e.length; i += 2) { adj[data.e[i]].push(data.e[i + 1]); adj[data.e[i + 1]].push(data.e[i]); }
    var px = parseFloat(svg.getAttribute("data-px")) || 1 / 60;
    var planSvg = plan ? all("svg", plan).filter(visible)[0] : null;
    W = {
      letter: letter, svg: svg, data: data, n: n, adj: adj, px: px, at: data.start, walked: {}, edges: [], trailD: "",
      moving: false, rooms: {}, spot: {}, dirs: {}, mode: "follow", G: null,
      plan: planSvg, planTrail: planSvg && planSvg.querySelector(".trail"), me: planSvg && planSvg.querySelector(".me"), here: planSvg && planSvg.querySelector(".here")
    };
    data.rooms.forEach(function (r) {
      W.rooms[r[0]] = { id: r[0], role: r[1], node: r[2], x: r[3], y: r[4], w: r[5], h: r[6] };
      W.spot[r[2]] = r[0];
    });
    W.guideEl = shape("path", "guide", svg);
    W.trail = shape("path", "trail", svg);
    W.lit = shape("path", "lit", svg);
    W.stride = shape("path", "stride", svg);
    W.handles = shape("g", "handles", svg);
    W.ring = shape("circle", "walker-ring", svg);
    W.dot = shape("circle", "walker", svg);
    W.guideEl.setAttribute("stroke-width", 2.2 * px);
    W.guideEl.style.strokeDasharray = (0.01 * px) + " " + (9 * px);
    W.trail.setAttribute("stroke-width", 2.4 * px);
    W.lit.setAttribute("stroke-width", 2.4 * px);
    W.stride.setAttribute("stroke-width", 2.4 * px);
    if (planSvg) {
      W.planLit = doc.createElementNS(SVG, "path");
      W.planLit.setAttribute("class", "trail");
      W.planLit.setAttribute("stroke-width", "0.34");
      planSvg.insertBefore(W.planLit, W.planTrail ? W.planTrail.nextSibling : null);
    }
    W.ring.setAttribute("r", 7 * px);
    W.ring.setAttribute("stroke-width", 1.2 * px);
    W.dot.setAttribute("r", 7 * px);
    buildGuide();
    var saved = store.get("unf-walk-" + data.sig);
    var free = store.get("unf-mode-" + data.sig) === "free" || !W.G;
    if (saved && saved.at >= 0 && saved.at < n && saved.e) {
      for (i = 0; i + 1 < saved.e.length; i += 2) {
        if (saved.e[i] < n && saved.e[i + 1] < n) { tread(saved.e[i], saved.e[i + 1]); }
      }
      if (free) { W.at = saved.at; }
    }
    W.mode = free ? "free" : "follow";
    put(X(W.at), Y(W.at));
    drawTrail();
    showWays();
    showFound();
    follow(true);
  }

  /* the line that leads through the maze. It is drawn as far as the page has scrolled. */
  function workAt(x, y) {
    var slug = "";
    Object.keys(W.rooms).forEach(function (id) {
      var r = W.rooms[id];
      if (r.role === "work" && x > r.x + 0.1 && x < r.x + r.w - 0.1 && y > r.y + 0.1 && y < r.y + r.h - 0.1) { slug = id.slice(5); }
    });
    return slug;
  }
  function roomAt(x, y) {
    var node = -1;
    Object.keys(W.rooms).forEach(function (id) {
      var r = W.rooms[id];
      if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) { node = r.node; }
    });
    return node;
  }
  function buildGuide() {
    var p = W.data.guide;
    if (!p || p.length < 2) { return; }
    var cum = [0], reach = [Y(p[0])], works = [workAt(X(p[0]), Y(p[0]))], d = "M" + X(p[0]) + " " + Y(p[0]), i;
    for (i = 1; i < p.length; i++) {
      cum.push(cum[i - 1] + span(p[i - 1], p[i]));
      reach.push(Math.max(reach[i - 1], Y(p[i])));
      works.push(workAt(X(p[i]), Y(p[i])));
      d += "L" + X(p[i]) + " " + Y(p[i]);
    }
    W.G = { path: p, cum: cum, reach: reach, works: works, total: cum[cum.length - 1], head: 0, target: 0, idx: 0, seen: -1, raf: 0 };
    W.guideEl.setAttribute("d", d);
    W.lit.setAttribute("d", d);
    W.lit.style.strokeDasharray = "0 " + (W.G.total + 1);
    if (W.planLit) { W.planLit.setAttribute("d", d); W.planLit.style.strokeDasharray = "0 " + (W.G.total + 1); }
  }
  function lastAtMost(list, value) {
    var lo = 0, hi = list.length - 1;
    while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (list[mid] <= value) { lo = mid; } else { hi = mid - 1; } }
    return lo;
  }
  /* how much of the line is drawn when this row of the maze sits a little below the middle of the window */
  function lengthFor(row) {
    var G = W.G;
    if (G.reach[0] > row) { return 0; }
    var i = lastAtMost(G.reach, row), len = G.cum[i];
    if (i < G.path.length - 1) {
      var a = G.path[i], b = G.path[i + 1];
      if (X(a) === X(b) && Y(b) > Y(a)) { len += Math.min(Y(b) - Y(a), Math.max(0, row - Y(a))); }   // a corridor that goes down is drawn as the page moves
    }
    return len;
  }
  /* how many works the line already passes when the page has not been scrolled at all */
  function atRest() {
    if (!W || !W.G || !inner) { return 0; }
    var rect = inner.getBoundingClientRect();
    var len = lengthFor((win.innerHeight * 0.62 - rect.top - win.scrollY) / (rect.width / W.data.cols));
    var last = Math.min(lastAtMost(W.G.cum, len), W.G.path.length - 1), seen = {}, n = 0, k;
    for (k = 0; k <= last; k++) {
      var slug = W.G.works[k];
      if (slug && !seen[slug]) { seen[slug] = 1; n++; }
    }
    return n;
  }
  /* nothing has happened yet: the visitor has not walked, and has found only what the first screen shows */
  function untouched() {
    return !!W && !W.edges.length && (!found.length || (!!W.G && W.mode === "follow" && found.length <= atRest()));
  }
  function drawHead() {
    var G = W.G, len = G.head, last = G.path.length - 1;
    var i = Math.min(lastAtMost(G.cum, len), last);
    var a = G.path[i], b = G.path[Math.min(i + 1, last)];
    var seg = G.cum[Math.min(i + 1, last)] - G.cum[i];
    var f = seg ? (len - G.cum[i]) / seg : 0;
    var dash = len + " " + (G.total + 1);
    W.lit.style.strokeDasharray = dash;
    if (W.planLit) { W.planLit.style.strokeDasharray = dash; }
    put(X(a) + (X(b) - X(a)) * f, Y(a) + (Y(b) - Y(a)) * f);
    G.idx = i;
    var news = false;
    while (G.seen < i) {
      G.seen++;
      var slug = G.works[G.seen];
      if (slug && found.indexOf(slug) < 0) { found.push(slug); news = true; }
    }
    if (news) { store.set("unf-found", found); showFound(); }
  }
  function tick() {
    if (!W || !W.G) { return; }
    var G = W.G;
    G.raf = 0;
    if (W.mode !== "follow") { return; }
    var gap = G.target - G.head;
    if (reduce || Math.abs(gap) < 0.03) { G.head = G.target; } else { G.head += gap * 0.14 + (gap > 0 ? 0.02 : -0.02); }
    drawHead();
    if (G.head !== G.target) { G.raf = win.requestAnimationFrame(tick); } else { W.at = G.path[G.idx]; showWays(); }
  }
  function follow(atOnce) {
    if (!W || !W.G || W.mode !== "follow" || !inner) { return; }
    var rect = inner.getBoundingClientRect();
    var G = W.G;
    G.target = lengthFor((win.innerHeight * 0.62 - rect.top) / (rect.width / W.data.cols));
    if (atOnce) { G.head = G.target; drawHead(); W.at = G.path[G.idx]; showWays(); return; }
    if (G.target !== G.head && !G.raf) { hideWays(); G.raf = win.requestAnimationFrame(tick); }
  }
  /* the visitor leaves the line: what was drawn so far becomes their own way */
  function toFree() {
    if (!W || W.mode !== "follow") { return; }
    var G = W.G;
    if (G) {
      if (G.raf) { win.cancelAnimationFrame(G.raf); G.raf = 0; }
      var i = Math.min(lastAtMost(G.cum, G.head), G.path.length - 1), k;
      for (k = 1; k <= i; k++) { tread(G.path[k - 1], G.path[k]); }
      W.at = G.path[i];
      put(X(W.at), Y(W.at));
      var none = "0 " + (G.total + 1);
      W.lit.style.strokeDasharray = none;
      if (W.planLit) { W.planLit.style.strokeDasharray = none; }
    }
    W.mode = "free";
    store.set("unf-mode-" + W.data.sig, "free");
    drawTrail();
    showWays();
    save();
  }
  function toFollow() {
    if (!W || !W.G || W.moving) { return; }
    W.mode = "follow";
    store.drop("unf-mode-" + W.data.sig);
    W.G.head = 0;
    drawTrail();
    follow();
  }

  function put(x, y) {
    W.dot.setAttribute("cx", x); W.dot.setAttribute("cy", y);
    W.ring.setAttribute("cx", x); W.ring.setAttribute("cy", y);
    if (W.me) { W.me.setAttribute("cx", x); W.me.setAttribute("cy", y); }
  }
  function tread(a, b) {
    var key = a < b ? a + "-" + b : b + "-" + a;
    if (W.walked[key]) { return; }
    W.walked[key] = 1;
    W.edges.push(a, b);
    W.trailD += "M" + X(a) + " " + Y(a) + "L" + X(b) + " " + Y(b);
  }
  function drawTrail() {
    W.trail.setAttribute("d", W.trailD);
    if (W.planTrail) { W.planTrail.setAttribute("d", W.trailD); }
    if (againButton) { againButton.hidden = untouched(); }
    if (followButton) { followButton.hidden = !(W.G && W.mode === "free"); }
  }
  function save() { store.set("unf-walk-" + W.data.sig, { at: W.at, e: W.edges }); }

  /* which ways are open from where the visitor stands */
  var UNIT = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };
  function wayOf(a, b) {
    var dx = X(b) - X(a), dy = Y(b) - Y(a);
    return Math.abs(dx) >= Math.abs(dy) ? (dx > 0 ? "right" : "left") : (dy > 0 ? "down" : "up");
  }
  function showWays() {
    while (W.handles.firstChild) { W.handles.removeChild(W.handles.firstChild); }
    W.dirs = {};
    W.adj[W.at].forEach(function (nb) { W.dirs[wayOf(W.at, nb)] = nb; });
    var x = X(W.at), y = Y(W.at), far = 30 * W.px, size = 10 * W.px;
    Object.keys(W.dirs).forEach(function (way) {
      var u = UNIT[way], cx = x + u[0] * far, cy = y + u[1] * far;
      var tip = [cx + u[0] * size, cy + u[1] * size];
      var a = [cx - u[0] * size * 0.5 - u[1] * size, cy - u[1] * size * 0.5 + u[0] * size];
      var b = [cx - u[0] * size * 0.5 + u[1] * size, cy - u[1] * size * 0.5 - u[0] * size];
      var handle = shape("path", "handle", W.handles);
      handle.setAttribute("d", "M" + tip.join(" ") + "L" + a.join(" ") + "L" + b.join(" ") + "Z");
      handle.setAttribute("stroke-width", 1.5 * W.px);
      handle.setAttribute("data-way", way);
    });
    if (pad) {
      all("[data-dir]", pad).forEach(function (button) { button.disabled = W.dirs[button.getAttribute("data-dir")] === undefined; });
    }
  }
  function hideWays() { while (W.handles.firstChild) { W.handles.removeChild(W.handles.firstChild); } }

  /* the shortest way between two places. In a maze there is usually only one. */
  function route(from, to) {
    var n = W.n, dist = new Float64Array(n), prev = new Int32Array(n), i;
    for (i = 0; i < n; i++) { dist[i] = Infinity; prev[i] = -1; }
    dist[from] = 0;
    var heap = [[0, from]];
    while (heap.length) {
      var top = heap[0], end = heap.pop();
      if (heap.length) {
        heap[0] = end;
        var k = 0;
        for (;;) {
          var l = 2 * k + 1, r = l + 1, m = k;
          if (l < heap.length && heap[l][0] < heap[m][0]) { m = l; }
          if (r < heap.length && heap[r][0] < heap[m][0]) { m = r; }
          if (m === k) { break; }
          var swap = heap[k]; heap[k] = heap[m]; heap[m] = swap; k = m;
        }
      }
      var u = top[1];
      if (top[0] > dist[u]) { continue; }
      if (u === to) { break; }
      var nbs = W.adj[u];
      for (i = 0; i < nbs.length; i++) {
        var d = top[0] + span(u, nbs[i]);
        if (d < dist[nbs[i]]) {
          dist[nbs[i]] = d; prev[nbs[i]] = u;
          var c = heap.push([d, nbs[i]]) - 1;
          while (c > 0) {
            var parent = (c - 1) >> 1;
            if (heap[parent][0] <= heap[c][0]) { break; }
            var up = heap[parent]; heap[parent] = heap[c]; heap[c] = up; c = parent;
          }
        }
      }
    }
    if (dist[to] === Infinity) { return null; }
    var path = [to];
    while (path[0] !== from) { path.unshift(prev[path[0]]); }
    return path;
  }
  function nearest(gx, gy, reach) {
    var best = -1, bestD = reach * reach;
    for (var i = 0; i < W.n; i++) {
      var dx = X(i) - gx, dy = Y(i) - gy, d = dx * dx + dy * dy;
      if (d < bestD) { bestD = d; best = i; }
    }
    return best;
  }

  function pageY(node) {
    var rect = inner.getBoundingClientRect();
    return win.scrollY + rect.top + Y(node) * rect.width / W.data.cols;
  }
  /* go to a place on the page at once. The stylesheet asks for smooth scrolling, and "auto" would obey it. */
  function jump(y) {
    var root = doc.documentElement, before = root.style.scrollBehavior;
    root.style.scrollBehavior = "auto";
    void win.getComputedStyle(root).scrollBehavior;      // the browser must read the new rule before the page moves
    win.scrollTo(0, Math.max(0, y));
    root.style.scrollBehavior = before;
  }
  function keepInView(node) {
    var y = pageY(node), view = win.innerHeight;
    if (y < win.scrollY + view * 0.22 || y > win.scrollY + view * 0.7) {
      win.scrollTo({ top: Math.max(0, y - view * 0.45), behavior: reduce ? "auto" : "smooth" });
    }
  }

  function go(path, keep) {
    if (!path || path.length < 2 || W.moving) { return; }
    W.moving = true;
    hideWays();
    var cum = [0], i;
    for (i = 1; i < path.length; i++) { cum.push(cum[i - 1] + span(path[i - 1], path[i])); }
    var total = cum[cum.length - 1];
    var last = path[path.length - 1];
    var time = reduce ? 0 : Math.min(2400, Math.max(240, total * 85));
    var d = "M" + X(path[0]) + " " + Y(path[0]);
    for (i = 1; i < path.length; i++) { d += "L" + X(path[i]) + " " + Y(path[i]); }
    W.stride.setAttribute("d", d);
    W.stride.style.strokeDasharray = "0 " + (total + 1);
    if (keep) { keepInView(last); }
    var t0 = null, seg = 0, maze = W;
    function finish() {
      if (W !== maze) { return; }
      for (i = 1; i < path.length; i++) { tread(path[i - 1], path[i]); }
      W.stride.setAttribute("d", "");
      W.at = last;
      W.moving = false;
      put(X(last), Y(last));
      drawTrail();
      showWays();
      arrive();
      save();
    }
    function frame(t) {
      if (W !== maze) { return; }
      if (t0 === null) { t0 = t; }
      var k = time ? Math.min(1, (t - t0) / time) : 1;
      var eased = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      var at = eased * total;
      while (seg < path.length - 2 && cum[seg + 1] < at) { seg++; }
      var a = path[seg], b = path[seg + 1], f = (at - cum[seg]) / ((cum[seg + 1] - cum[seg]) || 1);
      put(X(a) + (X(b) - X(a)) * f, Y(a) + (Y(b) - Y(a)) * f);
      W.stride.style.strokeDasharray = at + " " + (total + 1);
      if (k < 1) { win.requestAnimationFrame(frame); } else { finish(); }
    }
    win.requestAnimationFrame(frame);
  }

  /* one press of an arrow: walk that way until there is a choice to make, a room, or a dead end */
  function step(way) {
    if (!W || W.moving) { return; }
    toFree();
    var next = W.dirs[way];
    if (next === undefined) { return; }
    var path = [W.at, next], prev = W.at, cur = next;
    while (W.adj[cur].length === 2 && W.spot[cur] === undefined && path.length < 5000) {
      var onward = W.adj[cur][0] === prev ? W.adj[cur][1] : W.adj[cur][0];
      path.push(onward);
      prev = cur;
      cur = onward;
    }
    go(path, true);
  }
  function walkTo(node, keep) {
    if (!W || W.moving || node < 0) { return; }
    toFree();
    if (node === W.at) { return; }
    go(route(W.at, node), keep);
  }

  /* the works a visitor has found, in the order they found them */
  function arrive() {
    var x = X(W.at), y = Y(W.at);
    Object.keys(W.rooms).forEach(function (id) {
      var r = W.rooms[id];
      if (r.role !== "work") { return; }
      if (x > r.x + 0.1 && x < r.x + r.w - 0.1 && y > r.y + 0.1 && y < r.y + r.h - 0.1) {
        var slug = id.slice(5);
        if (found.indexOf(slug) < 0) { found.push(slug); store.set("unf-found", found); showFound(); }
      }
    });
  }
  function showFound() {
    WORKS.forEach(function (w) { w.el.classList.toggle("is-found", found.indexOf(w.slug) >= 0); });
    if (plan) {
      all("a[data-room]", plan).forEach(function (a) {
        a.classList.toggle("is-found", found.indexOf(a.getAttribute("data-room").slice(5)) >= 0);
      });
    }
    if (tally) {
      tally.textContent = (untouched() ? WORDS.walk : found.length >= WORKS.length ? WORDS.all : WORDS.some)
        .replace("{n}", found.length).replace("{m}", WORKS.length);
    }
    if (journey) {
      journey.hidden = !found.length;
      journey.textContent = "";
      if (found.length) {
        journey.appendChild(doc.createTextNode(WORDS.way + " "));
        found.forEach(function (slug, i) {
          var w = WORKS.filter(function (item) { return item.slug === slug; })[0];
          var a = doc.createElement("a");
          a.href = "#" + slug;
          a.textContent = (i + 1) + ". " + w.title;
          journey.appendChild(a);
        });
      }
    }
    if (againButton && W) { againButton.hidden = untouched(); }
  }
  /* start again: back to the top of the maze, nothing found, and the line leads again */
  function again() {
    if (!W || W.moving) { return; }
    store.drop("unf-walk-" + W.data.sig);
    store.drop("unf-mode-" + W.data.sig);
    store.drop("unf-found");
    found = [];
    W.walked = {}; W.edges = []; W.trailD = ""; W.at = W.data.start;
    if (W.G) { W.mode = "follow"; W.G.head = 0; W.G.seen = W.G.path.length; }
    put(X(W.at), Y(W.at));
    drawTrail();
    showWays();
    showFound();
    jump(pageY(W.at) - win.innerHeight * 0.62);
    if (W.G) { W.G.seen = -1; follow(true); }
    showFound();
    drawTrail();
  }
  function holdArrows() { if (pad) { var me = pad.querySelector("[data-find]"); if (me) { me.focus({ preventScroll: true }); } } }

  if (inner) {
    inner.addEventListener("click", function (event) {
      if (!W || W.moving) { return; }
      var t = event.target;
      if (!t.closest) { return; }
      var handle = t.closest(".handle");
      if (handle) { step(handle.getAttribute("data-way")); holdArrows(); return; }
      if (t.closest("a") || t.closest("button") || t.closest(".photo")) { return; }
      var rect = inner.getBoundingClientRect();
      var gx = (event.clientX - rect.left) / rect.width * W.data.cols;
      var gy = (event.clientY - rect.top) / rect.height * W.data.rows;
      var target = roomAt(gx, gy);
      if (target < 0) {
        var room = t.closest("[data-room]");
        target = room && W.rooms[room.getAttribute("data-room")] ? W.rooms[room.getAttribute("data-room")].node : nearest(gx, gy, 1.6);
      }
      if (target < 0) { return; }
      walkTo(target, false);
      holdArrows();
    });
  }
  if (pad) {
    pad.addEventListener("click", function (event) {
      var button = event.target.closest && event.target.closest("button");
      if (!button || !W) { return; }
      if (button.hasAttribute("data-dir")) { step(button.getAttribute("data-dir")); holdArrows(); }
      else if (button.hasAttribute("data-find")) { win.scrollTo({ top: Math.max(0, pageY(W.at) - win.innerHeight * 0.45), behavior: reduce ? "auto" : "smooth" }); }
      else if (button.hasAttribute("data-again")) { again(); }
      else if (button.hasAttribute("data-follow")) { toFollow(); }
    });
    pad.addEventListener("keydown", function (event) {
      var way = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right" }[event.key];
      if (way) { event.preventDefault(); step(way); }
    });
  }
  if (plan) {
    plan.addEventListener("click", function (event) {
      if (!W || !W.plan) { return; }
      var dot = event.target.closest && event.target.closest("a[data-room]");
      if (dot) {
        var room = W.rooms[dot.getAttribute("data-room")];
        if (room) {
          event.preventDefault();
          if (W.moving) { keepInView(room.node); } else if (room.node === W.at) { toFree(); keepInView(room.node); } else { walkTo(room.node, true); }
        }
        return;
      }
      var box = W.plan.getBoundingClientRect();
      var row = (event.clientY - box.top) / box.height * W.data.rows;
      var rect = inner.getBoundingClientRect();
      win.scrollTo({ top: win.scrollY + rect.top + row * rect.width / W.data.cols - win.innerHeight * 0.4, behavior: reduce ? "auto" : "smooth" });
    });
    all("a[data-name]", plan).forEach(function (a) {
      function on() {
        var dot = a.getBoundingClientRect();
        var box = plan.getBoundingClientRect();
        planLabel.textContent = a.getAttribute("data-name");
        planLabel.style.top = (dot.top + dot.height / 2 - box.top) + "px";
        planLabel.classList.add("is-on");
      }
      function off() { planLabel.classList.remove("is-on"); }
      a.addEventListener("mouseenter", on);
      a.addEventListener("focus", on);
      a.addEventListener("mouseleave", off);
      a.addEventListener("blur", off);
    });
  }

  function onScroll() {
    headerState();
    if (!inner) { return; }
    var rect = inner.getBoundingClientRect();
    var view = win.innerHeight;
    var inMaze = rect.top < view * 0.9 && rect.bottom > view * 0.6;
    if (plan) { plan.classList.toggle("is-on", inMaze); }
    if (pad) { pad.classList.toggle("is-on", inMaze && !!W); }
    if (W && W.here) {
      var unit = rect.width / W.data.cols;
      var top = Math.max(0, -rect.top / unit);
      var bottom = Math.min(W.data.rows, (view - rect.top) / unit);
      W.here.setAttribute("y", top);
      W.here.setAttribute("height", Math.max(0, bottom - top));
    }
    follow();
  }

  var resizeTimer = null;
  win.addEventListener("resize", function () {
    win.clearTimeout(resizeTimer);
    resizeTimer = win.setTimeout(function () { fitAll(); setup(); onScroll(); }, 120);
  });
  win.addEventListener("scroll", onScroll, { passive: true });
  setup();
  onScroll();

  /* the menu closes when a link in it is chosen, and with the Escape key */
  all("[data-menu]").forEach(function (menu) {
    menu.addEventListener("click", function (event) { if (event.target.closest && event.target.closest("nav a")) { menu.removeAttribute("open"); } });
    doc.addEventListener("keydown", function (event) { if (event.key === "Escape" && menu.hasAttribute("open")) { menu.removeAttribute("open"); menu.querySelector("summary").focus(); } });
  });
  /* the second skip link puts the keyboard on the arrows of the maze */
  all("[data-skip-walk]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      if (!W || !pad) { return; }
      event.preventDefault();
      jump(pageY(W.at) - win.innerHeight * 0.45);
      holdArrows();
    });
  });

  /* 5. a trailer, an outside video or a slide deck plays in the page when the visitor asks for it.
        Nothing is loaded from the other site before that. Opened as a file, the link goes to the other site instead. */
  all("[data-youtube], [data-vimeo], [data-frame]").forEach(function (link) {
    if (!/^https?:$/.test(win.location.protocol)) { return; }
    link.addEventListener("click", function (event) {
      event.preventDefault();
      var youtube = link.getAttribute("data-youtube"), vimeo = link.getAttribute("data-vimeo");
      var player = doc.createElement("iframe");
      player.src = youtube ? "https://www.youtube-nocookie.com/embed/" + youtube + "?autoplay=1&rel=0" :
        vimeo ? "https://player.vimeo.com/video/" + vimeo + "?autoplay=1&dnt=1" : link.getAttribute("data-frame");
      player.title = link.getAttribute("data-title") || "";
      player.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      player.setAttribute("allowfullscreen", "");
      link.parentNode.replaceChild(player, link);
    });
  });

  /* 6. in a lab note, a short silent clip plays while it is on screen. A click stops it or starts it again. */
  var clips = all("video[data-clip]");
  if (clips.length && "IntersectionObserver" in win && !reduce) {
    var watch = new win.IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var clip = entry.target;
        if (entry.isIntersecting && !clip.hasAttribute("data-stopped")) {
          var playing = clip.play();
          if (playing && playing.catch) { playing.catch(function () { clip.setAttribute("controls", ""); }); }
        } else { clip.pause(); }
      });
    }, { threshold: 0.35 });
    clips.forEach(function (clip) {
      clip.removeAttribute("controls");
      clip.setAttribute("tabindex", "0");
      function toggle() {
        if (clip.paused) { clip.removeAttribute("data-stopped"); clip.play(); } else { clip.setAttribute("data-stopped", ""); clip.pause(); }
      }
      clip.addEventListener("click", toggle);
      clip.addEventListener("keydown", function (event) { if (event.key === " " || event.key === "Enter") { event.preventDefault(); toggle(); } });
      watch.observe(clip);
    });
  }

  /* 7. a frame that holds a small page of this site is as tall as that page */
  all(".embed iframe").forEach(function (frame) {
    function size() {
      try {
        var inside = frame.contentDocument;
        if (inside && inside.body && inside.body.offsetHeight) { frame.style.height = Math.ceil(inside.body.offsetHeight + 4) + "px"; }
      } catch (e) { /* opened as a file: the height of the style sheet stays */ }
    }
    frame.addEventListener("load", function () {
      size();
      try { if ("ResizeObserver" in win) { new win.ResizeObserver(size).observe(frame.contentDocument.body); } } catch (e) { /* as above */ }
    });
    win.addEventListener("resize", size);
    size();
  });
})();
