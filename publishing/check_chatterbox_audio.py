"""Transcribe generated narration locally to flag omissions/repetitions for review."""
import json
from pathlib import Path
import re
import sys
import wave
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from publishing.chatterbox_videos import ROOT,WORK,OUT

def normalized(text):
    return re.findall(r'[a-z0-9]+',text.lower())

def distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a):
        current=[i+1]
        for j,y in enumerate(b):current.append(min(current[-1]+1,previous[j+1]+1,previous[j]+(x!=y)))
        previous=current
    return previous[-1]

def main():
    from faster_whisper import WhisperModel
    model=WhisperModel('base.en',device='cpu',compute_type='int8',download_root=str(ROOT/'.tools/models'))
    result=[]
    jobs=json.loads((WORK/'jobs.json').read_text(encoding='utf-8'))
    for job in jobs:
        for chunk in job['chunks']:
            path=WORK/chunk['file']
            if '--watch' in sys.argv:
                deadline=time.monotonic()+1800
                while not path.exists() and time.monotonic()<deadline:time.sleep(3)
                # Generation writes the complete short WAV before proceeding.
                time.sleep(.5)
            if not path.exists():continue
            segments,info=model.transcribe(str(path),language='en',beam_size=5)
            actual=' '.join(s.text.strip() for s in segments)
            expected=normalized(chunk['text']);observed=normalized(actual)
            rate=distance(expected,observed)/max(1,len(expected))
            with wave.open(str(path)) as w:seconds=w.getnframes()/w.getframerate()
            row=dict(file=chunk['file'],expected=chunk['text'],transcribed=actual,word_error_rate=round(rate,3),duration_seconds=round(seconds,2),flag=rate>.25)
            result.append(row)
            print(chunk['file'],f'WER={rate:.2f}', 'REVIEW' if row['flag'] else 'ok',flush=True)
    write=dict(method='Local Whisper base.en back-transcription; automated screening, not a listening or speaker-similarity judgment',checked_chunks=len(result),flagged_chunks=sum(r['flag'] for r in result),chunks=result)
    (OUT/'audio_checks.json').write_text(json.dumps(write,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
