const ORIGIN='http://127.0.0.1:8765';
function allowed(url,blank=false){if(blank&&url==='about:blank')return true;try{const u=new URL(url);return u.origin===ORIGIN&&!u.username&&!u.password}catch{return false}}
function windowKey(url){try{const u=new URL(url);return u.pathname.includes('/desktop')?'client:'+u.pathname+u.search:u.pathname+u.search}catch{return 'main'}}
function bounds(saved,displays){
 const valid=n=>Number.isFinite(n);if(!saved||![saved.x,saved.y,saved.width,saved.height].every(valid))return {width:1280,height:850};
 const visible=displays.some(({workArea:a})=>saved.x+saved.width>a.x+100&&saved.x<a.x+a.width-100&&saved.y>=a.y&&saved.y<a.y+a.height-60);
 if(!visible)return {width:1280,height:850};
 return {x:saved.x,y:saved.y,width:Math.max(640,Math.min(saved.width,3840)),height:Math.max(480,Math.min(saved.height,2160))};
}
module.exports={ORIGIN,allowed,windowKey,bounds};
