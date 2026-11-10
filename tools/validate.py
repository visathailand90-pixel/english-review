from pathlib import Path
import json,re
R=Path(__file__).resolve().parent.parent
rows=json.loads((R/'lesson-data/index.json').read_text(encoding='utf-8'))
ids=[r['id'] for r in rows]
assert len(set(ids))==len(ids)
assert set(['01','01p']+[f'{i:02}' for i in range(2,10)])<=set(ids)
for lid in ids:
 assert re.fullmatch(r'[0-9]+p?',lid)
 d=json.loads((R/f'lesson-data/{lid}.json').read_text(encoding='utf-8'))
 assert d['id']==lid
 for key in ['theory','vocab','l2','l3','l4','l5','l6','fix']: assert isinstance(d[key],list) and d[key]
for name in ['index.html','app-template.html']:
 s=(R/name).read_text(encoding='utf-8'); assert "english-review:v4" in s
for name in ['index.html','app-template.html','reader/index.html','words/index.html']:
 s=(R/name).read_text(encoding='utf-8')
 assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|-----BEGIN .*PRIVATE KEY-----',s),'Potential credential'
assert 'window.claude' not in (R/'reader/index.html').read_text(encoding='utf-8')
print('PASS lesson structure, stable progress key and credential-pattern checks. Human privacy review still required.')

bank=json.loads((R/'words/bank.json').read_text(encoding='utf-8'))
assert len({p['id'] for p in bank['packs']})==len(bank['packs'])
for p in bank['packs']:
 assert 1<=len(p['words'])<=20
 for w in p['words']:
  assert all(isinstance(w[k],str) and w[k] for k in ['en','ru','pr','ex','exru','ex2','ex2ru'])
  assert w['en']==w['en'].lower()
  assert '___' in w['s'],w['en']
for f in [R/'words/bank.js',R/'reader/context.js',*list((R/'backend').glob('*.mjs'))]:
 assert not re.search(r'\\bsk-[A-Za-z0-9_-]{20,}',f.read_text(encoding='utf-8')),'Potential API key'
print('PASS complete word-entry fields, pack IDs and server/client key pattern scan')
