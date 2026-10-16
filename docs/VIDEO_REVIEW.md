# Watch the three video review copies

The three matching article/video pairs, captions, and source descriptions are also
saved together in [deliverables/20261010T052912Z-1d2e8a](../deliverables/20261010T052912Z-1d2e8a/).
For one-file transfer, use the [verified ZIP archive](../deliverables/20261010T052912Z-1d2e8a.zip).
Both the videos and ZIP are local files; Git ignores the large binary files.

These are actual narrated MP4 files, rendered from the October 10 scripts. Each
contains six visual scenes, source labels, synthetic narration, and an embedded
English subtitle track. The student has uploaded the three videos:
[01](https://youtu.be/qWxMqmFNnIw), [02](https://youtu.be/Ej1c8o_LTf8), and
[03](https://youtu.be/oUOU5CditYM). Matching titles/channel were confirmed through
YouTube oEmbed on October 16; full playback was not independently checked.
Google Vids/HeyGen production remains undocumented.

| Piece | Article | Video | Runtime | Upload description |
| --- | --- | --- | --- | --- |
| 01 — Competitor research | [Article](../runs/20261010T052912Z-1d2e8a/video_previews/01-article.md) | [Watch MP4](../runs/20261010T052912Z-1d2e8a/video_previews/01-video.mp4) | 4:43 | [Description and sources](../runs/20261010T052912Z-1d2e8a/video_previews/01-youtube-description.md) |
| 02 — Checking AI claims | [Article](../runs/20261010T052912Z-1d2e8a/video_previews/02-article.md) | [Watch MP4](../runs/20261010T052912Z-1d2e8a/video_previews/02-video.mp4) | 4:12 | [Description and sources](../runs/20261010T052912Z-1d2e8a/video_previews/02-youtube-description.md) |
| 03 — Designing a pilot | [Article](../runs/20261010T052912Z-1d2e8a/video_previews/03-article.md) | [Watch MP4](../runs/20261010T052912Z-1d2e8a/video_previews/03-video.mp4) | 4:31 | [Description and sources](../runs/20261010T052912Z-1d2e8a/video_previews/03-youtube-description.md) |

All three passed full video/audio decoding with FFmpeg. Storyboard contact sheets
and the duration/hash manifest are in the same `video_previews/` folder. Captions
use approximate timing within each scene and require playback review. The large
MP4, WAV, and intermediate files are ignored by Git but available in this workspace.

## Finish in Google Vids

Import the MP4 or individual scene assets into your Google Vids project. Review
narration, source quotations, captions, and source cards; add the final title/end
card and resolve the visible review-copy footer during production. Preserve the
actual October 10 evidence date. This local renderer has not performed those steps.

Google documents MP4 editing in Vids and export to YouTube. A direct Vids export
starts as private, so set the finished upload to unlisted or public for course
access. Keep the Google Vids project link as production evidence, and cross-link
each final YouTube video and Substack article after publication.

References: [Google Vids media and sharing guide](https://support.google.com/docs/answer/15082958?hl=en)
and [edit Drive videos in Vids](https://support.google.com/docs/answer/16466593?hl=en).

## Reproduce these local review copies

The included storyboards are specific to the existing October 10 briefs. Install
`requirements-video.txt`, then run from the repository on Windows:

```powershell
& .tools/python/python.exe publishing/render_videos.py prepare runs/20261010T052912Z-1d2e8a
powershell.exe -NoProfile -ExecutionPolicy Bypass -File publishing/narrate_windows.ps1 -Manifest C:/Users/hp/Documents/GitHub/ps04/runs/20261010T052912Z-1d2e8a/video_previews/narration.json
& .tools/python/python.exe publishing/render_videos.py render runs/20261010T052912Z-1d2e8a
```

The narration command permits this script in that process only; it does not change
the machine's execution-policy setting. It uses the installed Microsoft Zira voice.

To recreate the local delivery folder and ZIP after rendering:

```powershell
& .tools/python/python.exe scripts/export_local.py runs/20261010T052912Z-1d2e8a
```
