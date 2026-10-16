"""Render local review copies. Google Vids/HeyGen production is a separate step."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from lib.common import ROOT, atomic_text, read_json, write_json
from lib.media_tools import ffmpeg_binary

STORYBOARDS = {
 '01': [
  ('THE QUESTION', 'Can you check the evidence?', ['Retrieve material', 'Inspect its sources', 'Maintain access + human control'], 'Crayon · NN/g · TechCrunch'),
  ('THE CAPABILITY', 'A route back to the source', ['Crayon says its API exposes insight details', 'Underlying text and links support inspection', 'Accuracy, cost and small-business fit: untested'], 'Crayon · Insights API · October 1, 2026'),
  ('THE CONSTRAINT', 'Connections need upkeep', ['Context can go stale or disappear', 'Integrations may need reconnecting', 'Include maintenance in the pilot'], 'NN/g · Context Libraries · October 9, 2026'),
  ('THE BOUNDARY', 'Keep human control visible', ['Reported internal evaluation restrictions', 'A different setting from a small business', 'No general failure rate established'], 'TechCrunch · Anthropic internal evaluations · October 10, 2026 UTC'),
  ('THE PILOT', 'One question. Repeated checks.', ['Use a bounded competitor question', 'Check each answer against its source', 'Record corrections, upkeep and actual cost'], 'Editorial proposal grounded in Crayon and NN/g'),
  ('WHAT TO WATCH', 'Judge the complete workflow', ['Evidence quality + total effort', 'Coverage + affordability + human control', 'Expand only when your pilot supports it'], 'Sources and full references accompany this video'),
 ],
 '02': [
  ('THE QUESTION', 'What makes a finding trustworthy?', ['Keep research evidence inspectable', 'Assess preparation and checking', 'Broad performance claims need validation'], 'Christopher Penn · NN/g · Marketing AI Institute'),
  ('CLASSIFICATION', 'Your context is part of the work', ['Define the task and categories', 'Supply the data and context', 'A practitioner account is not a benchmark'], 'Christopher Penn · Lightweight classification · October 6, 2026'),
  ('TRACEABILITY', 'Every finding needs a trail', ['Link notes to research artifacts', 'Label unsupported notes as assumptions', 'Keep contradictions and outliers visible'], 'NN/g · Empathy Mapping · October 2, 2026'),
  ('VERIFICATION', 'Agreement can still be wrong', ['Agents can flag claims and propose edits', 'A second agent can share the same error', 'Inspect the original evidence'], 'Marketing AI Institute · Fact-checking agents · September 23, 2026'),
  ('THE PILOT', 'Use an inspectable acceptance rule', ['Bound the task', 'Preserve references and check findings', 'Count preparation, review and rework'], 'Editorial inference connecting NN/g and Marketing AI Institute'),
  ('WHAT TO WATCH', 'Measure the work needed to trust it', ['Net time savings remain unproven', 'Language and small-business transfer are open', 'Judge evidence and complete effort together'], 'Sources and full references accompany this video'),
 ],
 '03': [
  ('THE QUESTION', 'Start with one business decision', ['Retain the research material', 'Name the interpretation owner', 'Compare the full workload'], 'NN/g · Greenbook · Insight Platforms'),
  ('THE EVIDENCE', 'Organize what you actually know', ['Use retained interviews or responses', 'Connect findings to supporting material', 'Assumptions are not customer evidence'], 'NN/g · Empathy Mapping · October 2, 2026'),
  ('THE OUTCOME', 'Measure decision support', ['Did the findings clarify the decision?', 'Implementation is not the only criterion', 'Enterprise experience does not establish SMB ROI'], 'Greenbook · Nadine van Rooyen · 16:05–16:20'),
  ('THE CONTEXT', 'Budget for interpretation', ['Check language and local meaning', 'Include the reviewer’s effort', 'Avoid treating regions as one customer profile'], 'Insight Platforms · Mpho Mpofu · 6:15–6:25 / 16:07–16:31'),
  ('THE COMPARISON', 'Record the complete workload', ['Preparation + organization + human checks', 'Corrections + maintenance + actual costs', 'Compare the same question and material'], 'Proposed pilot; no measured outcomes are shown'),
  ('WHAT TO WATCH', 'Keep evidence. Count the checking.', ['Look for independent small-business evaluations', 'Require baselines, total costs and failures', 'Expand only when the comparison supports it'], 'Sources and full references accompany this video'),
 ],
}


def clean(text):
    text = re.sub(r'\[claim:[^\]]+\]', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return re.sub(r'[*_`]', '', text).strip()


def wrapped(draw, text, font, width):
    lines, current = [], ''
    for word in text.split():
        trial = (current+' '+word).strip()
        if draw.textlength(trial, font=font) > width and current:
            lines.append(current)
            current = word
        else:
            current = trial
    return lines+[current] if current else lines


def frame(piece, number, data, destination, as_of):
    bg, ink, muted, accent = '#F5F3EA', '#112E36', '#48636A', '#007F78'
    canvas = Image.new('RGB', (1280,720), bg)
    draw = ImageDraw.Draw(canvas)
    fontdir = Path('C:/Windows/Fonts')
    regular = lambda n: ImageFont.truetype(str(fontdir/'arial.ttf'), n)
    bold = lambda n: ImageFont.truetype(str(fontdir/'arialbd.ttf'), n)
    draw.rectangle((0,0,1280,12), fill=accent)
    draw.text((64,43),'THE SMALL BUSINESS RESEARCH BRIEF',font=bold(20),fill=ink)
    draw.text((965,45),f'BRIEF {piece}  /  {number+1:02d}',font=regular(20),fill=muted)
    eyebrow, headline, bullets, source = data
    draw.text((64,112),eyebrow,font=bold(18),fill=accent)
    y=154
    for line in wrapped(draw,headline,bold(48),1125):
        draw.text((61,y),line,font=bold(48),fill=ink)
        y+=57
    y=max(y+30,285)
    for index,bullet in enumerate(bullets):
        draw.rounded_rectangle((64,y,104,y+38),radius=10,fill=accent)
        draw.text((77,y+6),str(index+1),font=bold(21),fill='white')
        lines=wrapped(draw,bullet,regular(28),1030)
        for offset,line in enumerate(lines):
            draw.text((126,y+offset*35),line,font=regular(28),fill=ink)
        y+=max(64,len(lines)*35+18)
    draw.line((64,562,1216,562),fill='#D1DAD6',width=2)
    for n,line in enumerate(wrapped(draw,source,regular(18),1110)):
        draw.text((64,579+n*23),line,font=regular(18),fill=muted)
    draw.text((64,630),f'Evidence as of {as_of}  ·  AI-assisted draft + synthetic narration',font=regular(17),fill=muted)
    draw.text((64,659),'REVIEW COPY · GOOGLE VIDS / HEYGEN PRODUCTION PENDING',font=bold(15),fill=accent)
    for i in range(6):
        draw.ellipse((1070+i*24,659,1080+i*24,669),fill=accent if i<=number else '#C7D1CB')
    canvas.save(destination)


def prepare(run):
    if run.name != '20261010T052912Z-1d2e8a':
        raise ValueError('These storyboards match the October 10 series. Update them against the new briefs before rendering another run.')
    folder=run/'video_previews'
    for name in ['frames','audio','segments']:
        (folder/name).mkdir(parents=True,exist_ok=True)
    jobs=[]
    meta=read_json(run/'run.json')
    for pid in ['01','02','03']:
        script=(run/'video_scripts'/f'{pid}.md').read_text(encoding='utf-8')
        narrations=[clean(text) for text in re.findall(r'\*\*Narration:\*\*(.*?)(?=\*\*Visual:|\n#{1,3} |\Z)',script,re.S)]
        if len(narrations)!=6:
            raise ValueError(f'{pid}: expected six narration scenes')
        for i,(narration,data) in enumerate(zip(narrations,STORYBOARDS[pid])):
            if pid=='03':
                narration=narration.replace('WEX','Wex')
            # Source-review tasks belong in the production checklist, not speech.
            narration=narration.replace('The student will produce and review the video in Google Vids before publication.','')
            name=f'{pid}-{i+1:02d}'
            frame(pid,i,data,folder/'frames'/f'{name}.png',meta['as_of_date'])
            jobs.append(dict(piece_id=pid,scene=i+1,text=narration,
                             wav=str(folder/'audio'/f'{name}.wav'),frame=f'frames/{name}.png'))
        description=script.split('## Draft YouTube description',1)[-1].strip()
        atomic_text(folder/f'{pid}-youtube-description.md',description+'\n')
        article=(run/'articles'/f'{pid}.md').read_text(encoding='utf-8')
        atomic_text(folder/f'{pid}-article.md',re.sub(r'\s*\[claim:[^\]]+\]','',article))
    write_json(folder/'narration.json',jobs)
    atomic_text(folder/'README.md', '# Local video review copies\n\nThese MP4s use the October 10 evidence and scripts, Windows synthetic narration, '
      'and locally rendered graphics. They have not been produced in Google Vids or HeyGen and are not published. '
      'Import the MP4s or individual scenes into Google Vids, verify captions/timing/source quotations, and export '
      'the final three videos there to complete that assignment requirement. Source URLs are in the descriptions. '
      'The review-copy footer is intentionally visible; remove it only during final production after review.\n')
    print(folder/'narration.json')


def stamp(seconds):
    value=int(round(seconds*1000)); hours,value=divmod(value,3600000); minutes,value=divmod(value,60000); sec,ms=divmod(value,1000)
    return f'{hours:02d}:{minutes:02d}:{sec:02d},{ms:03d}'


def render(run):
    folder=run/'video_previews'
    jobs=read_json(folder/'narration.json')
    exe=ffmpeg_binary()
    output=[]
    for pid in ['01','02','03']:
        scenes=[job for job in jobs if job['piece_id']==pid]
        durations=[]
        for job in scenes:
            with wave.open(job['wav'],'rb') as audio:
                durations.append(audio.getnframes()/audio.getframerate())
        # Keep the video comfortably within the required 3–5 minute range.
        speech_total=sum(durations)
        tempo=max(0.8,min(1.25,speech_total/240)) if not 180<=speech_total+12<=285 else 1.0
        elapsed=0; captions=[]; concat=[]
        for i,(job,duration) in enumerate(zip(scenes,durations)):
            speech_duration=duration/tempo
            total=speech_duration+2
            name=f'{pid}-{i+1:02d}'
            destination=folder/'segments'/f'{name}.mp4'
            command=[exe,'-y','-v','error','-loop','1','-framerate','15','-i',job['frame'],
                     '-i',job['wav'],'-af',f'atempo={tempo:.6f},apad=pad_dur=2',
                     '-t',f'{total:.3f}','-c:v','libx264','-preset','ultrafast','-crf','23',
                     '-tune','stillimage','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',str(destination)]
            subprocess.run(command,cwd=folder,check=True)
            words=job['text'].split()
            for start in range(0,len(words),13):
                chunk=words[start:start+13]
                begin=elapsed+speech_duration*start/len(words)
                end=elapsed+speech_duration*min(start+13,len(words))/len(words)
                captions.append(f'{len(captions)+1}\n{stamp(begin)} --> {stamp(end)}\n'+ ' '.join(chunk)+'\n')
            elapsed+=total
            concat.append(f"file 'segments/{name}.mp4'")
        atomic_text(folder/f'{pid}-concat.txt','\n'.join(concat)+'\n')
        atomic_text(folder/f'{pid}-captions.srt','\n'.join(captions))
        destination=folder/f'{pid}-video.mp4'
        subprocess.run([exe,'-y','-v','error','-f','concat','-safe','0','-i',f'{pid}-concat.txt',
                        '-i',f'{pid}-captions.srt','-map','0:v','-map','0:a','-map','1:0',
                        '-c:v','copy','-c:a','copy','-c:s','mov_text','-metadata:s:s:0','language=eng',
                        '-movflags','+faststart',str(destination)],cwd=folder,check=True)
        if not 180<=elapsed<=300:
            raise ValueError(f'{pid}: runtime {elapsed:.1f}s outside 3–5 minutes')
        output.append(dict(piece_id=pid,file=destination.name,duration_seconds=round(elapsed,2),
                           bytes=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                           narration='Microsoft Zira Desktop; synthetic voice',
                           captions='Word-weighted scene timing; verify in final video editor',
                           status='local_review_copy; Google Vids/HeyGen production pending'))
        print(f'Rendered {pid}: {elapsed:.1f}s',flush=True)
    write_json(folder/'manifest.json',output)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','render'])
    parser.add_argument('run')
    args=parser.parse_args()
    run=(ROOT/args.run).resolve()
    if not run.is_relative_to(ROOT):
        raise ValueError('Run must be inside the repository')
    (prepare if args.action=='prepare' else render)(run)
