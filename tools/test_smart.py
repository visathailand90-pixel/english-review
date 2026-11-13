import functools,http.server,threading,json,re,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent.parent
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
service='https://english-reader-owner.english-fc53e115b617.workers.dev/portal'
fixtures=[{'key':'l5:0','mode':'l5','kind':'text','prompt':'Она умная девушка.','correct':'She is a smart girl.','accept':['She is a smart girl.'],'why':'Артикль перед исчисляемым существительным.'},{'key':'l5:1','mode':'l5','kind':'text','prompt':'Мне нравится покупать одежду.','correct':'I like buying clothes.','accept':['I like buying clothes.'],'why':'Like + -ing / to + V1.'},{'key':'l5:2','mode':'l5','kind':'text','prompt':'Я начинаю работать в восемь утра.','correct':'I start work at eight am.','accept':['I start work at eight am.'],'why':'Время.'}]
answers=['She is smart girl.','I like to buy clothes.','I start work at eight a.m.']
try:
 with sync_playwright() as p:
  for engine in [p.chromium,p.webkit]:
   for scenario in ['success','uncertain','offline']:
    browser=engine.launch();ctx=browser.new_context(viewport={'width':390,'height':844},service_workers='block');page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    portal="""<script>opener.postMessage({type:'english-reader-ready'},'*');addEventListener('message',e=>{if(e.data.type!=='english-review-request')return;const b=e.data.request;window.batch=b;if(SCENARIO==='offline'){opener.postMessage({type:'english-review-error',requestId:b.requestId,error:'rate_limited'},'*');return;}const results=b.items.map((q,i)=>({id:q.id,verdict:i===0?(SCENARIO==='uncertain'?'uncertain':'incorrect'):'correct',correction:i===0?'She is a smart girl.':q.answer,errorPart:i===0?'Пропущен a перед smart girl':'',explanation:'Перед исчисляемым существительным нужен артикль; like допускает to.',rule:i===0?'a + adjective + noun':'like + to + V1',category:i===0?'articles':'collocations',example:'He is a good teacher.',exampleRu:'Он хороший учитель.'}));opener.postMessage({type:'english-review-results',requestId:b.requestId,results},'*');});</script>""".replace('SCENARIO',json.dumps(scenario))
    ctx.route(service,lambda route:route.fulfill(body=portal,content_type='text/html'))
    page.goto(url);page.locator('#lesson-select').select_option('03');page.locator('#view-nav [data-tab="l5"]').click()
    page.evaluate("([items,answers])=>{const s=__reviewDebug.getState();let b=s.drafts['03/l5'];b.items=items;b.answers={};b.checked=false;b.completed=false;b.assessments={};s.progress={};s.drafts['09/l3']={sentinel:'preserve'};localStorage.setItem('english-review:v4',JSON.stringify(s));}",[fixtures,answers]);page.reload()
    for i,a in enumerate(answers):page.locator('[data-answer-text="l5:'+str(i)+'"]').fill(a)
    with page.expect_popup() as popped:page.locator('#check-btn').click()
    pop=popped.value;pop.wait_for_function('window.batch');assert pop.evaluate('batch.items.length')==2
    if scenario=='success':
     page.wait_for_function("__reviewDebug.getState().drafts['03/l5'].completed")
     st=page.evaluate('__reviewDebug.getState()');assert st['progress']['03']['attempts'][0]['score']==2
     assert st['progress']['03']['mistakes']['l5:0']['category']=='articles'
     assert 'She is smart girl.' in page.locator('.explanation').first.inner_text()
     assert 'a + adjective + noun' in page.locator('.explanation').first.inner_text()
     assert page.locator('[data-self]').count()==0
     page.reload();assert page.evaluate("__reviewDebug.getState().progress['03'].attempts.length")==1
     page.locator('#view-nav [data-tab="weak"]').click();assert page.locator('.qcard').count()==1
    else:
     page.wait_for_function("__reviewDebug.getState().drafts['03/l5'].aiStatus")
     page.reload();st=page.evaluate('__reviewDebug.getState()');assert not st['drafts']['03/l5']['completed'];assert not st['progress']['03']['attempts'];assert not st['progress']['03']['mistakes']
     assert list(st['drafts']['03/l5']['answers'].values())==answers
     assert page.locator('#smart-retry').count()==1 and page.locator('[data-self]').count()==0
    assert page.evaluate("__reviewDebug.getState().drafts['09/l3'].sentinel")=='preserve'
    assert not errors,errors
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    browser.close();print('PASS smart',engine.name,scenario,flush=True)
   browser=engine.launch();ctx=browser.new_context(viewport={'width':390,'height':844},service_workers='block');page=ctx.new_page();page.goto(url+'/words/')
   assert page.evaluate('ENGLISH_WORD_BANK.irregularVerbs.length')==50;assert page.evaluate('ENGLISH_WORD_BANK.pastVerbs.length')==100
   page.evaluate("localStorage.setItem('work2:best',JSON.stringify({r1:23}))")
   page.locator('[data-mode="irregular"]').click();page.locator('#verb-input').fill('was');page.locator('#verb-check').click();page.reload();assert page.locator('#verb-input').input_value()=='was' and page.locator('#verb-input').is_disabled()
   page.locator('#verb-next').click();page.locator('#verb-input').fill('bean');page.locator('#verb-check').click();assert 'Неверно' in page.locator('.fb').inner_text()
   page.locator('[data-mode="past"]').click();assert page.locator('#verb-stage option').count()==10
   page.locator('#verb-input').fill('was');page.locator('#verb-check').click();assert 'Правильно' in page.locator('.fb').inner_text()
   assert page.evaluate("JSON.parse(localStorage.getItem('work2:best')).r1")==23
   assert 'Пропущено' in page.evaluate("spellingDiff('decision','decison')")
   assert 'Лишняя' in page.evaluate("spellingDiff('decision','decisiion')")
   assert page.evaluate("norm('jewellery')===norm('jewelry')")
   page.locator('[data-mode="cards"]').click();last=page.evaluate('__wordsDebug.packs.length-1');page.locator('[data-pack="'+str(last)+'"]').click();assert page.evaluate('W.length')==15
   assert page.evaluate('W.filter(w=>w.rep).length')==3
   page.locator('[data-mode="r5"]').click();assert not re.search('[a-z]',page.locator('.qprompt').inner_text(),re.I)
   page.locator('#win').fill('fit');page.reload();assert page.locator('#win').input_value()=='fit'
   assert page.locator('#win').evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')>=20
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   browser.close();print('PASS verbs, word refs, spelling and persistence',engine.name,flush=True)
finally:server.shutdown()
# Canonical additions contain no duplicate of any previously existing word.
prior=json.loads(subprocess.check_output(['git','show','1e0066f:words/bank.json'],cwd=R).decode('utf-8'));current=json.loads((R/'words/bank.json').read_text(encoding='utf-8'))
old={w['en'] for p in prior['packs'] for w in p['words']};new=[w['en'] for p in current['packs'][len(prior['packs']):] for w in p['words']]
assert len(new)==12 and len(set(new))==12 and not old.intersection(new)
for before,after in zip(prior['packs'],current['packs']):assert [w['en'] for w in before['words']]==[w['en'] for w in after['words']]
print('PASS canonical vocabulary additions and existing order')
