"""Offline contract/integration tests. All test evidence and approvals are fictional."""
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
BASH = 'C:/Program Files/Git/bin/bash.exe' if os.name=='nt' else 'bash'


def dump(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2),encoding='utf-8')


def lines(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')


def readlines(p):
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        work = ROOT/'tests/.work'
        work.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=work)
        self.repo = Path(self.temp.name)
        for directory in ['lib','collectors','processing','editorial','content','review','publishing','reporting','workflows','config','prompts','examples']:
            shutil.copytree(ROOT/directory,self.repo/directory,ignore=shutil.ignore_patterns('__pycache__'))
        (self.repo/'data').mkdir()
        for name in ['store.py','store.sh']:
            shutil.copy2(ROOT/'data'/name,self.repo/'data'/name)
        shutil.copy2(ROOT/'run.sh',self.repo/'run.sh')
        self.run = self.repo/'runs/test'
        self.run.mkdir(parents=True)
        shutil.copytree(self.repo/'config',self.run/'config')
        shutil.copytree(self.repo/'prompts',self.run/'prompts')
        dump(self.run/'run.json',dict(run_id='test',mode='example',started_at='2026-10-08T12:00:00Z',
                                     as_of_date='2026-10-08',previous_run_id=None))

    def tearDown(self):
        self.temp.cleanup()

    def cmd(self,script,*args,input='',code=0):
        env = dict(os.environ,PIPELINE_PYTHON=sys.executable,PIPELINE_BASH=BASH,PIPELINE_RUN_DIR='runs/test')
        result = subprocess.run([BASH,script,*args],cwd=self.repo,env=env,input=input,capture_output=True,
                                text=True,encoding='utf-8',timeout=60)
        self.assertEqual(result.returncode,code,result.stderr+'\n'+result.stdout[:1000])
        return result.stdout

    def test_store_replay_and_old_version(self):
        self.cmd('data/store.sh','init')
        first = self.cmd('data/store.sh','upsert','runs/test',input=(self.repo/'examples/items.jsonl').read_text())
        self.assertEqual([json.loads(l) for l in first.splitlines()],readlines(self.repo/'examples/initial_changes_expected.jsonl'))
        replay = self.cmd('data/store.sh','upsert','runs/test',input=(self.repo/'examples/replay_items.jsonl').read_text())
        self.assertEqual([json.loads(l) for l in replay.splitlines()],readlines(self.repo/'examples/replay_changes_expected.jsonl'))
        self.assertEqual(len(self.cmd('data/store.sh','list').splitlines()),3)
        old = readlines(self.repo/'examples/items.jsonl')[2]
        recovered = json.loads(self.cmd('data/store.sh','get',old['item_id'],old['version_id']))
        self.assertEqual(recovered['text_path'],old['text_path'])

    def test_store_collision_rolls_back_and_rejects_bad_json(self):
        rows=readlines(self.repo/'examples/items.jsonl')
        self.cmd('data/store.sh','upsert','runs/test',input=json.dumps(rows[0])+'\n')
        corrupt=dict(rows[0],title='Content changed but version did not')
        self.cmd('data/store.sh','upsert','runs/test',input=json.dumps(rows[1])+'\n'+json.dumps(corrupt)+'\n',code=2)
        self.assertEqual(len(self.cmd('data/store.sh','list').splitlines()),1)
        self.cmd('data/store.sh','upsert','runs/test',input='{bad json}',code=2)

    def test_interleaved_duplicate_does_not_revert_latest(self):
        original=readlines(self.repo/'examples/items.jsonl')[0]
        revised=dict(original,version_id='revised-version',title='A genuinely changed fixture')
        output=self.cmd('data/store.sh','upsert','runs/test',input=''.join(json.dumps(r)+'\n' for r in [original,revised,original]))
        self.assertEqual([json.loads(l)['change'] for l in output.splitlines()],['new','changed','unchanged'])
        latest=json.loads(self.cmd('data/store.sh','get',original['item_id']))
        self.assertEqual(latest['version_id'],'revised-version')

    def test_filter_inclusive_dates_and_unknowns(self):
        result=self.cmd('processing/filter_items.sh','runs/test',input=(self.repo/'examples/filter_input.jsonl').read_text())
        expected=json.loads((self.repo/'examples/filter_expected.json').read_text())
        self.assertEqual({json.loads(l)['item_id'] for l in result.splitlines()},set(expected['eligible_item_ids']))
        actual=readlines(self.run/'exclusions.jsonl')
        self.assertEqual({(r['item_id'],r['reason']) for r in actual},{(r['item_id'],r['reason']) for r in expected['exclusions']})
        self.assertTrue(list((self.run/'logs').glob('*filter_items*.json')))

    def test_empty_incomplete_run_summary(self):
        assessment=json.loads(self.cmd('review/check_content.sh','runs/test'))
        self.assertFalse(assessment['passed'])
        dump(self.run/'review.json',assessment)
        summary=json.loads(self.cmd('reporting/summarize_run.sh','runs/test'))
        self.assertEqual(summary['status'],'failed')
        self.assertIsNone(summary['counts']['articles'])
        self.assertIsNone(summary['counts']['discovered'])

    def test_collector_partial_failure_is_preserved(self):
        feed=self.repo/'written.xml'
        feed.write_text('<rss version="2.0"><channel><title>Fictional</title><item><title>Fictional written item</title><link>https://example.test/article</link><guid>one</guid><pubDate>Wed, 07 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>')
        good=dict(source_id='good',publisher_id='fictional',kind='feed',url=feed.as_uri())
        bad=dict(source_id='bad',publisher_id='fictional-bad',kind='feed',url=(self.repo/'missing.xml').as_uri())
        dump(self.run/'config/sources.json',[good,bad])
        output=self.cmd('collectors/fetch_feeds.sh','runs/test',code=1)
        self.assertEqual(len(output.splitlines()),1)
        receipt=json.loads(next((self.run/'logs').glob('*fetch_feeds*.json')).read_text(encoding='utf-8'))
        self.assertEqual(receipt['status'],'incomplete')
        self.assertTrue(receipt['errors'])

    def fixture_series(self):
        items=[]
        for n in range(12):
            kind=['feed','youtube','podcast'][n%3]
            text=f'Fictional evidence passage {n}; this is not real research. '+('Additional fictional methods and limitations. '*35)
            asset=self.repo/'data/assets'/str(n)
            asset.mkdir(parents=True)
            (asset/'text.txt').write_text(text)
            segments=None
            if kind!='feed':
                segments=f'data/assets/{n}/segments.json'
                dump(self.repo/segments,[dict(segment_id='s1',start_seconds=10,end_seconds=20,text=text)])
            items.append(dict(item_id=f'{kind}:fixture-{n}',source_id=f'source-{n}',publisher_id=f'publisher-{n%6}',kind=kind,
                 title=f'Fictional evidence {n}',url=f'https://example.test/{n}',published_at='2026-10-07T12:00:00Z',
                 retrieved_at='2026-10-08T12:00:00Z',media_url=f'https://example.test/{n}.mp3' if kind!='feed' else None,
                 version_id=f'v{n}',text_path=f'data/assets/{n}/text.txt',segments_path=segments))
        lines(self.run/'eligible.jsonl',items)
        lines(self.run/'items.jsonl',items)
        self.cmd('data/store.sh','upsert','runs/test',input=''.join(json.dumps(r)+'\n' for r in items))
        decisions=[dict(item_id=r['item_id'],version_id=r['version_id'],decision='accept',reason='Fictional test only',piece_ids=['01','02','03']) for r in items]
        lines(self.run/'decisions.jsonl',decisions)
        briefs=[]
        manifests={'articles':[],'video_scripts':[]}
        for pid in ['01','02','03']:
            evidence=[]
            for r in items[:3]:
                locator=dict(type='text',quote='Fictional evidence passage 0; this is not real research.') if r['kind']=='feed' else dict(type='segment',segment_id='s1')
                evidence.append(dict(item_id=r['item_id'],version_id=r['version_id'],locator=locator))
            claim=dict(claim_id=pid+'-c1',statement='Fictional synthesis.',type='inference',evidence=evidence)
            briefs.append(dict(piece_id=pid,title='Fictional '+pid,question='Question '+pid,argument='Distinct argument '+pid,
                               synthesis='Fictional reasoning across sources.',limitations='Entirely fictional fixture.',claims=[claim]))
            for folder in manifests:
                target=self.run/folder/(pid+'.md')
                target.parent.mkdir(exist_ok=True)
                body=f'# Fictional {pid}\nAs of 2026-10-08\n[claim:{pid}-c1]\n'+ '\n'.join(f"[Source {i}]({r['url']})" for i,r in enumerate(items[:3]))
                target.write_text(body,encoding='utf-8')
                manifests[folder].append(dict(piece_id=pid,path=target.relative_to(self.repo).as_posix(),claim_ids=[pid+'-c1']))
        lines(self.run/'briefs.jsonl',briefs)
        for folder,rows in manifests.items():
            lines(self.run/(folder+'.jsonl'),rows)
        return items

    def test_brief_correction_uses_exact_evidence_and_preserves_initial_answer(self):
        sys.path.insert(0,str(ROOT))
        from editorial.create_briefs import checked_briefs
        from lib.common import Receipt
        items = self.fixture_series()
        valid = readlines(self.run/'briefs.jsonl')
        invalid = copy.deepcopy(valid)
        invalid[0]['claims'][0]['evidence'][0]['locator']['quote'] = 'Invented quotation'
        decisions = readlines(self.run/'decisions.jsonl')
        with patch('lib.common.ROOT',self.repo), patch('editorial.create_briefs.infer',side_effect=[
            {'briefs':invalid,'error':''},{'briefs':valid,'error':''}]) as inference:
            actual = checked_briefs(self.run,'Fictional instructions',{'evidence':'fixture'},items,decisions,
                                    Receipt(self.run,'fictional_repair'))
        self.assertEqual(actual,valid)
        self.assertEqual(inference.call_count,2)
        repair = inference.call_args.args
        self.assertEqual(repair[1],'create_briefs_repair')
        self.assertTrue(repair[3]['validation_errors'])
        self.assertEqual(repair[3]['invalid_text_references'][0]['reference']['locator']['quote'],'Invented quotation')
        self.assertEqual(invalid[0]['claims'][0]['evidence'][0]['locator']['quote'],'Invented quotation')

    def test_brief_correction_is_bounded_and_still_rejects_unsupported_quotes(self):
        sys.path.insert(0,str(ROOT))
        from editorial.create_briefs import checked_briefs
        from lib.common import Receipt
        items = self.fixture_series()
        invalid = readlines(self.run/'briefs.jsonl')
        invalid[0]['claims'][0]['evidence'][0]['locator']['quote'] = 'Invented quotation'
        decisions = readlines(self.run/'decisions.jsonl')
        with patch('lib.common.ROOT',self.repo), patch('editorial.create_briefs.infer',return_value={
            'briefs':invalid,'error':''}) as inference:
            with self.assertRaisesRegex(ValueError,'after one correction attempt'):
                checked_briefs(self.run,'Fictional instructions',{},items,decisions,Receipt(self.run,'fictional_repair'))
        self.assertEqual(inference.call_count,2)

    def test_citation_links_survive_internal_marker_removal(self):
        sys.path.insert(0,str(ROOT))
        import re
        from content.support import format_citations
        items = [dict(publisher_id='fixture-publisher',title='Fictional source',url='https://example.test/source')]
        result = format_citations('Supported statement [claim:01-c1](https://example.test/source)',items)
        audience_copy = re.sub(r'\s*\[claim:[^\]]+\]','',result)
        self.assertIn('[Fixture Publisher](https://example.test/source)',audience_copy)
        self.assertNotIn('claim:',audience_copy)
        self.assertIn('[Fictional source](https://example.test/source)',format_citations('Draft with missing bibliography',items))

    def test_workflow_fails_when_completed_review_finds_invalid_content(self):
        self.fixture_series()
        for script, manifest in [('editorial/select_items.sh','decisions.jsonl'),
                                 ('editorial/create_briefs.sh','briefs.jsonl'),
                                 ('content/write_articles.sh','articles.jsonl'),
                                 ('content/write_video_scripts.sh','video_scripts.jsonl')]:
            (self.repo/script).write_text('#!/usr/bin/env bash\ncat "$1/'+manifest+'"\n',encoding='utf-8')
        self.cmd('workflows/create_series.sh','runs/test')
        self.assertTrue(json.loads((self.run/'review.json').read_text(encoding='utf-8'))['passed'])
        p=self.run/'articles/01.md'
        p.write_text(p.read_text().replace('[claim:01-c1]','[claim:unsupported]'))
        self.cmd('workflows/create_series.sh','runs/test',code=1)
        self.assertFalse(json.loads((self.run/'review.json').read_text(encoding='utf-8'))['passed'])

    def approve_fixture(self,review):
        dump(self.run/'approval.json',dict(review_id=review['review_id'],decision='approve',reviewer='FICTIONAL TEST ONLY',
                                          reviewed_at='2026-10-08T12:00:00Z',notes='Simulated approval in isolated offline test; not student approval.'))

    def test_package_requires_approval_and_preserves_links(self):
        self.fixture_series()
        review=json.loads(self.cmd('review/check_content.sh','runs/test'))
        self.assertTrue(review['passed'],review['issues'])
        dump(self.run/'review.json',review)
        self.cmd('publishing/prepare_package.sh','runs/test',code=1)
        self.approve_fixture(review)
        manifest=json.loads(self.cmd('publishing/prepare_package.sh','runs/test'))
        self.assertEqual(len(manifest['assets']),9)
        links=self.run/'package/publication_links.json'
        values=json.loads(links.read_text())
        values[0]['substack_url']='https://example.test/fictional-link'
        dump(links,values)
        self.cmd('publishing/prepare_package.sh','runs/test')
        self.assertEqual(json.loads(links.read_text())[0]['substack_url'],values[0]['substack_url'])
        self.assertNotIn('[claim:',(self.run/'package/01-article.md').read_text())

    def test_direct_packaging_blocks_changed_draft(self):
        self.fixture_series()
        review=json.loads(self.cmd('review/check_content.sh','runs/test'))
        self.approve_fixture(review)
        article=self.run/'articles/01.md'
        article.write_text(article.read_text()+'\nChanged after approval.\n')
        new_review=json.loads(self.cmd('review/check_content.sh','runs/test'))
        self.assertNotEqual(review['review_id'],new_review['review_id'])
        self.cmd('publishing/prepare_package.sh','runs/test',code=1)

    def test_tampered_evidence_changes_fingerprint(self):
        items=self.fixture_series()
        review=json.loads(self.cmd('review/check_content.sh','runs/test'))
        target=self.repo/items[0]['text_path']
        target.write_text('Changed source without the quoted passage')
        changed=json.loads(self.cmd('review/check_content.sh','runs/test'))
        self.assertFalse(changed['passed'])
        self.assertNotEqual(review['review_id'],changed['review_id'])

    def test_missing_media_segment_and_source_independence_block(self):
        self.fixture_series()
        dump(self.repo/'data/assets/1/segments.json',[])
        brief=readlines(self.run/'briefs.jsonl')
        brief[0]['claims'][0]['evidence']=brief[0]['claims'][0]['evidence'][:1]
        lines(self.run/'briefs.jsonl',brief)
        review=json.loads(self.cmd('review/check_content.sh','runs/test'))
        self.assertFalse(review['passed'])
        self.assertTrue(any('independent publishers' in i['explanation'] for i in review['issues']))

    def test_invalid_entry_arguments(self):
        self.cmd('run.sh','--unknown',code=2)
        self.cmd('data/store.sh','get',code=2)
        self.cmd('processing/filter_items.sh',code=2)

    def test_failed_live_entry_keeps_summary_and_snapshots(self):
        dump(self.repo/'config/sources.json',[dict(source_id='deliberate-test-failure',publisher_id='fictional',
            kind='feed',url=(self.repo/'missing.xml').as_uri())])
        summary=json.loads(self.cmd('run.sh',code=1))
        self.assertEqual(summary['status'],'failed')
        self.assertFalse(summary['collection_complete'])
        self.assertEqual(summary['counts']['discovered'],0)
        self.assertIsNone(summary['counts']['articles'])
        folder=self.repo/'runs'/summary['run_id']
        self.assertTrue((folder/'config/project.json').is_file())
        self.assertTrue((folder/'prompts/select_items.md').is_file())
        self.assertTrue((folder/'summary.json').is_file())

    def test_youtube_runtime_works_without_path(self):
        sys.path.insert(0,str(ROOT))
        from lib.youtube_runtime import javascript_options
        import yt_dlp
        with patch('lib.youtube_runtime.shutil.which',return_value=None):
            options=javascript_options()
        self.assertIn('deno',options['js_runtimes'])
        self.assertTrue(Path(options['js_runtimes']['deno']['path']).is_file())
        # Exercise yt-dlp's actual runtime discovery without contacting YouTube.
        with yt_dlp.YoutubeDL(dict(quiet=True,**options)) as downloader:
            self.assertIsNotNone(downloader._js_runtimes['deno'].info)

    def test_timestamped_transcript_formats(self):
        sys.path.insert(0,str(ROOT))
        from processing.extract_content import transcript
        vtt=b'WEBVTT\n\n00:01.500 --> 00:04.000\nA timed passage.\n\n'
        parsed=transcript(vtt,'vtt')
        self.assertEqual((parsed[0]['start_seconds'],parsed[0]['end_seconds']),(1.5,4.0))
        json3=json.dumps(dict(events=[dict(tStartMs=2000,dDurationMs=3000,segs=[dict(utf8='Evidence')])])).encode()
        self.assertEqual(transcript(json3,'json3')[0]['text'],'Evidence')
        with self.assertRaises(RuntimeError):
            transcript(b'No timed content','vtt')

    def test_page_date_ignores_refreshed_modified_date(self):
        sys.path.insert(0,str(ROOT))
        from processing.extract_content import original_page_date
        raw=b'<html><head><script type="application/ld+json">{"@type":"Article","url":"https://example.test/a","datePublished":"2020-01-01T00:00:00Z","dateModified":"2026-10-08T00:00:00Z"}</script></head></html>'
        self.assertEqual(original_page_date(raw,'https://example.test/a'),'2020-01-01T00:00:00Z')
        self.assertIsNone(original_page_date(raw,'https://example.test/other'))

    def test_parley_request_usage_schema_and_no_saved_key(self):
        sys.path.insert(0,str(ROOT))
        from lib.common import Receipt
        from lib.model import infer, obj, STRING
        from lib.parley import ENDPOINT
        project=json.loads((self.run/'config/project.json').read_text(encoding='utf-8'))
        project['ai'].update(provider='parley',model='openai')
        dump(self.run/'config/project.json',project)
        reply=dict(model='FICTIONAL-SERVED-MODEL', usage=dict(prompt_tokens=10,completion_tokens=5,total_tokens=15),
                   choices=[dict(finish_reason='stop',message=dict(content='{"answer":"offline fixture"}'))])
        opener=MagicMock()
        opener.open.return_value=io.BytesIO(json.dumps(reply).encode())
        receipt=Receipt(self.run,'parley_test')
        with patch.dict(os.environ,{'PARLEY_API_KEY':'FICTIONAL-SECRET-DO-NOT-SAVE'}), patch('urllib.request.build_opener',return_value=opener):
            result=infer(self.run,'parley','Offline fixture',{},obj(dict(answer=STRING)),receipt)
        self.assertEqual(result,{'answer':'offline fixture'})
        request=opener.open.call_args.args[0]
        self.assertEqual(request.full_url,ENDPOINT)
        self.assertEqual(request.get_header('Authorization'),'Bearer FICTIONAL-SECRET-DO-NOT-SAVE')
        self.assertEqual(json.loads(request.data)['model'],'openai')
        self.assertIsNone(receipt.value['cost_usd'])
        self.assertEqual(receipt.value['usage'][0]['total_tokens'],15)
        self.assertIn('FICTIONAL-SERVED-MODEL',receipt.value['models'])
        saved=''.join(p.read_text(encoding='utf-8') for p in (self.run/'ai_calls').rglob('*') if p.is_file())
        self.assertNotIn('FICTIONAL-SECRET-DO-NOT-SAVE',saved)

    def test_parley_missing_configuration_does_not_connect(self):
        sys.path.insert(0,str(ROOT))
        from lib.parley import complete
        with patch.dict(os.environ,{},clear=True), patch('lib.parley.LOCAL_KEY_FILE',self.run/'missing-key'), patch('urllib.request.build_opener') as connection:
            with self.assertRaisesRegex(RuntimeError,'PARLEY_API_KEY'):
                complete('openai','fixture',1)
            connection.assert_not_called()
        with patch.dict(os.environ,{'PARLEY_API_KEY':'FICTIONAL'}), patch('urllib.request.build_opener') as connection:
            with self.assertRaises(ValueError):
                complete(None,'fixture',1)
            connection.assert_not_called()

    def test_parley_errors_are_redacted_without_retry(self):
        sys.path.insert(0,str(ROOT))
        from lib.parley import complete, ENDPOINT, NoRedirect
        from urllib.error import HTTPError
        opener=MagicMock()
        opener.open.side_effect=HTTPError(ENDPOINT,401,'FICTIONAL-SECRET',{},io.BytesIO(b'FICTIONAL-SECRET'))
        with patch.dict(os.environ,{'PARLEY_API_KEY':'FICTIONAL-SECRET'}), patch('urllib.request.build_opener',return_value=opener):
            with self.assertRaisesRegex(RuntimeError,'Parley HTTP 401') as caught:
                complete('openai','fixture',1)
        self.assertNotIn('FICTIONAL-SECRET',str(caught.exception))
        opener.open.assert_called_once()
        with self.assertRaisesRegex(RuntimeError,'redirected'):
            NoRedirect().redirect_request(None,None,302,'',{},'https://example.test/')

    def test_parley_rejects_invalid_or_incomplete_answers(self):
        sys.path.insert(0,str(ROOT))
        from lib.parley import complete
        for content,reason in [('not JSON','stop'),('{"answer":"partial"}','length'),(None,'stop')]:
            with self.subTest(content=content,reason=reason):
                opener=MagicMock()
                opener.open.return_value=io.BytesIO(json.dumps(dict(choices=[dict(finish_reason=reason,message=dict(content=content))])).encode())
                with patch.dict(os.environ,{'PARLEY_API_KEY':'FICTIONAL'}), patch('urllib.request.build_opener',return_value=opener):
                    with self.assertRaises(RuntimeError):
                        complete('openai','fixture',1)

    def test_parley_schema_failure_is_not_saved_as_valid_response(self):
        sys.path.insert(0,str(ROOT))
        from lib.common import Receipt
        from lib.model import infer, obj, STRING
        from jsonschema import ValidationError
        project=json.loads((self.run/'config/project.json').read_text(encoding='utf-8'))
        project['ai'].update(provider='parley',model='openai')
        dump(self.run/'config/project.json',project)
        opener=MagicMock()
        opener.open.return_value=io.BytesIO(b'{"choices":[{"message":{"content":"{}"},"finish_reason":"stop"}]}')
        with patch.dict(os.environ,{'PARLEY_API_KEY':'FICTIONAL'}), patch('urllib.request.build_opener',return_value=opener):
            with self.assertRaises(ValidationError):
                infer(self.run,'bad-schema','Offline fixture',{},obj(dict(answer=STRING)),Receipt(self.run,'parley_schema'))
        self.assertEqual(list((self.run/'ai_calls').rglob('response.json')),[])

    def test_parley_explicit_local_key_handoff(self):
        sys.path.insert(0,str(ROOT))
        from lib.parley import complete
        secret=self.run/'fixture-key.txt'
        secret.write_text('FICTIONAL-LOCAL-KEY',encoding='utf-8')
        opener=MagicMock()
        opener.open.return_value=io.BytesIO(b'{"choices":[{"message":{"content":"{\\"answer\\":true}"},"finish_reason":"stop"}]}')
        with patch.dict(os.environ,{},clear=True), patch('lib.parley.LOCAL_KEY_FILE',secret), patch('urllib.request.build_opener',return_value=opener):
            result,details=complete('openai','fixture',1)
        self.assertEqual(result,{'answer':True})
        self.assertEqual(opener.open.call_args.args[0].get_header('Authorization'),'Bearer FICTIONAL-LOCAL-KEY')
        self.assertNotIn('FICTIONAL-LOCAL-KEY',json.dumps(details))

    def test_local_youtube_transcription_skips_subtitle_requests(self):
        sys.path.insert(0,str(ROOT))
        from lib.common import Receipt
        from processing.extract_content import extract_video
        audio=self.repo/'audio.m4a'
        audio.write_bytes(b'fictional audio; not decoded')
        downloader=MagicMock()
        downloader.__enter__.return_value=downloader
        downloader.extract_info.return_value={'id':'fixture'}
        downloader.prepare_filename.return_value=str(audio)
        segments=[dict(segment_id='s00001',start_seconds=0,end_seconds=1,text='Offline fixture')]
        with patch('processing.extract_content.ROOT',self.repo), patch('yt_dlp.YoutubeDL',return_value=downloader) as factory, patch('processing.extract_content.local_transcribe',return_value=segments):
            result,filename,basis=extract_video({'item_id':'youtube:fixture','url':'https://example.test/video'},
                {'youtube_transcript_mode':'local','allow_local_transcription':True},Receipt(self.run,'fixture_video'))
        options=factory.call_args.args[0]
        self.assertFalse(options['writesubtitles'])
        self.assertFalse(options['writeautomaticsub'])
        self.assertTrue(options['ffmpeg_location'])
        downloader.extract_info.assert_called_once()
        self.assertEqual(result,segments)
        self.assertIn('local speech recognition',basis)

    def test_exact_saved_model_response_reuses_without_inference(self):
        sys.path.insert(0,str(ROOT))
        from lib.common import Receipt
        from lib.model import infer, obj, STRING
        project=json.loads((self.run/'config/project.json').read_text(encoding='utf-8'))
        project['ai'].update(provider='ollama',model='FICTIONAL-CACHE-TEST')
        dump(self.run/'config/project.json',project)
        schema=obj(dict(answer=STRING))
        payload={'fixture':True}
        instruction='Offline cache fixture'
        prompt=instruction+'\n\nReturn only JSON matching this schema:\n'+json.dumps(schema)+'\n\nINPUT DATA:\n'+json.dumps(payload,ensure_ascii=False)
        prior=self.run/'ai_calls/cache-previous'
        prior.mkdir(parents=True)
        (prior/'prompt.txt').write_text(prompt,encoding='utf-8')
        dump(prior/'metadata.json',dict(provider='ollama',model='FICTIONAL-CACHE-TEST'))
        dump(prior/'response.json',{'answer':'fictional response'})
        receipt=Receipt(self.run,'cache_test')
        with patch('urllib.request.urlopen',side_effect=AssertionError('Network must not be called')):
            result=infer(self.run,'cache',instruction,payload,schema,receipt)
        self.assertEqual(result,{'answer':'fictional response'})
        self.assertTrue(receipt.value['notes'])
        with patch('urllib.request.urlopen',side_effect=RuntimeError('MOCK endpoint reached')):
            with self.assertRaisesRegex(RuntimeError,'MOCK endpoint reached'):
                infer(self.run,'cache',instruction,{'fixture':'changed'},schema,Receipt(self.run,'cache_miss'))


if __name__=='__main__':
    unittest.main(verbosity=2)
