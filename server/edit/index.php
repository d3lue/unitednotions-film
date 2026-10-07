<?php
// United Notions Film: the editing page, at https://unitednotions.film/edit/ behind a password.
// A page of the site is a folder in the workshop (build/pages-in/<name>/): index.html, es.html for the Spanish, and its pictures.
// Here a page is written or pasted, its pictures dropped beside it, previewed, saved, and published. The server rebuilds the site.
// This page runs nothing: Publish leaves a marker, and a cron job on the server (once a minute) runs server-publish.sh.
// Nothing here is public: the folder's .htaccess asks for the password kept in the workshop's .htpasswd.

declare(strict_types=1);
$HOME  = dirname($_SERVER['DOCUMENT_ROOT'] ?? '');                    // /home/unfweb: a user that owns only this site, nothing else
$W     = "$HOME/unf-workshop";
$IN    = "$W/build/pages-in";
$LOG   = "$W/publish.log";
$LOCK  = "$W/publish.lock";
$ASK   = "$W/publish.requested";
$LIVE  = 'https://unitednotions.film';
$SECTIONS = ['research' => 'Research', 'news' => 'News'];
$MIME = ['jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'png' => 'image/png', 'gif' => 'image/gif', 'webp' => 'image/webp', 'avif' => 'image/avif',
         'svg' => 'image/svg+xml', 'mp4' => 'video/mp4', 'webm' => 'video/webm', 'mov' => 'video/quicktime', 'm4v' => 'video/mp4',
         'mp3' => 'audio/mpeg', 'm4a' => 'audio/mp4', 'wav' => 'audio/wav', 'ogg' => 'audio/ogg', 'pdf' => 'application/pdf',
         'css' => 'text/css', 'js' => 'text/javascript', 'json' => 'application/json', 'txt' => 'text/plain', 'woff' => 'font/woff',
         'woff2' => 'font/woff2', 'glb' => 'model/gltf-binary', 'gltf' => 'model/gltf+json'];

// ---------------------------------------------------------------------------------------------------------- helpers
function h(?string $s): string { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
function slugify(string $s): string {
    $s = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $s) ?: $s;
    $s = strtolower(trim(preg_replace('/[^a-zA-Z0-9]+/', '-', $s), '-'));
    return preg_replace('/-{2,}/', '-', $s);
}
function safe_name(string $f): string {
    $f = basename(str_replace('\\', '/', $f));
    $f = preg_replace('/[^A-Za-z0-9._-]+/', '-', $f);
    return ltrim($f, '.');
}
function allowed(string $f): bool { global $MIME; return isset($MIME[strtolower(pathinfo($f, PATHINFO_EXTENSION))]); }
function rmtree(string $d): void {
    foreach (array_diff(scandir($d), ['.', '..']) as $f) { $p = "$d/$f"; is_dir($p) && !is_link($p) ? rmtree($p) : unlink($p); }
    rmdir($d);
}
function meta(string $html, string $name): string {
    if (preg_match('~<meta\s+name=["\']' . $name . '["\']\s+content=["\']([^"\']*)["\']~i', $html, $m)
        || preg_match('~<meta\s+content=["\']([^"\']*)["\']\s+name=["\']' . $name . '["\']~i', $html, $m)) return html_entity_decode(trim($m[1]), ENT_QUOTES, 'UTF-8');
    return '';
}
function tag_text(string $tag, string $html): string {
    return preg_match("~<$tag\b[^>]*>(.*?)</$tag>~is", $html, $m) ? trim(html_entity_decode(preg_replace('/\s+/', ' ', strip_tags($m[1])), ENT_QUOTES, 'UTF-8')) : '';
}
function read_page(string $file): array {
    return parse_page(is_file($file) ? (string)file_get_contents($file) : '');
}
function parse_page(string $html): array {
    // the fields of a page as the editor shows them, from any HTML: ours, or one written elsewhere and pasted in
    $f = ['title' => '', 'description' => '', 'date' => '', 'place' => '', 'content' => '', 'section' => ''];
    if ($html === '') return $f;
    $f['section'] = strtolower(meta($html, 'section'));
    $body = preg_match('~<body[^>]*>(.*?)</body>~is', $html, $m) ? $m[1] : preg_replace('~(?is)<head>.*?</head>|<!doctype[^>]*>|</?html[^>]*>~', '', $html);
    $head = preg_match('~<head[^>]*>(.*?)</head>~is', $html, $m) ? $m[1] : '';
    preg_match_all('~<style\b[^>]*>.*?</style>~is', $head, $styles);
    $f['title'] = tag_text('h1', $body) ?: tag_text('title', $html);
    $f['description'] = meta($html, 'description') ?: tag_text('p', $body);
    $f['date'] = meta($html, 'date') ?: (preg_match('~<time[^>]+datetime=["\'](\d{4}-\d{2}-\d{2})~i', $html, $m) ? $m[1] : '');
    $f['place'] = meta($html, 'place');
    $body = preg_replace('~<h1\b[^>]*>.*?</h1>\s*~is', '', $body, 1);
    $f['content'] = trim(implode("\n", $styles[0]) . "\n" . trim($body));
    return $f;
}
function write_page(string $file, array $f, string $lang, string $section): void {
    $out = "<!doctype html>\n<html lang=\"$lang\">\n<head>\n<meta charset=\"utf-8\">\n<title>" . h($f['title']) . "</title>\n"
         . ($f['description'] !== '' ? '<meta name="description" content="' . h($f['description']) . "\">\n" : '')
         . ($f['date'] !== '' ? '<meta name="date" content="' . h($f['date']) . "\">\n" : '')
         . ($f['place'] !== '' ? '<meta name="place" content="' . h($f['place']) . "\">\n" : '')
         . '<meta name="section" content="' . h($section) . "\">\n</head>\n<body>\n<h1>" . h($f['title']) . "</h1>\n"
         . str_replace("\r\n", "\n", $f['content']) . "\n</body>\n</html>\n";
    file_put_contents($file, $out);
}
function page_section(string $dir): string {
    global $SECTIONS;
    $said = is_file("$dir/section.txt") ? trim((string)file_get_contents("$dir/section.txt")) : '';
    if ($said === '' && is_file("$dir/index.html")) $said = meta((string)file_get_contents("$dir/index.html"), 'section');
    return isset($SECTIONS[strtolower($said)]) ? strtolower($said) : 'research';
}
function page_files(string $dir): array {
    // the files of a page other than its HTML: name => size, pictures first, in the order the first one is the card's
    $files = [];
    if (!is_dir($dir)) return $files;
    $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS));
    foreach ($it as $f) {
        $rel = substr((string)$f, strlen($dir) + 1);
        if (in_array(strtolower($rel), ['index.html', 'es.html', 'section.txt'], true) || $rel[0] === '.') continue;
        $files[$rel] = $f->getSize();
    }
    ksort($files, SORT_NATURAL | SORT_FLAG_CASE);
    return $files;
}
function first_picture(string $html): string {
    return preg_match('~<img[^>]+src=["\'](?!https?:|//|/|data:)([^"\'?#]+)~i', $html, $m) ? $m[1] : '';
}
function start_publish(): void { global $ASK; touch($ASK); }

// ---------------------------------------------------------------------------------------------------------- a file of a page, for the preview
if (isset($_GET['file'])) {
    [$slug, $rel] = array_pad(explode('/', (string)$_GET['file'], 2), 2, '');
    $slug = slugify($slug);
    $rel = implode('/', array_map('safe_name', array_filter(explode('/', $rel), fn($p) => $p !== '' && $p !== '..')));
    $path = "$IN/$slug/$rel";
    if ($slug === '' || $rel === '' || !is_file($path) || !allowed($rel)) { http_response_code(404); exit('No such file.'); }
    header('Content-Type: ' . $MIME[strtolower(pathinfo($rel, PATHINFO_EXTENSION))]);
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    readfile($path);
    exit;
}

// ---------------------------------------------------------------------------------------------------------- what was asked
$notes = [];
$running = (file_exists($LOCK) && (time() - (int)@filemtime($LOCK) < 900)) || (file_exists($ASK) && (time() - (int)@filemtime($ASK) < 300));
$open = null;        // the page the editor shows

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $site = $_SERVER['HTTP_SEC_FETCH_SITE'] ?? 'same-origin';
    if (!in_array($site, ['same-origin', 'none'], true)) { http_response_code(403); exit('Not from this site.'); }
    $do = $_POST['do'] ?? '';
    $slug = slugify($_POST['name'] ?? '');

    if ($do === 'save') {
        $f = ['title' => trim((string)($_POST['title'] ?? '')), 'description' => trim((string)($_POST['description'] ?? '')),
              'date' => trim((string)($_POST['date'] ?? '')), 'place' => trim((string)($_POST['place'] ?? '')), 'content' => trim((string)($_POST['content'] ?? ''))];
        $es = ['title' => trim((string)($_POST['title_es'] ?? '')), 'description' => trim((string)($_POST['description_es'] ?? '')),
               'date' => $f['date'], 'place' => $f['place'], 'content' => trim((string)($_POST['content_es'] ?? ''))];
        $section = isset($SECTIONS[$_POST['section'] ?? '']) ? $_POST['section'] : 'research';
        $new = ($_POST['is_new'] ?? '') === '1';
        foreach (['f', 'es'] as $v) {                 // a whole page pasted as content: its head fills the empty fields, its body is the content
            if (preg_match('/<html|<body|<head/i', $$v['content'])) {
                $p = parse_page($$v['content']);
                foreach (['title', 'description', 'date', 'place'] as $k) if ($$v[$k] === '' && $p[$k] !== '') $$v[$k] = $p[$k];
                if ($v === 'f' && isset($SECTIONS[$p['section']]) && !isset($_POST['section'])) $section = $p['section'];
                $$v['content'] = $p['content'];
            }
        }
        $es['date'] = $f['date']; $es['place'] = $f['place'];
        if ($new) $slug = slugify((string)($_POST['address'] ?? '')) ?: slugify($f['title']);
        if ($f['title'] === '' && $f['content'] === '') $notes[] = ['bad', 'The page needs at least a title or some content.'];
        elseif ($slug === '') $notes[] = ['bad', 'Give the page a title: its address is made from it.'];
        elseif ($new && is_dir("$IN/$slug")) { $notes[] = ['bad', "There is already a page at /$section/<b>$slug</b>. Open it below to change it, or give this one another title or address."]; }
        else {
            $dir = "$IN/$slug";
            @mkdir($dir, 0755, true);
            if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $f['date'])) $f['date'] = $es['date'] = ($new || !is_file("$dir/index.html")) ? date('Y-m-d') : read_page("$dir/index.html")['date'];
            write_page("$dir/index.html", $f, 'en', $section);
            if ($es['title'] !== '' || $es['content'] !== '') { if ($es['title'] === '') $es['title'] = $f['title']; write_page("$dir/es.html", $es, 'es', $section); }
            elseif (is_file("$dir/es.html")) unlink("$dir/es.html");
            file_put_contents("$dir/section.txt", "$section\n");
            // pictures dropped with this save
            $got = []; $files = $_FILES['files'] ?? null;
            if ($files && is_array($files['name'])) {
                foreach ($files['name'] as $i => $name) {
                    if ($files['error'][$i] === UPLOAD_ERR_NO_FILE) continue;
                    if ($files['error'][$i] !== UPLOAD_ERR_OK) { $notes[] = ['bad', h($name) . " was not received (error {$files['error'][$i]})."]; continue; }
                    $clean = safe_name($name);
                    if ($clean === '' || !allowed($clean)) { $notes[] = ['bad', h($name) . ' was left out: a page uses pictures, videos, sounds, PDFs, styles and fonts.']; continue; }
                    move_uploaded_file($files['tmp_name'][$i], "$dir/$clean"); chmod("$dir/$clean", 0644); $got[] = $clean;
                }
            }
            $notes[] = ['good', "Saved <b>" . h($f['title'] ?: $slug) . "</b>" . ($got ? ' with ' . count($got) . ' new file' . (count($got) > 1 ? 's' : '') : '') . ". It goes to <b>{$SECTIONS[$section]}</b>, at /$section/$slug." . (($_POST['then'] ?? '') === 'publish' ? '' : ' It is on the site after the next Publish.')];
            $open = $slug;
            if (($_POST['then'] ?? '') === 'publish') $do = 'publish';
        }
    } elseif ($do === 'delete_file' && $slug !== '' && is_dir("$IN/$slug")) {
        $rel = implode('/', array_map('safe_name', array_filter(explode('/', (string)($_POST['file'] ?? '')), fn($p) => $p !== '' && $p !== '..')));
        if ($rel !== '' && is_file("$IN/$slug/$rel") && !in_array(strtolower($rel), ['index.html', 'es.html', 'section.txt'], true)) { unlink("$IN/$slug/$rel"); $notes[] = "Removed <b>" . h($rel) . "</b> from the page."; }
        $open = $slug;
    } elseif ($do === 'delete' && $slug !== '' && is_dir("$IN/$slug")) {
        rmtree("$IN/$slug");
        $notes[] = "Removed the page <b>$slug</b>. It leaves the site at the next Publish.";
    }
    if ($do === 'publish') {
        if ($running) $notes[] = 'A publish is already running.';
        else { @unlink($LOG); start_publish(); $running = true; $notes[] = 'Publishing. It starts within a minute and takes about two. This page refreshes by itself.'; }
    }
}

// ---------------------------------------------------------------------------------------------------------- what is there
$pages = [];
if (is_dir($IN)) {
    foreach (array_diff(scandir($IN), ['.', '..']) as $d) {
        if (!is_dir("$IN/$d") || $d[0] === '.') continue;
        $p = read_page("$IN/$d/index.html");
        $pages[$d] = ['title' => $p['title'] ?: $d, 'date' => $p['date'], 'section' => page_section("$IN/$d"), 'es' => is_file("$IN/$d/es.html"),
                      'files' => count(page_files("$IN/$d")), 'when' => date('j M Y, H:i', (int)filemtime("$IN/$d"))];
    }
    uasort($pages, fn($a, $b) => strcmp($b['date'], $a['date']));
}
if ($open === null && isset($_GET['page']) && isset($pages[slugify($_GET['page'])])) $open = slugify($_GET['page']);
$new = $open === null && isset($_GET['new']);
$log = is_file($LOG) ? (string)file_get_contents($LOG) : '';
$done = !$running && $log !== '';
$ok = $done && str_contains($log, 'failed: 0');
if ($open !== null) {
    $dir = "$IN/$open";
    $en = read_page("$dir/index.html"); $es = read_page("$dir/es.html");
    $section = page_section($dir); $files = page_files($dir); $card = first_picture($en['content']);
} elseif ($new) {
    $en = $es = read_page(''); $section = isset($SECTIONS[$_GET['section'] ?? '']) ? $_GET['section'] : 'research'; $files = []; $card = '';
    $en['date'] = date('Y-m-d');
}
$editing = $open !== null || $new;
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title><?= $editing ? ($new ? 'New page' : 'Editing ' . h($en['title'] ?: $open)) : 'Editing' ?> | United Notions Film</title>
<?php if ($running): ?><meta http-equiv="refresh" content="6"><?php endif; ?>
<style>
  :root { color-scheme: light dark; --ink:#111; --paper:#fff; --line:#d9d9d9; --soft:#f4f4f4; --go:#0b57d0; --warn:#b3261e; --good:#1b6e3a; --mute:#666; }
  @media (prefers-color-scheme: dark) { :root { --ink:#eee; --paper:#141414; --line:#333; --soft:#1e1e1e; --go:#8ab4f8; --warn:#f2b8b5; --good:#8fd3a6; --mute:#aaa; } }
  * { box-sizing: border-box; }
  body { margin:0; padding:20px 16px 90px; font:15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--ink); background:var(--paper); }
  .wrap { max-width:1500px; margin:0 auto; }
  h1 { font-size:20px; margin:0 0 2px; } h2 { font-size:16px; margin:28px 0 8px; }
  p.lead { margin:0 0 20px; color:var(--mute); }
  .top { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; }
  .msg { background:var(--soft); border-left:4px solid var(--go); padding:10px 14px; margin:0 0 12px; border-radius:4px; }
  .msg.bad { border-color:var(--warn); } .msg.good { border-color:var(--good); }
  table { width:100%; border-collapse:collapse; } td, th { text-align:left; padding:10px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  th { font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--mute); font-weight:600; }
  td small, .hint { color:var(--mute); } a { color:var(--go); }
  button, .btn { font:inherit; padding:8px 14px; border:1px solid var(--line); background:var(--soft); color:var(--ink); border-radius:6px; cursor:pointer; text-decoration:none; display:inline-block; }
  button.go, .btn.go { background:var(--go); color:#fff; border-color:var(--go); font-weight:600; }
  button.big { padding:12px 22px; }
  button.quiet { background:none; border:none; color:var(--go); padding:4px 6px; text-decoration:underline; }
  button.danger { color:var(--warn); } button[disabled] { opacity:.5; cursor:default; }
  form.inline { display:inline; }
  label { display:block; margin:14px 0 4px; font-weight:600; } label small { font-weight:400; color:var(--mute); }
  input[type=text], input[type=date], select, textarea { font:inherit; padding:8px 10px; border:1px solid var(--line); border-radius:6px; background:var(--paper); color:var(--ink); width:100%; }
  textarea { font:13px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace; min-height:120px; resize:vertical; }
  textarea.content { min-height:380px; }
  .hint { font-size:13px; margin:5px 0 0; }
  .editor { display:grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap:28px; align-items:start; }
  @media (max-width: 1000px) { .editor { grid-template-columns: 1fr; } }
  .row2 { display:grid; grid-template-columns: 1fr 1fr; gap:14px; } .row3 { display:grid; grid-template-columns: 1fr 1fr 1fr; gap:14px; }
  @media (max-width: 600px) { .row2, .row3 { grid-template-columns: 1fr; } }
  .drop { border:2px dashed var(--line); border-radius:10px; padding:16px; margin-top:6px; background:var(--soft); text-align:center; position:relative; }
  .drop.over { border-color:var(--go); background:color-mix(in srgb, var(--go) 10%, var(--soft)); }
  .drop input { position:absolute; inset:0; width:100%; height:100%; opacity:0; cursor:pointer; }
  .files { list-style:none; margin:10px 0 0; padding:0; display:grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap:10px; }
  .files li { border:1px solid var(--line); border-radius:8px; padding:8px; font-size:12.5px; background:var(--paper); }
  .files img, .files video { width:100%; aspect-ratio:3/2; object-fit:cover; border-radius:4px; background:var(--soft); display:block; margin-bottom:6px; }
  .files .name { word-break:break-all; display:block; } .files .card { color:var(--good); font-weight:600; }
  .files .acts { display:flex; justify-content:space-between; margin-top:4px; } .files .acts button { padding:2px 4px; font-size:12px; }
  .preview { position:sticky; top:12px; }
  .preview iframe { width:100%; height:calc(100vh - 120px); min-height:480px; border:1px solid var(--line); border-radius:8px; background:#fff; }
  details.adv { margin-top:18px; } details.adv summary { cursor:pointer; color:var(--mute); }
  pre.log { background:var(--soft); padding:12px; border-radius:6px; font-size:12.5px; max-height:320px; overflow:auto; white-space:pre-wrap; }
  .bar { position:fixed; bottom:0; left:0; right:0; background:var(--paper); border-top:1px solid var(--line); padding:12px 16px; display:flex; gap:14px; align-items:center; justify-content:center; flex-wrap:wrap; z-index:5; }
  .bar span { font-size:13px; color:var(--mute); }
</style>
</head>
<body>
<div class="wrap">
<div class="top">
  <div><h1>United Notions Film: editing</h1>
  <p class="lead"><?= $editing ? 'Write or paste the page on the left; the right shows it as it will read. Save keeps it in the workshop; Publish puts the whole site live.' : 'The pages written here. Open one to change it, or start a new one. Publish puts everything live, in about two minutes.' ?></p></div>
  <div><?php if ($editing): ?><a class="btn" href="./">All pages</a><?php else: ?><a class="btn go" href="?new=1">New page</a><?php endif; ?></div>
</div>

<?php foreach ($notes as $m): ?>
  <?php if (is_array($m)): ?><p class="msg <?= $m[0] ?>"><?= $m[1] ?></p><?php else: ?><p class="msg"><?= $m ?></p><?php endif; ?>
<?php endforeach; ?>

<?php if ($running): ?>
  <p class="msg"><?= file_exists($LOCK) ? 'Publishing now.' : 'Waiting for the publish to start (within a minute).' ?> This page refreshes by itself until it is done.</p>
  <?php if ($log): ?><pre class="log"><?= h(substr($log, -3000)) ?></pre><?php endif; ?>
<?php elseif ($done && !$editing): ?>
  <p class="msg <?= $ok ? 'good' : 'bad' ?>"><?= $ok ? 'The last publish went through and the live site answered every check.' : 'The last publish ended with a problem. The log is below.' ?></p>
  <details<?= $ok ? '' : ' open' ?>><summary>Log of the last publish</summary><pre class="log"><?= h(substr($log, -6000)) ?></pre></details>
<?php endif; ?>

<?php if ($editing): ?>
<form method="post" enctype="multipart/form-data" id="editor">
  <input type="hidden" name="do" value="save">
  <input type="hidden" name="is_new" value="<?= $new ? '1' : '0' ?>">
  <input type="hidden" name="name" value="<?= h($open ?? '') ?>">
  <input type="hidden" name="then" value="" id="then">
  <div class="editor">
    <div>
      <label for="title">Title</label>
      <input id="title" type="text" name="title" value="<?= h($en['title']) ?>" placeholder="The title of the page" autocomplete="off">
      <div class="row3">
        <div><label for="section">Where it goes</label>
          <select id="section" name="section">
            <?php foreach ($SECTIONS as $k => $label): ?><option value="<?= $k ?>"<?= $k === $section ? ' selected' : '' ?>><?= $label ?></option><?php endforeach; ?>
          </select>
          <p class="hint">Research: a lab note, listed by year. News: an update, listed at the top of News.</p></div>
        <div><label for="date">Date</label><input id="date" type="date" name="date" value="<?= h($en['date']) ?>"></div>
        <div><label for="place">Place <small>(optional)</small></label><input id="place" type="text" name="place" value="<?= h($en['place']) ?>" placeholder="Cochabamba"></div>
      </div>
      <label for="description">Summary <small>(one or two sentences: shown in the list, and to search engines)</small></label>
      <textarea id="description" name="description" style="min-height:64px"><?= h($en['description']) ?></textarea>

      <label for="content">Content <small>(HTML: write it, or paste a whole page; its title, summary and date fill the fields above)</small></label>
      <textarea id="content" name="content" class="content" spellcheck="false" placeholder="<p>The first paragraph.</p>
<img src=&quot;a-picture.jpg&quot; alt=&quot;What it shows&quot;>
<p>More.</p>"><?= h($en['content']) ?></textarea>
      <p class="hint">Pictures are named as their files below: <code>&lt;img src="whale.jpg" alt="..."&gt;</code>. The first picture of the page is the one shown in the list. Styles and any layout are kept as written.</p>

      <label>Pictures and videos</label>
      <div class="drop" id="drop">
        <input type="file" name="files[]" id="files" multiple accept="image/*,video/*,audio/*,.pdf,.css,.woff,.woff2,.js,.json,.txt,.svg">
        <div>Drop files here, or click to choose. They are kept with the page when you save.</div>
      </div>
      <ul class="files" id="filelist">
        <?php foreach ($files as $rel => $size): $ext = strtolower(pathinfo($rel, PATHINFO_EXTENSION)); $url = '?file=' . rawurlencode($open) . '/' . str_replace('%2F', '/', rawurlencode($rel)); ?>
        <li data-name="<?= h($rel) ?>">
          <?php if (str_starts_with($MIME[$ext] ?? '', 'image/')): ?><img src="<?= h($url) ?>" alt=""><?php elseif (str_starts_with($MIME[$ext] ?? '', 'video/')): ?><video src="<?= h($url) ?>" muted preload="metadata"></video><?php else: ?><div style="aspect-ratio:3/2;background:var(--soft);border-radius:4px;margin-bottom:6px"></div><?php endif; ?>
          <span class="name"><?= h($rel) ?></span><small><?= number_format($size / 1024) ?> KB<?= $rel === $card ? ' · <span class="card">in the list</span>' : '' ?></small>
          <div class="acts"><button type="button" class="quiet" onclick="insertFile('<?= h($rel) ?>', '<?= h($MIME[$ext] ?? '') ?>')">Insert</button>
          <button type="submit" class="quiet danger" formaction="?page=<?= h($open) ?>" name="do" value="delete_file" onclick="document.querySelector('[name=file]').value='<?= h($rel) ?>'; return confirm('Remove <?= h($rel) ?> from the page?')">Remove</button></div>
        </li>
        <?php endforeach; ?>
      </ul>
      <input type="hidden" name="file" value="">

      <details class="adv"<?= ($es['title'] !== '' || $es['content'] !== '') ? ' open' : '' ?>>
        <summary>Spanish version<?= ($es['title'] !== '' || $es['content'] !== '') ? ' (written)' : ' (optional: without it, the Spanish site shows the English)' ?></summary>
        <label for="title_es">Title in Spanish</label><input id="title_es" type="text" name="title_es" value="<?= h($es['title']) ?>">
        <label for="description_es">Summary in Spanish</label><textarea id="description_es" name="description_es" style="min-height:64px"><?= h($es['description']) ?></textarea>
        <label for="content_es">Content in Spanish</label><textarea id="content_es" name="content_es" class="content" style="min-height:240px" spellcheck="false"><?= h($es['content']) ?></textarea>
      </details>

      <details class="adv">
        <summary>The address of the page</summary>
        <?php if ($new): ?>
          <label for="address">Address <small>(optional)</small></label>
          <input id="address" type="text" name="address" placeholder="made from the title: 'The whale that watches back' becomes the-whale-that-watches-back">
          <p class="hint">The page will be at unitednotions.film/<span id="addr-section"><?= h($section) ?></span>/<b id="addr">the-title</b>. Only small letters, digits and dashes are used.
            Once the page is published, its address stays: change the title later and the address does not move, so links to it keep working.</p>
        <?php else: ?>
          <p class="hint">This page is at <a href="<?= h("$LIVE/$section/$open") ?>" target="_blank" rel="noopener"><?= h("unitednotions.film/$section/$open") ?></a>. The address was made from its first title and does not change,
            so links to it keep working. Changing "Where it goes" moves it between /research/ and /news/ at the next Publish.</p>
        <?php endif; ?>
      </details>

      <?php if (!$new): ?>
      <p style="margin-top:28px"><button type="submit" class="quiet danger" formaction="./" name="do" value="delete" onclick="return confirm('Remove this page from the site? It leaves the site at the next Publish.')">Remove this page</button></p>
      <?php endif; ?>
    </div>
    <div class="preview">
      <label style="margin-top:14px">As it will read</label>
      <iframe id="preview" sandbox="allow-same-origin" title="Preview"></iframe>
      <p class="hint">The look of the live site is close to this, with the site's header, date and footer around it.</p>
    </div>
  </div>
</form>
<?php else: ?>

<h2>Pages written here</h2>
<?php if (!$pages): ?>
  <p class="hint">None yet. Press "New page" to write the first.</p>
<?php else: ?>
<table>
  <tr><th>Page</th><th>Where</th><th>Date</th><th>Pictures</th><th>Last saved</th></tr>
  <?php foreach ($pages as $slug => $p): ?>
  <tr>
    <td><a href="?page=<?= h($slug) ?>"><b><?= h($p['title']) ?></b></a><br><small><a href="<?= h("$LIVE/{$p['section']}/$slug") ?>" target="_blank" rel="noopener"><?= h("/{$p['section']}/$slug") ?></a><?= $p['es'] ? ' · Spanish ✓' : '' ?></small></td>
    <td><?= $SECTIONS[$p['section']] ?></td>
    <td><?= h($p['date']) ?></td>
    <td><?= (int)$p['files'] ?></td>
    <td><small><?= h($p['when']) ?></small></td>
  </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>
<p class="hint" style="margin-top:16px">The other pages of the site (Work, About, People, Film Futurism, Press, and the press clippings on News) are written in the workshop's text files and published from a Mac: see EDITING.txt.</p>
<?php endif; ?>
</div>

<div class="bar">
  <?php if ($editing): ?>
    <button type="submit" form="editor" class="big">Save</button>
    <button type="submit" form="editor" class="go big" onclick="document.getElementById('then').value='publish'" <?= $running ? 'disabled' : '' ?>>Save and publish</button>
    <span><?= $running ? 'A publish is running.' : 'Save keeps the page in the workshop. Save and publish also rebuilds the site: about two minutes.' ?></span>
  <?php else: ?>
    <form method="post"><input type="hidden" name="do" value="publish"><button type="submit" class="go big" <?= $running ? 'disabled' : '' ?>>Publish</button></form>
    <span><?= $running ? 'Running…' : 'Rebuilds the whole site with what is here and checks it. About two minutes.' ?></span>
  <?php endif; ?>
</div>

<?php if ($editing): ?>
<script>
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var slug = <?= json_encode($open ?? '') ?>;
  var picked = {};                                 // files chosen but not yet saved: name -> object URL, for the preview

  function slugify(s) {
    s = s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').replace(/-{2,}/g, '-');
    return s;
  }
  function fileUrl(name) {
    if (picked[name]) return picked[name];
    if (!slug) return '';
    return '?file=' + encodeURIComponent(slug) + '/' + name.split('/').map(encodeURIComponent).join('/');
  }
  function resolved(html) {
    return html.replace(/(src|href|poster)=(["'])(?!https?:|\/\/|\/|#|data:|mailto:)([^"']+)\2/gi, function (m, a, q, t) {
      var u = fileUrl(t.split('?')[0].split('#')[0]); return u ? a + '=' + q + u + q : m;
    });
  }
  function preview() {
    var t = $('title').value, d = $('description').value, c = $('content').value, date = $('date').value, place = $('place').value;
    var when = [date, place].filter(Boolean).join(', ');
    var doc = '<!doctype html><html><head><meta charset="utf-8"><base target="_blank"><link rel="stylesheet" href="/assets/css/site.css">'
      + '<style>html{background:#fff}body{margin:0;padding:24px 20px 60px;background:#fff;color:#111}.note-body{max-width:46em}.note-body img,.note-body video{max-width:100%;height:auto}'
      + 'h1{font-family:var(--head,system-ui);font-weight:700;letter-spacing:-0.02em;line-height:1;font-size:clamp(28px,4vw,52px);margin:0 0 10px}.when{font-size:13px;letter-spacing:.05em;text-transform:uppercase;color:#666;margin:0 0 8px}'
      + '.lead{font-size:18px;color:#333;margin:0 0 28px}</style></head><body class="lab"><main><article class="lab-note">'
      + (when ? '<p class="when">' + esc(when) + '</p>' : '') + '<h1>' + (esc(t) || '<span style="color:#aaa">Title</span>') + '</h1>'
      + (d ? '<p class="lead">' + esc(d) + '</p>' : '') + '<div class="note-body" id="note">' + resolved(c) + '</div></article></main></body></html>';
    $('preview').srcdoc = doc;
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (ch) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]; }); }
  function fill(id, v) { if (v && !$(id).value) $(id).value = v; }
  function pasted() {
    // a whole page pasted in: its title, summary, date and place go to the fields; its styles and body stay as the content
    var v = $('content').value;
    if (!/<html|<body|<head/i.test(v)) return;
    var doc = new DOMParser().parseFromString(v, 'text/html');
    var h1 = doc.querySelector('h1'), m = function (n) { var e = doc.querySelector('meta[name="' + n + '"]'); return e ? e.getAttribute('content') || '' : ''; };
    fill('title', h1 ? h1.textContent.trim() : (doc.title || '').trim());
    fill('description', m('description') || (doc.querySelector('p') ? doc.querySelector('p').textContent.trim() : ''));
    var date = m('date'); if (!date) { var tm = doc.querySelector('time[datetime]'); date = tm ? tm.getAttribute('datetime').slice(0, 10) : ''; }
    if (/^\d{4}-\d{2}-\d{2}$/.test(date)) $('date').value = date;
    fill('place', m('place'));
    var sec = (m('section') || '').toLowerCase(); if (sec === 'news' || sec === 'research') $('section').value = sec;
    if (h1) h1.remove();
    var styles = Array.prototype.map.call(doc.head.querySelectorAll('style'), function (s) { return s.outerHTML; }).join('\n');
    $('content').value = (styles ? styles + '\n' : '') + doc.body.innerHTML.trim();
  }
  var timer;
  ['title', 'description', 'content', 'date', 'place'].forEach(function (id) { $(id).addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(preview, 150); }); });
  $('content').addEventListener('paste', function () { setTimeout(function () { pasted(); preview(); }, 0); });
  if ($('addr')) {
    var upd = function () { $('addr').textContent = slugify($('address').value) || slugify($('title').value) || 'the-title'; $('addr-section').textContent = $('section').value; };
    $('title').addEventListener('input', upd); $('address').addEventListener('input', upd); $('section').addEventListener('change', upd); upd();
  } else { $('section').addEventListener('change', function () {}); }
  // the drop zone: show what was chosen, and let the preview see it before it is saved
  var drop = $('drop'), input = $('files');
  ['dragenter', 'dragover'].forEach(function (e) { drop.addEventListener(e, function (ev) { ev.preventDefault(); drop.classList.add('over'); }); });
  ['dragleave', 'drop'].forEach(function (e) { drop.addEventListener(e, function () { drop.classList.remove('over'); }); });
  drop.addEventListener('drop', function (ev) { ev.preventDefault(); input.files = ev.dataTransfer.files; chosen(); });
  input.addEventListener('change', chosen);
  function chosen() {
    var list = $('filelist');
    Array.prototype.forEach.call(input.files, function (f) {
      var name = f.name.replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^\.+/, '');
      picked[name] = URL.createObjectURL(f);
      var li = document.createElement('li'); li.setAttribute('data-name', name);
      li.innerHTML = (f.type.indexOf('image/') === 0 ? '<img src="' + picked[name] + '" alt="">' : f.type.indexOf('video/') === 0 ? '<video src="' + picked[name] + '" muted></video>' : '<div style="aspect-ratio:3/2;background:var(--soft);border-radius:4px;margin-bottom:6px"></div>')
        + '<span class="name">' + esc(name) + '</span><small>' + Math.round(f.size / 1024) + ' KB · <b>not saved yet</b></small>'
        + '<div class="acts"><button type="button" class="quiet">Insert</button></div>';
      li.querySelector('button').addEventListener('click', function () { insertFile(name, f.type); });
      list.appendChild(li);
    });
    drop.querySelector('div').textContent = input.files.length + ' file' + (input.files.length > 1 ? 's' : '') + ' chosen: saved with the page when you press Save.';
    preview();
  }
  window.insertFile = function (name, type) {
    var ta = $('content'), tag = type.indexOf('video/') === 0 ? '<video src="' + name + '" controls></video>' : type.indexOf('image/') === 0 ? '<img src="' + name + '" alt="">' : '<a href="' + name + '">' + name + '</a>';
    var s = ta.selectionStart || ta.value.length, e = ta.selectionEnd || s;
    ta.value = ta.value.slice(0, s) + (s > 0 && ta.value[s - 1] !== '\n' ? '\n' : '') + tag + '\n' + ta.value.slice(e);
    ta.focus(); ta.selectionStart = ta.selectionEnd = s + tag.length + 2; preview();
  };
  preview();
})();
</script>
<?php endif; ?>
</body>
</html>
