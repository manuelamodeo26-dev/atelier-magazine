(() => {
  const grid = document.getElementById('story-grid');
  const empty = document.getElementById('empty-state');
  const count = document.getElementById('story-count');
  const filters = document.getElementById('filters');
  const menuToggle = document.getElementById('menu-toggle');
  const nav = document.getElementById('main-nav');
  const searchDialog = document.getElementById('search-dialog');
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');
  let articles = [];
  let activeFilter = 'Tutti';
  let showAll = false;

  const fallback = [
    {title:'La moda come spazio di ricerca, non soltanto di tendenza.',category:'Fashion',excerpt:'Un punto di partenza per leggere il presente attraverso forme, materiali e nuove idee.',source:'ATELIER',date:'2026-11-11',url:'#',image:'',featured:true},
    {title:'Quando il design incontra la vita quotidiana.',category:'Design',excerpt:'Oggetti, ambienti e dettagli che raccontano il nostro tempo.',source:'ATELIER',date:'2026-11-11',url:'#',image:''},
    {title:'Le nuove energie creative da tenere d’occhio.',category:'Art & Culture',excerpt:'Una selezione di linguaggi e visioni che attraversano la cultura contemporanea.',source:'ATELIER',date:'2026-11-11',url:'#',image:''}
  ];

  function escapeHTML(value='') {
    return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  function formatDate(value) {
    if (!value) return 'ATELIER';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? escapeHTML(value) : date.toLocaleDateString('it-IT',{day:'2-digit',month:'short',year:'numeric'}).toUpperCase();
  }
  function card(article, index) {
    const visual = article.image
      ? `<a class="article-image" href="${escapeHTML(article.url || '#')}" target="_blank" rel="noopener noreferrer"><img src="${escapeHTML(article.image)}" alt="" loading="lazy"></a>`
      : `<div class="story-placeholder ${index%3===0?'placeholder-red':index%3===1?'placeholder-cream':'placeholder-black'}"><span>${escapeHTML((article.category || 'ATELIER').toUpperCase())}<br>JOURNAL</span><b>A/${String(index+1).padStart(2,'0')}</b></div>`;
    return `<article class="story-card">${visual}<div class="story-meta">${escapeHTML(article.category || 'JOURNAL')} · ${formatDate(article.date)} · ${escapeHTML(article.source || 'ATELIER')}</div><h3>${escapeHTML(article.title)}</h3><p>${escapeHTML(article.excerpt || '')}</p>${article.url && article.url !== '#' ? `<a class="text-link card-link" href="${escapeHTML(article.url)}" target="_blank" rel="noopener noreferrer">LEGGI LA FONTE ↗</a>` : ''}</article>`;
  }
  function render() {
    const visible = articles.filter(a => activeFilter==='Tutti' || a.category===activeFilter || (activeFilter==='Art & Culture' && a.category==='Culture'));
    const list = showAll ? visible : visible.slice(0,9);
    grid.innerHTML = list.map(card).join('');
    empty.hidden = list.length !== 0;
    count.textContent = `${visible.length} ${visible.length===1?'ARTICOLO':'ARTICOLI'} · ${activeFilter.toUpperCase()}`;
    document.getElementById('show-more').textContent = showAll ? 'MOSTRA MENO ↑' : 'MOSTRA TUTTI GLI ARTICOLI ↗';
  }
  async function loadArticles() {
    try {
      const response = await fetch('./data/articles.json', {cache:'no-store'});
      if (!response.ok) throw new Error('Archivio non disponibile');
      const data = await response.json();
      articles = Array.isArray(data.articles) ? data.articles : fallback;
      if (!articles.length) articles = fallback;
    } catch (_) { articles = fallback; }
    render();
  }
  filters.addEventListener('click', event => {
    const button = event.target.closest('[data-filter]');
    if (!button) return;
    activeFilter = button.dataset.filter;
    filters.querySelectorAll('.filter-chip').forEach(el => el.classList.toggle('active', el===button));
    showAll = false;
    render();
  });
  document.querySelectorAll('[data-jump-filter]').forEach(link => link.addEventListener('click', () => {
    const target = link.dataset.jumpFilter;
    activeFilter = target;
    filters.querySelectorAll('.filter-chip').forEach(el => el.classList.toggle('active', el.dataset.filter===target));
    render();
  }));
  document.getElementById('show-more').addEventListener('click', () => { showAll=!showAll; render(); });
  menuToggle.addEventListener('click', () => {
    const opened = nav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(opened));
  });
  nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));
  document.getElementById('search-open').addEventListener('click', () => {
    searchDialog.showModal(); searchInput.focus();
  });
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLocaleLowerCase('it');
    if (!q) { searchResults.innerHTML=''; return; }
    const found = articles.filter(a => `${a.title} ${a.excerpt} ${a.category}`.toLocaleLowerCase('it').includes(q)).slice(0,12);
    searchResults.innerHTML = found.length ? found.map(a => `<div class="search-result"><small>${escapeHTML(a.category)} · ${formatDate(a.date)}</small><h4>${escapeHTML(a.title)}</h4>${a.url && a.url!=='#' ? `<a class="text-link" href="${escapeHTML(a.url)}" target="_blank" rel="noopener">APRI FONTE ↗</a>`:''}</div>`).join('') : '<p>Nessun risultato trovato.</p>';
  });
  document.getElementById('newsletter-form').addEventListener('submit', e => {
    e.preventDefault(); alert('La newsletter non è ancora attiva. Non è stato inviato alcun dato.');
  });
  document.getElementById('today-label').textContent = new Date().toLocaleDateString('it-IT',{day:'2-digit',month:'long',year:'numeric'}).toUpperCase() + ' · ITALIA';
  loadArticles();
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(()=>{}));
  }
})();