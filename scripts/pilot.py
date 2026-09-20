"""Bounded lesson acceptance pilot; standard library only, run with uv."""
import argparse, hashlib, json, os, random, re, sqlite3, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('LESSON_ACCEPTANCE_EVIDENCE', str(ROOT / 'evidence' / 'pilot-v1'))).resolve()
MODEL = 'docker.io/ai/qwen3:8B-Q4_K_M'
URL = 'https://mac-studio-7hr7.taile71f88.ts.net/engines/v1/chat/completions'

def save(name, data):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + '\n')

def ask(name, prompt):
    p = OUT / (name + '.json')
    request = {'model': MODEL, 'messages': [
        {'role': 'system', 'content': 'You are a careful SQLite reporting engineer. Follow requirements and preserve all obligations. /no_think'},
        {'role': 'user', 'content': prompt}], 'temperature': 0, 'max_tokens': 4096}
    if '27b' in MODEL:
        request['chat_template_kwargs'] = {'enable_thinking': False}
    if p.exists():
        cached = json.loads(p.read_text())
        if cached['request'] != request:
            raise RuntimeError('cache request mismatch: ' + name)
        return cached['text']
    interrupted = sum(json.loads(p.read_text()).get('calls',0) for p in OUT.glob('*serving-interruption*.json'))
    if len(list((OUT / 'calls').glob('*.json'))) + interrupted >= 60:
        raise RuntimeError('call budget exhausted')
    budget_path = OUT / 'budget.json'
    if not budget_path.exists():
        start_unix = 1789861615 if OUT == ROOT / 'evidence' / 'pilot-v1' else time.time()
        save('budget.json', {'start_unix':start_unix, 'deadline_unix':start_unix + 45 * 60, 'call_ceiling':60})
    deadline = json.loads(budget_path.read_text())['deadline_unix']
    if time.time() >= deadline:
        raise RuntimeError('45-minute session budget exhausted')
    start = time.monotonic()
    try:
        req = urllib.request.Request(URL, json.dumps(request).encode(), {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=240) as response:
            result = json.load(response)
        text = result['choices'][0]['message']['content']
        save(name + '.json', {'request': request, 'request_sha256': hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(), 'response': result, 'text': text,
                              'wall_seconds': time.monotonic() - start})
        print(name, round(time.monotonic() - start, 2), flush=True)
        if not text.strip():
            raise RuntimeError('empty model answer; inspect preserved response')
        return text
    except Exception as exc:
        save(name + '-failed.json', {'request': request, 'error': repr(exc), 'wall_seconds': time.monotonic() - start})
        raise

def sql(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.S).strip()
    blocks = re.findall(r'```(?:sql|sqlite)?\s*(.*?)```', text, re.S)
    return (blocks[0] if blocks else text).strip().rstrip(';')

def execute(schema, rows, query):
    start = time.monotonic()
    db = sqlite3.connect(':memory:')
    db.executescript(schema)
    for table, values in rows.items():
        if values:
            db.executemany('INSERT INTO ' + table + ' VALUES (' + ','.join('?' for _ in values[0]) + ')', values)
    db.set_authorizer(lambda op, *args: sqlite3.SQLITE_OK if op in
                      (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE) else sqlite3.SQLITE_DENY)
    ticks = [0]
    def progress():
        ticks[0] += 1
        return ticks[0] > 10000
    db.set_progress_handler(progress, 1000)
    try:
        cur = db.execute(query)
        result = {'columns': [d[0] for d in cur.description], 'rows': cur.fetchall()}
    except Exception as exc:
        result = {'error': str(exc)}
    db.close()
    return {**result, 'wall_seconds': time.monotonic() - start}

HISTORIES = {
 'billing': {
  'schema': 'CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT); CREATE TABLE invoices(id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id), amount INTEGER, status TEXT); CREATE TABLE payments(id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id), amount INTEGER);',
  'task': 'Return each customer id and name, total non-void invoice amount as billed, and total payment amount as paid. Include customers with no invoices or payments using 0. Keep different customer ids separate even if names match. Sort by customer id. Status void is excluded from billed only.',
  'rows': {'customers': [[1,'Ada'],[2,'Ben'],[3,'Cy']], 'invoices': [[1,1,100,'open'],[2,2,50,'void']], 'payments': [[1,1,40],[2,2,15]]}},
 'attendance': {
  'schema': 'CREATE TABLE events(id INTEGER PRIMARY KEY, title TEXT); CREATE TABLE registrations(id INTEGER PRIMARY KEY, event_id INTEGER REFERENCES events(id), seats INTEGER, status TEXT); CREATE TABLE tags(id INTEGER PRIMARY KEY, event_id INTEGER REFERENCES events(id), label TEXT);',
  'task': 'Return each event id and title, total seats for confirmed registrations as seats, and number of tag records as tags. Include events without registrations or tags using 0. Keep different event ids separate even if titles match. Sort by event id. Only confirmed registrations contribute seats; all tags count.',
  'rows': {'events': [[1,'Talk'],[2,'Lab'],[3,'Walk']], 'registrations': [[1,1,5,'confirmed'],[2,2,3,'cancelled']], 'tags': [[1,1,'science'],[2,2,'social']]}}
}

def material(h, rows=None):
    return json.dumps({'schema': h['schema'], 'requirements': h['task'], 'rows': rows or h['rows']})

def challenge(key):
    if key == 'billing':
        return {'customers': [[11,'Probe'],[12,'Empty']], 'invoices': [[11,11,19,'open'],[12,11,31,'open'],[13,11,7,'void']], 'payments': [[11,11,5],[12,11,9]]}
    return {'events': [[11,'Probe'],[12,'Empty']], 'registrations': [[11,11,2,'confirmed'],[12,11,7,'confirmed'],[13,11,3,'cancelled']], 'tags': [[11,11,'a'],[12,11,'b']]}

def collect():
    for key,h in HISTORIES.items():
        original = ask('calls/' + key + '-source', material(h) + '\nWrite one SQLite SELECT in a SQL code block. No other statements.')
        query = sql(original)
        result = execute(h['schema'], h['rows'], query)
        source = {'task': h, 'query': query, 'execution': result}
        proposal = ask('calls/' + key + '-proposal', json.dumps(source) + '\nExtract at most two reusable lessons from this actual episode. State evidence and scope; do not invent outcomes. Return prose.')
        source['proposal'] = proposal
        save(key + '-source.json', source)
        base = json.dumps(source) + '\nDecide accept, decline or defer for each original lesson as reusable guidance. Use careful reflection, explicit keys, SQL semantics, source rows and requirements. Preserve original wording; any narrower rewrite must be separately labeled. Avoid overclaiming from one slice.'
        cheap = ask('calls/' + key + '-cheap', base)
        probe_rows = challenge(key)
        probe = {'origin': 'investigator-authored development multiplicity challenge', 'rows': probe_rows,
                 'query': query, 'execution': execute(h['schema'], probe_rows, query)}
        paid = ask('calls/' + key + '-paid', base + '\nAdditional paid execution evidence: ' + json.dumps(probe))
        save(key + '-acceptance.json', {'cheap': cheap, 'paid': paid, 'probe': probe})

REVIEW = '''Audit the actual SQL, not just the prose. For every join, derive its
cardinality from schema constraints (foreign keys do not imply uniqueness).
Check independent aggregates for row multiplication, filtering, empty groups,
duplicate values, and stable identifiers. Separate validity of a narrow lesson
from validity of the whole source program. If execution evidence is supplied,
quote its actual returned numbers and reconcile them with the input rows; never
claim an unobserved output. Decide accept/decline/defer for each original lesson,
preserve its wording, and label any revised scope separately. State what code is
safe to reuse. No external answer key is available.'''

def develop():
    for key in HISTORIES:
        source = json.loads((OUT / (key + '-source.json')).read_text())
        old = json.loads((OUT / (key + '-acceptance.json')).read_text())
        base = json.dumps(source) + '\n' + REVIEW
        cheap = ask('calls/' + key + '-cheap-developed', base)
        paid = ask('calls/' + key + '-paid-developed', base + '\nAdditional paid execution evidence: ' + json.dumps(old['probe']))
        save(key + '-developed.json', {'cheap': cheap, 'paid': paid, 'probe': old['probe']})

def competence():
    global MODEL
    MODEL = 'docker.io/ai/qwen3.8:27b-q4_K_M'
    for key in HISTORIES:
        source = json.loads((OUT / (key + '-source.json')).read_text())
        old = json.loads((OUT / (key + '-acceptance.json')).read_text())
        base = json.dumps(source) + '\n' + REVIEW
        cheap = ask('calls/' + key + '-cheap-27b-direct', base)
        paid = ask('calls/' + key + '-paid-27b-direct', base + '\nAdditional paid execution evidence: ' + json.dumps(old['probe']))
        save(key + '-27b.json', {'cheap': cheap, 'paid': paid, 'probe': old['probe']})

def fresh(key, seed):
    rng = random.Random(seed)
    ids = [seed * 10 + i for i in range(4)]
    parent, detail, aux = ('customers', 'invoices', 'payments') if key == 'billing' else ('events', 'registrations', 'tags')
    rows = {parent: [[p, 'Shared' if i < 2 else 'Group' + str(i)] for i,p in enumerate(ids)], detail: [], aux: []}
    detail_counts, aux_counts = ([1,1,0,1], [1,0,1,0]) if seed == 801 else (([3,2,0,1], [2,0,2,0]) if seed == 802 else ([2,4,0,1], [3,2,1,0]))
    for i,p in enumerate(ids):
        for j in range(detail_counts[i]):
            value = rng.randint(2,30)
            status = ('void' if j == 2 else 'open') if key == 'billing' else ('cancelled' if j == 2 else 'confirmed')
            rows[detail].append([len(rows[detail])+1,p,value,status])
        for j in range(aux_counts[i]):
            rows[aux].append([len(rows[aux])+1,p, rng.randint(2,20) if key == 'billing' else 'tag' + str(j)])
    # Equal-valued legitimate records challenge SUM(DISTINCT amount) repairs.
    rows[detail][1][2] = rows[detail][0][2]
    return rows

def expected(key, rows):
    if key == 'billing':
        return [[p,n,sum(x[2] for x in rows['invoices'] if x[1] == p and x[3] != 'void'),sum(x[2] for x in rows['payments'] if x[1] == p)] for p,n in rows['customers']]
    return [[p,n,sum(x[2] for x in rows['registrations'] if x[1] == p and x[3] == 'confirmed'),sum(x[1] == p for x in rows['tags'])] for p,n in rows['events']]

def evaluate():
    global MODEL
    MODEL = 'docker.io/ai/qwen3.8:27b-q4_K_M'
    records = []
    for key,h in HISTORIES.items():
        source = json.loads((OUT / (key + '-source.json')).read_text())
        policies = json.loads((OUT / (key + '-27b.json')).read_text())
        raw = {k:v for k,v in source.items() if k != 'proposal'}
        for seed in [801, 802, 803]:
            rows = fresh(key, seed)
            for arm in ['raw', 'cheap', 'paid']:
                memory = {'retained_source': raw}
                if arm != 'raw':
                    memory.update({'original_proposals': source['proposal'], 'acceptance': policies[arm]})
                if arm == 'paid':
                    memory['paid_evidence'] = policies['probe']
                prompt = 'Retained experience (may contain errors; use critically):\n' + json.dumps(memory) + '\nNew complete task:\n' + material(h, rows) + '\nWrite one SQLite SELECT in a SQL block. You may reuse or repair source code. Independently check requirements, join cardinality, all aggregate values and zero groups. Your SQL will be executed and you can revise once.'
                name = f'calls/final-{key}-{seed}-{arm}'
                first = sql(ask(name + '-initial', prompt))
                execution = execute(h['schema'], rows, first)
                final_prompt = prompt + '\nYour first SQL:\n' + first + '\nActual execution:\n' + json.dumps(execution) + '\nAudit against the visible input rows and requirements. Return your final SQL in a SQL block, correcting any issue; repeat it if correct.'
                final = sql(ask(name + '-revision', final_prompt))
                result = execute(h['schema'], rows, final)
                truth = expected(key, rows)
                rec = {'history': key, 'seed': seed, 'arm': arm, 'input': rows, 'initial_sql': first, 'initial_execution': execution, 'final_sql': final, 'final_execution': result, 'expected': truth,
                       'initial_pass': [list(r) for r in execution.get('rows', [])] == truth,
                       'final_pass': [list(r) for r in result.get('rows', [])] == truth}
                records.append(rec)
                save(f'grades/{key}-{seed}-{arm}.json', rec)
    save('results.json', records)

def summarize():
    records = json.loads((OUT / 'results.json').read_text())
    costs = {}
    for p in sorted((OUT / 'calls').glob('*.json')):
        r = json.loads(p.read_text())
        if p.stem.startswith('final-'):
            category = 'later-' + p.stem.split('-')[-2]
        elif p.stem.endswith('-source'):
            category = 'shared-source'
        elif p.stem.endswith('-proposal'):
            category = 'shared-proposal'
        elif p.stem.endswith('-27b-direct'):
            category = 'acceptance-' + ('cheap' if 'cheap' in p.stem else 'paid')
        elif '27b' in p.stem:
            category = 'experimental-serving-27b'
        else:
            category = 'experimental-search-8b'
        c = costs.setdefault(category, {'calls':0,'wall_seconds':0,'prompt_tokens':0,'completion_tokens':0, 'cached_prompt_tokens':0, 'money_usd':None})
        c['calls'] += 1
        c['wall_seconds'] += r['wall_seconds']
        for k in ['prompt_tokens', 'completion_tokens']:
            c[k] += r.get('response', {}).get('usage', {}).get(k, 0)
        c['cached_prompt_tokens'] += r.get('response', {}).get('usage', {}).get('prompt_tokens_details', {}).get('cached_tokens', 0)
    save('summary.json', {'outcomes': {a: {'n': sum(r['arm']==a for r in records), 'initial_pass':sum(r['arm']==a and r['initial_pass'] for r in records), 'final_pass':sum(r['arm']==a and r['final_pass'] for r in records)} for a in ['raw','cheap','paid']}, 'costs': costs,
      'unknown_costs': ['investigator and delegated model tokens/money', 'engineering time', 'remote energy/hardware cost', 'server load and network variance'],
      'probe_sql_seconds': sum(json.loads((OUT / (k + '-acceptance.json')).read_text())['probe']['execution']['wall_seconds'] for k in HISTORIES)})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['collect','develop','competence','evaluate','summarize'])
    args = parser.parse_args()
    if args.phase in ['competence', 'evaluate']:
        MODEL = 'docker.io/ai/qwen3.8:27b-q4_K_M'
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = 'instrument-' + args.phase + '-' + str(time.time_ns()) + '.json'
    save(manifest, {'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'model': MODEL, 'endpoint': URL, 'source_snapshot': Path(__file__).read_text(), 'python':sys.version, 'sqlite':sqlite3.sqlite_version, 'start_unix':time.time(), 'protocol_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'protocols').glob('*.md')}})
    globals()[args.phase]()
