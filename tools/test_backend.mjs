import assert from "node:assert/strict";
import {DatabaseSync} from "node:sqlite";
import {handle} from "../backend/worker.mjs";
import {validateStory} from "../backend/contracts.mjs";
const sql=new DatabaseSync(":memory:");
sql.exec("CREATE TABLE sessions(token TEXT PRIMARY KEY,csrf TEXT,expires INTEGER);CREATE TABLE quota(key TEXT PRIMARY KEY,n INTEGER);CREATE TABLE flags(key TEXT PRIMARY KEY,value TEXT);CREATE TABLE texts(id TEXT PRIMARY KEY,data TEXT,created INTEGER)");
const DB={prepare(q){let args=[];return {bind(...a){args=a;return this;},async first(){return sql.prepare(q).get(...args)||null;},async all(){return {results:sql.prepare(q).all(...args)};},async run(){return sql.prepare(q).run(...args);}};}};
const sha=async s=>Buffer.from(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s))).toString("hex");
const env={DB,PAGES_ORIGIN:"https://owner.example",OWNER_SECRET_SALT:"test-salt",OWNER_SECRET_HASH:await sha("test-salt"+"test-owner-passphrase"),GENERATION_ENABLED:"true",BONUS_ONLY_CONFIRMED:"true",BONUS_EXPIRES_AT:new Date(Date.now()+60000).toISOString(),OPENAI_MODEL:"mock-only-model",OPENAI_API_KEY:"mock-not-a-real-key"};
const origin="https://reader-owner.example";let cookie="",csrf="";let calls=0;
function request(path,data,headers={}){return new Request(origin+path,{method:data?"POST":"GET",headers:{...(data?{"Content-Type":"application/json",Origin:origin}:{}),...(cookie?{Cookie:cookie}:{}),...(csrf?{"X-CSRF":csrf}:{}),...headers},body:data?JSON.stringify(data):undefined});}
const story={title:"A visit",paragraphs:Array.from({length:3},()=>Array(20).fill("We buy apples.").join(" ")),glossary:[{f:"we",l:"we",ru:"мы"},{f:"buy",l:"buy",ru:"покупаем"},{f:"apples",l:"apple",ru:"яблоки"}],phrases:[]};
const mock=async()=>{calls++;return Response.json({status:"completed",output:[{content:[{type:"output_text",text:JSON.stringify(story)}]}]});};
assert.equal((await handle(request("/api/generate",{}),env,mock)).status,401);
assert.equal((await handle(request("/api/login",{password:"wrong"}),env,mock)).status,401);
assert.equal((await handle(request("/api/login",{password:"test-owner-passphrase"},{Origin:"https://evil.example"}),env,mock)).status,403);
let r=await handle(request("/api/login",{password:"test-owner-passphrase"}),env,mock);assert.equal(r.status,200);
cookie=r.headers.get("set-cookie").split(";")[0];csrf=(await r.json()).csrf;assert.match(r.headers.get("set-cookie"),/Secure; HttpOnly; SameSite=Strict/);
const b={lesson:"03",format:"story",level:"A2",words:180,topic:"Food",context:"neutral words only"};
assert.equal((await handle(request("/api/generate",b,{"X-CSRF":"bad"}),env,mock)).status,403);
assert.equal((await handle(request("/api/generate",b),{...env,GENERATION_ENABLED:"false"},mock)).status,503);
assert.equal((await handle(request("/api/generate",b),{...env,BONUS_EXPIRES_AT:"2000-01-01"},mock)).status,503);
assert.equal(calls,0);
let expiryState=await handle(request("/api/session"),{...env,BONUS_EXPIRES_AT:"2000-01-01"},mock);expiryState=await expiryState.json();assert.equal(expiryState.enabled,false);assert.equal(expiryState.reason,"bonus_window_expired");

r=await handle(request("/api/generate",b),env,mock);assert.equal(r.status,200);assert.equal((await r.json()).story.title,story.title);
r=await handle(request("/api/texts"),env,mock);assert.equal((await r.json()).texts.length,1);
await handle(request("/api/texts",story),env,mock);assert.equal(sql.prepare("SELECT count(*) as n FROM texts").get().n,1);
assert.throws(()=>validateStory({...story,paragraphs:["Unlistedword."],glossary:[]}),/incomplete_glossary/);
assert.throws(()=>validateStory({...story,paragraphs:["We buy apples.","We buy apples.","We buy apples."]},180),/invalid_length/);
r=await handle(request("/api/generate",b),env,async()=>Response.json({error:{code:"credit_balance_exhausted"}},{status:429}));assert.equal(r.status,429);
assert.equal((await handle(request("/api/generate",b),env,mock)).status,503);
sql.prepare("DELETE FROM flags").run();sql.prepare("DELETE FROM quota").run();
for(let i=0;i<3;i++)assert.equal((await handle(request("/api/generate",b),env,mock)).status,200);
assert.equal((await handle(request("/api/generate",b),env,mock)).status,429);
sql.prepare("DELETE FROM quota").run();
const rejected={...story,paragraphs:["Too short."]};
r=await handle(request("/api/generate",b),env,async()=>Response.json({status:"completed",output:[{content:[{type:"output_text",text:JSON.stringify(rejected)}]}]}));
assert.equal(r.status,502);assert.equal((await r.json()).reason,"invalid_length");
assert.equal(sql.prepare("SELECT count(*) as n FROM texts").get().n,1);
r=await handle(request("/api/diagnostics"),env,mock);assert.equal((await r.json()).reason,"invalid_length");
await assert.rejects(()=>handle(request("/api/recover",b),env,mock),/invalid_length/);
assert.equal((await handle(request("/api/recover",b,{"X-CSRF":"bad"}),env,mock)).status,403);
sql.prepare("INSERT OR REPLACE INTO flags(key,value) VALUES('last_generation_error',?)").run(JSON.stringify({reason:"invalid_length",candidate:JSON.stringify(story)}));
const callsBeforeRecovery=calls;
r=await handle(request("/api/recover",b),env,mock);assert.equal(r.status,200);assert.equal((await r.json()).story.title,story.title);
assert.equal(calls,callsBeforeRecovery);assert.equal(sql.prepare("SELECT count(*) as n FROM texts").get().n,1);
assert.equal((await handle(request("/api/logout",{}),env,mock)).status,200);
assert.equal((await handle(request("/api/session"),env,mock)).status,401);
assert.equal((await handle(request("/api/diagnostics"),env,mock)).status,401);
assert.equal((await handle(request("/api/recover",b),env,mock)).status,401);
// Boundary checks use the public handler: generic failures never include provider details.
const module=await import('../backend/worker.mjs');
const fail=await module.default.fetch(new Request(origin+'/api/login',{method:'POST',headers:{'Origin':origin,'Content-Type':'application/json'},body:'not-json'}),env);
assert.equal(fail.status,502);
assert.doesNotMatch(await fail.text(),/mock-not-a-real-key/);
const repair=validateStory({title:"Test",paragraphs:["A new a mouse."],glossary:[{f:"a",l:"a",ru:"артикль"},{f:"new",l:"new",ru:"новый"},{f:"mouse",l:"mouse",ru:"мышь"}],phrases:[]});
assert.equal(repair.paragraphs[0],"A new mouse.");
console.log("PASS owner authentication, CSRF/origin, bonus guard, schema validation, atomic limits, credit exhaustion, cloud dedup and logout; no network API calls");

const absentPhrase=validateStory({...story,phrases:[{p:"not in the story",ru:"unused"},{p:"buy apples",ru:"valid"}]});
assert.deepEqual(absentPhrase.phrases.map(p=>p.p),["buy apples"]);

// Assessment uses the SAME owner session, expiry and quota, with cached delivery.
sql.prepare("DELETE FROM quota").run();sql.prepare("DELETE FROM flags").run();
r=await handle(request("/api/login",{password:"test-owner-passphrase"}),env,mock);cookie=r.headers.get("set-cookie").split(";")[0];csrf=(await r.json()).csrf;
const assessment={requestId:"batch1",items:[{id:"q1",question:"She is a smart girl.",reference:"She is a smart girl.",answer:"She is smart girl."}]};
const evaluation={results:[{id:"q1",verdict:"incorrect",correction:"She is a smart girl.",errorPart:"a",explanation:"Missing article",rule:"a + adjective + noun",category:"articles",example:"He is a good teacher.",exampleRu:"Example translation"}]};let assessments=0;
const assessMock=async()=>{assessments++;return Response.json({status:"completed",output:[{content:[{type:"output_text",text:JSON.stringify(evaluation)}]}]});};
assert.equal((await handle(request("/api/check",assessment,{"X-CSRF":"bad"}),env,assessMock)).status,403);
r=await handle(request("/api/check",assessment),env,assessMock);assert.equal(r.status,200);assert.equal((await r.json()).results[0].category,"articles");
assert.equal((await handle(request("/api/check",assessment),env,assessMock)).status,200);assert.equal(assessments,1);
assert.equal((await handle(request("/api/check",{...assessment,requestId:"expired"}),{...env,BONUS_EXPIRES_AT:"2000-01-01"},assessMock)).status,503);
await assert.rejects(()=>handle(request("/api/check",{...assessment,requestId:"bad-result"}),env,async()=>Response.json({output:[{content:[{type:"output_text",text:'{"results":[]}'}]}]})),/invalid_response/);
const exhausted=await handle(request("/api/check",{...assessment,requestId:"exhausted"}),env,async()=>Response.json({error:{code:"credit_balance_exhausted"}},{status:402}));assert.equal(exhausted.status,429);
assert.equal((await handle(request("/api/check",{...assessment,requestId:"stopped"}),env,assessMock)).status,503);
console.log("PASS assessment auth, CSRF, cache no extra call, bonus expiry, malformed response and credit stop");

const {portal:portalHtml}=await import("../backend/portal.mjs");const {Script}=await import("node:vm");new Script(portalHtml("https://owner.example").match(/<script>([\s\S]*?)<\/script>/)[1]);console.log("PASS portal embedded script syntax");
