export const storySchema = {
 type:"object",additionalProperties:false,
 properties:{
 title:{type:"string"},paragraphs:{type:"array",items:{type:"string"}},
 glossary:{type:"array",items:{type:"object",additionalProperties:false,properties:{f:{type:"string"},l:{type:"string"},ru:{type:"string"}},required:["f","l","ru"]}},
 phrases:{type:"array",items:{type:"object",additionalProperties:false,properties:{p:{type:"string"},ru:{type:"string"}},required:["p","ru"]}}
 },required:["title","paragraphs","glossary","phrases"]
};
export function validateStory(r){
 if(!r||typeof r.title!=="string"||!r.title.trim()||r.title.length>150||!Array.isArray(r.paragraphs)||r.paragraphs.length<1||r.paragraphs.length>12||r.paragraphs.some(s=>typeof s!=="string"||s.length>4000))throw Error("invalid_response");
 if(r.paragraphs.join(" ").length>15000)throw Error("invalid_response");
 if(!Array.isArray(r.glossary)||r.glossary.length>500||!Array.isArray(r.phrases)||r.phrases.length>40)throw Error("invalid_response");
 const forms=new Set((r.paragraphs.join(" ").toLowerCase().match(/[a-z]+(?:['’-][a-z]+)*/g)||[]).map(s=>s.replace(/’/g,"'")));
 const covered=new Set();
 for(const g of r.glossary){
  if(!g||["f","l","ru"].some(k=>typeof g[k]!=="string"||!g[k]||g[k].length>140)||!forms.has(g.f.toLowerCase().replace(/’/g,"'")))throw Error("invalid_glossary");
  covered.add(g.f.toLowerCase().replace(/’/g,"'"));
 }
 if([...forms].some(f=>!covered.has(f)))throw Error("incomplete_glossary");
 const txt=r.paragraphs.join(" ").toLowerCase().replace(/’/g,"'");
 for(const p of r.phrases)if(!p||typeof p.p!=="string"||typeof p.ru!=="string"||p.p.length>100||p.ru.length>140||!txt.includes(p.p.toLowerCase().replace(/’/g,"'")))throw Error("invalid_phrases");
 return r;
}
export function validateRequest(b){
 const ids=["01","01p","02","03","04","05","06","07","08","09"];
 if(!b||!ids.includes(b.lesson)||!["story","dialogue","article","posts"].includes(b.format)||!["A2","A2+"].includes(b.level)||![120,180,250].includes(b.words)||typeof b.topic!=="string"||b.topic.length>200||typeof b.context!=="string"||b.context.length>7000)throw Error("invalid_request");
 return {lesson:b.lesson,format:b.format,level:b.level,words:b.words,topic:b.topic,context:b.context};
}
export function ready(env){
 return env.GENERATION_ENABLED==="true"&&env.BONUS_ONLY_CONFIRMED==="true"&&Date.parse(env.BONUS_EXPIRES_AT)>Date.now()&&!!env.OPENAI_MODEL&&!!env.OPENAI_API_KEY;
}
