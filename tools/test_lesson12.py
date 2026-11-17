"""Lesson 12 acceptance: source preservation, offline answers, Safari/mobile and storage.
No production API calls, personal sources or owner credentials are used.
"""
import functools,http.server,json,re,subprocess,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent.parent
baseline='418171bee8f690ff6f9ef4c5c6b995374b0d36b5'
def prior(file):return json.loads(subprocess.check_output(['git','show',baseline+':'+file],cwd=R).decode('utf-8'))
index=json.loads((R/'lesson-data/index.json').read_text(encoding='utf-8'))
assert index[:-1]==prior('lesson-data/index.json') and index[-1]['id']=='12'
assert '11' not in [x['id'] for x in index]
for row in index[:-1]:assert json.loads((R/f"lesson-data/{row['id']}.json").read_text(encoding='utf-8'))==prior(f"lesson-data/{row['id']}.json")
old=prior('words/bank.json');bank=json.loads((R/'words/bank.json').read_text(encoding='utf-8'))
assert bank['packs'][:len(old['packs'])]==old['packs']
for k in old:
 if k!='packs':assert bank[k]==old[k],k
new=bank['packs'][len(old['packs']):];assert len(new)==5
canonical=[w['en'] for p in bank['packs'] for w in p['words']]
added=[w['en'] for p in new for w in p['words']]
previous={w['en'] for p in old['packs'] for w in p['words']}
assert len(added)==81 and len(added)==len(set(added)) and not previous.intersection(added)
for pack in new:
 assert 15<=len(pack['words'])+len(pack['wordRefs'])<=20
 assert len(pack['wordRefs'])==3
 for w in pack['words']:assert not w['rep'] and len(w['collocations'])>=2 and w['ex']!=w['ex2']
assert len(bank['transportReference'])==27
L=json.loads((R/'lesson-data/12.json').read_text(encoding='utf-8'))
assert {k:len(L[k]) for k in ['vocab','l2','l3','l4','l5','fix','l6']}==dict(vocab=30,l2=30,l3=26,l4=20,l5=18,fix=16,l6=10)
assert len(L['theory'])==10
for s in L['theory']:
 assert 3<=len(s['ex'])<=6 and len(s['warn'])>=2 and s['practice']
for mode in ['l2','l3','l4','l5','fix']:
 for q in L[mode]:assert 'Ещё пример:' in q['why'] and re.search('[А-Яа-я]',q['why'])
for phrase in ['many thoughts','near my house','late for work','a good option','There is','They are','traffic lights','through','across']:
 assert phrase in json.dumps(L,ensure_ascii=False),phrase
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)))
threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as p:
  for engine,width in [(p.chromium,1280),(p.chromium,390),(p.webkit,390)]:
   browser=engine.launch();ctx=browser.new_context(viewport={'width':width,'height':844},service_workers='block');page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   instrument=(R/'index.html').read_text(encoding='utf-8').replace('window.__reviewDebug=', 'window.__lesson12Test={poolFor,grade};window.__reviewDebug=')
   page.route(url+'/',lambda route:route.fulfill(body=instrument,content_type='text/html'))
   page.goto(url)
   assert page.evaluate('''()=>{const L=ENGLISH_LESSONS['12'];let n=0;for(const mode of ['l1','l2','l3','l4','l5','fix'])for(const q of __lesson12Test.poolFor(L,mode)){const values=q.kind==='choice'?[q.correctIndex]:q.kind==='build'?[Array.from({length:q.correctTokenCount},(_,i)=>i)]:q.accept;for(const answer of values){const b={checked:true,answers:{[q.key]:answer}};if(__lesson12Test.grade(q,b)!==true)throw Error(mode+q.key);n++;}if(q.kind==='choice'&&__lesson12Test.grade(q,{checked:true,answers:{[q.key]:(q.correctIndex+1)%q.options.length}})!==false)throw Error('wrong choice accepted');}return n>=140;}''')
   page.locator('#lesson-select').select_option('03');page.locator('[data-tab="l3"]').first.click()
   olddraft=page.evaluate("__reviewDebug.getState().drafts['03/l3']")
   page.locator('#lesson-select').select_option('12');page.locator('[data-tab="theory"]').first.click()
   assert page.locator('.theory-body').count()==10
   for detail in page.locator('.section > details').all():detail.evaluate('el=>el.open=true')
   assert page.locator('.theory-body .example').count()>=50
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   for mode in ['l1','l2','l3','l4','l5','fix']:
    page.locator('#view-nav [data-tab="'+mode+'"]').click();assert page.locator('.qcard').count()==4
    assert page.locator('.explanation').count()==0
    key='12/'+('l1:en' if mode=='l1' else mode)
    if mode=='l4':
     block=page.evaluate('(k)=>__reviewDebug.getState().drafts[k]',key)
     assert all(len(q['tokens'])==q['correctTokenCount']+3 for q in block['items'])
    # Correct known answers are entirely local, including sentence-build token selection.
    page.evaluate('''key=>{const s=__reviewDebug.getState(),b=s.drafts[key];for(const q of b.items)b.answers[q.key]=q.kind==='choice'?q.correctIndex:q.kind==='build'?Array.from({length:q.correctTokenCount},(_,i)=>i):q.accept[0];localStorage.setItem('english-review:v4',JSON.stringify(s));}''',key)
    page.reload();page.locator('#check-btn').click()
    assert page.evaluate('(k)=>__reviewDebug.getState().drafts[k].completed',key)
    assert page.evaluate('(k)=>__reviewDebug.getState().drafts[k].percentage',key)==100
    assert len(ctx.pages)==1,'Known answers must not open an API popup'
    assert page.locator('.explanation').count()==4
    page.reload();assert page.evaluate('(k)=>__reviewDebug.getState().drafts[k].completed',key)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.locator('#view-nav [data-tab="conversation"]').click()
   assert page.locator('[data-conversation]').count()==4
   assert page.locator('[data-conversation-reveal]').first.is_disabled()
   assert page.locator('.example').count()==0
   page.locator('[data-conversation="0"]').fill('I go by bus.');page.reload()
   assert page.locator('[data-conversation="0"]').input_value()=='I go by bus.'
   page.locator('[data-conversation-reveal="0"]').click();assert page.locator('.example').count()==1
   page.reload();assert page.locator('.example').count()==1
   page.locator('[data-conversation-page="1"]').click();assert page.locator('[data-conversation="4"]').count()==1
   assert page.evaluate("__reviewDebug.getState().drafts['03/l3']")==olddraft
   page.locator('#view-nav [data-tab="history"]').click()
   assert page.evaluate("__reviewDebug.getState().progress['12'].attempts.length")==6
   with page.expect_download() as info:page.locator('#export-btn').click()
   saved=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
   assert saved['state']['drafts']['12/conversation']['answers']['0']=='I go by bus.'
   page.on('dialog',lambda d:d.accept())
   page.locator('#import-file').set_input_files({'name':'progress.json','mimeType':'application/json','buffer':json.dumps(saved).encode()})
   page.wait_for_timeout(100)
   assert page.evaluate("__reviewDebug.getState().progress['12'].attempts.length")==6
   page.goto(url+'/words/')
   assert page.locator('details').filter(has_text='расширенный справочник').count()==1
   packs=page.evaluate("__wordsDebug.packs.map((p,i)=>({id:p.id,i,n:p.words.length})).filter(p=>p.id.startsWith('lesson12-'))")
   for pack in packs:
    assert 15<=pack['n']<=20
    page.locator('[data-pack="'+str(pack['i'])+'"]').click();page.locator('[data-mode="r5"]').click()
    assert not re.search('[a-z]',page.locator('.qprompt').inner_text(),re.I)
    page.locator('#win').fill('draft');page.reload();assert page.locator('#win').input_value()=='draft'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.goto(url+'/reader/');assert page.locator('#genLesson option[value="12"]').count()==1
   assert page.locator('#genTopic optgroup option').count()==6
   page.locator('#genLesson').select_option('12');page.locator('#genTopic').select_option(label='An accessible city')
   req=page.evaluate('requestForReader()');assert req['lesson']=='12' and req['topic']=='An accessible city'
   context=json.loads(req['context']);selected=next(x for x in context['selected'] if x['lesson']=='12')
   assert 'There is/are vs they are' in selected['grammar'][0]
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   assert not errors,errors
   browser.close();print('PASS lesson12 mobile/content/local answers/drafts/words/reader',engine.name,width,flush=True)
finally:server.shutdown()
print('PASS old lessons/packs byte-equivalent, 81 canonical additions, deferred sources excluded')
