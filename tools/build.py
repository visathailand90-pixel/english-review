#!/usr/bin/env python3
"""Build embedded standalone English Review index.html from lesson-data/*.json.
Run from repository root: python tools/build.py
No external dependencies. Does NOT change local browser progress or publish anything.
"""
from pathlib import Path
import json,re,sys,hashlib
ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'lesson-data'
word_bank=json.loads((ROOT/'words/bank.json').read_text(encoding='utf-8'))
(ROOT/'words/bank.js').write_text('window.ENGLISH_WORD_BANK='+json.dumps(word_bank,ensure_ascii=False).replace('<','\\u003c')+';'+chr(10),encoding='utf-8')

index=json.loads((SRC/'index.json').read_text(encoding='utf-8'))
assert isinstance(index,list) and index,'Empty index'
all_data={'index':index}
seen=set()
for row in index:
  lesson_id=row['id']
  assert lesson_id not in seen,'Duplicate lesson id '+lesson_id
  seen.add(lesson_id)
  lesson=json.loads((SRC/(lesson_id+'.json')).read_text(encoding='utf-8'))
  assert lesson['id']==lesson_id and all(k in lesson for k in ['title','theory','vocab','l2','l3','l4','l5','l6','fix']), 'Incomplete '+lesson_id
  all_data[lesson_id]=lesson
raw=json.dumps(all_data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
source=(ROOT/'app-template.html').read_text(encoding='utf-8')
assert source.count('__LESSONS_JSON__')==1
(ROOT/'index.html').write_text(source.replace('__LESSONS_JSON__',raw),encoding='utf-8')
# Cache version follows bundle bytes so clients pick up published lesson revisions.
sw=ROOT/'sw.js'
text=sw.read_text(encoding='utf-8')
short=hashlib.sha256((source+raw+(ROOT/'reader'/'index.html').read_text(encoding='utf-8')+(ROOT/'words'/'index.html').read_text(encoding='utf-8')+(ROOT/'words/bank.js').read_text(encoding='utf-8')).encode()).hexdigest()[:9]
text=re.sub(r"english-review-v5-[A-Za-z0-9]+",'english-review-v5-'+short,text)
sw.write_text(text,encoding='utf-8')
print('Built index.html with',len(index),'sections, cache',short)

# Anonymised learning context: no private answers, source boards or identity.
context=[]
for row in index:
    L=all_data[row['id']]
    context.append({'id':row['id'],'title':L['title'],'grammar':[s['h'] for s in L['theory']], 'vocab':[v['en'].lower() for v in L['vocab']]})
(ROOT/'reader/context.js').write_text('window.ENGLISH_READING_CONTEXT='+json.dumps(context,ensure_ascii=False).replace('<','\\\\u003c')+';'+chr(10),encoding='utf-8')
