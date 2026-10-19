# Example: The Power of Compounding (75 s)

A test of the full pipeline. The voice is a robotic test TTS (espeak-ng), aligned with `align_script.py` because no Whisper model was available offline.

- `script.txt`: narration
- `storyboard.json`: 23 scenes, showing most element types (character, props, text, title, label, card, arrow, counter, bars, linechart, split background, camera punch, thumbnail)
- `demo_output.mp4`, `demo_thumbnail.jpg`, `demo_contact_sheet.png`: rendered results

Reproduce:
```bash
espeak-ng -v en-us -s 150 -f script.txt -w raw.wav      # or use your own recording
python ../../scripts/prep_audio.py raw.wav work
python ../../scripts/align_script.py work/voice.wav script.txt work
cp storyboard.json work/ && python ../../scripts/build.py work
```
