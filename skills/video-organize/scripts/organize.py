"""Index local media and optionally copy unique files; never move or delete sources."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

EXTENSIONS = {'.jpg','.jpeg','.png','.heic','.heif','.webp','.tif','.tiff','.mov','.mp4','.m4v','.mkv','.wav','.mp3','.m4a'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def date_info(path):
    if shutil.which('exiftool'):
        result = subprocess.run(['exiftool','-json','-DateTimeOriginal','-CreateDate',str(path)],capture_output=True,timeout=30)
        if result.returncode == 0:
            values = json.loads(result.stdout)[0]
            for key in ('DateTimeOriginal','CreateDate'):
                if values.get(key):
                    return str(values[key]), 'exiftool:'+key
    if shutil.which('ffprobe'):
        result = subprocess.run(['ffprobe','-v','error','-show_entries','format_tags=creation_time:stream_tags=creation_time','-of','json',str(path)],capture_output=True,timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            values = [data.get('format',{})] + data.get('streams',[])
            for item in values:
                raw = item.get('tags',{}).get('creation_time')
                if raw:
                    return raw,'ffprobe:creation_time'
    return '', 'unknown'


def organize(source, output, copy=False):
    source, output = source.resolve(), output.resolve()
    if not source.is_dir():
        raise ValueError('Source must be a directory')
    if source == output or source in output.parents:
        raise ValueError('Output cannot be inside source')
    if output.exists():
        raise ValueError('Output already exists; choose a new directory')
    paths = sorted(p for p in source.rglob('*') if p.suffix.lower() in EXTENSIONS and p.is_file() and not p.is_symlink())
    output.mkdir(parents=True)
    rows, errors, groups, copies = [], [], defaultdict(list), {}
    for path in paths:
        relative = str(path.relative_to(source))
        # Do not follow media symlinks or parent-directory links outside source.
        if not path.resolve().is_relative_to(source):
            errors.append({'source':relative,'error':'Outside source root; skipped'})
            continue
        try:
            fingerprint = digest(path)
            try:
                raw, origin = date_info(path)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                raw, origin = '', 'unknown'
                errors.append({'source':relative,'error':'Metadata unavailable: '+str(error)})
            match = re.match(r'^(\d{4})[:-](\d{2})[:-](\d{2})',raw)
            date = '-'.join(match.groups()) if match else '日期未知'
            if match:
                try:
                    datetime.strptime(date,'%Y-%m-%d')
                except ValueError:
                    date = '日期未知'
            row = {'source':relative,'bytes':path.stat().st_size,'sha256':fingerprint,
                   'date_raw':raw,'date_source':origin,'date_bucket':date,
                   'timezone_inferred':False,'copy':''}
            groups[fingerprint].append(relative)
            if copy:
                if fingerprint not in copies:
                    dest = output/'分类副本'/date/(fingerprint+path.suffix.lower())
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(path,dest)
                    if digest(dest) != fingerprint:
                        raise ValueError('Source changed while copying; copy is not verified')
                    copies[fingerprint] = str(dest.relative_to(output))
                row['copy'] = copies[fingerprint]
            rows.append(row)
        except (OSError, ValueError) as error:
            errors.append({'source':relative,'error':str(error)})
    report = {'generated_at':datetime.now(timezone.utc).isoformat(),'source_root':str(source),
              'files':rows,'duplicates':[v for v in groups.values() if len(v)>1],
              'copied_unique_files':len(copies),'errors':errors,'original_files_changed':False}
    (output/'素材索引.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--copy',action='store_true');args=parser.parse_args()
    try:
        report=organize(args.source,args.output,args.copy)
        print(json.dumps({'files':len(report['files']),'duplicate_groups':len(report['duplicates']),
                          'copied':report['copied_unique_files'],'errors':report['errors']},ensure_ascii=False))
        sys.exit(1 if report['errors'] else 0)
    except (OSError,ValueError) as error:
        print(str(error),file=sys.stderr);sys.exit(1)
