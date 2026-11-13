import {dictionary} from "./glossary.mjs";
export const storySchema = {
 type:"object",additionalProperties:false,
 properties:{
 title:{type:"string"},paragraphs:{type:"array",minItems:3,maxItems:6,items:{type:"string",minLength:80}},
 glossary:{type:"array",items:{type:"object",additionalProperties:false,properties:{f:{type:"string",pattern:"^[A-Za-z]+(?:['’-][A-Za-z]+)*$"},l:{type:"string"},ru:{type:"string"}},required:["f","l","ru"]}},
 phrases:{type:"array",items:{type:"object",additionalProperties:false,properties:{p:{type:"string"},ru:{type:"string"}},required:["p","ru"]}}
 },required:["title","paragraphs","glossary","phrases"]
};
export function validateStory(r,expectedWords){
 if(!r||typeof r.title!=="string"||!r.title.trim()||r.title.length>150||!Array.isArray(r.paragraphs)||r.paragraphs.length<1||r.paragraphs.length>12||r.paragraphs.some(s=>typeof s!=="string"||s.length>4000))throw Error("invalid_response");
 // Repair only mechanical duplicate determiners caused by article-bearing vocabulary chunks.
 r.paragraphs=r.paragraphs.map(p=>p.replace(/\b(a|an)\s+(new|old|small|big|large|nice|beautiful)\s+(?:a|an)\s+/gi,"$1 $2 ").replace(/\b(a|an)\s+(?:a|an)\s+/gi,"$1 "));
 if(r.paragraphs.join(" ").length>15000)throw Error("invalid_response");
 if(!Array.isArray(r.glossary)||r.glossary.length>500||!Array.isArray(r.phrases)||r.phrases.length>40)throw Error("invalid_response");
 const forms=new Set((r.paragraphs.join(" ").toLowerCase().match(/[a-z]+(?:['’-][a-z]+)*/g)||[]).map(s=>s.replace(/’/g,"'")));
 if(expectedWords){const count=r.paragraphs.join(" ").trim().split(/\s+/).length;if(r.paragraphs.length<3||count<({120:90,180:144,250:220}[expectedWords]||expectedWords*.8)||count>({120:150,180:220,250:300}[expectedWords]||expectedWords*1.3))throw Error("invalid_length");}
 const covered=new Set();
 r.glossary=r.glossary.filter(g=>g&&typeof g.f==="string"&&forms.has(g.f.toLowerCase().replace(/’/g,"\x27")));
 for(const g of r.glossary){
  if(!g||["f","l","ru"].some(k=>typeof g[k]!=="string"||!g[k]||g[k].length>140)||!forms.has(g.f.toLowerCase().replace(/’/g,"'")))throw Error("invalid_glossary");
  covered.add(g.f.toLowerCase().replace(/’/g,"'"));
 }
 for(const f of forms){if(!covered.has(f)&&dictionary[f]){r.glossary.push({f,l:dictionary[f].l,ru:dictionary[f].ru,source:"dictionary"});covered.add(f);}}
 if([...forms].some(f=>!covered.has(f)))throw Error("incomplete_glossary");
 const txt=r.paragraphs.join(" ").toLowerCase().replace(/’/g,"'");
 for(const p of r.phrases)if(!p||typeof p.p!=="string"||typeof p.ru!=="string"||p.p.length>100||p.ru.length>140)throw Error("invalid_phrases");
 // Optional phrase hints absent from the final text cannot be tapped; omit them.
 r.phrases=r.phrases.filter(p=>txt.includes(p.p.toLowerCase().replace(/’/g,"'")));
 return r;
}
export function validateRequest(b){
 const ids=["01","01p","02","03","04","05","06","07","08","09","10"];
 if(!b||!ids.includes(b.lesson)||!["story","dialogue","article","posts"].includes(b.format)||!["A2","A2+"].includes(b.level)||![120,180,250].includes(b.words)||typeof b.topic!=="string"||b.topic.length>200||typeof b.context!=="string"||b.context.length>7000)throw Error("invalid_request");
 return {lesson:b.lesson,format:b.format,level:b.level,words:b.words,topic:b.topic,context:b.context};
}
export function ready(env){
 return env.GENERATION_ENABLED==="true"&&env.BONUS_ONLY_CONFIRMED==="true"&&Date.parse(env.BONUS_EXPIRES_AT)>Date.now()&&!!env.OPENAI_MODEL&&!!env.OPENAI_API_KEY;
}

export const assessmentSchema={type:"object",additionalProperties:false,properties:{results:{type:"array",minItems:1,maxItems:10,items:{type:"object",additionalProperties:false,properties:{id:{type:"string"},verdict:{type:"string",enum:["correct","incorrect","uncertain"]},correction:{type:"string"},errorPart:{type:"string"},explanation:{type:"string"},rule:{type:"string"},category:{type:"string",enum:["articles","tenses","prepositions","endings","word_order","collocations","meaning","other"]},example:{type:"string"},exampleRu:{type:"string"}},required:["id","verdict","correction","errorPart","explanation","rule","category","example","exampleRu"]}}},required:["results"]};
export function validateAssessmentRequest(b){
 if(!b||typeof b.requestId!=="string"||b.requestId.length>100||!Array.isArray(b.items)||!b.items.length||b.items.length>10)throw Error("invalid_request");
 const ids=new Set();const items=b.items.map(q=>{if(!q||["id","question","reference","answer"].some(k=>typeof q[k]!=="string"||!q[k].trim()||q[k].length>1000)||ids.has(q.id)||q.id.length>80)throw Error("invalid_request");ids.add(q.id);return {id:q.id,question:q.question,reference:q.reference,answer:q.answer};});
 return {requestId:b.requestId,items};
}
export function validateAssessment(r,b){
 if(!r||!Array.isArray(r.results)||r.results.length!==b.items.length)throw Error("invalid_response");
 const ids=new Set(b.items.map(q=>q.id)),seen=new Set();
 for(const q of r.results){if(!q||!ids.has(q.id)||seen.has(q.id)||!["correct","incorrect","uncertain"].includes(q.verdict)||!["articles","tenses","prepositions","endings","word_order","collocations","meaning","other"].includes(q.category))throw Error("invalid_response");seen.add(q.id);for(const k of ["correction","errorPart","explanation","rule","example","exampleRu"])if(typeof q[k]!=="string"||q[k].length>1600)throw Error("invalid_response");if(q.verdict!=="uncertain"&&["correction","explanation","rule","example","exampleRu"].some(k=>!q[k].trim()))throw Error("invalid_response");}
 return {requestId:b.requestId,results:r.results};
}
