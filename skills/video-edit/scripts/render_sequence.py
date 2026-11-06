"""Assemble known SDR clips/photos with original audio. No AI service required."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def run(args):
    result = subprocess.run(args, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8',errors='replace')[-2000:])
    return result.stdout


def render(timeline, output):
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        raise ValueError('Install FFmpeg and ffprobe on PATH first')
    timeline, output = timeline.resolve(), output.resolve()
    if output.exists():
        raise ValueError('Output exists; choose a new filename')
    data = json.loads(timeline.read_text(encoding='utf-8'))
    w,h,fps = data.get('width',1080),data.get('height',1920),data.get('fps',30)
    if any(type(x) is not int or x<=0 for x in (w,h,fps)) or w%2 or h%2 or fps>60:
        raise ValueError('Use positive even dimensions and integer fps from 1 to 60')
    clips = data.get('clips',[])
    if not clips:
        raise ValueError('Timeline has no clips')
    validated=[]
    for item in clips:
        path=(timeline.parent/item['path']).resolve()
        if not path.is_file():
            raise ValueError('Missing source: '+str(path))
        start=float(item.get('start',0));duration=float(item['duration'])
        if not all(math.isfinite(v) for v in (start,duration)) or start<0 or duration<=0:
            raise ValueError('Invalid start/duration')
        # Exact frame grid prevents cumulative concat drift.
        if abs(duration*fps-round(duration*fps))>1e-6:
            raise ValueError('Duration must be a whole number of frames')
        info=json.loads(run([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(path)]))
        video=next((s for s in info['streams'] if s.get('codec_type')=='video' and not s.get('disposition',{}).get('attached_pic')),None)
        if not video:
            raise ValueError('Source has no video/image stream')
        image=path.suffix.lower() in ('.jpg','.jpeg','.png')
        if image:
            if start or item.get('verified_srgb') is not True:
                raise ValueError('Photos need start=0 and verified_srgb=true after actual profile check/conversion')
        else:
            for key in ('color_space','color_primaries','color_transfer'):
                if video.get(key)!='bt709':
                    raise ValueError('Needs verified SDR bt709 conversion first: '+str(path))
            if video.get('color_range') not in ('tv','pc'):
                raise ValueError('Video color range unknown')
            available=float(info.get('format',{}).get('duration',0))
            if start+duration > available+0.02:
                raise ValueError('Clip exceeds source duration')
        audio=not image and any(s.get('codec_type')=='audio' for s in info['streams'])
        validated.append((path,start,duration,image,audio))
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='video-edit-') as work:
        work=Path(work); parts=[]
        for index,(path,start,duration,image,audio) in enumerate(validated):
            segment=work/f'part{index:04}.mp4'
            command=[ffmpeg,'-nostdin','-v','error','-n']
            command+=['-loop','1'] if image else ['-ss',str(start)]
            command+=['-i',str(path)]
            if not audio:
                command+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
            scale=f'scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2:out_color_matrix=bt709:out_range=tv,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=limited'
            command+=['-map','0:v:0','-map','0:a:0' if audio else '1:a:0','-t',str(duration),
                      '-vf',scale,'-af','apad,aresample=48000','-ac','2',
                      '-c:v','libx264','-preset','fast','-crf','20','-c:a','aac','-b:a','160k',
                      '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',str(segment)]
            run(command);parts.append(segment)
        listing=work/'concat.txt'
        listing.write_text(''.join(f"file '{p.name}'\n" for p in parts),encoding='utf-8')
        final=work/'final.mp4'
        run([ffmpeg,'-nostdin','-v','error','-n','-f','concat','-safe','1','-i',str(listing),
             '-c','copy','-movflags','+faststart',str(final)])
        check_script=Path(__file__).resolve().parents[2]/'video-workflow/scripts/check_media.py'
        if not check_script.is_file():
            raise ValueError('Install the complete five-skill package; media checker missing')
        check_args=[sys.executable,str(check_script),str(final),'--width',str(w),'--height',str(h),
                    '--duration',str(sum(v[2] for v in validated))]
        if data.get('deliberate_silent') is True:
            check_args.append('--allow-silent')
        result=json.loads(run(check_args))
        # Exclusive create: never replace a file that appeared during rendering.
        with output.open('xb') as target, final.open('rb') as source:
            shutil.copyfileobj(source,target)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('timeline',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    try:
        print(json.dumps(render(args.timeline,args.output),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr);sys.exit(1)
