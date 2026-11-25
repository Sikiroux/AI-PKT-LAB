const fs=require('fs'),vm=require('vm');
const fixture=fs.readFileSync(__dirname+'/test_messaging_ui.js','utf8').split('(async()=>{ctx.messagingApp')[0];
const scenario=`
(async()=>{
 const original=ctx.fetch;ctx.fetch=async(url,opts)=>{const response=await original(url,opts);const data=await response.json();data.channels.push({...structuredClone(channel),id:'INC-2',requester:'Bob',messages:[{key:'bob-one',question:'Question Bob',answer:'Réponse Bob'}]});return{...response,json:async()=>data}};
 ctx.messagingApp('INC-LIVE-1');await tick();
 const contact=name=>all(root).find(e=>e.className==='messaging-contact'&&all(e).some(child=>child.textContent===name));
 const messages=()=>all(root).find(e=>e.className==='messaging-messages');
 messages().scrollHeight=1000;messages().clientHeight=200;messages().scrollTop=140;
 await contact('Bob').onclick();await tick();messages().scrollHeight=900;messages().clientHeight=200;messages().scrollTop=70;
 await contact('Alice').onclick();await tick();assert.equal(messages().scrollTop,140,'Alice keeps her own reading position');
 await contact('Bob').onclick();await tick();assert.equal(messages().scrollTop,70,'Bob keeps a separate reading position');
 destroyHandlers[0]();console.log('Messaging scroll: conversation-specific reading positions survive selection and read updates OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixture+scenario,{require,__dirname,process,console,setImmediate,structuredClone,URLSearchParams},{filename:__filename});
