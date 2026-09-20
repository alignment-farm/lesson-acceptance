"""Offline replay and independent SQL oracle checks. Makes no model requests."""
import json, re, time
from pathlib import Path
import pilot

ORACLES = {
 'billing': '''SELECT c.id,c.name,
 COALESCE((SELECT SUM(i.amount) FROM invoices i WHERE i.customer_id=c.id AND i.status <> 'void'),0),
 COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.customer_id=c.id),0)
 FROM customers c ORDER BY c.id''',
 'attendance': '''SELECT e.id,e.title,
 COALESCE((SELECT SUM(r.seats) FROM registrations r WHERE r.event_id=e.id AND r.status='confirmed'),0),
 (SELECT COUNT(*) FROM tags t WHERE t.event_id=e.id)
 FROM events e ORDER BY e.id'''
}

def main():
    previous = pilot.OUT / 'offline-verification.json'
    if previous.exists():
        pilot.save('verification-history/' + str(time.time_ns()) + '.json', json.loads(previous.read_text()))
    checked = []
    for key,h in pilot.HISTORIES.items():
        source = json.loads((pilot.OUT / (key+'-source.json')).read_text())
        for kind, rows in [('source',h['rows']),('probe',pilot.challenge(key))]:
            oracle = pilot.execute(h['schema'],rows,ORACLES[key])
            truth = pilot.expected(key,rows)
            assert [list(r) for r in oracle['rows']] == truth
            acquired = pilot.execute(h['schema'],rows,source['query'])
            checked.append({'history':key,'split':kind,'oracle':truth,'oracle_execution':oracle,'acquired':acquired,
                            'pass': [list(r) for r in acquired.get('rows',[])] == truth})
    final_checks = []
    replay_baselines = []
    for path in sorted((pilot.OUT/'grades').glob('*.json')):
        r = json.loads(path.read_text())
        h = pilot.HISTORIES[r['history']]
        oracle = pilot.execute(h['schema'],r['input'],ORACLES[r['history']])
        assert [list(x) for x in oracle['rows']] == r['expected']
        replay = pilot.execute(h['schema'],r['input'],r['final_sql'])
        passed = [list(x) for x in replay.get('rows',[])] == r['expected']
        assert passed == r['final_pass']
        # Evaluate acquired programs on independent numerical material offline.
        # Never exposed to model; no policy selection based on these results.
        behaviors = []
        behavior_executions = []
        for seed in [907,911]:
            rows = pilot.fresh(r['history'],seed)
            output = pilot.execute(h['schema'],rows,r['final_sql'])
            behaviors.append([list(x) for x in output.get('rows',[])] == pilot.expected(r['history'],rows))
            behavior_executions.append({'seed':seed,'execution':output})
        final_checks.append({'file':path.name,'history':r['history'],'replay_pass':passed,'independent_behavior_pass':behaviors,'oracle_execution':oracle,'replay_execution':replay,'behavior_executions':behavior_executions})
        if r['arm'] == 'raw':
            source = json.loads((pilot.OUT / (r['history']+'-source.json')).read_text())
            policies = json.loads((pilot.OUT / (r['history']+'-27b.json')).read_text())
            for arm in ['raw','cheap','paid']:
                blocks = re.findall(r'```(?:sql|sqlite)\s*(.*?)```',policies.get(arm,''),re.S)
                query = source['query'] if arm == 'raw' else (blocks[-1].strip().rstrip(';') if blocks else None)
                output = pilot.execute(h['schema'],r['input'],query) if query else {'error':'no acquired complete SQL block'}
                replay_baselines.append({'history':r['history'],'seed':r['seed'],'arm':arm,'query':query,'execution':output,'pass':[list(x) for x in output.get('rows',[])] == r['expected']})
    pilot.save('offline-verification.json',{'source_and_probe':checked,'final_checks':final_checks,'fixed_program_replay':replay_baselines})
    print(json.dumps({'source_probe_checked':len(checked),'final_checked':len(final_checks)}))

if __name__ == '__main__':
    main()
