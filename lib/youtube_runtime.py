"""Find an installed JavaScript runtime for both yt-dlp entry points."""
import shutil


def javascript_options():
    # The portable Python Scripts directory is not necessarily on the user's PATH.
    # yt-dlp's deno extra installs this package and the matching executable.
    try:
        from deno import find_deno_bin
        executable = find_deno_bin()
    except (ImportError, FileNotFoundError):
        executable = shutil.which('deno')
    if executable:
        return {'js_runtimes': {'deno': {'path': str(executable)}}}
    executable = shutil.which('node')
    if executable:
        # Node is not enabled by yt-dlp's defaults; explicitly opt in.
        return {'js_runtimes': {'node': {'path': executable}}}
    raise RuntimeError(
        'YouTube needs a JavaScript runtime. Install the project requirements '
        'with the pipeline Python: python -m pip install -r requirements.txt')
