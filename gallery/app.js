/* Local assets for curated downloads; native model rendering for custom layouts. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!window.NOCTURNE) { $('grid').textContent = 'Render the collection with generate.py to build the catalog.'; return; }
  const all = window.NOCTURNE.wallpapers;
  const familyOrder = new Map([...new Set(all.map(w => w.family))].map((f,i) => [f,i]));
  const curated = [...all].sort((a,b) => a.variant-b.variant || familyOrder.get(a.family)-familyOrder.get(b.family));
  const themes = [...new Set(all.map(w => w.theme))];
  const layouts = {
    original: {name:'Curated', note:'The finished composition, rendered for this screen shape.'},
    fill: {name:'Fill frame', note:'A closer, expansive view of the source pattern. Forms continue beyond the frame.'},
    repeat: {name:'Repeat', note:'The source pattern repeated across a staggered grid, with black space between forms.'},
    scatter: {name:'Scatter', note:'An artistic arrangement of the source pattern across the screen, with varied sizes and angles.'}
  };
  let saved;
  try { saved = new Set(JSON.parse(localStorage.getItem('nocturne-saved') || '[]')); } catch { saved = new Set(); }
  let theme='', format='ultrawide', page=0, onlySaved=false, filtered=curated, active=null;
  let layout='original', density=2, arrangement=0, previewController=null, previewRevision=0;
  let previewURL=null, downloadBusy=false, densityTimer=null;
  const perPage=36;
  const query = new URLSearchParams(location.search);
  if (themes.includes(query.get('theme'))) theme=query.get('theme');
  if (query.get('format')==='standard') format='standard';
  if (Object.hasOwn(layouts,query.get('layout'))) layout=query.get('layout');
  if (query.has('density')) density=Math.min(5,Math.max(2,parseInt(query.get('density'),10)||2));
  if (query.has('arrangement')) arrangement=Math.min(9999,Math.max(0,parseInt(query.get('arrangement'),10)||0));
  const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
  const composerReady = detectComposer();
  $('total-count').textContent=all.length;

  async function detectComposer() {
    if (location.protocol==='file:') return false;
    try {
      const response=await fetch('api/health',{cache:'no-store'});
      if (!response.ok) return false;
      return (await response.json()).composition===true;
    } catch { return false; }
  }
  function favoriteCount(){ $('favorite-count').textContent=saved.size; }
  function save(id){
    saved.has(id)?saved.delete(id):saved.add(id);
    try { localStorage.setItem('nocturne-saved',JSON.stringify([...saved])); } catch {}
    favoriteCount();render();
    if(active){$('view-save').textContent=saved.has(active.id)?'♥':'♡';$('view-save').setAttribute('aria-label',saved.has(active.id)?'Unsave wallpaper':'Save wallpaper');}
  }
  function updateURL(){
    const q=new URLSearchParams();
    if(theme)q.set('theme',theme);
    if(format!=='ultrawide')q.set('format',format);
    if(layout!=='original'){q.set('layout',layout);q.set('density',density);if(arrangement)q.set('arrangement',arrangement);}
    if(active&&$('viewer').open)q.set('item',active.id);
    try{history.replaceState(null,'',location.pathname+(q.size?'?'+q:''));}catch{}
  }
  function buildThemes(){
    const nav=$('themes');nav.replaceChildren();
    for(const t of ['',...themes]){
      const b=el('button','theme',t||'All studies');
      b.append(el('span','',t?all.filter(w=>w.theme===t).length:all.length));
      b.setAttribute('aria-pressed',String(t===theme));
      b.onclick=()=>{theme=t;page=0;$('family').value='';buildThemes();buildFamilies();render();updateURL();};
      nav.append(b);
    }
  }
  function buildFamilies(){
    const select=$('family');select.replaceChildren(new Option('All systems',''));
    const families=new Map(all.filter(w=>!theme||w.theme===theme).map(w=>[w.family,w.family_name]));
    for(const [id,name] of families)select.add(new Option(name,id));
  }
  function render(){
    const term=$('search').value.toLowerCase().trim(), family=$('family').value;
    filtered=curated.filter(w=>(!theme||w.theme===theme)&&(!family||w.family===family)&&(!onlySaved||saved.has(w.id))&&(!term||[w.title,w.description,w.theme,w.model,w.palette].join(' ').toLowerCase().includes(term)));
    page=Math.min(page,Math.max(0,Math.ceil(filtered.length/perPage)-1));
    const shown=filtered.slice(page*perPage,(page+1)*perPage),grid=$('grid');grid.replaceChildren();
    document.documentElement.style.setProperty('--ratio',format==='ultrawide'?'5120/2160':'16/9');
    for(const w of shown){
      const card=el('article','card'),open=el('button','card-open');open.setAttribute('aria-label','Explore '+w.title);
      const picture=el('span','card-picture'),img=el('img');
      img.src=w.previews[format];img.alt=w.description;img.loading='lazy';img.decoding='async';img.width=format==='ultrawide'?1280:960;img.height=540;picture.append(img);
      const caption=el('span','card-caption');caption.append(el('span','card-title',w.family_name),el('span','card-number',String(w.variant).padStart(2,'0')));
      const details=el('span','card-details'),palette=el('span','palette-label',w.palette),dot=el('i','palette-dot');dot.style.background=w.colors[2];palette.prepend(dot);details.append(el('span','',w.theme),palette);
      open.append(picture,caption,details);open.onclick=()=>show(w);
      const favorite=el('button','save-button',saved.has(w.id)?'♥':'♡');favorite.setAttribute('aria-label',(saved.has(w.id)?'Unsave ':'Save ')+w.title);favorite.setAttribute('aria-pressed',String(saved.has(w.id)));favorite.onclick=()=>save(w.id);
      card.append(open,favorite);grid.append(card);
    }
    $('result-count').textContent=filtered.length?`${page*perPage+1}–${Math.min((page+1)*perPage,filtered.length)} of ${filtered.length} studies`:'0 studies';
    $('page-count').textContent=`${page+1} / ${Math.max(1,Math.ceil(filtered.length/perPage))}`;
    $('prev').disabled=page===0;$('next').disabled=(page+1)*perPage>=filtered.length;$('empty').hidden=filtered.length>0;
    favoriteCount();document.querySelectorAll('[data-format]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.format===format)));
  }
  function compositionURL(w,width,height,download=false,settings={layout,density,arrangement}){
    const q=new URLSearchParams({id:w.id,layout:settings.layout,width:String(width),height:String(height),density:String(settings.density),seed:String(settings.arrangement)});
    if(download)q.set('download','1');
    return 'api/compose?'+q;
  }
  function syncControls(){
    document.querySelectorAll('[data-layout]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.layout===layout)));
    $('density-control').hidden=!['repeat','scatter'].includes(layout);
    $('shuffle-composition').hidden=layout!=='scatter';
    $('composition-density').value=density;$('density-value').value=density;$('viewer-format').value=format;
    $('composition-note').textContent=layouts[layout].note;
  }
  function previewStatus(message,error=false){
    $('composition-status').textContent=message;$('composition-status').hidden=!message;
    $('composition-status').classList.toggle('error',error);
  }
  async function paintPreview(){
    previewController?.abort();const revision=++previewRevision;
    const w=active;if(!w)return;
    const width=format==='ultrawide'?1280:960;
    $('view-image').alt=w.description+' — '+layouts[layout].name+' composition';
    $('viewer-picture').style.aspectRatio=width+'/540';
    if(previewURL){URL.revokeObjectURL(previewURL);previewURL=null;}
    $('view-image').src=w.previews[format];
    $('viewer-picture').setAttribute('aria-busy',layout==='original'?'false':'true');
    if(layout==='original'){previewStatus('');return;}
    previewStatus('Rendering your composition…');
    if(!await composerReady){
      if(revision!==previewRevision)return;
      $('viewer-picture').setAttribute('aria-busy','false');
      previewStatus('Custom layouts need the composition server. Open the gallery at localhost:8765.',true);
      $('view-image').alt=w.description+' — curated composition shown';
      return;
    }
    if(revision!==previewRevision)return;
    previewController=new AbortController();
    try{
      const response=await fetchComposition(compositionURL(w,width,540),previewController.signal);
      if(!response.ok)throw new Error(await responseMessage(response));
      if(!response.headers.get('content-type')?.startsWith('image/png'))throw new Error('The server did not return an image.');
      const blob=await response.blob();if(revision!==previewRevision)return;
      previewURL=URL.createObjectURL(blob);$('view-image').src=previewURL;
      $('viewer-picture').setAttribute('aria-busy','false');previewStatus('');
    }catch(error){
      if(error.name==='AbortError'||revision!==previewRevision)return;
      $('viewer-picture').setAttribute('aria-busy','false');previewStatus('Could not render this layout. '+error.message,true);
    }
  }
  async function fetchComposition(url,signal){
    for(let attempt=0;attempt<4;attempt++){
      const response=await fetch(url,{signal,cache:'no-cache'});
      if(![429,503].includes(response.status)||attempt===3)return response;
      await response.body?.cancel();
      await new Promise((resolve,reject)=>{
        const abort=()=>{clearTimeout(timer);reject(new DOMException('Aborted','AbortError'));};
        const timer=setTimeout(()=>{signal?.removeEventListener('abort',abort);resolve();},700+attempt*600);
        if(signal?.aborted)abort();else signal?.addEventListener('abort',abort,{once:true});
      });
    }
  }
  async function responseMessage(response){
    try{const data=await response.json();return data.error||data.message||`Server returned ${response.status}.`;}catch{return `Server returned ${response.status}.`;}
  }
  function updateDownloads(){
    if(!active)return;
    const w=active,downloads=$('download-links');downloads.replaceChildren();
    const ordered=[...w.files].sort((a,b)=>{const target=format==='ultrawide',au=a.width/a.height>2,bu=b.width/b.height>2;return Number(bu===target)-Number(au===target);});
    for(const f of ordered){
      const a=el('a','',`${f.width.toLocaleString()} × ${f.height.toLocaleString()}`);
      a.href=layout==='original'?f.path:compositionURL(w,f.width,f.height,true);
      a.download=layout==='original'?f.path.split('/').pop():`${w.id}-${layout}-${f.width}x${f.height}.png`;
      a.append(el('span','',layout==='original'?(f.bytes/1e6).toFixed(1)+' MB ↓':'Create PNG ↓'));
      if(layout!=='original')a.onclick=e=>{e.preventDefault();exportComposition(w,f,{layout,density,arrangement});};
      if(downloadBusy)a.setAttribute('aria-disabled','true');
      downloads.append(a);
    }
    $('view-black').textContent=layout==='original'?`${(w.metrics[format].exact_black_fraction*100).toFixed(1)}% exact black in 2160p master · sRGB`:'Rendered at the selected resolution · True-black background';
  }
  async function exportComposition(w,file,settings){
    if(downloadBusy)return;
    $('download-status').classList.remove('error');
    if(!await composerReady){$('download-status').textContent='Open localhost:8765 to download a custom layout.';return;}
    downloadBusy=true;updateDownloads();
    $('download-status').textContent=`Preparing ${file.width} × ${file.height} PNG…`;
    try{
      const response=await fetchComposition(compositionURL(w,file.width,file.height,true,settings));
      if(!response.ok)throw new Error(await responseMessage(response));
      if(!response.headers.get('content-type')?.startsWith('image/png'))throw new Error('The server did not return a PNG.');
      const blob=await response.blob(),url=URL.createObjectURL(blob),a=el('a');
      a.href=url;a.download=`${w.id}-${settings.layout}-d${settings.density}-s${settings.arrangement}-${file.width}x${file.height}.png`;
      document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
      $('download-status').textContent=`PNG ready · ${(blob.size/1e6).toFixed(1)} MB`;
    }catch(error){$('download-status').textContent='Download failed. '+error.message;$('download-status').classList.add('error');}
    finally{downloadBusy=false;updateDownloads();}
  }
  function show(w){
    active=w;$('view-title').textContent=w.title;$('view-number').textContent='NOCTURNE / '+w.id.toUpperCase();
    $('view-theme').textContent=w.theme+' · '+w.palette;$('view-description').textContent=w.description;$('view-model').textContent=w.model;
    $('view-parameters').textContent='Seed '+w.seed+' · '+JSON.stringify(w.composition_parameters?.[format]||w.parameters);
    $('view-save').textContent=saved.has(w.id)?'♥':'♡';$('view-save').setAttribute('aria-label',saved.has(w.id)?'Unsave wallpaper':'Save wallpaper');
    const sources=$('view-sources');sources.replaceChildren();
    for(const s of w.sources){const li=el('li'),a=el('a','',s.title);a.href=s.url;a.target='_blank';a.rel='noopener noreferrer';li.append(a);sources.append(li);}
    if(!downloadBusy)$('download-status').textContent='';
    syncControls();updateDownloads();paintPreview();
    if(!$('viewer').open)$('viewer').showModal();updateURL();
  }
  function step(delta){if(!active||!filtered.length)return;const index=filtered.findIndex(w=>w.id===active.id);show(filtered[(index+delta+filtered.length)%filtered.length]);}
  function changeComposition(){syncControls();updateDownloads();paintPreview();updateURL();}
  $('search').oninput=()=>{page=0;render();};$('family').onchange=()=>{page=0;render();};
  $('favorites').onclick=()=>{onlySaved=!onlySaved;page=0;$('favorites').setAttribute('aria-pressed',String(onlySaved));render();};
  $('clear').onclick=()=>{theme='';onlySaved=false;$('search').value='';$('favorites').setAttribute('aria-pressed','false');buildThemes();buildFamilies();render();updateURL();};
  for(const b of document.querySelectorAll('[data-format]'))b.onclick=()=>{format=b.dataset.format;render();if(active)show(active);updateURL();};
  for(const b of document.querySelectorAll('[data-layout]'))b.onclick=()=>{layout=b.dataset.layout;changeComposition();};
  $('composition-density').oninput=()=>{density=Number($('composition-density').value);$('density-value').value=density;clearTimeout(densityTimer);densityTimer=setTimeout(changeComposition,220);};
  $('shuffle-composition').onclick=()=>{arrangement=(arrangement+1)%10000;changeComposition();};
  $('viewer-format').onchange=()=>{format=$('viewer-format').value;render();if(active)show(active);};
  $('prev').onclick=()=>{page--;render();$('collection').scrollIntoView();};$('next').onclick=()=>{page++;render();$('collection').scrollIntoView();};
  $('random').onclick=()=>{const pool=filtered.length?filtered:all;show(pool[crypto.getRandomValues(new Uint32Array(1))[0]%pool.length]);};
  $('view-close').onclick=()=>$('viewer').close();
  $('viewer').addEventListener('close',()=>{active=null;previewController?.abort();previewRevision++;clearTimeout(densityTimer);if(previewURL){URL.revokeObjectURL(previewURL);previewURL=null;}updateURL();});
  $('viewer').addEventListener('click',e=>{if(e.target===$('viewer')){const rect=$('viewer').getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)$('viewer').close();}});
  $('view-prev').onclick=()=>step(-1);$('view-next').onclick=()=>step(1);$('view-save').onclick=()=>{if(active)save(active.id);};
  document.addEventListener('keydown',e=>{if(!$('viewer').open||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;if(e.key==='ArrowRight')step(1);if(e.key==='ArrowLeft')step(-1);});
  buildThemes();buildFamilies();render();
  const hero=all.find(w=>w.family==='torus-filaments'&&w.variant===1)||all[0];
  if(hero){$('hero-image').src=hero.previews.standard;$('hero-image').alt=hero.description;$('hero-title').textContent=hero.title;$('hero').onclick=()=>show(hero);}
  const requested=all.find(w=>w.id===query.get('item'));if(requested)show(requested);
})();
