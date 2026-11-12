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
  function imageFor(article){
    const original=safeURL(article.image);
    if(original)return {url:original,verified:article.image_verified===true,sourceImage:true};
    const category=categoryOf(article.category);
    const choices=fallbackPhotos[category]||fallbackPhotos.Fashion;
    const seed=String(article.title||article.id||'ATELIER').split('').reduce((sum,char)=>sum+char.charCodeAt(0),0);
    const photo=choices[seed%choices.length];
    return {url:'https://images.unsplash.com/'+photo+'?auto=format&fit=crop&w=1400&q=82',verified:false,sourceImage:false};
  }
  function categoryOf(value){
    const c=String(value||'').trim().toLowerCase();
    if(c==='culture'||c==='art'||c==='art & culture'||c==='art and culture') return 'Art & Culture';
    if(c==='tech'||c==='technology'||c==='tecnologia') return 'Technology';
    if(c==='architecture'||c==='business'||c==='lifestyle'||c==='streetwear'||c==='fashion'||c==='design') return c.charAt(0).toUpperCase()+c.slice(1);
    return value||'Rivista';
  }
  function categoryLabel(value){
    return ({Fashion:'Moda', 'Art & Culture':'Arte e cultura', Technology:'Tecnologia', Architecture:'Architettura', Business:'Impresa', Lifestyle:'Stili di vita', Design:'Design', Streetwear:'Streetwear', Journal:'Rivista'})[categoryOf(value)] || categoryOf(value);
  }
  function formatDate(value){
    if(!value) return 'DATA NON DISPONIBILE';
    const date=new Date(value);
    return Number.isNaN(date.getTime())?'DATA NON DISPONIBILE':date.toLocaleDateString('it-IT',{day:'2-digit',month:'short',year:'numeric'}).toUpperCase();
  }
  function card(article,index){
    const imageInfo=imageFor(article), image=imageInfo.url;
    const category=categoryOf(article.category);
    const visual=image
      ?'<div class="article-image"><img src="'+escapeHTML(image)+'" alt="'+escapeHTML(article.title||'Immagine editoriale ATELIER')+'" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.closest(\'.article-image\').classList.add(\'image-unavailable\');this.remove()"><span class="image-verified '+(imageInfo.verified?'':'image-illustrative')+'">'+(imageInfo.verified?'IMMAGINE VERIFICATA TECNICAMENTE':imageInfo.sourceImage?'IMMAGINE DELLA FONTE · NON VERIFICATA':'IMMAGINE ILLUSTRATIVA')+'</span></div>'
      :'<div class="story-placeholder '+(index%3===0?'placeholder-red':index%3===1?'placeholder-cream':'placeholder-black')+'"><span>'+escapeHTML(categoryLabel(category).toLocaleUpperCase('it'))+'<br>ATELIER</span><b>A/'+String(index+1).padStart(2,'0')+'</b></div>';
    const articleId=article.id||article.url||String(index);
    return '<article class="story-card'+(index===0?' feature-card':'')+'">'+visual+'<div class="story-meta">'+escapeHTML(categoryLabel(category))+' · '+formatDate(article.date)+' · '+escapeHTML(article.source||'Fonte non indicata')+'</div><h3>'+escapeHTML(article.title||'Senza titolo')+'</h3><p>'+escapeHTML(article.excerpt||'')+'</p><a class="text-link card-link" href="./article.html?id='+encodeURIComponent(articleId)+'">APRI ARTICOLO ↗</a><button type="button" class="save-article" data-save-article="'+escapeHTML(articleId)+'" aria-label="Salva articolo nei preferiti">♡ SALVA</button></article>';
  }
  function articleDetail(article){
    const imageInfo=imageFor(article), image=imageInfo.url;
    const date=formatDate(article.date);
    const category=categoryLabel(article.category);
    const source=article.source||'Editore non identificato';
    const author=article.author?'<p class="detail-byline">A cura di '+escapeHTML(article.author)+'</p>':'';
    const editorial=String(article.editorial_summary||'').trim();
    const editorialHtml=editorial
      ?'<section class="detail-section editorial-summary"><p class="eyebrow">IL RACCONTO ATELIER · '+(article.editorial_level==='approfondimento'?'APPROFONDIMENTO':'NOTIZIA')+'</p>'+editorial.split(/\n\s*\n/).map(p=>'<p class="detail-excerpt">'+escapeHTML(p)+'</p>').join('')+'</section>'
      :'';
    const sourceExcerpt=article.excerpt
      ?'<section class="detail-section"><p class="eyebrow">'+(editorial?'DESCRIZIONE DELLA FONTE':'IL RACCONTO DELLA FONTE')+'</p><p class="detail-excerpt">'+escapeHTML(article.excerpt)+'</p></section>'
      :'';
    const excerpt=editorialHtml+sourceExcerpt||(editorial?'':'<section class="detail-section"><p class="eyebrow">SINTESI FORNITA DALLA FONTE</p><p class="detail-muted">La fonte non mette a disposizione una descrizione più ampia. ATELIER non aggiunge dettagli non verificati.</p></section>');
    const photo=image
      ?'<figure class="detail-figure"><img src="'+escapeHTML(image)+'" alt="'+escapeHTML(article.title||'Immagine editoriale ATELIER')+'" referrerpolicy="no-referrer" onerror="this.closest(\'.detail-figure\').classList.add(\'image-unavailable\');this.remove()"><figcaption>'+(imageInfo.verified?'Immagine verificata tecnicamente · ':imageInfo.sourceImage?'Immagine della fonte, non verificata · ':'Immagine illustrativa · ')+escapeHTML(source)+'</figcaption></figure>'
      :'<div class="detail-no-image">IMMAGINE NON DISPONIBILE O NON VERIFICATA</div>';
    const sourceUrl=safeURL(article.url);
    const sourceBlock='<section class="detail-sources"><p class="eyebrow">FONTI E ATTRIBUZIONI</p><p><strong>'+escapeHTML(source)+'</strong> · Fonte originale del contenuto e delle informazioni riportate in questa scheda.</p>'+(sourceUrl?'<a class="text-link" href="'+escapeHTML(sourceUrl)+'" target="_blank" rel="noopener noreferrer">CONSULTA LA FONTE ORIGINALE ↗</a>':'<p class="detail-muted">Collegamento alla fonte non disponibile.</p>')+'<p class="detail-muted">Le fotografie contrassegnate come verificate provengono dai metadati della fonte e hanno superato i controlli tecnici. Le immagini illustrative sono alternative visive e non documentano necessariamente il fatto narrato.</p></section>';
    return '<div class="detail-topline"><span>'+escapeHTML(category.toLocaleUpperCase('it'))+'</span><span>'+escapeHTML(date)+'</span></div><h2 class="detail-title">'+escapeHTML(article.title||'Senza titolo')+'</h2>'+author+photo+excerpt+'<div class="detail-metadata"><span>EDITORE</span><strong>'+escapeHTML(source)+'</strong><span>DATA DI PUBBLICAZIONE</span><strong>'+escapeHTML(date)+'</strong><span>CATEGORIA</span><strong>'+escapeHTML(category)+'</strong>'+(article.language?'<span>LINGUA</span><strong>'+escapeHTML(String(article.language).toLocaleUpperCase('it'))+'</strong>':'')+'</div>'+sourceBlock;
  }
  function openArticle(identifier){
    const article=articles.find(item=>(item.id||item.url)===identifier);
    if(!article)return;
    let dialog=$('#article-dialog');
    if(!dialog){
      dialog=document.createElement('dialog');
      dialog.id='article-dialog';
      dialog.className='article-dialog';
      dialog.innerHTML='<form method="dialog" class="detail-close-row"><button class="dialog-close" type="submit" aria-label="Chiudi scheda">×</button></form><article id="article-detail-content"></article>';
      document.body.appendChild(dialog);
    }
    $('#article-detail-content',dialog).innerHTML=articleDetail(article);
    if(!dialog.open)dialog.showModal();
    dialog.scrollTop=0;
  }
  function visibleArticles(){
    return articles.filter(a=>activeFilter==='Tutti'||categoryOf(a.category)===activeFilter);
  }
  function render(){
    const visible=visibleArticles(), list=showAll?visible:visible.slice(0,9);
    grid.innerHTML=list.map(card).join('');
    empty.hidden=list.length!==0;
    count.textContent=visible.length+' '+(visible.length===1?'ARTICOLO':'ARTICOLI')+' · '+categoryLabel(activeFilter).toLocaleUpperCase('it');
    $('#show-more').hidden=visible.length<=9;
    $('#show-more').textContent=showAll?'MOSTRA MENO ↑':'MOSTRA TUTTI GLI ARTICOLI ↗';
    document.dispatchEvent(new Event('atelier:articles-rendered'));
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
    const heroImage=articles.find(article=>article.image_verified===true&&safeURL(article.image));
    if(heroImage){
      const heroArt=$('.hero-art');
      if(heroArt&&!heroArt.querySelector('.hero-photo')){
        const photo=document.createElement('img');
        photo.className='hero-photo';
        photo.src=safeURL(heroImage.image);
        photo.alt='Fotografia editoriale dalla selezione ATELIER';
        photo.loading='eager';
        photo.decoding='async';
        photo.referrerPolicy='no-referrer';
        photo.onerror=()=>photo.remove();
        heroArt.prepend(photo);
        heroArt.classList.add('has-photo');
      }
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
    const found=articles.filter(a=>[a.title,a.excerpt,a.editorial_summary,a.category,a.source,a.language].join(' ').toLocaleLowerCase('it').includes(q)).slice(0,12);
    searchResults.innerHTML=found.length?found.map(a=>{
      const url=safeURL(a.url);
      return '<div class="search-result"><small>'+escapeHTML(categoryLabel(a.category))+' · '+formatDate(a.date)+'</small><h4>'+escapeHTML(a.title)+'</h4><a class="text-link" href="./article.html?id='+encodeURIComponent(a.id||a.url||'')+'">APRI ARTICOLO ↗</a></div>';
    }).join(''):'<p>Nessun risultato trovato.</p>';
  });
  const today=$('#today-label');
  if(today)today.textContent=new Date().toLocaleDateString('it-IT',{day:'2-digit',month:'long',year:'numeric'}).toUpperCase()+' · ITALIA';
  filters.querySelectorAll('[data-filter]').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.filter==='Tutti')));
  loadArticles();
  if('serviceWorker' in navigator && location.protocol==='https:'){
    window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(error=>console.warn('ATELIER: service worker non registrato.',error)));
  }
})();