"""Exhaustive finite answer banks and real mobile flows. No external API is allowed."""
import collections,functools,http.server,json,re,subprocess,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent.parent
index=json.loads((R/'lesson-data/index.json').read_text(encoding='utf-8'))
rules=json.loads((R/'lesson-data/answerrules.json').read_text(encoding='utf-8'))
def tokens(s):return re.sub(r'[!?.,;:"()]','',s.replace('’',"'")).lower().split()
banks=0
for key,r in rules.items():
 assert r['why'].strip() and all(r['example'][k].strip() for k in ['en','ru','source']),key
 assert not re.search('Сравни смысл и формулу|Сравни структуру с образцом',r['why']),key
 if 'wordBank' not in r:continue
 banks+=1;b=r['wordBank'];assert r['closed'] and r['translation'] and len(b['distractors'])==3,key
 stock=collections.Counter(tokens(' '.join(b['required']+b['alternatives'])))
 for a in r['accept']:assert not collections.Counter(tokens(a))-stock,(key,a)
 assert not set(w.lower() for w in b['distractors']).intersection(stock),key
assert banks>200
assert rules['05/l3:15']['example']['en']=='According to the report, sales increased.'
texts=json.loads((R/'reader/texts.json').read_text(encoding='utf-8'))
assert [t['id'] for t in texts[:4]]==['l3a','b1','b2','b3']
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)))
threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
html=(R/'index.html').read_text(encoding='utf-8').replace('window.__reviewDebug=','window.__offlineTest={poolFor,mkWord,grade,norm,localFailure,snapshotAnswer,countsFor,feedbackFor};window.__reviewDebug=')
try:
 with sync_playwright() as p:
  # Full content check uses the exact production checker, not a parallel Python grader.
  browser=p.chromium.launch();context=browser.new_context(service_workers='block');page=context.new_page()
  page.route(url+'/',lambda r:r.fulfill(body=html,content_type='text/html'));page.goto(url)
  result=page.evaluate('''()=>{const T=__offlineTest;let references=0,builds=0,recognition=0;
   for(const row of ENGLISH_LESSONS.index)for(const mode of ['l2','l3','l4','l5','fix',...(row.id==='13'?['h1','h2','h3','h4','h5']:[])])for(const q of T.poolFor(ENGLISH_LESSONS[row.id],mode)){
    const rule=ENGLISH_LESSONS.answerRules[row.id+'/'+q.key],B={checked:true,lesson:row.id,answers:{}};
    if(q.kind==='choice'){B.answers[q.key]=q.correctIndex;if(T.grade(q,B)!==true)throw Error(row.id+q.key);references++;continue;}
    for(const a of rule.accept){B.answers[q.key]=a;if(T.grade({...q,kind:'text'},B)!==true)throw Error(row.id+q.key+a);references++;
     if(q.kind==='build'){const used=new Set();B.answers[q.key]=a.replace(/[!?.,;:()]/g,'').split(/\s+/).map(t=>{const j=q.tokens.findIndex((w,k)=>!used.has(k)&&w.toLowerCase()===t.toLowerCase().replace(/’/g,"'"));if(j<0)throw Error('Missing token '+row.id+q.key+t);used.add(j);return j});if(T.grade(q,B)!==true)throw Error('Variant cannot be built '+row.id+q.key+a);}}
    for(const e of rule.bad){B.answers[q.key]=e.answer;if(T.grade({...q,kind:'text'},B)!==false)throw Error('Known error not rejected '+row.id+q.key+e.answer);}

    if(q.kind==='build'){builds++;B.answers[q.key]=Array.from({length:q.correctTokenCount},(_,i)=>i);if(T.grade(q,B)!==true)throw Error('Impossible canonical '+row.id+q.key);
     B.answers[q.key]=[0];if(T.grade(q,B)!==false)throw Error('Incomplete is not locally incorrect '+row.id+q.key);
     B.answers[q.key]=q.order;if(T.grade(q,B)!==false)throw Error('Distractors accepted '+row.id+q.key);
     B.answers[q.key]=[];if(T.grade(q,B)!=='skipped')throw Error('Empty not skipped');}
   }
   for(const row of ENGLISH_LESSONS.index)for(const direction of ['en','ru'])for(let i=0;i<ENGLISH_LESSONS[row.id].vocab.length;i++){const q=T.mkWord(ENGLISH_LESSONS[row.id],i,direction),B={checked:true,lesson:row.id,answers:{[q.key]:q.correctIndex}};if(T.grade(q,B)!==true)throw Error('Recognition '+row.id+q.key);B.answers[q.key]=(q.correctIndex+1)%q.options.length;if(T.grade(q,B)!==false)throw Error('Wrong recognition accepted');delete B.answers[q.key];if(T.grade(q,B)!=='skipped')throw Error('Empty recognition not skipped');recognition++;}
   const find=(lid,mode,predicate)=>T.poolFor(ENGLISH_LESSONS[lid],mode).find(predicate);
   const check=(q,answer,expected)=>{if(!q)throw Error('Missing regression task');const B={checked:true,lesson:q.lessonId,answers:{[q.key]:answer}};if(T.grade({...q,kind:'text'},B)!==expected)throw Error(q.key+' '+answer);};
   check(find('05','l4',q=>q.correct.includes('podcast')),"If I'm a bored, I listen to podcast.",false);
   const tired=find('05','l4',q=>q.correct.includes('lie down'));check(tired,'If I am tired, I lie down.',true);check(tired,"If I'm tired, I lie down.",true);
   check(find('05','l4',q=>q.correct.includes('waste time')),"Don't waste time on way to the office.",false);
   check(find('05','l3',q=>q.correct==='according'),'Eccording',false);
   for(const a of ['Talita likes her job.','She helps her parents.',"I'm very busy. How about you?"])check(find('04','l5',q=>ENGLISH_LESSONS.answerRules['04/'+q.key].accept.some(v=>T.norm(v)===T.norm(a))),a,true);
   const decision=find('13','l5',q=>q.correct==='I made a decision.');check(decision,'I made decision.',false);check(decision,'I made a decision.',true);
   const smart=find('13','l5',q=>q.correct==='She is a smart girl.');check(smart,'She is smart girl.',false);
   check(find('04','fix',q=>q.key==='fix:1'),"He don't earn money.",false);
   check(find('04','fix',q=>q.key==='fix:0'),'How is going?',false);
   check(find('04','fix',q=>q.key==='fix:3'),'This centre helps people take care of their kids.',true);
   check(find('04','fix',q=>q.key==='fix:3'),'THIS CENTER HELPS PEOPLE TAKE CARE OF THEIR KIDS!',true);
   const buying={key:'regression:like',mode:'l5',kind:'text',lessonId:'13',prompt:'Мне нравится покупать одежду.',correct:'I like buying clothes.',accept:['I like buying clothes.','I like to buy clothes.']};check(buying,'I like to buy clothes.',true);check(buying,'I like buying clothes.',true);
   if(T.norm("She's got a job.")===T.norm('She is got a job.'))throw Error('Ambiguous contraction changes meaning');
   return {references,builds,recognition};}''')
  browser.close();print('PASS exhaustive local references/banks and requested regressions',result,flush=True)
  for engine in [p.chromium,p.webkit]:
   browser=engine.launch()
   for width in [320,360,375,390,430]:
    context=browser.new_context(viewport={'width':width,'height':844},color_scheme='dark',service_workers='block')
    page=context.new_page();errors=[];calls=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def route(r):
     if r.request.url.startswith(url):r.continue_()
     else:
      if '.workers.dev' in r.request.url or 'api.openai.com' in r.request.url:calls.append(r.request.url)
      r.abort()
    context.route('**/*',route)
    page.goto(url);page.locator('#lesson-select').select_option('05');page.locator('#view-nav [data-tab="l4"]').click()
    # Submit one actual clicked token; every other task remains empty.
    page.locator('.qcard').first.locator('[data-word-add]').first.click();assert page.locator('#check-btn').is_enabled()
    page.locator('#check-btn').click();st=page.evaluate("__reviewDebug.getState().drafts['05/l4']")
    assert st['completed'] and st['counts']=={'correct':0,'incorrect':1,'skipped':7,'ungraded':0},st.get('counts')
    assert page.locator('#smart-retry,#continue-local,#edit-pending').count()==0
    assert page.evaluate("Object.keys(__reviewDebug.getState().progress['05'].mistakes).length")==1
    assert 'Пропущено:' in page.locator('.assessment-counts').inner_text()
    saved=st['answers'];page.reload();assert page.evaluate("__reviewDebug.getState().drafts['05/l4'].answers")==saved
    # Existing iPhone drafts that were checked but pending must finish locally after upgrade.
    page.evaluate('''()=>{const s=__reviewDebug.getState(),b=s.drafts['05/l4'];b.completed=false;delete b.bankVersion;delete b.results;s.progress['05'].attempts=[];localStorage.setItem('english-review:v4',JSON.stringify(s));}''');page.reload()
    assert page.evaluate("__reviewDebug.getState().drafts['05/l4'].completed") and page.locator('#smart-retry').count()==0
    assert page.evaluate("Object.keys(__reviewDebug.getState().progress['05'].mistakes).length")==1
    page.screenshot(path=str(R.parent/'reports'/f'offline-{engine.name}-{width}-build.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('build',engine.name,width)
    # Bottom navigation and primary action have separate rows on narrow screens.
    assert page.locator('.page-navigation').bounding_box()['y']<page.locator('.check-actions').bounding_box()['y']
    # A synthetic keyboard viewport verifies the handler without claiming a physical iPhone test.
    page.evaluate("Object.defineProperty(visualViewport,'height',{value:340,configurable:true});visualViewport.dispatchEvent(new Event('resize'))")
    assert page.locator('#footer').evaluate("e=>getComputedStyle(e).position")=='static'
    page.evaluate("delete visualViewport.height;visualViewport.dispatchEvent(new Event('resize'))")

    page.locator('#lesson-select').select_option('13');page.locator('#view-nav [data-tab="l5"]').click()
    page.locator('[data-answer-text]').first.fill('My own ambiguous translation.');page.locator('#check-btn').click()
    assert page.locator('#smart-retry').count()==1 and 'Правильный вариант:' in page.locator('.explanation').first.inner_text()
    assert page.evaluate("__reviewDebug.getState().drafts['13/l5'].counts.ungraded")==1
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('free',engine.name,width)
    page.locator('#continue-local').click();assert page.evaluate("__reviewDebug.getState().progress['13'].pendingAttempts.length")==1
    page.goto(url+'/#homework13');assert page.locator('[data-homework-answer]').count()==8
    assert 'go past an old church' in page.locator('#body').inner_text() and 'opposite a big bookshop' in page.locator('#body').inner_text()
    page.locator('[data-homework-answer="0"]').fill('My own route sentence.');page.locator('#homework-route').fill('Turn left at the lights.');page.reload()
    assert page.locator('#homework-route').input_value()=='Turn left at the lights.'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('homework',engine.name,width)
    page.goto(url+'/words/');page.locator('[data-mode="cards"]').click()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('words',engine.name,width)
    page.locator('.card').first.click()
    assert page.locator('.face.back').evaluate('(e)=>e.scrollHeight>=e.clientHeight')
    page.screenshot(path=str(R.parent/'reports'/f'offline-{engine.name}-{width}-words.png'),full_page=True)
    page.locator('[data-mode="r5"]').click();page.locator('#win').fill('unfinished');page.reload();assert page.locator('#win').input_value()=='unfinished'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('writing',engine.name,width)
    page.goto(url+'/reader/');assert page.locator('#genBox').get_attribute('open') is None
    page.locator('#textList .card').first.click();assert page.locator('#rText .w').count()>20
    page.locator('#rText .w').first.click();assert page.locator('#sheet').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('reader',engine.name,width)
    page.screenshot(path=str(R.parent/'reports'/f'offline-{engine.name}-{width}-reader.png'),full_page=True)
    assert page.locator('input[type="password"]').count()==0 and not calls,calls
    assert not errors,errors
    context.close();print('PASS API disconnected, incomplete/skip statistics, reload and mobile',engine.name,width,flush=True)
   browser.close()
finally:server.shutdown()
print('PASS',len(rules),'audited exercise rules;',banks,'complete sentence banks; all mobile sizes')
