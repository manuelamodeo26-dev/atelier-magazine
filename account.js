(() => {
  'use strict';
  const cfg = window.ATELIER_SUPABASE || {};
  const configured = /^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(cfg.url || '') &&
    typeof cfg.anonKey === 'string' && cfg.anonKey.length > 20 &&
    !cfg.url.includes('INSERISCI') && !cfg.anonKey.includes('INSERISCI');
  const categories = ['Fashion','Streetwear','Design','Art & Culture','Technology','Architecture','Business','Lifestyle'];
  const fallbackPhotos={
    Fashion:['photo-1529139574466-a303027c1d8b','photo-1483985988355-763728e1935b','photo-1490481651871-ab68de25d43d'],
    Streetwear:['photo-1523398002811-999ca8dec234','photo-1529139574466-a303027c1d8b'],
    Design:['photo-1497366754035-f200968a6e72','photo-1494438639946-1ebd1d20bf85'],
    'Art & Culture':['photo-1513364776144-60967b0f800f','photo-1518998053901-5348d3961a04'],
    Architecture:['photo-1487958449943-2429e8be8625','photo-1511818966892-d7d671e672a2'],
    Technology:['photo-1518770660439-4636190af475','photo-1519389950473-47ba0277781c'],
    Business:['photo-1486406146926-c627a92ad1ab'],
    Lifestyle:['photo-1490481651871-ab68de25d43d','photo-1515886657613-9f3515b0c78f']
  };
  const labels = {'Fashion':'Moda','Streetwear':'Streetwear','Design':'Design','Art & Culture':'Arte e cultura','Technology':'Tecnologia','Architecture':'Architettura','Business':'Impresa','Lifestyle':'Stili di vita'};
  let client=null, user=null, saved=new Set(), savedRecords=new Map(), liked=new Set(), likeCounts=new Map(), preferred=categories.slice(), articles=[];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const $=(s,r=document)=>r.querySelector(s);
  const safeURL=v=>{try{const raw=String(v||'').trim();if(!raw||raw==='#')return '';const u=new URL(raw,location.href);return ['http:','https:'].includes(u.protocol)?u.href:'';}catch(_){return '';}};
  function mount(){
    const header=$('.site-header');
    if(header && !$('#account-open')){
      const b=document.createElement('button'); b.id='account-open'; b.className='search-open account-open'; b.type='button'; b.setAttribute('aria-controls','account-dialog'); b.setAttribute('aria-haspopup','dialog'); b.textContent='ACCEDI ↗';
      header.appendChild(b);
    }
    if(!$('#account-dialog')){
      const d=document.createElement('dialog'); d.id='account-dialog'; d.className='search-dialog account-dialog'; d.setAttribute('aria-labelledby','account-heading'); d.setAttribute('aria-describedby','account-status');
      d.innerHTML='<form method="dialog"><button class="dialog-close" type="submit" aria-label="Chiudi">×</button></form><p class="eyebrow">ATELIER / ACCOUNT</p><h2 id="account-heading" class="account-heading">Il tuo spazio.</h2><p id="account-status" class="account-status" role="status" aria-live="polite">Accedi o crea un account per personalizzare la rivista.</p><form id="account-form" class="account-form"><label for="account-name">Nickname (visibile nella community)</label><input id="account-name" autocomplete="nickname" minlength="3" maxlength="20" pattern="[A-Za-z0-9_]{3,20}" placeholder="es. Atelier_01"><label for="account-email">Email</label><input id="account-email" type="email" autocomplete="email" required placeholder="nome@email.com"><label for="account-password">Password</label><input id="account-password" type="password" autocomplete="current-password" minlength="8" required placeholder="Almeno 8 caratteri"><label class="auth-remember"><input id="account-remember" type="checkbox"> Resta collegato su questo dispositivo</label><div class="account-actions"><button class="outline-button" type="submit" data-mode="login">ACCEDI</button><button class="outline-button" type="submit" data-mode="signup">REGISTRATI</button></div></form><div id="account-tools" hidden><h3>Il mio feed</h3><p class="account-help">Scegli gli argomenti che vuoi vedere nel tuo feed personale.</p><div id="account-categories" class="account-categories"></div><button id="save-preferences" class="outline-button" type="button">SALVA PREFERENZE</button><button id="account-logout" class="outline-button" type="button">ESCI DALL’ACCOUNT</button></div><p id="account-message" class="account-message" role="status" aria-live="polite"></p>';
      document.body.appendChild(d);
    }
    if(!$('#personal-feed')){
      const host=document.createElement('section'); host.id='personal-feed'; host.className='section-block personal-area'; host.hidden=true;
      host.innerHTML='<div class="section-heading"><div><p class="eyebrow">ATELIER / PER TE</p><h2>Il tuo <em>feed.</em></h2></div><button type="button" class="text-link" id="open-account-settings">GESTISCI PREFERENZE ↗</button></div><div class="story-grid" id="personal-feed-grid"></div><p id="personal-feed-empty" class="empty-state" hidden>Non ci sono ancora articoli nei tuoi argomenti preferiti.</p><div class="section-heading saved-heading"><div><p class="eyebrow">ATELIER / COLLEZIONE PERSONALE</p><h2>I tuoi <em>preferiti.</em></h2></div></div><div class="story-grid" id="saved-grid"></div><p id="saved-empty" class="empty-state">Accedi per conservare gli articoli che vuoi ritrovare.</p></section>';
      const manifesto=$('.manifesto'); if(manifesto) manifesto.before(host);
    }
    $('#account-open')?.addEventListener('click',()=>$('#account-dialog').showModal());
    $('#open-account-settings')?.addEventListener('click',()=>$('#account-dialog').showModal());
    $('#account-form')?.addEventListener('submit',handleAuth);
    $('#account-logout')?.addEventListener('click',logout);
    $('#save-preferences')?.addEventListener('click',savePreferences);
    document.addEventListener('atelier:articles-rendered',()=>{syncSaveButtons();syncLikeButtons();syncLikeCounts();});
    document.addEventListener('atelier:article-rendered',()=>{syncSaveButtons();syncLikeButtons();syncLikeCounts();});
    document.addEventListener('click',event=>{
      const btn=event.target.closest?.('[data-save-article]');
      if(btn){event.preventDefault();event.stopPropagation();toggleSaved(btn.dataset.saveArticle);}
      const like=event.target.closest?.('[data-like-article]');
      if(like){event.preventDefault();event.stopPropagation();toggleLiked(like.dataset.likeArticle);}
    });
  }
  function message(text,error=false){const el=$('#account-message');if(el){el.textContent=text;el.classList.toggle('is-error',error);}}
  function status(text){const el=$('#account-status');if(el)el.textContent=text;}
  function setLoggedIn(on){
    const open=$('#account-open');
    if(open)open.textContent=on?'IL MIO ACCOUNT ↗':'ACCEDI ↗';
    const form=$('#account-form'), tools=$('#account-tools'), feed=$('#personal-feed');
    if(form)form.hidden=on;if(tools)tools.hidden=!on;if(feed)feed.hidden=!on;
    if(on)status('Accesso effettuato. Il tuo spazio ATELIER è pronto.');
    else status(configured?'Accedi o crea un account per personalizzare la rivista.':'Configurazione necessaria: collega prima il progetto Supabase.');
  }
  async function handleAuth(event){
    event.preventDefault();
    if(!client){message('Il servizio account non è ancora configurato.',true);return;}
    const mode=event.submitter?.dataset.mode||'login';
    const email=$('#account-email').value.trim(), password=$('#account-password').value, name=$('#account-name').value.trim();
    if(password.length<8){message('La password deve contenere almeno 8 caratteri.',true);return;}
    window.ATELIER_SET_REMEMBER?.($('#account-remember')?.checked===true);
    message('Operazione in corso…');
    try{
      if(mode==='signup'){
        if(!/^[A-Za-z0-9_]{3,20}$/.test(name)){message('Scegli un nickname di 3–20 caratteri: lettere, numeri o underscore.',true);return;}
        const {data,error}=await client.auth.signUp({email,password,options:{data:{display_name:name}}});
        if(error)throw error;
        if(data.session){user=data.user;const profile=await client.from('profiles').upsert({id:user.id,display_name:name},{onConflict:'id'});if(profile.error)throw profile.error;await loadUserData();message('Account creato. Benvenuto in ATELIER.');}
        else message('Registrazione avviata. Controlla la tua email per confermare l’indirizzo, poi accedi.');
      }else{
        const {data,error}=await client.auth.signInWithPassword({email,password});
        if(error)throw error; user=data.user; const existing=await client.from('profiles').select('id,display_name').eq('id',user.id).maybeSingle();if(existing.error)throw existing.error;if(!existing.data){const fallback=String(user.user_metadata?.display_name||('Membro_'+user.id.slice(0,6))).replace(/[^A-Za-z0-9_]/g,'').slice(0,20)||('Membro_'+user.id.slice(0,6));const created=await client.from('profiles').insert({id:user.id,display_name:fallback});if(created.error&&created.error.code!=='23505')throw created.error;} await loadUserData(); message('Accesso effettuato.');
      }
    }catch(e){message(e.message||'Non è stato possibile completare l’operazione.',true);}
  }
  async function loadUserData(){
    const [prefs,favs,likes]=await Promise.all([
      client.from('user_preferences').select('categories').eq('user_id',user.id).maybeSingle(),
      client.from('saved_articles').select('article_id,title,category,excerpt,source,url,image,saved_at').eq('user_id',user.id),
      client.from('article_likes').select('article_id').eq('user_id',user.id)
    ]);
    if(prefs.error)throw prefs.error;if(favs.error)throw favs.error;if(likes.error)throw likes.error;
    preferred=Array.isArray(prefs.data?.categories)?prefs.data.categories:categories.slice();
    savedRecords=new Map((favs.data||[]).map(x=>[x.article_id,x]));
    saved=new Set(savedRecords.keys());
    liked=new Set((likes.data||[]).map(x=>x.article_id));
    renderAccount();setLoggedIn(true);
  }
  function syncSaveButtons(){
    document.querySelectorAll('[data-save-article]').forEach(b=>{
      const active=saved.has(b.dataset.saveArticle);
      b.classList.toggle('is-saved',active);
      b.setAttribute('aria-pressed',String(active));
      b.setAttribute('aria-label',active?'Rimuovi dai preferiti':'Salva articolo nei preferiti');
      b.textContent=active?'♥ SALVATO':'♡ SALVA';
    });
  }
  function syncLikeButtons(){
    document.querySelectorAll('[data-like-article]').forEach(b=>{
      const active=liked.has(b.dataset.likeArticle);
      b.classList.toggle('is-liked',active);
      b.setAttribute('aria-pressed',String(active));
      b.setAttribute('aria-label',active?'Rimuovi Mi piace':'Mi piace');
      const count=b.querySelector('[data-like-count]');
      if(count)count.textContent=String(likeCounts.get(b.dataset.likeArticle)||0);
    });
  }
  function syncLikeCounts(){
    document.querySelectorAll('[data-like-count]').forEach(el=>{el.textContent=String(likeCounts.get(el.dataset.likeCount)||0);});
  }
  async function loadLikeCounts(){
    const ids=[...new Set([...articles.map(a=>String(a.id||a.url||'')),...savedRecords.keys()].filter(Boolean))];
    if(!client||!ids.length)return;
    const {data,error}=await client.from('article_like_counts').select('article_id,like_count').in('article_id',ids);
    if(error)throw error;
    likeCounts=new Map((data||[]).map(row=>[row.article_id,Number(row.like_count)||0]));
    syncLikeButtons();syncLikeCounts();
  }
  async function toggleLiked(id){
    if(!user){$('#account-dialog').showModal();message('Accedi per mettere Mi piace alle notizie.');return;}
    const wasLiked=liked.has(id);
    message('Aggiornamento Mi piace…');
    try{
      if(wasLiked){
        const {error}=await client.from('article_likes').delete().eq('user_id',user.id).eq('article_id',id);
        if(error)throw error;liked.delete(id);likeCounts.set(id,Math.max(0,(likeCounts.get(id)||0)-1));
      }else{
        const {error}=await client.from('article_likes').insert({user_id:user.id,article_id:id});
        if(error)throw error;liked.add(id);likeCounts.set(id,(likeCounts.get(id)||0)+1);
      }
      syncLikeButtons();syncLikeCounts();message(wasLiked?'Mi piace rimosso.':'Hai messo Mi piace.');
    }catch(e){message(e.message||'Errore durante l’aggiornamento del Mi piace.',true);}
  }
  function renderAccount(){
    const box=$('#account-categories');
    if(box)box.innerHTML=categories.map(c=>'<label class="account-category"><input type="checkbox" value="'+esc(c)+'" '+(preferred.includes(c)?'checked':'')+'> '+esc(labels[c])+'</label>').join('');
    syncSaveButtons();syncLikeButtons();syncLikeCounts();
    renderPersonal();
  }
  function renderPersonal(){
    const feed=$('#personal-feed-grid'), fav=$('#saved-grid'); if(!feed||!fav)return;
    const picked=articles.filter(a=>preferred.includes(a.category)).slice(0,9);
    feed.innerHTML=picked.map((a,i)=>accountCard(a,i)).join('');
    $('#personal-feed-empty').hidden=picked.length>0;
    const currentById=new Map(articles.map(a=>[String(a.id||a.url||''),a]));
    const favourites=[...savedRecords.values()].map(record=>{
      const id=String(record.article_id||'');
      const current=currentById.get(id);
      return current||{
        id, article_id:id, title:record.title||'Articolo salvato',
        category:record.category||'Fashion', excerpt:record.excerpt||'',
        source:record.source||'', url:record.url||'', image:record.image||'',
        image_verified:false, date:record.saved_at||'', archived:false
      };
    });
    fav.innerHTML=favourites.map((a,i)=>accountCard(a,i)).join('');
    $('#saved-empty').hidden=favourites.length>0;
  }
  function accountCard(a,i){
    const id=String(a.id||a.article_id||a.url||'');
    const inArchive=articles.some(item=>String(item.id||item.url||'')===id);
    const original=typeof a.image==='string'&&/^https:\/\//.test(a.image)?a.image:'';
    const choices=fallbackPhotos[a.category]||fallbackPhotos.Fashion;
    const seed=String(a.title||id).split('').reduce((n,c)=>n+c.charCodeAt(0),0);
    const image=original||('https://images.unsplash.com/'+choices[seed%choices.length]+'?auto=format&fit=crop&w=1200&q=82');
    const imageLabel=a.image_verified===true?'IMMAGINE VERIFICATA TECNICAMENTE':original?'IMMAGINE DELLA FONTE · NON VERIFICATA':'IMMAGINE ILLUSTRATIVA';
    const visual='<div class="article-image"><img loading="lazy" decoding="async" src="'+esc(image)+'" alt="'+esc(a.title||'Immagine editoriale ATELIER')+'" referrerpolicy="no-referrer" onerror="this.parentElement.classList.add(\'image-unavailable\');this.remove()"><span class="image-verified '+(a.image_verified===true?'':'image-illustrative')+'">'+imageLabel+'</span></div>';
    const preview=String(a.excerpt||a.editorial_summary||'').trim();
    const teaser=preview?(preview.length>260?preview.slice(0,257).trimEnd()+'…':preview):'La fonte non mette a disposizione un estratto editoriale.';
    const action=inArchive
      ?'<a class="text-link card-link" href="./article.html?id='+encodeURIComponent(id)+'">APRI ARTICOLO ↗</a>'
      :safeURL(a.url)?'<a class="text-link card-link" href="'+esc(safeURL(a.url))+'" target="_blank" rel="noopener noreferrer">APRI FONTE ORIGINALE ↗</a>'
      :'<span class="card-link detail-muted">CONTENUTO NON PIÙ DISPONIBILE</span>';
    return '<article class="story-card">'+visual+'<div class="story-meta">'+esc(labels[a.category]||a.category||'ATELIER')+' · '+esc(a.source||'')+'</div><h3>'+esc(a.title)+'</h3><p>'+esc(teaser)+'</p>'+action+'<button type="button" class="like-article '+(liked.has(id)?'is-liked':'')+'" data-like-article="'+esc(id)+'" aria-label="Mi piace" aria-pressed="'+String(liked.has(id))+'">♡ <span data-like-count="'+esc(id)+'">'+(likeCounts.get(id)||0)+'</span></button><button type="button" class="save-article '+(saved.has(id)?'is-saved':'')+'" data-save-article="'+esc(id)+'" aria-label="Salva articolo nei preferiti" aria-pressed="'+String(saved.has(id))+'">'+(saved.has(id)?'♥ SALVATO':'♡ SALVA')+'</button></article>';
  }
  async function toggleSaved(id){
    if(!user){$('#account-dialog').showModal();message('Accedi per salvare i tuoi articoli.');return;}
    const a=articles.find(x=>String(x.id||x.url)===id);
    const wasSaved=saved.has(id);
    if(!wasSaved&&!a)return;
    message('Aggiornamento preferiti…');
    try{
      if(wasSaved){
        const {error}=await client.from('saved_articles').delete().eq('user_id',user.id).eq('article_id',id);
        if(error)throw error;
        saved.delete(id);savedRecords.delete(id);
      }else{
        const record={user_id:user.id,article_id:id,title:a.title,category:a.category,excerpt:a.excerpt||'',source:a.source||'',url:a.url||'',image:a.image_verified===true?a.image||'':''};
        const {error}=await client.from('saved_articles').insert(record);
        if(error)throw error;
        saved.add(id);savedRecords.set(id,{...record,saved_at:new Date().toISOString()});
      }
      renderAccount();message(wasSaved?'Articolo rimosso dai preferiti.':'Articolo aggiunto ai preferiti.');
    }catch(e){message(e.message||'Errore durante il salvataggio.',true);}
  }
  async function savePreferences(){
    const chosen=[...$('#account-categories').querySelectorAll('input:checked')].map(x=>x.value);
    if(!chosen.length){message('Seleziona almeno un argomento.',true);return;}
    const {error}=await client.from('user_preferences').upsert({user_id:user.id,categories:chosen,updated_at:new Date().toISOString()});
    if(error){message(error.message,true);return;} preferred=chosen;renderPersonal();message('Preferenze aggiornate.');
  }
  async function logout(){
    const {error}=await client.auth.signOut();
    if(error){message(error.message,true);return;}
    user=null;saved.clear();savedRecords.clear();liked.clear();setLoggedIn(false);renderAccount();message('Hai effettuato la disconnessione.');
  }
  async function init(){
    mount();
    try{
      const response=await fetch('./data/articles.json',{cache:'no-store'});const data=await response.json();articles=(data.articles||[]).map(a=>({...a,category:a.category||'Fashion'}));
    }catch(_){articles=[];}
    if(!configured){setLoggedIn(false);message('Per attivare gli account: collega il progetto Supabase.',true);return;}
    try{
      const {createClient}=await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
      client=createClient(cfg.url,cfg.anonKey,{auth:{storage:window.ATELIER_AUTH_STORAGE,persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
      const {data}=await client.auth.getSession();
      if(data.session){user=data.session.user;await loadUserData();}else setLoggedIn(false);
      loadLikeCounts().catch(error=>console.warn('ATELIER: conteggi Mi piace non disponibili.',error));
      client.auth.onAuthStateChange((_event,session)=>{setTimeout(async()=>{try{user=session?.user||null;if(user){await loadUserData();loadLikeCounts().catch(error=>console.warn('ATELIER: conteggi Mi piace non disponibili.',error));}else{saved.clear();savedRecords.clear();liked.clear();setLoggedIn(false);renderAccount();}}catch(e){user=null;saved.clear();setLoggedIn(false);message(e.message||'Impossibile caricare i dati dell’account.',true);}},0);});
    }catch(e){setLoggedIn(false);message('Servizio account non raggiungibile. Riprova più tardi.',true);}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();