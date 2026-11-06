"""Read-only environment report; does not check credentials or install software."""
import json
import platform
import shutil
import sys

if __name__ == '__main__':
    tools = {name: shutil.which(name) for name in ('ffmpeg','ffprobe','exiftool','sau')}
    print(json.dumps({
        'system': platform.system(), 'python': platform.python_version(),
        'python_supported': sys.version_info >= (3,10), 'tools': tools,
        'inventory_available': sys.version_info >= (3,10),
        'basic_render_dependencies_present': bool(tools['ffmpeg'] and tools['ffprobe']),
        'exif_date_optional': bool(tools['exiftool']),
        'upload_cli_present_not_verified': bool(tools['sau']),
        'accounts_checked': False, 'network_requests': 0,
        'next': 'Check ffmpeg encoders/filters with a sample; tool presence alone does not prove rendering or publishing works.'
    }, ensure_ascii=False, indent=2))
    sys.exit(0 if sys.version_info >= (3,10) else 1)
