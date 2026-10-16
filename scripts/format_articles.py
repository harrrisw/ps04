"""Format the local article subset of Markdown for browser copy/paste and plain text."""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)|\*\*(.+?)\*\*|\*([^*]+)\*')


def inline(text):
    result, offset = [], 0
    for match in TOKEN.finditer(text):
        result.append(html.escape(text[offset:match.start()]))
        label, url, bold, italic = match.groups()
        if url:
            result.append(f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>')
        elif bold:
            result.append('<strong>'+inline(bold)+'</strong>')
        else:
            result.append('<em>'+inline(italic)+'</em>')
        offset = match.end()
    result.append(html.escape(text[offset:]))
    return ''.join(result)


def blocks(markdown):
    output = []
    for block in re.split(r'\n\s*\n', markdown.strip()):
        lines = block.splitlines()
        heading = re.fullmatch(r'(#{1,6}) (.+)', block)
        if heading:
            level = len(heading[1])
            output.append(f'<h{level}>{inline(heading[2])}</h{level}>')
        elif all(line.startswith('- ') for line in lines):
            output.append('<ul>'+''.join('<li>'+inline(line[2:])+'</li>' for line in lines)+'</ul>')
        else:
            paragraph = ''.join(inline(line.rstrip()) + ('<br>' if line.endswith('  ') else ' ')
                                for line in lines).strip()
            output.append('<p>'+paragraph+'</p>')
    return '\n'.join(output)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.append(dict(attrs)['href'])


def main():
    folder = (ROOT/sys.argv[1]).resolve()
    if not folder.is_relative_to(ROOT/'deliverables'):
        raise ValueError('Expected a local deliverables directory')
    for pid in ['01','02','03']:
        original = (folder/f'{pid}-article.md').read_text(encoding='utf-8')
        heading, body = original.split('\n',1)
        title = heading.removeprefix('# ').strip()
        rendered = blocks(body)
        parser = Links()
        parser.feed(rendered)
        expected = re.findall(r'\[[^\]]+\]\((https?://[^)]+)\)',body)
        if parser.urls != expected:
            raise ValueError(f'{pid}: source links changed during conversion')
        document = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>'''+html.escape(title)+'''</title>
<style>
body{margin:0;background:#faf9f6;color:#242424;font:19px/1.75 Georgia,serif}
.sheet{max-width:740px;margin:36px auto;padding:32px 40px 64px;background:white}
h1{font-size:38px;line-height:1.2;letter-spacing:-.6px;margin:24px 0}
h2{font-size:26px;line-height:1.3;margin-top:36px}p{margin:22px 0}
a{color:#175d73;text-underline-offset:3px}li{margin:10px 0}
aside{font:14px/1.5 system-ui,sans-serif;background:#edf3f4;padding:16px 20px;border-radius:8px}
button{font:inherit;cursor:pointer;padding:8px 14px;background:#175d73;color:white;border:0;border-radius:5px;margin-top:10px}
@media(max-width:600px){.sheet{margin:0;padding:22px}h1{font-size:30px}}
@media print{aside{display:none}.sheet{margin:0;padding:0;max-width:none}body{background:white}}
</style></head><body><div class="sheet">
<aside>Paste the title below into Substack's title field. Select and copy the article body,
then paste it into the post editor. Check formatting and links before publishing.<br>
<button type="button" onclick="const r=document.createRange();r.selectNodeContents(document.getElementById('article-body'));const s=window.getSelection();s.removeAllRanges();s.addRange(r);">Select article body</button>
</aside>
<h1>'''+html.escape(title)+'''</h1>
<main id="article-body">'''+rendered+'''</main>
</div></body></html>
'''
        (folder/f'{pid}-article.html').write_text(document,encoding='utf-8')
        plain = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'\1 (\2)',original)
        plain = re.sub(r'(?m)^#{1,6} ', '', plain)
        plain = plain.replace('**','').replace('*','')
        (folder/f'{pid}-article.txt').write_text(plain,encoding='utf-8')
        print(f'{pid}: HTML + TXT saved; {len(expected)} links preserved')
    readme = folder/'README.md'
    text = readme.read_text(encoding='utf-8').split('\n## Formatted articles')[0]
    text += '\n## Formatted articles\n\nOpen an HTML file in your browser for readable article formatting. Copy the title separately; use “Select article body,” then Ctrl+C and paste into Substack. Plain-text copies are also included.\n\n'
    for pid in ['01','02','03']:
        text += f'- Article {pid}: [Formatted HTML]({pid}-article.html) · [Plain text]({pid}-article.txt)\n'
    readme.write_text(text,encoding='utf-8')
    manifest_path = folder/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    prior = {item['file']: item for item in manifest['files']}
    for file in list(folder.glob('*-article.html'))+list(folder.glob('*-article.txt')):
        prior[file.name] = dict(file=file.name,bytes=file.stat().st_size,
                               sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    manifest['files'] = list(prior.values())
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    archive = folder.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
        for file in sorted(folder.iterdir()):
            if file.is_file():
                bundle.write(file,arcname=folder.name+'/'+file.name)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None


if __name__=='__main__':
    main()
