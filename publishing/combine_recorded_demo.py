"""Join the student's two screen recordings into an edited technical demonstration.

Inputs remain local. The edit list and source hashes document cuts and playback speed.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw,ImageFont
from lib.media_tools import ffmpeg_binary
from publishing.render_videos import stamp

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.tools/recorded-demo'
OUT=ROOT/'deliverables/recorded-demo'
SOURCES={1:Path('C:/Users/hp/Downloads/MicrosoftTeams-video.mp4'),2:Path('C:/Users/hp/Downloads/MicrosoftTeams-video (1).mp4')}
# Cuts preserve the student's meaning; shorter navigation/repeated transitions are omitted.
EDITS=[
 (1,0.8,41.8,'Project and audience'),
 (1,48.0,128.8,'Architecture and entry point'),
 (1,149.6,170.5,'Published claim and evidence trail'),
 (1,171.0,212.9,'Published claim and evidence trail'),
 (1,231.4,257.8,'Two runs | Parley cost: $0.80, student reported'),
 (1,267.5,288.95,'Two runs | Parley cost: $0.80, student reported'),
 (2,11.75,60.6,'Duplicate handling and assisted recovery'),
 (2,86.0,128.0,'Student feedback and policy revision'),
 (2,136.5,159.6,'Student feedback and policy revision'),
 (2,165.0,173.64,'Architectural tradeoff and reflection'),
 (2,175.8,176.95,'Architectural tradeoff and reflection'),
 (2,179.4,215.95,'Architectural tradeoff and reflection'),
 (2,216.5,247.5,'Architectural tradeoff and reflection'),
 (2,248.3,270.0,'Source approval confirmed by the student'),
]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ff=str(ffmpeg_binary());total=sum(b-a for _,a,b,_ in EDITS)
    speed=max(1.0,total/352)
    if speed>1.3:raise ValueError('Edit is too long for modest speed adjustment')
    frames=[];captions=[];timeline=[];offset=0
    for i,(part,start,end,title) in enumerate(EDITS):
        duration=(end-start)/speed
        bar=Image.new('RGBA',(1280,44),'#12333C');draw=ImageDraw.Draw(bar)
        draw.text((20,10),title,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',22),fill='white')
        barpath=WORK/f'bar-{i:02}.png';bar.save(barpath)
        segment=WORK/f'cut-{i:02}.mp4'
        filters=f'[0:v]setpts=(PTS-STARTPTS)/{speed},fps=15[v];[v][1:v]overlay=0:0[out];[0:a]asetpts=PTS-STARTPTS,atempo={speed},afade=t=in:d=0.012,afade=t=out:st={max(0,duration-.012)}:d=0.012[a]'
        subprocess.run([ff,'-y','-v','error','-ss',str(start),'-t',str(end-start),'-i',str(SOURCES[part]),'-i',str(barpath),'-filter_complex',filters,'-map','[out]','-map','[a]','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',str(segment)],check=True)
        timeline.append(dict(part=part,input_start=start,input_end=end,output_start=round(offset,3),output_duration=round(duration,3),section=title))
        rows=json.loads((WORK/f'part{part}.json').read_text(encoding='utf-8'))
        words=[w for row in rows for w in row['words'] if w['start']>=start and w['end']<=end]
        for j in range(0,len(words),10):
            chunk=words[j:j+10]
            text=''.join(w['word'] for w in chunk).strip()
            text=text.replace('Ming Shiwong','Mingxi Wang').replace('SQL light','SQLite').replace('SQL light','SQLite')
            captions.append(f'{len(captions)+1}\n{stamp(offset+(chunk[0]["start"]-start)/speed)} --> {stamp(offset+(chunk[-1]["end"]-start)/speed)}\n{text}\n')
        offset+=duration
        print(f'Edited section {i+1}/{len(EDITS)}',flush=True)
    concat=WORK/'recorded-concat.txt';concat.write_text('\n'.join(f"file 'cut-{i:02}.mp4'" for i in range(len(EDITS))),encoding='utf-8')
    srt=OUT/'captions.srt';srt.write_text('\n'.join(captions),encoding='utf-8')
    video=OUT/'technical-demo.mp4'
    subprocess.run([ff,'-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-i',str(srt),'-map','0:v','-map','0:a','-map','1:0','-c:v','copy','-c:a','aac','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart',str(video)],check=True)
    subprocess.run([ff,'-v','error','-i',str(video),'-map','0:v','-map','0:a','-f','null','-'],check=True)
    sheet=Image.new('RGB',(1280,1080),'white')
    for i,t in enumerate([15,65,125,185,245,315]):
        image=WORK/f'final-{t}.png'
        subprocess.run([ff,'-y','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1',str(image)],check=True)
        sheet.paste(Image.open(image).resize((640,360)),((i%2)*640,(i//2)*360))
    sheet.save(OUT/'contact-sheet.png')
    manifest=dict(created_on='2026-10-18',narrator='Mingxi Wang; student-recorded speech',source_files=[dict(part=k,file=v.name,sha256=hashlib.sha256(v.read_bytes()).hexdigest()) for k,v in SOURCES.items()],editing='Navigation/repeated transitions removed; original speech and screen sequence retained; pitch-preserving speed adjustment and volume normalization',playback_speed=speed,duration_seconds=round(offset,2),timeline=timeline,sha256=hashlib.sha256(video.read_bytes()).hexdigest(),bytes=video.stat().st_size,full_decode='passed',captions='Optional automatic Whisper captions; may contain recognition errors')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('FINAL',round(offset,2),'seconds;',round(speed,3),'x;',video.stat().st_size,'bytes')

if __name__=='__main__':main()
