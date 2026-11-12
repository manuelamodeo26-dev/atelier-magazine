(() => {
  'use strict';
  const $ = (selector, root=document) => root.querySelector(selector);
  const grid=$('#story-grid'), empty=$('#empty-state'), count=$('#story-count');
  const filters=$('#filters'), menuToggle=$('#menu-toggle'), nav=$('#main-nav');
  const searchDialog=$('#search-dialog'), searchInput=$('#search-input'), searchResults=$('#search-results');
  const fallback=[
    {title:'La moda come spazio di ricerca, non soltanto di tendenza.',category:'Fashion',excerpt:'Un punto di partenza per leggere il presente attraverso forme, materiali e nuove idee.',source:'ATELIER',date:'2026-11-11',url:'#'},
    {title:'Quando il design incontra la vita quotidiana.',category:'Design',excerpt:'Oggetti, ambienti e dettagli che raccontano il nostro tempo.',source:'ATELIER',date:'2026-11-11',url:'#'},
    {title:'Le nuove energie creative da tenere d’occhio.',category:'Art & Culture',excerpt:'Una selezione di linguaggi e visioni che attraversano la cultura contemporanea.',source:'ATELIER',date:'2026-11-11',url:'#'}
  ];
  let articles=[], activeFilter='Tutti', showAll=false;
  const escapeHTML=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function safeURL(value){
    if(typeof value!=='string'||!value.trim()||value.trim()==='#') return '';
    try { const url=new URL(value.trim(),location.href); return ['http:','https:'].includes(url.protocol)?url.href:''; }
    catch (_) { return ''; }
  }
  function categoryOf(value){
    const c=String(value||'').trim().toLowerCase();
    if(c==='culture'||c==='art'||c==='art & culture'||c==='art and culture') return 'Art & Culture';
    if(c==='tech'||c==='technology') return 'Technology';
    if(c==='architecture'||c==='business'||c==='lifestyle'||c==='streetwear'||c==='fashion'||c==='design') return c.charAt(0).toUpperCase()+c.slice(1);
    return value||'Journal';
  }
  function formatDate(value){
    if(!value) return 'DATA NON DISPONIBILE';
    const date=new Date(value);
    return Number.isNaN(date.getTime())?'DATA NON DISPONIBILE':date.toLocaleDateString('it-IT',{day:'2-digit',month:'short',year:'numeric'}).toUpperCase();
  }
  function card(article,index){
    const url=safeURL(article.url), image=safeURL(article.image), category=categoryOf(article.category);
    const visual=image?'<a class="article-image" href="'+escapeHTML(url||image)+'" target="_blank" rel="noopener noreferrer"><img src="'+escapeHTML(image)+'" alt="" loading="lazy" referrerpolicy="no-referrer"></a>':
      '<div class="story-placeholder '+(index%3===0?'placeholder-red':index%3===1?'placeholder-cream':'placeholder-black')+'"><span>'+escapeHTML(String(category).toUpperCase())+'<br>JOURNAL</span><b>A/'+String(index+1).padStart(2,'0')+'</b></div>';
    const language=String(article.language||'').toLowerCase();
    const languageNote=language&&language!=='it'?' · ORIGINALE '+escapeHTML(language.toUpperCase()):'';
    return '<article class="story-card">'+visual+'<div class="story-meta">'+escapeHTML(category)+' · '+formatDate(article.date)+' · '+escapeHTML(article.source||'ATELIER')+languageNote+'</div><h3>'+escapeHTML(article.title||'Senza titolo')+'</h3><p>'+escapeHTML(article.excerpt||'')+'</p>'+(url?'<a class="text-link card-link" href="'+escapeHTML(url)+'" target="_blank" rel="noopener noreferrer">LEGGI LA FONTE ↗</a>':'')+'</article>';
  }
  function visibleArticles(){
    return articles.filter(a=>activeFilter==='Tutti'||categoryOf(a.category)===activeFilter);
  }
  function render(){
    const visible=visibleArticles(), list=showAll?visible:visible.slice(0,9);
    grid.innerHTML=list.map(card).join('');
    empty.hidden=list.length!==0;
    count.textContent=visible.length+' '+(visible.length===1?'ARTICOLO':'ARTICOLI')+' · '+activeFilter.toUpperCase();
    $('#show-more').hidden=visible.length<=9;
    $('#show-more').textContent=showAll?'MOSTRA MENO ↑':'MOSTRA TUTTI GLI ARTICOLI ↗';
  }
  async function loadArticles(){
    try{
      const response=await fetch('./data/articles.json',{cache:'no-store'});
      if(!response.ok) throw new Error('Archivio non disponibile ('+response.status+')');
      const data=await response.json();
      if(!data||!Array.isArray(data.articles)) throw new Error('Formato archivio non valido');
      articles=data.articles.filter(a=>a&&typeof a.title==='string'&&a.title.trim()).map(a=>({...a,category:categoryOf(a.category)}));
      if(!articles.length) articles=fallback;
    }catch(error){
      console.warn('ATELIER: impossibile caricare le notizie.',error);
      articles=fallback;
    }
    render();
  }
  filters.addEventListener('click',event=>{
    const button=event.target.closest('[data-filter]');
    if(!button)return;
    activeFilter=button.dataset.filter; showAll=false;
    filters.querySelectorAll('.filter-chip').forEach(el=>{const active=el===button;el.classList.toggle('active',active);el.setAttribute('aria-pressed',String(active));});
    render();
  });
  document.querySelectorAll('[data-jump-filter]').forEach(link=>link.addEventListener('click',()=>{
    activeFilter=link.dataset.jumpFilter; showAll=false;
    filters.querySelectorAll('.filter-chip').forEach(el=>{const active=el.dataset.filter===activeFilter;el.classList.toggle('active',active);el.setAttribute('aria-pressed',String(active));});
    render();
  }));
  $('#show-more').addEventListener('click',()=>{showAll=!showAll;render();});
  menuToggle.addEventListener('click',()=>{
    const opened=nav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded',String(opened));
    menuToggle.setAttribute('aria-label',opened?'Chiudi menu':'Apri menu');
  });
  nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{
    nav.classList.remove('open');menuToggle.setAttribute('aria-expanded','false');menuToggle.setAttribute('aria-label','Apri menu');
  }));
  $('#search-open').addEventListener('click',()=>{searchDialog.showModal();searchInput.focus();});
  searchInput.addEventListener('input',()=>{
    const q=searchInput.value.trim().toLocaleLowerCase('it');
    if(!q){searchResults.innerHTML='';return;}
    const found=articles.filter(a=>[a.title,a.excerpt,a.category,a.source,a.language].join(' ').toLocaleLowerCase('it').includes(q)).slice(0,12);
    searchResults.innerHTML=found.length?found.map(a=>{
      const url=safeURL(a.url);
      return '<div class="search-result"><small>'+escapeHTML(categoryOf(a.category))+' · '+formatDate(a.date)+'</small><h4>'+escapeHTML(a.title)+'</h4>'+(url?'<a class="text-link" href="'+escapeHTML(url)+'" target="_blank" rel="noopener noreferrer">APRI FONTE ↗</a>':'')+'</div>';
    }).join(''):'<p>Nessun risultato trovato.</p>';
  });
  const today=$('#today-label');
  if(today)today.textContent=new Date().toLocaleDateString('it-IT',{day:'2-digit',month:'long',year:'numeric'}).toUpperCase()+' · ITALIA';
  loadArticles();
  if('serviceWorker' in navigator && location.protocol==='https:'){
    window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(error=>console.warn('ATELIER: service worker non registrato.',error)));
  }
})();