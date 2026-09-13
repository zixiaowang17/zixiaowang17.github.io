'use strict';
const DATA=JSON.parse(document.getElementById('data').textContent);
const $=id=>document.getElementById(id);
const routes=new Map([...DATA.interfaces,...DATA.papers,...DATA.papers.flatMap(p=>p.theorems)].map(x=>[x.route,x]));
const state={paper:{q:'',kind:'',work:''},apis:{q:'',kind:'',work:''}};
const workLabels={use_mathlib:'Use mathlib',small_adaptation:'Small adaptation',new_infrastructure:'New infrastructure',needs_work:'Needs more work'};
const hasWorkStatus=DATA.interfaces.some(x=>x.work_status);
let view='paper',active=null,lastFocus=null,readerStack=[],pendingScroll=null;
const buttons=new Map();
function node(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function saveControls(){state[view]={q:$('search').value,kind:$('kind').value,work:$('work-status').value};}
function syncWorkButtons(){document.querySelectorAll('#work-filters button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.workStatus===state[view].work)));}
function writeURL(push=false){const u=new URL(location.href);u.searchParams.set('view',view);u.searchParams.delete('coverage');for(const key of ['q','kind','work']){const v=state[view][key];if(v)u.searchParams.set(key,v);else u.searchParams.delete(key);}u.hash=active?encodeURIComponent(active):'';history[push?'pushState':'replaceState'](null,'',u);}
function markActive(){buttons.forEach((b,r)=>b.setAttribute('aria-current',String(r===active)));}
function closeReader(update=true){finishResize();$('reader').hidden=true;$('shell').classList.remove('has-reader');$('page').removeAttribute('src');active=null;readerStack=[];pendingScroll=null;markActive();if(update)writeURL();if(lastFocus?.isConnected)lastFocus.focus({preventScroll:true});else if(lastFocus?.dataset?.route&&buttons.has(lastFocus.dataset.route))buttons.get(lastFocus.dataset.route).focus({preventScroll:true});else $('tab-'+view).focus({preventScroll:true});}
function show(route,{update=true,focus=true,keepStack=false,scroll=null,expanded=[]}={}){const record=routes.get(route);if(!record)return;
if(focus&&!keepStack)lastFocus=document.activeElement;if(!keepStack)readerStack=[];active=route;pendingScroll=scroll===null?null:{scroll,expanded};$('reader').hidden=false;$('shell').classList.add('has-reader');updateSplit();$('back').hidden=!readerStack.length;$('page').src=record.url;$('page').title=record.name;$('open-page').href=record.url;markActive();if(update)writeURL(true);if(focus)$('close').focus({preventScroll:true});}
function needs(record){return record.api_count?`${record.api_count} required ${record.api_count===1?'API':'APIs'}`:'No linked APIs';}
function resultButton(record,cls){const b=node('button',undefined,cls);b.type='button';b.dataset.route=record.route;b.addEventListener('click',()=>show(record.route));buttons.set(record.route,b);return b;}
function render(){const q=state[view].q.toLocaleLowerCase().trim(),kind=state[view].kind;$('list').replaceChildren();buttons.clear();let count=0;
if(view==='apis'){
 const records=DATA.interfaces.filter(x=>(!kind||x.kind===kind)&&(!state[view].work||x.work_status===state[view].work)&&(!q||x.search.toLocaleLowerCase().includes(q)));
 const grouped=new Set(DATA.interfaces.map(x=>x.rank_group)).size>1;
 for(const x of records){
  const b=resultButton(x,'api-result');b.append(node('span',String(x.rank),'rank'));
  const content=node('span',undefined,'result-content');content.append(node('span',x.name,'name'));
  if(grouped)content.querySelector('.name').append(node('small',x.rank_group,'rank-group'));
  const counts=node('span',undefined,'api-counts');
  counts.append(node('span','Theorems / Papers','column-label'));
  const value=node('span',`${x.theorem_count} / ${x.paper_count}`,'count-value');
  value.setAttribute('aria-label',`${x.theorem_count} ${x.theorem_count===1?'theorem':'theorems'} in ${x.paper_count} ${x.paper_count===1?'paper':'papers'}`);
  counts.append(value);
  const statusCell=node('span',undefined,'api-status');statusCell.append(node('span','Status','column-label'));
  if(x.work_status){const status=node('span',workLabels[x.work_status],'work-status');status.dataset.workStatus=x.work_status;statusCell.append(status);}
  else statusCell.append(node('span','Not audited','muted'));
  b.append(content,counts,statusCell);$('list').append(b);
 }count=records.length;
 $('results').textContent=count===DATA.interfaces.length?`${count} APIs`:`${count} of ${DATA.interfaces.length} APIs`; 
}else{
 for(const p of DATA.papers){const titleMatch=p.search.toLocaleLowerCase().includes(q);const matching=p.theorems.filter(t=>(!q||titleMatch||t.search.toLocaleLowerCase().includes(q)));if((q&&!titleMatch&&!matching.length))continue;
 const row=node('article',undefined,'paper-result');const b=resultButton(p,'paper-result-button');b.append(node('span',p.name,'name'),node('span',`${p.theorem_count} ${p.theorem_count===1?'theorem':'theorems'}`,'count'),node('span',needs(p),'paper-needs'));row.append(b);
 if(q){const matches=node('div',undefined,'theorem-matches');for(const t of matching){const tb=resultButton(t,'theorem-match');tb.append(node('span',t.name),node('small',needs(t)));matches.append(tb);}if(!matching.length)matches.append(node('p','No matching theorems.','muted'));row.append(matches);}
 $('list').append(row);count++;}
 $('results').textContent=`${count} of ${DATA.papers.length} papers`;
}
if(!count)$('list').append(node('p','No matches. Try a different search or API kind.','empty'));markActive();}
function selectView(next,{update=true,focus=false,save=true}={}){if(save)saveControls();view=next;for(const v of ['paper','apis']){const b=$('tab-'+v);b.setAttribute('aria-selected',String(v===view));b.tabIndex=v===view?0:-1;}$('search-panel').setAttribute('aria-labelledby','tab-'+view);$('search').value=state[view].q;$('kind').value=state[view].kind;$('kind').hidden=view!=='apis';$('work-status').value=state[view].work;$('work-status').hidden=true;$('work-filters').hidden=view!=='apis'||!hasWorkStatus;syncWorkButtons();$('search').placeholder=view==='paper'?'Search papers, theorems or required APIs':'Search APIs, theorem labels or papers';$('search').setAttribute('aria-label',view==='paper'?'Search papers and theorems':'Search APIs');$('ranking-note').hidden=view!=='apis';$('api-columns').hidden=view!=='apis';render();if(update)writeURL();if(focus)$('tab-'+view).focus();}
[...new Set(DATA.interfaces.map(x=>x.kind))].sort().forEach(k=>{const o=node('option',k);o.value=k;$('kind').append(o);});
for(const v of ['paper','apis'])$('tab-'+v).addEventListener('click',()=>selectView(v));
document.querySelector('.view-tabs').addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();selectView(e.key==='Home'?'paper':e.key==='End'?'apis':view==='paper'?'apis':'paper',{focus:true});}});
for(const id of ['search','kind','work-status'])$(id).addEventListener(id==='search'?'input':'change',()=>{saveControls();syncWorkButtons();render();writeURL();});
for(const button of document.querySelectorAll('#work-filters button'))button.addEventListener('click',()=>{$('work-status').value=state[view].work===button.dataset.workStatus?'':button.dataset.workStatus;saveControls();syncWorkButtons();render();writeURL();});
$('close').addEventListener('click',()=>closeReader());$('back').addEventListener('click',()=>{const previous=readerStack.pop();if(previous)show(previous.route,{keepStack:true,scroll:previous.scroll,expanded:previous.expanded});});
$('page').addEventListener('load',()=>{if(pendingScroll!==null){$('page').contentWindow.postMessage({action:'restore-reader-scroll',...pendingScroll},'*');pendingScroll=null;}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&active)closeReader();});
window.addEventListener('message',e=>{if(e.source!==$('page').contentWindow)return;if(e.data?.action==='close-theorem-reader')closeReader();if(e.data?.action==='open-census-route'&&routes.has(e.data.route)){readerStack.push({route:active,scroll:Number(e.data.scroll)||0,expanded:Array.isArray(e.data.expanded)?e.data.expanded:[]});show(e.data.route,{keepStack:true});}});
function restoreURL(){const u=new URL(location.href);let route='';try{route=decodeURIComponent(u.hash.slice(1));}catch{}const mode=u.searchParams.get('view');const next=['paper','apis'].includes(mode)?mode:route.startsWith('interface:')?'apis':'paper';saveControls();const work=u.searchParams.get('work');state[next]={q:u.searchParams.get('q')||'',kind:u.searchParams.get('kind')||'',work:hasWorkStatus&&workLabels[work]?work:''};selectView(next,{update:false,save:false});if(routes.has(route))show(route,{update:false,focus:false});else closeReader(false);}
// Keep the split independent of search/navigation state and tolerate blocked storage.
const splitStorageKey='statistical-census-pane-ratio';
let splitRatio=.38,resizePointer=null;
try{const saved=Number(localStorage.getItem(splitStorageKey));if(saved>0&&saved<1)splitRatio=saved;}catch{}
function splitBounds(){const width=$('shell').getBoundingClientRect().width;return {width,min:310,max:Math.max(310,width-360)};}
function updateSplit(pixels){
 if(innerWidth<=800)return;
 const {width,min,max}=splitBounds();
 const left=Math.max(min,Math.min(max,pixels??width*splitRatio));
 if(pixels!==undefined)splitRatio=left/width;
 $('shell').style.setProperty('--catalog-width',`${left}px`);
 const divider=$('pane-divider');
 for(const [key,value] of Object.entries({min:min/width*100,max:max/width*100,now:left/width*100}))divider.setAttribute('aria-value'+key,String(Math.round(value)));
 divider.setAttribute('aria-valuetext',`${Math.round(left/width*100)}% list, ${Math.round((width-left)/width*100)}% reading pane`);
}
function saveSplit(){try{localStorage.setItem(splitStorageKey,String(splitRatio));}catch{}}
function finishResize(){
 if(resizePointer===null)return;
 const pointer=resizePointer;resizePointer=null;
 document.body.classList.remove('resizing');
 if($('pane-divider').hasPointerCapture(pointer))$('pane-divider').releasePointerCapture(pointer);
 saveSplit();
}
$('pane-divider').addEventListener('pointerdown',e=>{
 if(e.button!==0||innerWidth<=800||!active)return;
 e.preventDefault();resizePointer=e.pointerId;$('pane-divider').setPointerCapture(e.pointerId);
 $('pane-divider').focus({preventScroll:true});document.body.classList.add('resizing');
});
$('pane-divider').addEventListener('pointermove',e=>{
 if(e.pointerId===resizePointer)updateSplit(e.clientX-$('shell').getBoundingClientRect().left);
});
for(const event of ['pointerup','pointercancel','lostpointercapture'])$('pane-divider').addEventListener(event,finishResize);
$('pane-divider').addEventListener('dblclick',()=>{splitRatio=.38;updateSplit();saveSplit();});
$('pane-divider').addEventListener('keydown',e=>{
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)||innerWidth<=800)return;
 e.preventDefault();const {min,max}=splitBounds();
 const current=$('reader').getBoundingClientRect().left-$('shell').getBoundingClientRect().left;
 updateSplit(e.key==='Home'?min:e.key==='End'?max:current+(e.key==='ArrowLeft'?-1:1)*(e.shiftKey?64:24));saveSplit();
});
window.addEventListener('resize',()=>{if(innerWidth<=800)finishResize();updateSplit();});
window.addEventListener('blur',finishResize);
window.addEventListener('popstate',restoreURL);window.addEventListener('hashchange',restoreURL);restoreURL();
