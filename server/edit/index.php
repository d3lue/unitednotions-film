<?php
// United Notions Film: the editing page. It lives at https://unitednotions.film/edit/ behind a password.
// A page of the site is a folder in the workshop (build/pages-in/<name>/) holding index.html and its pictures.
// Here you add one, replace one, correct one, or remove one, and press Publish. The server rebuilds the site.
// Nothing here is public: the folder's .htaccess asks for the password kept in the workshop's .htpasswd.

declare(strict_types=1);
$W     = '/home/danfal17/unf-workshop';
$IN    = "$W/build/pages-in";
$LOG   = "$W/publish.log";
$LOCK  = "$W/publish.lock";
$LIVE  = 'https://unitednotions.film';
$TYPES = ['html', 'htm', 'css', 'js', 'json', 'txt', 'md', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'avif', 'svg', 'mp4', 'webm', 'mov', 'm4v', 'mp3', 'm4a', 'wav', 'ogg', 'pdf', 'woff', 'woff2', 'glb', 'gltf', 'zip'];

$notes = [];
function slugify(string $s): string {
    $s = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $s) ?: $s;
    $s = strtolower(trim(preg_replace('/[^a-zA-Z0-9]+/', '-', $s), '-'));
    return preg_replace('/-{2,}/', '-', $s);
}
function h(?string $s): string { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
function rmtree(string $d): void {
    foreach (array_diff(scandir($d), ['.', '..']) as $f) { $p = "$d/$f"; is_dir($p) && !is_link($p) ? rmtree($p) : unlink($p); }
    rmdir($d);
}
function page_title(string $html): string {
    if (preg_match('~<h1[^>]*>(.*?)</h1>~is', $html, $m) || preg_match('~<title[^>]*>(.*?)</title>~is', $html, $m)) {
        return trim(html_entity_decode(preg_replace('/\s+/', ' ', strip_tags($m[1])), ENT_QUOTES, 'UTF-8'));
    }
    return '';
}
function safe_name(string $f): string {
    $f = basename(str_replace('\\', '/', $f));
    return preg_replace('/[^A-Za-z0-9._-]+/', '-', $f);
}
function allowed(string $f): bool { global $TYPES; return in_array(strtolower(pathinfo($f, PATHINFO_EXTENSION)), $TYPES, true); }
// This page never runs anything. It leaves a marker, and a cron job on the server (once a minute) sees it and runs server-publish.sh:
//     * * * * * cd $HOME/unf-workshop && if [ -f publish.requested ]; then rm -f publish.requested; sh server-publish.sh; fi >/dev/null 2>&1
$ASK = "$W/publish.requested";
function start_publish(): void { global $ASK; touch($ASK); }

$running = (file_exists($LOCK) && (time() - (int)@filemtime($LOCK) < 900)) || (file_exists($ASK) && (time() - (int)@filemtime($ASK) < 300));

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $site = $_SERVER['HTTP_SEC_FETCH_SITE'] ?? 'same-origin';
    if (!in_array($site, ['same-origin', 'none'], true)) { http_response_code(403); exit('Not from this site.'); }
    $do = $_POST['do'] ?? '';
    $slug = slugify($_POST['name'] ?? '');

    if ($do === 'upload') {
        $files = $_FILES['files'] ?? null;
        if (!$files || !is_array($files['name'])) { $notes[] = 'No files were chosen.'; }
        else {
            $tmp = sys_get_temp_dir() . '/unf-page-' . bin2hex(random_bytes(4));
            mkdir($tmp, 0700, true);
            $got = [];
            foreach ($files['name'] as $i => $name) {
                if ($files['error'][$i] !== UPLOAD_ERR_OK) { $notes[] = "$name was not received (error {$files['error'][$i]})."; continue; }
                $clean = safe_name($name);
                if (!allowed($clean)) { $notes[] = "$name was left out: that kind of file is not used by a page."; continue; }
                if (strtolower(pathinfo($clean, PATHINFO_EXTENSION)) === 'zip') {
                    $z = new ZipArchive();
                    if ($z->open($files['tmp_name'][$i]) === true) {
                        for ($k = 0; $k < $z->numFiles; $k++) {
                            $entry = $z->getNameIndex($k);
                            if (substr($entry, -1) === '/' || str_contains($entry, '..') || str_starts_with(basename($entry), '.') || str_contains($entry, '__MACOSX')) continue;
                            if (!allowed($entry)) continue;
                            // the folder inside the zip, if there is one, is dropped: the page's files sit at the top
                            $parts = array_values(array_filter(explode('/', $entry), fn($p) => $p !== ''));
                            if (count($parts) > 1 && !in_array(strtolower(end($parts)), ['index.html', 'es.html'], true) && count($parts) > 2) array_shift($parts);
                            elseif (count($parts) > 1 && in_array(strtolower(end($parts)), ['index.html', 'es.html'], true)) $parts = [end($parts)];
                            $rel = implode('/', array_map('safe_name', $parts));
                            @mkdir(dirname("$tmp/$rel"), 0700, true);
                            file_put_contents("$tmp/$rel", $z->getFromIndex($k));
                            $got[] = $rel;
                        }
                        $z->close();
                    } else { $notes[] = "$name could not be opened as a zip."; }
                } else {
                    move_uploaded_file($files['tmp_name'][$i], "$tmp/$clean");
                    $got[] = $clean;
                }
            }
            $index = null;
            foreach ($got as $g) { if (strtolower($g) === 'index.html' || (strtolower(pathinfo($g, PATHINFO_EXTENSION)) === 'html' && !$index && strtolower($g) !== 'es.html')) $index = $g; }
            if (!$index) { $notes[] = 'The page needs an HTML file (index.html).'; rmtree($tmp); }
            else {
                if ($index !== 'index.html') { rename("$tmp/$index", "$tmp/index.html"); }
                $html = (string)file_get_contents("$tmp/index.html");
                if ($slug === '') $slug = slugify(page_title($html));
                if ($slug === '') { $notes[] = 'Give the page a name, or a title inside the HTML.'; rmtree($tmp); }
                else {
                    $dest = "$IN/$slug";
                    $was = is_dir($dest);
                    @mkdir($IN, 0755, true);
                    if (!$was) mkdir($dest, 0755, true);
                    // copy over: new files replace old ones of the same name, other old files stay
                    $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($tmp, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::SELF_FIRST);
                    foreach ($it as $f) {
                        $rel = substr((string)$f, strlen($tmp) + 1);
                        if ($f->isDir()) { @mkdir("$dest/$rel", 0755, true); continue; }
                        copy((string)$f, "$dest/$rel"); chmod("$dest/$rel", 0644);
                    }
                    rmtree($tmp);
                    $notes[] = ($was ? 'Updated' : 'Added') . " the page <b>$slug</b> (" . count($got) . ' files). Press Publish to put it on the site.';
                }
            }
        }
    } elseif ($do === 'save' && $slug !== '' && is_dir("$IN/$slug")) {
        $which = ($_POST['which'] ?? 'index') === 'es' ? 'es.html' : 'index.html';
        file_put_contents("$IN/$slug/$which", str_replace("\r\n", "\n", (string)($_POST['html'] ?? '')));
        $notes[] = "Saved $which of <b>$slug</b>. Press Publish to put it on the site.";
    } elseif ($do === 'delete' && $slug !== '' && is_dir("$IN/$slug")) {
        rmtree("$IN/$slug");
        $notes[] = "Removed the page <b>$slug</b>. Press Publish to take it off the site.";
    } elseif ($do === 'publish') {
        if ($running) $notes[] = 'A publish is already running.';
        else { @unlink($LOG); start_publish(); $running = true; $notes[] = 'Publishing. It starts within a minute and takes about two. This page refreshes by itself.'; }
    }
}

// what is there
$pages = [];
if (is_dir($IN)) {
    foreach (array_diff(scandir($IN), ['.', '..']) as $d) {
        if (!is_dir("$IN/$d") || $d[0] === '.') continue;
        $html = is_file("$IN/$d/index.html") ? (string)file_get_contents("$IN/$d/index.html") : '';
        $n = 0; foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator("$IN/$d", FilesystemIterator::SKIP_DOTS)) as $f) $n++;
        $pages[$d] = ['title' => page_title($html) ?: $d, 'files' => $n, 'es' => is_file("$IN/$d/es.html"), 'when' => date('j M Y, H:i', (int)filemtime("$IN/$d"))];
    }
}
$editing = isset($_GET['edit']) && isset($pages[slugify($_GET['edit'])]) ? slugify($_GET['edit']) : null;
$which = ($_GET['which'] ?? 'index') === 'es' ? 'es' : 'index';
$log = is_file($LOG) ? (string)file_get_contents($LOG) : '';
$done = !$running && $log !== '';
$ok = $done && str_contains($log, 'failed: 0');
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Editing | United Notions Film</title>
<?php if ($running): ?><meta http-equiv="refresh" content="6"><?php endif; ?>
<style>
  :root { color-scheme: light dark; --ink:#111; --paper:#fff; --line:#ddd; --soft:#f3f3f3; --go:#0b57d0; --warn:#b3261e; --good:#1b6e3a; }
  @media (prefers-color-scheme: dark) { :root { --ink:#eee; --paper:#141414; --line:#333; --soft:#1e1e1e; --go:#8ab4f8; --warn:#f2b8b5; --good:#8fd3a6; } }
  body { margin:0; padding:24px 16px 80px; font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--ink); background:var(--paper); max-width:900px; margin-inline:auto; }
  h1 { font-size:22px; margin:0 0 4px; } h2 { font-size:17px; margin:36px 0 10px; }
  p.lead { margin:0 0 24px; opacity:.8; }
  .msg { background:var(--soft); border-left:4px solid var(--go); padding:10px 14px; margin:0 0 16px; border-radius:4px; }
  .msg.bad { border-color:var(--warn); } .msg.good { border-color:var(--good); }
  table { width:100%; border-collapse:collapse; } td, th { text-align:left; padding:10px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  th { font-size:13px; text-transform:uppercase; letter-spacing:.04em; opacity:.7; }
  td small { opacity:.7; } a { color:var(--go); }
  form.inline { display:inline; } button, .btn { font:inherit; padding:8px 14px; border:1px solid var(--line); background:var(--soft); color:var(--ink); border-radius:6px; cursor:pointer; }
  button.go { background:var(--go); color:#fff; border-color:var(--go); font-weight:600; padding:12px 22px; }
  button.quiet { background:none; border:none; color:var(--go); padding:4px 6px; text-decoration:underline; }
  button.danger { color:var(--warn); }
  label { display:block; margin:14px 0 4px; font-weight:600; } input[type=text] { font:inherit; padding:8px 10px; width:100%; max-width:420px; border:1px solid var(--line); border-radius:6px; background:var(--paper); color:var(--ink); }
  input[type=file] { display:block; margin-top:4px; }
  .drop { border:2px dashed var(--line); border-radius:10px; padding:20px; margin-top:8px; background:var(--soft); }
  .hint { font-size:14px; opacity:.75; margin:6px 0 0; }
  textarea { width:100%; min-height:420px; font:13px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace; padding:10px; border:1px solid var(--line); border-radius:6px; background:var(--paper); color:var(--ink); }
  pre.log { background:var(--soft); padding:12px; border-radius:6px; font-size:12.5px; max-height:320px; overflow:auto; white-space:pre-wrap; }
  .publish { position:fixed; bottom:0; left:0; right:0; background:var(--paper); border-top:1px solid var(--line); padding:12px 16px; display:flex; gap:14px; align-items:center; justify-content:center; }
  .publish span { font-size:14px; opacity:.8; }
</style>
</head>
<body>
<h1>United Notions Film: editing</h1>
<p class="lead">A page is a folder with an HTML file and its pictures. Add it here, then press Publish. The site is rebuilt in about two minutes.</p>

<?php foreach ($notes as $m): ?><p class="msg"><?= $m ?></p><?php endforeach; ?>

<?php if ($running): ?>
  <p class="msg"><?= file_exists($LOCK) ? 'Publishing now.' : 'Waiting for the publish to start (within a minute).' ?> This page refreshes by itself until it is done.</p>
  <?php if ($log): ?><pre class="log"><?= h(substr($log, -3000)) ?></pre><?php endif; ?>
<?php elseif ($done): ?>
  <p class="msg <?= $ok ? 'good' : 'bad' ?>"><?= $ok ? 'The last publish went through and the live site answered every check.' : 'The last publish ended with a problem. The log is below.' ?></p>
  <details<?= $ok ? '' : ' open' ?>><summary>Log of the last publish</summary><pre class="log"><?= h(substr($log, -6000)) ?></pre></details>
<?php endif; ?>

<?php if ($editing): $file = "$IN/$editing/" . ($which === 'es' ? 'es.html' : 'index.html'); ?>
  <h2>Correcting <?= h($pages[$editing]['title']) ?> <small>(<?= $which === 'es' ? 'es.html, the Spanish' : 'index.html, the English' ?>)</small></h2>
  <p class="hint"><a href="?edit=<?= h($editing) ?>&amp;which=index">English</a> · <a href="?edit=<?= h($editing) ?>&amp;which=es">Spanish</a><?= !is_file($file) ? ' · this file does not exist yet; saving creates it' : '' ?> · <a href="./">back to the list</a></p>
  <form method="post">
    <input type="hidden" name="do" value="save"><input type="hidden" name="name" value="<?= h($editing) ?>"><input type="hidden" name="which" value="<?= h($which) ?>">
    <textarea name="html" spellcheck="false"><?= h(is_file($file) ? (string)file_get_contents($file) : '') ?></textarea>
    <p><button type="submit" class="go">Save</button></p>
  </form>
<?php endif; ?>

<h2>Add a page, or replace one</h2>
<form method="post" enctype="multipart/form-data">
  <input type="hidden" name="do" value="upload">
  <div class="drop">
    <label for="files">The files of the page</label>
    <input id="files" type="file" name="files[]" multiple required>
    <p class="hint">Choose them all at once: index.html and its pictures. Or one zip of the folder. Up to 512 MB.
      The Spanish version, if there is one, is a second file named es.html.</p>
    <label for="name">Its address <small>(optional)</small></label>
    <input id="name" type="text" name="name" placeholder="taken from the page's title if left empty">
    <p class="hint">Letters, digits and dashes. The page will be at <?= h($LIVE) ?>/research/<b>that-name</b>.
      To replace a page, use its name again: new files win, the rest stay.</p>
  </div>
  <p><button type="submit" class="go">Add it</button></p>
</form>
<p class="hint">Inside the HTML, the date and place are read from <code>&lt;meta name="date" content="2026-10-07"&gt;</code> and <code>&lt;meta name="place" content="Cochabamba"&gt;</code>,
  the title from the first <code>&lt;h1&gt;</code>, the summary from <code>&lt;meta name="description"&gt;</code> or the first paragraph, and the card's picture is the first <code>&lt;img&gt;</code>.
  Pictures are named in the HTML as they are in the folder: <code>&lt;img src="whale.jpg"&gt;</code>.</p>

<h2>Pages written here</h2>
<?php if (!$pages): ?>
  <p class="hint">None yet. The lab notes of the old site are kept another way and do not show here.</p>
<?php else: ?>
<table>
  <tr><th>Page</th><th>Files</th><th>Changed</th><th></th></tr>
  <?php foreach ($pages as $slug => $p): ?>
  <tr>
    <td><b><?= h($p['title']) ?></b><br><small><a href="<?= h("$LIVE/research/$slug") ?>" target="_blank" rel="noopener"><?= h("/research/$slug") ?></a><?= $p['es'] ? ' · Spanish ✓' : ' · no Spanish yet' ?></small></td>
    <td><?= (int)$p['files'] ?></td>
    <td><small><?= h($p['when']) ?></small></td>
    <td>
      <a class="btn" href="?edit=<?= h($slug) ?>">Correct</a>
      <form class="inline" method="post" onsubmit="return confirm('Remove the page <?= h($slug) ?> from the workshop?')">
        <input type="hidden" name="do" value="delete"><input type="hidden" name="name" value="<?= h($slug) ?>">
        <button type="submit" class="quiet danger">Remove</button>
      </form>
    </td>
  </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>

<div class="publish">
  <form method="post"><input type="hidden" name="do" value="publish"><button type="submit" class="go" <?= $running ? 'disabled' : '' ?>>Publish</button></form>
  <span><?= $running ? 'Running…' : 'Rebuilds the whole site with what is here and checks it. About two minutes.' ?></span>
</div>
</body>
</html>
