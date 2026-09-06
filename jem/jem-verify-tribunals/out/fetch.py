"""Fetch public evidence into out/fetch_log with an audit manifest."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '_vendor'))
from pypdf import PdfReader

def fetch(label, url):
    folder = ROOT / 'fetch_log'
    body = folder / (label + '.response')
    headers = folder / (label + '.headers')
    result = subprocess.run([
        'curl', '--silent', '--show-error', '--location', '--max-time', '40',
        '--connect-timeout', '15', '--max-filesize', '100000000',
        '--proto', '=https', '--proto-redir', '=https',
        '--dump-header', str(headers), '--output', str(body),
        '--write-out', '%{http_code}\n%{url_effective}', url
    ], capture_output=True, text=True)
    record = dict(label=label, requested_url=url,
                  fetched_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  curl_exit=result.returncode, response=result.stdout, error=result.stderr)
    if body.exists():
        data = body.read_bytes()
        record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                      body=str(body.relative_to(ROOT)))
        if data.startswith(b'%PDF'):
            try:
                reader = PdfReader(body)
                extracted = '\n'.join(f'\n[PDF page {i + 1}]\n' + (p.extract_text() or '')
                                      for i, p in enumerate(reader.pages))
                body.with_suffix('.txt').write_text(extracted)
                record['pdf_pages'] = len(reader.pages)
            except Exception as exc:
                record['extraction_error'] = str(exc)
        else:
            from html.parser import HTMLParser
            class Text(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.parts = []
                    self.skip = 0
                def handle_starttag(self, tag, attrs):
                    if tag in ('script', 'style'):
                        self.skip += 1
                def handle_endtag(self, tag):
                    if tag in ('script', 'style') and self.skip:
                        self.skip -= 1
                def handle_data(self, data):
                    if not self.skip and data.strip():
                        self.parts.append(data.strip())
            parser = Text()
            parser.feed(data.decode('utf-8', errors='replace'))
            body.with_suffix('.txt').write_text('\n'.join(parser.parts))
    with (folder / 'manifest.jsonl').open('a') as stream:
        stream.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)

if __name__ == '__main__':
    fetch(sys.argv[1], sys.argv[2])
