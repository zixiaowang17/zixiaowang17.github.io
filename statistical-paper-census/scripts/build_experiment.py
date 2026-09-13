#!/usr/bin/env python3
"""Run the maintained generator and its full --check, sharing only its render cache."""
import hashlib
import importlib.util
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    aggregate = Path('experiments/aos-2024')
    script = Path('skills/statistical-census-html/scripts/build_report.py')
    spec = importlib.util.spec_from_file_location('census_release_renderer', script)
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    arguments = [str(script), str(aggregate / 'audited.json'), str(aggregate / 'report.html'),
                 '--census', str(aggregate / 'ranked-interfaces.json')]
    phase = {'name': 'generation'}
    stopped = threading.Event()

    def report_progress():
        while not stopped.wait(30):
            print(phase['name'], 'render cache', renderer.render_statement.cache_info(), flush=True)

    threading.Thread(target=report_progress, daemon=True).start()
    try:
        # Independent Pandoc calls populate the generator's ordinary in-memory
        # cache. The maintained generation and full --check still run unchanged.
        phase['name'] = 'render preparation'
        data = json.loads((aggregate / 'audited.json').read_text())
        sources = {c['statement_original'] for c in data['claims']}
        for interface in data['interfaces']:
            sources.update(n['text'] for n in interface.get('theorem_explanations', {}).values())
            for member in interface['members']:
                sources.add(member['statement_original'])
                for symbol in member.get('highlight_symbols', []):
                    sources.update(('$' + symbol + '$', r'\[' + symbol + r'\]'))
        print(f'Rendering {len(sources)} distinct source fragments with 8 workers.', flush=True)
        with ThreadPoolExecutor(max_workers=8) as pool:
            for _ in pool.map(renderer.render_statement, sorted(sources)):
                pass
        phase['name'] = 'generation'
        sys.argv = arguments
        generated = renderer.main()
        assert generated == 0, 'Generation failed'
        phase['name'] = 'reproduction check'
        print('Generation complete; starting the full --check.', flush=True)
        start = time.monotonic()
        sys.argv = arguments + ['--check']
        checked = renderer.main()
        result = {
            'status': 'passed' if checked == 0 else 'failed',
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'command': ['python3', *sys.argv], 'exit_code': checked,
            'elapsed_seconds': round(time.monotonic() - start, 2),
            'mode': 'Eight independent workers prepare source fragments through the maintained render_statement function. The maintained generator main() and complete --check then run sequentially in one interpreter using that standard in-memory cache; every output is regenerated and compared.',
            'report_sha256': hashlib.sha256((aggregate / 'report.html').read_bytes()).hexdigest(),
            'generator_sha256': hashlib.sha256(script.read_bytes()).hexdigest()
        }
        (aggregate / 'render-verification.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        assert checked == 0, 'Reproduction check failed'
    finally:
        stopped.set()


if __name__ == '__main__':
    main()
