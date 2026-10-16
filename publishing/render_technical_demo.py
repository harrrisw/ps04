"""Create a disclosed, AI-narrated walkthrough of retained evidence, not a live run."""
import asyncio
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from lib.media_tools import ffmpeg_binary

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/technical-demo'
WORK = ROOT / '.tools/technical-demo'
SCENES = [
    ('A research pipeline you can inspect', [
        'Audience: small-business market researchers',
        'Three published article / video pairs',
        'AI narration • retained-artifact walkthrough',
        'Prepared October 16, 2026; not a live execution'],
     'SUBMISSION.md',
     'This is an AI-narrated technical walkthrough of the Small Business Research Brief. The audience is small-business market researchers who need useful evidence without a large research budget. The project asks where AI tools deserve a practical pilot, and where their claims still need testing. Three articles and their matching videos have been published. This demonstration walks through real saved files and records. It does not show a new live execution, and it does not substitute for the student reviewing the work or explaining the architecture.'),
    ('Separate stages, one evidence trail', [
        'Discover → Extract → Store → Filter',
        'Select → Brief → Articles + scripts → Check',
        'Human approval → Package → Manual publication',
        'Entry point: bash run.sh'],
     'run.sh  |  docs/IMPLEMENTATION.md  |  data/store.sh',
     'The entry point is bash run dot sh. Sixteen Bash interfaces divide orchestration, collection, storage, editorial work, checking, and packaging. The collectors discover feeds, YouTube videos, and podcasts. Extraction produces substantive text or timed transcripts. JSON Lines carry records between stages. Only the store component accesses the SQLite evidence index. Filtering applies the thirty-day window. AI then selects sources, develops briefs, and drafts articles and video scripts. Checks precede human review. Packaging requires an approval fingerprint that matches the reviewed content. The architecture diagram and component contracts are preserved in the repository.'),
    ('Trace a published claim to its source', [
        'Crayon: Insights API → accepted source',
        'Brief 01-C01 → article 01, “What source access changes”',
        '“Ask for more and you get the full text and source link”',
        'Vendor capability claim; effectiveness is unproven'],
     'runs/20261010T052912Z-1d2e8a/briefs.jsonl',
     'Here is one published claim. Article one says Crayon describes access to underlying text and source links. The saved source passage says, Ask for more and you get the full text and source link. The evidence record has a stable item identifier and an immutable version identifier. Its editorial decision is accept, and brief claim zero one C zero one carries the supporting citation. The published article attributes this capability to the vendor. It does not turn the announcement into independent proof of accuracy, affordability, or business effectiveness. The claim-trace document links the exact retained files.'),
    ('Two actual collection dates', [
        'October 10: 39 eligible items / 9 publishers',
        'October 16: 60 eligible items / 9 publishers',
        'Final Oct 16 batch: 2 new / 38 unchanged',
        'Later date, sources, model and policy all changed'],
     'runs/20261016T153525Z-231399/feedback_comparison.md',
     'The published October tenth series used thirty-nine eligible items from nine publishers. The final October sixteenth run used sixty eligible items, also from nine publishers, and produced another three articles and scripts. Those later drafts are retained separately from the published series. Its immediate collection batch recorded two new and thirty-eight unchanged records; those counts are not the comparison against October tenth. The saved comparison documents changes in evidence and editorial decisions. Because the date window, sources, model provider, and policy changed together, the comparison cannot isolate a policy effect. October sixteenth was after the supplied deadline.'),
    ('Replay and recovery remain visible', [
        'Duplicate replay: 28 items → 28 logical items',
        'all_unchanged: true / same_latest_versions: true',
        'Subtitle throttling → local audio transcription',
        'Unsupported Parley alias → supported model ID'],
     'runs/20261010T052041Z-15fd8c/replays/store-e46554b8/replay.json',
     'The duplicate demonstration re-ingested exactly twenty-eight saved items. Every record was unchanged, the store still held twenty-eight logical items, and the latest versions stayed identical. This is explicitly labeled a replay, not another live collection day. Failure records are preserved too. YouTube subtitle throttling motivated local audio transcription, with Deno and FFmpeg supporting media extraction. An unsupported Parley model alias failed before a supported model identifier was configured. A later run also stopped briefing because no YouTube source had been accepted. Adding a relevant webinar enabled the next attempt without weakening that coverage check.'),
    ('Human feedback changes the policy', [
        'Student feedback: 3 accept + 3 defer judgments',
        'Policy v3: inspectable workflows; measured baselines',
        'Citation repairs retain before / after records',
        'Assistant corrections are labeled separately'],
     'config/editorial_policy.md  |  docs/POLICY_CHANGE_PROPOSAL.md',
     'The student supplied three accept judgments and three defer judgments. They favored practical workflows, inspectable competitor evidence, and a concrete multi-agent checking process. They requested stronger evidence for frameworks, measured baselines for speed and cost claims, and tested workflows behind announcements. Policy version three records that revision. The October sixteenth generation still needed assistance: invalid quotations remained after an automated repair, and documented assistant edits corrected their source attribution. Original and corrected outputs are retained. These assistant corrections are not presented as student corrections or final approval. Mechanical checks passing still leaves source interpretation for human review.'),
    ('Tradeoffs and the submission boundary', [
        'Bash interfaces + focused Python implementations',
        'Versioned evidence; reconstructable SQLite index',
        'Cached media saves work; refresh needs judgment',
        'Open: production evidence, review and reflection'],
     'docs/EVALUATION.md  |  docs/RUNS.md  |  SUBMISSION.md',
     'The main architectural tradeoff is inspectability versus operational complexity. Separate Bash interfaces make each stage easy to inspect and replay; Python handles parsing, model calls, and storage. Immutable evidence preserves provenance, but a fresh clone must reconstruct the ignored SQLite index. Media caching reduces repeated downloads and transcription, while silent source edits may require an explicit refresh. Actual model dollar cost remains unknown where the provider did not report it. The submission links the six publications, all retained attempts, and this demonstration. Remaining requirements include Google Vids or HeyGen production evidence, final human verification, and the student reflection. This AI-generated walkthrough is ready for the student to review.'),
]

def stamp(seconds):
    millis = round(seconds * 1000)
    h, millis = divmod(millis, 3600000)
    m, millis = divmod(millis, 60000)
    s, millis = divmod(millis, 1000)
    return f'{h:02}:{m:02}:{s:02},{millis:03}'

def slide(index, title, bullets, source):
    im = Image.new('RGB', (1280, 720), '#F5F3EA')
    d = ImageDraw.Draw(im)
    def font(size, bold=False):
        return ImageFont.truetype('C:/Windows/Fonts/arial'+('bd' if bold else '')+'.ttf', size)
    d.rectangle((0,0,1280,12), fill='#007F78')
    d.text((60,42), 'THE SMALL BUSINESS RESEARCH BRIEF / TECHNICAL WALKTHROUGH', font=font(20,True), fill='#007F78')
    d.text((60,113), title, font=font(43,True), fill='#112E36')
    y = 225
    for j, bullet in enumerate(bullets):
        d.text((60,y), f'{j+1:02}', font=font(26,True), fill='#007F78')
        words, line, lines = bullet.split(), '', []
        for word in words:
            trial = (line+' '+word).strip()
            if d.textlength(trial,font=font(29)) > 1050:
                lines.append(line); line=word
            else: line=trial
        lines.append(line)
        for line in lines:
            d.text((118,y),line,font=font(29),fill='#112E36'); y+=38
        y+=24
    assert y < 590, (title, y)
    d.line((60,595,1220,595),fill='#B6C9C4',width=2)
    d.text((60,612),source,font=font(18),fill='#48636A')
    d.text((60,668),'AI narration • saved records, not live execution • 2026-10-16',font=font(18),fill='#48636A')
    d.text((1140,668),f'{index+1} / 7',font=font(18,True),fill='#007F78')
    im.save(WORK/f'{index:02}.png')
    return im

async def main():
    OUT.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
    ffmpeg = str(ffmpeg_binary())
    frames, scenes, srt = [], [], []
    offset = 0.0
    for i,(title,bullets,source,narration) in enumerate(SCENES):
        frames.append(slide(i,title,bullets,source))
        audio=WORK/f'{i:02}.mp3'
        if not audio.exists():
            await edge_tts.Communicate(narration,voice='en-US-AriaNeural',rate='-5%').save(str(audio))
        probe=subprocess.run([ffmpeg,'-i',str(audio)],capture_output=True,text=True)
        match=re.search(r'Duration: (\d+):(\d+):([\d.]+)',probe.stderr)
        if not match: raise RuntimeError(probe.stderr)
        h,m,s=map(float,match.groups()); duration=h*3600+m*60+s+0.4
        segment=WORK/f'{i:02}.mp4'
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-loop','1','-framerate','10','-i',str(WORK/f'{i:02}.png'),'-i',str(audio),'-t',str(duration),'-c:v','libx264','-preset','fast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-af','apad',str(segment)],check=True)
        words=narration.split(); chunks=[' '.join(words[j:j+12]) for j in range(0,len(words),12)]
        for j,chunk in enumerate(chunks):
            srt.append(f'{len(srt)+1}\n{stamp(offset+j*duration/len(chunks))} --> {stamp(offset+(j+1)*duration/len(chunks))}\n{chunk}\n')
        scenes.append(dict(title=title,start_seconds=round(offset,2),duration_seconds=duration,source=source,narration=narration))
        offset+=duration
        print(f'Scene {i+1}: {duration:.2f}s',flush=True)
    if not 240 <= offset <= 360: raise ValueError(f'Duration outside 4–6 minutes: {offset}')
    captions=OUT/'captions.srt'; captions.write_text('\n'.join(srt),encoding='utf-8')
    concat=WORK/'concat.txt'; concat.write_text('\n'.join(f"file '{i:02}.mp4'" for i in range(len(SCENES))),encoding='utf-8')
    video=OUT/'technical-demo.mp4'
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(captions),'-map','0:v','-map','0:a','-map','1:0','-c','copy','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart',str(video)],check=True)
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-i',str(video),'-map','0:v','-map','0:a','-f','null','-'],check=True)
    contact=Image.new('RGB',(1280,4*360),'white')
    for i,im in enumerate(frames): contact.paste(im.resize((640,360)),((i%2)*640,(i//2)*360))
    contact.save(OUT/'storyboard.png')
    manifest=dict(created_on='2026-10-16',kind='AI-narrated retained-artifact walkthrough, not live execution',voice='en-US-AriaNeural',tts='edge-tts 7.3.1',duration_seconds=round(offset,2),bytes=video.stat().st_size,sha256=hashlib.sha256(video.read_bytes()).hexdigest(),full_decode='passed',captions='Approximate word-group timing; review playback',student_approval=False,scenes=scenes)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (OUT/'script.md').write_text('# Technical demonstration narration\n\nAI-written and synthetically narrated. Saved-artifact walkthrough, not a live run. Student review pending.\n\n'+'\n\n'.join(f'## {stamp(s["start_seconds"]).split(",")[0]} — {s["title"]}\n\n{s["narration"]}\n\nRecord: `{s["source"]}`' for s in scenes)+'\n',encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ['duration_seconds','bytes','full_decode']}))

if __name__ == '__main__': asyncio.run(main())
