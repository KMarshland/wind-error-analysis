import subprocess
import os

def download_file(url, output_path, debug=True):
    if debug:
        print('\t[Download Utility] Downloading %s to %s' % (url, output_path))

    remote_bytes = get_remote_bytes(url, debug)

    if debug:
        print('\t[Download Utility] Downloading %d bytes' % remote_bytes)

    partial_name = output_path.split('.')[0] + '.partial'

    call = subprocess.run(['curl', '-o', partial_name, url])
    call.check_returncode()

    local_bytes = os.path.getsize(partial_name)

    if local_bytes != remote_bytes:
        raise Exception('Local bytes does not match remote bytes')

    os.rename(partial_name, output_path)

    if debug:
        print('\t[Download Utility] Download complete: %s' % output_path)

    return output_path

def get_remote_bytes(dataset_url, _debug):
    call = subprocess.run(['curl', '-I', dataset_url], stdout=subprocess.PIPE)
    call.check_returncode()
    lines = call.stdout.decode('utf-8').split("\n")

    for line in lines:
        if not line.startswith('Content-Length:'):
            continue

        return int(line.split(': ')[-1])

    raise Exception('Could not find the number of remote bytes')