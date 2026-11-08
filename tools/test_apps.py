import contextlib, functools, http.server, json, re, subprocess, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for width in (1280,390):
   context=browser.new_context(viewport={'width':width,'height':844},service_workers='block')
   page=context.new_page(); errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
   for route in ('/','/reader/','/words/'):
    page.goto(url+route); page.wait_for_timeout(150)
    assert page.locator('body').inner_text().strip()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), f'Overflow {route} {width}'
   page.goto(url+'/reader/')
   page.locator('#textList .card').first.click()
   assert page.locator('#rText .w').count()>20
   page.locator('#rText .w').first.click()
   assert page.locator('#sheet').is_visible()
   assert page.evaluate("localStorage.getItem('chitalka.last')")
   page.goto(url+'/words/')
   page.locator('[data-pack="0"]').click()
   page.reload(); assert page.locator('[data-pack="0"]').get_attribute('aria-pressed')=='true'
   page.locator('[data-mode="r1"]').click()
   assert page.locator('body').inner_text().strip()
   page.goto(url)
   assert page.locator('#lesson-select option').count()==10
   page.locator('#lesson-select').select_option('03')
   page.locator('#view-nav [data-tab="l1"]').click()
   assert page.locator('.qcard').count()==4
   for direction in ('en','ru'):
    page.locator('#recognition-dir').select_option(direction)
    page.evaluate('''() => {const s=window.__reviewDebug.getState(); const b=s.drafts['03/l1:'+s.prefs.l1Direction]; for(const q of b.items) b.answers[q.key]=q.correctIndex; localStorage.setItem('english-review:v4',JSON.stringify(s));}''')
    page.reload(); page.locator('#check-btn').click()
    assert page.locator('.explanation').count()==4
    assert page.locator('#footer .centre').inner_text().startswith('1/')
   state=page.evaluate('window.__reviewDebug.getState()')
   assert len(state['progress']['03']['attempts'])==2
   assert len(state['drafts']['03/l1:en']['answers'])>0
   page.locator('#view-nav [data-tab="l4"]').click()
   block=page.evaluate("window.__reviewDebug.getState().drafts['03/l4']")
   assert all(len(q['tokens'])==q['correctTokenCount']+3 for q in block['items'])
   page.reload(); assert page.evaluate("window.__reviewDebug.getState().progress['03'].attempts.length")==2
   # Real v4 state migration, preserving history, drafts, mistakes and unlock data.
   legacy={'version':4,'lesson':'03','tab':'theory','prefs':{'pageSize':2},'progress':state['progress'],'drafts':state['drafts']}
   page.evaluate('(s)=>localStorage.setItem("english-review:v4",JSON.stringify(s))',legacy)
   page.reload(); migrated=page.evaluate('window.__reviewDebug.getState()')
   assert migrated['prefs']['pageSize']==4
   assert migrated['progress']==legacy['progress'] and migrated['drafts']==legacy['drafts']
   page.locator('#view-nav [data-tab="history"]').click()
   with page.expect_download() as info: page.locator('#export-btn').click()
   exported=json.loads(Path(info.value.path()).read_text(encoding='utf-8'))
   assert exported['format']=='english-review-v4'
   page.on('dialog',lambda d:d.accept())
   page.locator('#import-file').set_input_files({'name':'progress.json','mimeType':'application/json','buffer':json.dumps(exported).encode()})
   assert page.evaluate('window.__reviewDebug.getState().progress')==exported['state']['progress']
   assert not errors,errors
   context.close(); print('PASS browser desktop/mobile',width)
  context=browser.new_context(service_workers='block'); page=context.new_page()
  instrument=(ROOT/'index.html').read_text(encoding='utf-8').replace('window.__reviewDebug=', 'window.__test={norm,finish,grade,prog};window.__reviewDebug=')
  page.route(url+'/',lambda route:route.fulfill(body=instrument,content_type='text/html'))
  page.goto(url)
  assert page.evaluate("__test.norm('9 a.m.')===__test.norm('9 am')")
  assert page.evaluate('''__test.norm("I am at work.")===__test.norm("i am at work")''')
  page.evaluate("""() => {const p=__test.prog(); const q={key:'l2:0',mode:'l2',kind:'choice',prompt:'test',correct:'yes',correctIndex:0,options:['yes','no'],why:'Учебный пример'};
  for(const [i,answer] of [1,0,0].entries()){const b={id:'test-'+i,lesson:'03',mode:'l2',items:[q],answers:{'l2:0':answer},self:{},checked:true}; __test.finish(b); if(i<2 && !p.mistakes['l2:0'])throw Error('Mistake disappeared early');}
  if(p.mistakes['l2:0'])throw Error('Mistake persisted after two correct answers'); }""")
  print('PASS time normalization and two-correct mistake recovery')
  context.close(); browser.close()
finally: server.shutdown()
# Syntax check every inline script without running it.
for name in ('index.html','reader/index.html','words/index.html'):
 for script in re.findall(r'<script[^>]*>(.*?)</script>',(ROOT/name).read_text(encoding='utf-8'),re.S):
  result=subprocess.run(['node','--check'],input=script,text=True,encoding='utf-8',capture_output=True)
  assert result.returncode==0,result.stderr
print('PASS all inline JavaScript syntax')
