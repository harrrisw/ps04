"""Copy an existing reviewed-for-structure series into a local delivery folder.

This exports review copies, without claiming student approval or publication.
"""
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/export_local.py runs/RUN_ID')
    run = (ROOT / sys.argv[1]).resolve()
    if not run.is_relative_to(ROOT / 'runs'):
        raise ValueError('Expected a run inside this repository')
    preview = run / 'video_previews'
    videos = json.loads((preview / 'manifest.json').read_text(encoding='utf-8'))
    review = json.loads((run / 'review.json').read_text(encoding='utf-8'))
    links_path = run / 'publication_links.json'
    links = json.loads(links_path.read_text(encoding='utf-8')) if links_path.exists() else []
    by_piece = {row['piece_id']: row for row in links}
    if not review['passed']:
        raise ValueError('Source series must pass mechanical checks before local delivery')
    destination = ROOT / 'deliverables' / run.name
    destination.mkdir(parents=True, exist_ok=True)
    exported = []
    for video in videos:
        pid = video['piece_id']
        source = preview / video['file']
        if hashlib.sha256(source.read_bytes()).hexdigest() != video['sha256']:
            raise ValueError(f'{pid}: video differs from its render manifest')
        for suffix in ['article.md', 'video.mp4', 'captions.srt', 'youtube-description.md']:
            source = preview / f'{pid}-{suffix}'
            target = destination / source.name
            shutil.copy2(source, target)
            if suffix == 'article.md' and by_piece.get(pid, {}).get('youtube_url'):
                text = target.read_text(encoding='utf-8')
                text = re.sub(r'\[Placeholder[^\]]*\]',
                              '[Watch the accompanying video]('+by_piece[pid]['youtube_url']+')',text)
                target.write_text(text,encoding='utf-8')
            exported.append(dict(file=target.name, bytes=target.stat().st_size,
                                 sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    manifest = dict(source_run=run.name, review_id=review['review_id'],
                    status='local review copies; see publication_links for reported uploads; Google Vids/HeyGen production pending',
                    publication_links=links,
                    files=exported)
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    table = '| Piece | Article | Local video | Runtime | YouTube |\n| --- | --- | --- | --- | --- |\n'
    for video in videos:
        pid = video['piece_id']
        seconds = round(video['duration_seconds'])
        table += (f'| {pid} | [Read article]({pid}-article.md) | '
                  f'[Watch MP4]({pid}-video.mp4) | {seconds//60}:{seconds%60:02d} | '
                  + (f"[Watch on YouTube]({by_piece[pid]['youtube_url']})" if by_piece.get(pid,{}).get('youtube_url') else 'Pending')+' |\n')
    (destination / 'README.md').write_text(
        '# The Small Business Research Brief — local files\n\n'
        f'Source run: `{run.name}`. Evidence retains its original as-of date.\n\n'
        'Open the three `article.md` files in your editor and the three `video.mp4` '
        'files in a video player. Each numbered article matches the same-numbered '
        'video. Separate SRT captions and source descriptions are included.\n\n'+table+'\n'+
        'These are AI-assisted review copies with synthetic narration. Student-reported '
        'YouTube uploads are linked above; article publication and final editorial approval remain pending. '
        'The videos were rendered locally, not in '
        'Google Vids/HeyGen. Review source quotations and caption timing before '
        'final production. The large media and ZIP are saved locally and ignored by Git.\n',
        encoding='utf-8')
    archive = ROOT / 'deliverables' / (run.name+'.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for file in sorted(destination.iterdir()):
            if file.is_file():
                bundle.write(file, arcname=destination.name+'/'+file.name)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('Archive integrity check failed')
    print(destination)
    print(archive)


if __name__ == '__main__':
    main()
