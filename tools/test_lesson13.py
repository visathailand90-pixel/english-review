"""Lesson 13 P0/P1 acceptance. Synthetic browser fixtures only; no provider requests."""
import functools,http.server,json,re,subprocess,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent.parent
basecommit='4323bf254b85e44ecf715ec362e909e8e18f352b'
def previous(f):return json.loads(subprocess.check_output(['git','show',basecommit+':'+f],cwd=R).decode('utf-8'))
index=json.loads((R/'lesson-data/index.json').read_text(encoding='utf-8'));oldindex=previous('lesson-data/index.json')
assert index[:len(oldindex)]==oldindex and index[len(oldindex)]['id']=='13'
for row in oldindex:
 before=previous(f"lesson-data/{row['id']}.json");after=json.loads((R/f"lesson-data/{row['id']}.json").read_text(encoding='utf-8'))
 if row['id']=='05':
  before['l4'][11]['ru']='Если мне скучно, я слушаю подкаст.';before['l4'][5]['en']='If I am tired, I lie down.'
 assert after==before, row['id']
bank=json.loads((R/'words/bank.json').read_text(encoding='utf-8'));old=previous('words/bank.json');assert bank['packs'][:len(old['packs'])]==old['packs']
new=[p for p in bank['packs'][len(old['packs']):] if p['id'].startswith('lesson13-')];words=[w['en'] for p in new for w in p['words']];assert len(words)==49 and len(set(words))==49
assert not {w['en'] for p in old['packs'] for w in p['words']}.intersection(words)
assert new[0]['id']=='lesson13-homework'
for pack in new:assert 10<=len(pack['words'])+len(pack.get('wordRefs',[]))<=15
L=json.loads((R/'lesson-data/13.json').read_text(encoding='utf-8'));assert len(L['homework'])==8
assert [x['answer'] for x in L['homework']]==['over','through','along','past','to','at','on','opposite']
assert sum(len(a) for a in L['homeworkPractice'].values())==40
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
service='https://english-reader-owner.english-fc53e115b617.workers.dev'
instrument=(R/'index.html').read_text(encoding='utf-8').replace('window.__reviewDebug=', 'window.__acceptance={poolFor,grade,localFailure,answerDifference,norm};window.__reviewDebug=')
portal=subprocess.check_output(['node','--input-type=module','-e',"import {portal} from './backend/portal.mjs';process.stdout.write(portal("+json.dumps(url)+"));"],cwd=R).decode('utf-8')
assert not re.search(r'<form|type=[\"\x27]password|/api/login',portal,re.I)
try:
 with sync_playwright() as p:
  for engine,width in [(p.chromium,1280),(p.chromium,390),(p.webkit,390)]:
   browser=engine.launch();ctx=browser.new_context(viewport={'width':width,'height':844},service_workers='block');page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));requests=[]
   ctx.on('request',lambda r:requests.append(r.url) if service in r.url or 'api.openai.com' in r.url else None)
   page.route(url+'/',lambda route:route.fulfill(body=instrument,content_type='text/html'))
   page.goto(url+'/#homework13');assert 'Домашняя работа' in page.locator('#body h2').inner_text()
   assert page.locator('[data-homework-answer]').count()==8;assert page.locator('#homework-route').input_value()==''
   assert page.locator('svg[role="img"]').count()==9
   for i in range(8):page.locator('[data-homework-answer="'+str(i)+'"]').fill('My own sentence '+str(i))
   page.locator('#homework-route').fill('Start at the park. Walk past the café.');page.reload()
   assert page.locator('[data-homework-answer="7"]').input_value()=='My own sentence 7'
   assert page.locator('#homework-route').input_value().startswith('Start at the park')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   with page.expect_download() as d:page.locator('#homework-export').click()
   text=Path(d.value.path()).read_text(encoding='utf-8');assert 'My own sentence 7' in text and 'Start at the park' in text and 'Cross over the road at the crossing.' not in text
   for i in range(5):page.locator('#map-ask').click()
   assert page.locator('#map-ask').is_disabled()
   page.goto(url+'/#homework13')
   for mode in ['h1','h2','h3','h4','h5']:
    page.locator('#body [data-tab="'+mode+'"]').click();assert page.locator('.qcard').count()==4
    key='13/'+mode
    page.evaluate('''k=>{const s=__reviewDebug.getState(),b=s.drafts[k];for(const q of b.items)b.answers[q.key]=q.kind==='choice'?q.correctIndex:q.kind==='build'?Array.from({length:q.correctTokenCount},(_,i)=>i):q.accept[0];localStorage.setItem('english-review:v4',JSON.stringify(s));}''',key)
    assert page.evaluate('location.hash')!='#homework13'
    page.reload();assert page.evaluate('__reviewDebug.getState().tab')==mode;page.locator('#check-btn').click()
    assert page.evaluate('(k)=>__reviewDebug.getState().drafts[k].completed',key)
    assert page.evaluate('(k)=>__reviewDebug.getState().drafts[k].percentage',key)==100
    page.locator('#view-nav [data-tab="homework"]').click()
   assert not requests,'Basic homework must not call AI'
   # Audit all finite reference variants and context-specific regressions locally.
   result=page.evaluate('''()=>{const T=__acceptance,L=ENGLISH_LESSONS;let count=0;for(const row of L.index)for(const mode of ['l2','l3','l4','l5','fix',...(row.id==='13'?['h1','h2','h3','h4','h5']:[])])for(const q of T.poolFor(L[row.id],mode)){const rule=L.answerRules[row.id+'/'+q.key];if(q.kind==='choice'){if(T.grade(q,{checked:true,lesson:row.id,answers:{[q.key]:q.correctIndex}})!==true)throw Error(q.key);count++;continue;}for(const answer of rule.accept){const candidate={...q,kind:'text'};if(T.grade(candidate,{checked:true,lesson:row.id,answers:{[q.key]:answer}})!==true)throw Error(row.id+q.key+answer);count++;}}const check=(lid,mode,index,answer,expected)=>{const q=T.poolFor(L[lid],mode)[index],b={checked:true,lesson:lid,answers:{[q.key]:answer}};if(T.grade(q,b)!==expected)throw Error(lid+q.key+answer);return T.localFailure(q,b);};check('13','h5',0,'You can cross over the road here.',true);check('13','h5',6,'There is a café on your right.',true);check('04','l5',6,'Talita likes her job.',true);check('04','l5',3,'She helps her parents.',true);check('04','l5',1,"I'm very busy. How about you?",true);check('04','fix',0,'How is it going?',true);check('04','fix',3,'This center helps people to take care of kids.',true);check('04','fix',1,"Right now he isn't earning any money from his job.",true);check('04','fix',2,'This girl works in Central.',null);const i=L['13'].l5.findIndex(q=>q.a[0]==='I made a decision.');const e=check('13','l5',i,'I made decision.',false);if(!e.part.includes('a')||e.part.includes('decision'))throw Error('Spelling blamed instead of article');check('13','l5',i,'I made a decision.',true);const j=L['13'].l5.findIndex(q=>q.a[0]==='She is a smart girl.');check('13','l5',j,'She is smart girl.',false);check('13','l5',j,'She is a smart girl.',true);for(const row of L.index)for(const q of T.poolFor(L[row.id],'l5'))if(q.correct.includes('like buying')){const answer=q.correct.replace('like buying','like to buy');if(T.grade(q,{checked:true,lesson:row.id,answers:{[q.key]:answer}})!==true)throw Error('like alternative');}return count;}''')
   assert result>1700 and not requests
   # Local results displayed immediately while one open answer remains pending.
   page.locator('#lesson-select').select_option('13');page.locator('#view-nav [data-tab="l5"]').click()
   page.evaluate("""()=>{const s=__reviewDebug.getState(),b=s.drafts['13/l5'];for(const q of b.items)b.answers[q.key]=q.accept[0];b.answers[b.items[0].key]='My own different sentence.';localStorage.setItem('english-review:v4',JSON.stringify(s));}""");page.reload();page.locator('#check-btn').click()
   before=page.evaluate("__reviewDebug.getState().drafts['13/l5'].answers");assert len(ctx.pages)==1 and not requests
   assert 'Правильно' in page.locator('#body').inner_text() and 'без оценки' in page.locator('#body').inner_text()
   page.reload();assert page.evaluate("__reviewDebug.getState().drafts['13/l5'].answers")==before
   # Optional secure portal: no session and all service failure states preserve all answers.
   ctx.route(service+'/portal',lambda route:route.fulfill(body=portal,content_type='text/html'))
   for code in [401,403,429,0]:
    def api_mock(route,request,code=code):
     if code==0:route.abort('timedout')
     else:route.fulfill(status=code,content_type='application/json',body=json.dumps({'error':{401:'unauthorized',403:'csrf_denied',429:'rate_limited'}[code]}))
    ctx.route(service+'/api/**',api_mock)
    with page.expect_popup() as d:page.locator('#smart-retry').click()
    popup=d.value;popup.wait_for_function("document.querySelector('#status').textContent!=='Проверяю доступность сохранённой сессии…'")
    assert popup.locator('form,input').count()==0
    assert page.evaluate("__reviewDebug.getState().drafts['13/l5'].answers")==before
    popup.close();ctx.unroute(service+'/api/**',api_mock)
    page.reload();assert page.evaluate("__reviewDebug.getState().drafts['13/l5'].answers")==before
   # Continue saves an immutable copy, without unconfirmed mistakes or fake score.
   page.locator('#continue-local').click();assert page.evaluate("__reviewDebug.getState().progress['13'].pendingAttempts[0].answers")==before
   page.locator('#view-nav [data-tab="history"]').click()
   with page.expect_download() as d:page.locator('#export-btn').click()
   exported=json.loads(Path(d.value.path()).read_text(encoding='utf-8'));assert exported['state']['drafts']['13/homework']['route'].startswith('Start')
   page.on('dialog',lambda d:d.accept());page.locator('#import-file').set_input_files({'name':'state.json','mimeType':'application/json','buffer':json.dumps(exported).encode()});page.wait_for_function("__reviewDebug.getState().progress['13'].pendingAttempts.length===1")
   # Offline after load: no protected endpoint needed for editing or grading.
   page.locator('#view-nav [data-tab="homework"]').click();ctx.set_offline(True);page.locator('[data-homework-answer="0"]').fill('Offline own sentence');assert page.evaluate("__reviewDebug.getState().drafts['13/homework'].answers['0']")=='Offline own sentence';ctx.set_offline(False);page.reload();assert page.locator('[data-homework-answer="0"]').input_value()=='Offline own sentence'
   page.screenshot(path=str(R.parent/'reports'/f'lesson13-{engine.name}-{width}.png'))
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
   page.goto(url+'/reader/');page.locator('#genBox > summary').click();assert page.locator('form,input[type="password"],#ownerEndpoint').count()==0;assert page.locator('#genLesson option[value="13"]').count()==1
   # With an already confirmed session, the real portal script can generate without any form.
   provider_mock_calls=[]
   story={'title':'Synthetic saved library test','paragraphs':['We walk to the library.'],'glossary':[{'f':'we','l':'we','ru':'мы'},{'f':'walk','l':'walk','ru':'идти'},{'f':'to','l':'to','ru':'к'},{'f':'the','l':'the','ru':'артикль'},{'f':'library','l':'library','ru':'библиотека'}],'phrases':[]}
   def confirmed_session(route):
    path=route.request.url.split('/api/')[-1]
    if path=='session':route.fulfill(content_type='application/json',body=json.dumps({'csrf':'synthetic-csrf','enabled':True,'bonusExpiresAt':'2026-11-29T21:00:00Z','limits':{'hour':3,'day':8}}))
    elif path=='generate':
     assert route.request.headers.get('x-csrf')=='synthetic-csrf'
     provider_mock_calls.append(route.request.post_data_json)
     route.fulfill(content_type='application/json',body=json.dumps({'id':'synthetic13','story':story}))
    else:raise AssertionError('Unexpected or login request: '+path)
   ctx.route(service+'/api/**',confirmed_session)
   page.locator('#genLesson').select_option('13')
   with page.expect_popup() as d:page.locator('#genBtn').click()
   popup=d.value;popup.locator('#create').wait_for(state='visible');assert popup.locator('form,input').count()==0
   popup.locator('#create').click();page.wait_for_function("JSON.parse(localStorage.getItem('chitalka.gen')).some(t=>t.id==='cloud-synthetic13')")
   page.reload();assert page.evaluate("JSON.parse(localStorage.getItem('chitalka.gen')).some(t=>t.id==='cloud-synthetic13')")
   assert len(provider_mock_calls)==1 and provider_mock_calls[0]['lesson']=='13'
   popup.close();ctx.unroute(service+'/api/**',confirmed_session)
   browser.close();print('PASS homework13, all local references/regressions, 0 basic API, failure preservation, mobile',engine.name,width,flush=True)
finally:server.shutdown()
print('PASS old lessons and packs unchanged; new words49; homework40; no input credentials')
