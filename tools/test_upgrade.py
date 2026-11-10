import functools,http.server,threading,json,subprocess,re
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent.parent
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as p:
  for engine,width in [(p.chromium,1280),(p.chromium,390),(p.webkit,390)]:
   browser=engine.launch();context=browser.new_context(viewport={'width':width,'height':844},service_workers='block')
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url+'/words/')
   assert page.evaluate('__wordsDebug.packs.length')>=20
   assert page.evaluate('__wordsDebug.packs[0].id')=='clothes1'
   assert page.evaluate('__wordsDebug.packs[1].id')=='work2'
   for name in ['copy','r5']:
    page.locator('[data-mode="'+name+'"]').click()
    page.evaluate("Q.order=[0];Q.i=0;renderQ()")
    target=page.evaluate('W[0].en')
    if name=='copy':assert target in page.locator('.qprompt').inner_text()
    else: assert target not in page.locator('.qprompt').inner_text()
    page.locator('#win').fill(target+'x');page.locator('#check').click()
    assert 'С позиции' in page.locator('.fb').inner_text()
    page.reload();assert page.evaluate('__wordsDebug.getRound().answered')
    assert page.evaluate('Object.keys(__wordsDebug.getLearning().mistakes).length')==1
    page.locator('#nextq').click()
    for i in range(2):
     page.locator('[data-mode="'+name+'"]').click();page.evaluate("Q.order=[0];Q.i=0;renderQ()")
     page.locator('#win').fill(target);page.locator('#check').click();page.locator('#nextq').click()
    assert page.evaluate('Object.keys(__wordsDebug.getLearning().mistakes).length')==0
    assert page.evaluate("__wordsDebug.getLearning().streaks['"+name+"']")>=2
   # Data persisted separately for each pack, with old best untouched.
   page.evaluate("localStorage.setItem('work2:best',JSON.stringify({r1:23}))")
   page.locator('[data-pack="2"]').click();page.locator('[data-mode="copy"]').click()
   page.reload();assert page.evaluate("JSON.parse(localStorage.getItem('work2:best')).r1")==23
   for path in ['/','/words/','/reader/']:
    page.goto(url+path);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(engine.name,path)
   # Old generated texts survive; JSON export includes them; no endpoint => no API request.
   old={'id':'legacy-reading','title':'Old saved text','topic':'Local','paragraphs':['We buy apples.'],'dict':{'we':{'l':'we','ru':'мы','ipa':''}},'phr':{}}
   page.evaluate('(t)=>localStorage.setItem("chitalka.gen",JSON.stringify([t]))',old);page.reload()
   page.locator('#ownerEndpoint').evaluate('(el)=>el.value=""');page.locator('#genBtn').click();assert 'не подключён' in page.locator('#genStatus').inner_text()
   assert page.locator('#textList .card').count()>1
   with page.expect_download() as info:page.locator('#readerExport').click()
   saved=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
   assert saved['generated'][0]['id']=='legacy-reading'
   # A mock popup uses exactly the production postMessage handshake; no real provider.
   portal='''<script>const source=window.opener;source.postMessage({type:'english-reader-ready'},'*');addEventListener('message',e=>{if(e.data.type==='english-reader-request'){window.req=e.data.request;}});</script>'''
   context.route('https://mock-reader.workers.dev/portal',lambda route:route.fulfill(body=portal,content_type='text/html'))
   page.locator('details').filter(has=page.locator('#ownerEndpoint')).locator('summary').click()
   page.locator('#ownerEndpoint').fill('https://mock-reader.workers.dev/')
   with page.expect_popup() as popup:page.locator('#genBtn').click()
   pop=popup.value;pop.wait_for_function('window.req')
   assert pop.evaluate('req.lesson')=='03'
   assert 'verified_test_error' not in pop.evaluate('req.context')
   story={'title':'A new visit','paragraphs':['We buy apples.'],'glossary':[{'f':'we','l':'we','ru':'мы'},{'f':'buy','l':'buy','ru':'покупаем'},{'f':'apples','l':'apple','ru':'яблоки'}],'phrases':[]}
   for code in ['unauthorized','rate_limited','credits_or_limit_exhausted','timeout']:
    pop.evaluate("(error)=>opener.postMessage({type:'english-reader-error',error},'*')",code);page.wait_for_timeout(50)
    assert page.locator('#genStatus').inner_text()
   pop.evaluate("(story)=>opener.postMessage({type:'english-reader-story',id:'test-hash',story,lesson:'03'},'*')",story)
   page.wait_for_function("JSON.parse(localStorage.getItem('chitalka.gen')).length===2")
   assert page.locator('#rTitle').inner_text()=='A new visit'
   page.locator('#rText .w').first.click();assert 'мы' in page.locator('#sheet').inner_text()
   page.reload();assert page.evaluate("JSON.parse(localStorage.getItem('chitalka.gen')).some(t=>t.id==='legacy-reading')")
   assert not errors,errors
   if width==390:
    shots=R.parent/'reports/upgrade-20261110';shots.mkdir(exist_ok=True)
    for path,name in [('/','review'),('/words/','words'),('/reader/','reader')]:
     page.goto(url+path);page.screenshot(path=str(shots/f'{engine.name}-{name}.png'),full_page=True)
   browser.close();print('PASS upgrade',engine.name,width,': typing, spelling, two-correct recovery, persistence, library export, popup generation 200/401/429/timeout mocks')
finally:server.shutdown()
# Every old lesson, task and ordering remains a prefix.
baseline='86ab3f6'
for f in [R/'lesson-data'/n for n in ['index.json','01.json','01p.json']+[f'{i:02}.json' for i in range(2,10)]]:
 before=json.loads(subprocess.check_output(['git','show',baseline+':lesson-data/'+f.name],cwd=R).decode('utf-8'))
 after=json.loads(f.read_text(encoding='utf-8'))
 if f.stem=='index':assert after==before
 else:
  for k in ['vocab','l2','l3','l4','l5','l6','fix','theory']:assert after[k][:len(before[k])]==before[k],(f.name,k)
old=subprocess.check_output(['git','show',baseline+':words/index.html'],cwd=R).decode('utf-8')
new=(R/'words/index.html').read_text(encoding='utf-8')
assert old[old.index('const PACK1'):old.index('const PACKS')]==new[new.index('const PACK1'):new.index('const PACKS')]
print('PASS append-only lesson and legacy word-pack integrity')
