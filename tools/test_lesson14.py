"""Lesson 14: append-only regression, homework drafts and API-free mobile use."""
import functools,http.server,json,re,subprocess,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent.parent
BASE='60781928b5532b185facafbbafe44e654948b2bf'
def load(f):return json.loads((R/f).read_text(encoding='utf8'))
def old(f):return json.loads(subprocess.check_output(['git','show',BASE+':'+f],cwd=R).decode('utf8'))
index=load('lesson-data/index.json');before=old('lesson-data/index.json')
assert index[:-1]==before and index[-1]['id']=='14' and not any(x['id']=='11' for x in index)
for x in before:assert load('lesson-data/'+x['id']+'.json')==old('lesson-data/'+x['id']+'.json'),x['id']
rules=load('lesson-data/answerrules.json');previous=old('lesson-data/answerrules.json')
assert all(rules[k]==v for k,v in previous.items())
assert len(rules)-len(previous)==241 and all(k.startswith('14/') for k in rules.keys()-previous.keys())
bank=load('words/bank.json');ob=old('words/bank.json');assert bank['packs'][:len(ob['packs'])]==ob['packs']
assert {k:v for k,v in bank.items() if k!='packs'}=={k:v for k,v in ob.items() if k!='packs'}
new=bank['packs'][len(ob['packs']):];assert [p['id'] for p in new]==['lesson14-1','lesson14-2','lesson14-3']
nw=[w for p in new for w in p['words']];assert len(nw)==39 and len({w['en'] for w in nw})==39
assert not {w['en'].lower() for w in nw}&{w['en'].lower() for p in ob['packs'] for w in p['words']}
assert [len(p['words'])+len(p['wordRefs']) for p in new]==[18,18,15]
assert len({w for p in new for w in p['wordRefs']})==7
L=load('lesson-data/14.json');assert len(L['theory'])==20 and len(L['homework'])==15
assert sum(len(L[k]) for k in ['l2','l3','l4','l5','fix'])==166
assert len(L['vocab'])==46 and [len(v) for v in L['homeworkPractice'].values()]==[15]*5
texts=load('reader/texts.json');assert texts[:4]==old('reader/texts.json') and len(texts)==7
assert [t['id'] for t in texts[4:]]==['lesson14-route','lesson14-late','lesson14-questions']
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)))
threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
html=(R/'index.html').read_text(encoding='utf8').replace('window.__reviewDebug=','window.__lesson14Test={poolFor,grade};window.__reviewDebug=')
try:
 with sync_playwright() as p:
  for engine in [p.chromium,p.webkit]:
   browser=engine.launch()
   for width in [320,360,375,390,430]:
    ctx=browser.new_context(viewport={'width':width,'height':844},color_scheme='dark',service_workers='block',accept_downloads=True);requests=[];errors=[]
    ctx.on('request',lambda r:requests.append(r.url) if not r.url.startswith(url) else None)
    ctx.route('https://**/*',lambda r:r.abort());page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.route(url+'/',lambda r:r.fulfill(body=html,content_type='text/html'));page.goto(url)
    assert page.locator('#homework-link').get_attribute('href')=='#homework14'
    page.goto(url+'/#homework13');page.locator('[data-homework-answer="0"]').fill('Old homework sentence');page.locator('#homework-route').fill('Old route')
    page.goto(url+'/#homework14');page.reload()
    assert page.locator('[data-homework14-answer]').count()==15 and page.locator('#homework14-story').input_value()==''
    assert all(page.locator('[data-homework14-answer]').nth(i).input_value()=='' for i in range(15))
    page.locator('[data-homework14-answer="0"]').fill('My own homework sentence.');page.locator('#homework14-story').fill('My own story.');page.reload()
    assert page.locator('#homework14-story').input_value()=='My own story.'
    with page.expect_download() as d:page.locator('#homework14-export').click()
    exported=Path(d.value.path()).read_text(encoding='utf8');assert 'My own homework sentence.' in exported and 'My own story.' in exported
    assert 'My alarm did not go off, so I woke up late.' not in exported
    if not page.evaluate('document.documentElement.scrollWidth<=innerWidth'):
     page.screenshot(path=str(R.parent/'reports'/f'lesson14-overflow-{engine.name}-{width}.png'))
     print(page.evaluate("[innerWidth,document.documentElement.scrollWidth,...Array.from(document.querySelectorAll('main *,#body *')).filter(e=>e.getBoundingClientRect().right>innerWidth+.5).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right,e.textContent.slice(0,50)])]"),flush=True)
     raise AssertionError('Homework document overflow')
    if width in [320,390]:page.screenshot(path=str(R.parent/'reports'/f'lesson14-homework-{engine.name}-{width}.png'))
    for mode in ['h1','h2','h3','h4','h5']:
     page.locator('#body [data-tab="'+mode+'"]').click();key='14/'+mode
     page.evaluate('''k=>{const s=__reviewDebug.getState(),b=s.drafts[k];for(const q of b.items)b.answers[q.key]=q.kind==='choice'?q.correctIndex:q.kind==='build'?Array.from({length:q.correctTokenCount},(_,i)=>i):q.accept[0];localStorage.setItem('english-review:v4',JSON.stringify(s));}''',key)
     page.reload();assert page.evaluate('location.hash')!='#homework14';page.locator('#check-btn').click()
     assert page.evaluate('(k)=>__reviewDebug.getState().drafts[k].percentage',key)==100
     page.locator('#view-nav [data-tab="homework14"]').click()
    page.locator('#body [data-tab="homework"]').click();assert page.locator('[data-homework-answer="0"]').input_value()=='Old homework sentence'
    assert page.locator('#homework-route').input_value()=='Old route'
    page.locator('#lesson-select').select_option('14');page.locator('#view-nav [data-tab="l4"]').click()
    assert page.locator('#check-btn').is_enabled();page.locator('.qcard').first.locator('[data-word-add]').first.click();page.locator('#check-btn').click()
    assert page.evaluate("__reviewDebug.getState().drafts['14/l4'].checked")
    assert not requests,requests
    page.goto(url+'/words/');overlays=page.evaluate("__wordsDebug.packs.filter(p=>p.id.startsWith('lesson14-')).flatMap(p=>p.words).filter(w=>w.canonicalRef).map(w=>[w.en,w.canonicalRef])")
    assert ['cancel','cancelled'] in overlays and ['get lost','lost'] in overlays
    page.goto(url+'/reader/');assert page.locator('#genLesson option[value="14"]').count()==0;assert page.locator('#textList .card').count()==7
    unresolved=page.evaluate('''()=>window.ENGLISH_STATIC_TEXTS.filter(t=>t.id.startsWith('lesson14-')).map(t=>({id:t.id,missing:[...new Set(t.paragraphs.join(' ').match(/[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[-'’][A-Za-z]+)*/g))].filter(f=>!resolve(f,t))}))''')
    assert not any(x['missing'] for x in unresolved),unresolved
    assert not errors,errors
    ctx.close();print('PASS lesson14 mobile homework, drafts, export, old13, no API',engine.name,width,flush=True)
   browser.close()
finally:server.shutdown();server.server_close()
print('PASS baseline6078192 preserved; new39 words, 241 exercises, 3 original reader texts')
