"""Local, disclosed voice-cloned revisions; original published artifacts are untouched.

Run prepare/render with the pipeline Python; synthesize with the isolated Chatterbox Python.
Voice reference, checkpoints, and intermediate audio remain in ignored .tools/.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
WORK=ROOT/'.tools/chatterbox-production'
OUT=ROOT/'deliverables/20261017-chatterbox'
SOURCE=ROOT/'runs/20261010T052912Z-1d2e8a/video_previews'

def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def prepare():
    from PIL import Image,ImageDraw,ImageFont
    from publishing.render_technical_demo import SCENES,slide
    import publishing.render_technical_demo as demo
    WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    frames=WORK/'frames';frames.mkdir(exist_ok=True)
    jobs=json.loads((SOURCE/'narration.json').read_text(encoding='utf-8'))
    for job in jobs:
        job['frame']=str(SOURCE/job['frame'])
        job.pop('wav',None)
    demo.WORK=frames
    technical=[]
    for i,(title,bullets,source,text) in enumerate(SCENES):
        bullets=[b.replace('Prepared October 16, 2026','Revised October 17, 2026') for b in bullets]
        text=text.replace('and it does not substitute for the student reviewing the work or explaining the architecture.', 'and the narration is AI-generated using the student’s supplied voice recording.')
        if i==6:
            bullets[-1]='Reflection recorded; source review + production pending'
            text=text.replace('and the student reflection.', 'and final human approval. The student’s reflection is now recorded in the submission.')
        demo.slide(i,title,bullets,source)
        technical.append(dict(piece_id='04',scene=i+1,text=text,frame=str(frames/f'{i:02}.png')))
    # Actual grouped architecture diagram, not a simulated terminal screenshot.
    im=Image.new('RGB',(1280,720),'#F5F3EA');d=ImageDraw.Draw(im)
    font=lambda n,b=False:ImageFont.truetype('C:/Windows/Fonts/arial'+('bd' if b else '')+'.ttf',n)
    d.text((42,30),'PIPELINE ARCHITECTURE',font=font(35,True),fill='#112E36')
    d.text((42,83),'Entry: bash run.sh  |  JSON Lines between independently runnable stages',font=font(23),fill='#48636A')
    boxes=[('1  Collect sources',['fetch_feeds.sh','fetch_youtube.sh','fetch_podcasts.sh']),('2  Extract + retain',['extract_content.sh','data/store.sh','Immutable evidence + SQLite']),('3  Filter + select',['filter_items.sh: 30-day window','select_items.sh: policy + AI']),('4  Build arguments',['create_briefs.sh','Exact source / version / quote']),('5  Draft + check',['write_articles.sh','write_video_scripts.sh','check_content.sh']),('6  Review + handoff',['Human approval fingerprint','prepare_package.sh','Manual platform publication'])]
    for i,(heading,lines) in enumerate(boxes):
        x=42+(i%3)*410;y=145+(i//3)*205
        d.rounded_rectangle((x,y,x+380,y+175),radius=14,fill='#E1ECE7',outline='#007F78',width=2)
        d.text((x+15,y+16),heading,font=font(24,True),fill='#112E36')
        for j,line in enumerate(lines):d.text((x+15,y+61+j*31),line,font=font(20),fill='#112E36')
        if i%3<2:d.text((x+384,y+69),'→',font=font(27,True),fill='#007F78')
    d.text((42,552),'Video: scripts + private voice → Chatterbox Nano → FFmpeg + captions → review',font=font(22),fill='#007F78')
    d.text((42,589),'Coordinators: collect_sources.sh + create_series.sh; reporting: summarize_run.sh',font=font(20),fill='#48636A')
    d.text((42,619),'Local renders are separate from Google Vids/HeyGen production and platform uploads.',font=font(19),fill='#48636A')
    im.save(frames/'architecture.png');technical[1]['frame']=str(frames/'architecture.png')
    jobs+=technical
    for job in jobs:
        key=f"{job['piece_id']}-{job['scene']:02}"
        im=Image.open(job['frame']).convert('RGB');d=ImageDraw.Draw(im)
        d.rectangle((0,625 if job['piece_id']!='04' else 644,1280,720),fill='#F5F3EA')
        d.text((42,652),'AI-generated narration using the student’s supplied voice • Chatterbox Nano',font=font(19,True),fill='#007F78')
        label='Evidence: 2026-10-10 • Local revision; Google Vids/HeyGen production unverified' if job['piece_id']!='04' else 'Saved-artifact walkthrough • Revised 2026-10-17 • Source review remains pending'
        d.text((42,685),label,font=font(17),fill='#48636A')
        im.save(frames/f'{key}.png');job['frame']=f'frames/{key}.png'
        sentences=re.split(r'(?<=[.!?])\s+',job['text'])
        chunks=[];current=''
        for sentence in sentences:
            if current and len((current+' '+sentence).split())>45:
                chunks.append(current);current=''
            current=(current+' '+sentence).strip()
        if current:chunks.append(current)
        job['chunks']=[dict(text=t,file=f'audio/{key}-{n:02}.wav') for n,t in enumerate(chunks)]
    write(WORK/'jobs.json',jobs)
    (WORK/'audio').mkdir(exist_ok=True)
    for pid in ['01','02','03','04']:
        scenes=[j for j in jobs if j['piece_id']==pid]
        (OUT/f'{pid}-script.md').write_text('# Voice-cloned video '+pid+'\n\nAI-generated narration using the student’s supplied voice; Chatterbox Nano.\n\n'+'\n\n'.join(f'## Scene {j["scene"]}\n\n{j["text"]}' for j in scenes)+'\n',encoding='utf-8')
    print('Prepared',len(jobs),'scenes;',sum(len(j['chunks']) for j in jobs),'speech chunks')

def synthesize(limit=None):
    os.environ['HF_HOME']=str(ROOT/'.tools/chatterbox/hf')
    os.environ['HF_HUB_DISABLE_XET']='1'
    os.environ['TQDM_DISABLE']='1'
    import torch,soundfile as sf
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    torch.set_num_threads(8);torch.manual_seed(17)
    model=ChatterboxTurboTTS.from_local(ROOT/'.tools/chatterbox/models/nano',device='cpu',nano=True)
    model.prepare_conditionals(str(ROOT/'.tools/voice-reference/reference.wav'))
    jobs=json.loads((WORK/'jobs.json').read_text(encoding='utf-8'))
    count=0
    for job in jobs:
        for chunk in job['chunks']:
            target=WORK/chunk['file']
            if target.exists():continue
            wav=model.generate(chunk['text'])
            sf.write(str(target),wav.squeeze().numpy(),model.sr,subtype='PCM_16')
            print('Generated',chunk['file'],round(len(wav.squeeze())/model.sr,2),'seconds',flush=True)
            count+=1
            if limit and count>=limit:return

def render(pieces=None):
    from PIL import Image
    from lib.media_tools import ffmpeg_binary
    from publishing.render_videos import stamp
    ff=str(ffmpeg_binary());jobs=json.loads((WORK/'jobs.json').read_text(encoding='utf-8'))
    prior=OUT/'manifest.json'
    manifest=json.loads(prior.read_text(encoding='utf-8')) if prior.exists() else []
    for pid in (pieces or ['01','02','03','04']):
        manifest=[row for row in manifest if row['piece_id']!=pid]
        scenes=[j for j in jobs if j['piece_id']==pid]
        durations=[]
        for job in scenes:
            ds=[]
            for chunk in job['chunks']:
                with wave.open(str(WORK/chunk['file'])) as w:ds.append(w.getnframes()/w.getframerate())
            durations.append(ds)
        total=sum(sum(ds) for ds in durations)+len(scenes)
        target=285 if pid=='04' else 245
        lo,hi=(240,355) if pid=='04' else (180,295)
        tempo=1 if lo<=total<=hi else (total-len(scenes))/(target-len(scenes))
        if not .8<=tempo<=1.25:raise ValueError(f'{pid}: narration pacing needs review: tempo={tempo}')
        elapsed=0;caps=[];segments=[]
        for job,ds in zip(scenes,durations):
            key=f'{pid}-{job["scene"]:02}'
            wavs=[WORK/c['file'] for c in job['chunks']]
            combined=WORK/f'{key}.wav'
            with wave.open(str(combined),'wb') as dest:
                for n,p in enumerate(wavs):
                    with wave.open(str(p)) as src:
                        if n==0:dest.setparams(src.getparams())
                        dest.writeframes(src.readframes(src.getnframes()))
            for chunk,duration in zip(job['chunks'],ds):
                words=chunk['text'].split();duration/=tempo
                for start in range(0,len(words),11):
                    caps.append(f'{len(caps)+1}\n{stamp(elapsed+duration*start/len(words))} --> {stamp(elapsed+duration*min(start+11,len(words))/len(words))}\n'+ ' '.join(words[start:start+11])+'\n')
                elapsed+=duration
            elapsed+=1
            segment=WORK/f'{key}.mp4';segments.append(segment)
            subprocess.run([ff,'-y','-v','error','-loop','1','-framerate','10','-i',str(WORK/job['frame']),'-i',str(combined),'-af',f'atempo={tempo},apad=pad_dur=1','-t',str(sum(ds)/tempo+1),'-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',str(segment)],check=True)
        captions=OUT/f'{pid}-captions.srt';captions.write_text('\n'.join(caps),encoding='utf-8')
        concat=WORK/f'{pid}-concat.txt';concat.write_text('\n'.join("file '"+p.name+"'" for p in segments),encoding='utf-8')
        video=OUT/f'{pid}-video.mp4'
        subprocess.run([ff,'-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-i',str(captions),'-map','0:v','-map','0:a','-map','1:0','-c','copy','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart',str(video)],check=True)
        subprocess.run([ff,'-v','error','-i',str(video),'-map','0:v','-map','0:a','-f','null','-'],check=True)
        sheet=Image.new('RGB',(1280,360*((len(scenes)+1)//2)),'white')
        for n,job in enumerate(scenes):sheet.paste(Image.open(WORK/job['frame']).resize((640,360)),((n%2)*640,(n//2)*360))
        sheet.save(OUT/f'{pid}-storyboard.png')
        manifest.append(dict(piece_id=pid,file=video.name,duration_seconds=round(elapsed,2),tempo=tempo,sha256=hashlib.sha256(video.read_bytes()).hexdigest(),bytes=video.stat().st_size,full_decode='passed',narration='Chatterbox Nano; AI-generated using student-supplied voice',captions='Chunk-based approximate timing; playback review advised',publication='local revision, not uploaded',source_run='20261010T052912Z-1d2e8a' if pid!='04' else 'Saved October 10 and October 16 records; architecture as of October 17'))
        print('Rendered',pid,round(elapsed,2),'seconds',flush=True)
    write(OUT/'manifest.json',sorted(manifest,key=lambda row:row['piece_id']))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','synthesize','render']);parser.add_argument('--limit',type=int);parser.add_argument('--pieces',nargs='+',choices=['01','02','03','04'])
    args=parser.parse_args()
    if args.action=='synthesize':synthesize(args.limit)
    elif args.action=='render':render(args.pieces)
    else:globals()[args.action]()
