(() => {
'use strict';
const content=document.getElementById('article-content');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const url=v=>{try{const u=new URL(String(v||''),location.href);return ['http:','https:'].includes(u.protocol)&&String(v||'').trim()!=='#'?u.href:'';}catch(_){return '';}};
const cat=v=>({'Fashion':'Moda','Streetwear':'Streetwear','Design':'Design','Art & Culture':'Arte e cultura','Technology':'Tecnologia','Architecture':'Architettura','Business':'Impresa','Lifestyle':'Stili di vita','Journal':'Rivista'})[v]||v||'Rivista';
const date=v=>{const d=new Date(v);return v&&!Number.isNaN(d.getTime())?d.toLocaleDateString('it-IT',{day:'2-digit',month:'long',year:'numeric'}).toUpperCase():'DATA NON DISPONIBILE';};
function fail(msg){content.innerHTML='<p class="eyebrow">ATELIER / ARCHIVIO</p><h1 class="detail-title">Articolo non disponibile.</h1><p class="detail-excerpt">'+esc(msg)+'</p><a class="text-link" href="./">TORNA ALLA RIVISTA ↗</a>';}
function render(a){
const source=a.source||'Editore non identificato', category=cat(a.category), published=date(a.date), image=a.image_verified===true?url(a.image):'';
const photo=image?'<figure class="detail-figure"><img src="'+esc(image)+'" alt="Fotografia verificata: '+esc(a.title)+'" referrerpolicy="no-referrer"><figcaption>Immagine verificata · '+esc(String(a.image_width||'')+(a.image_width?' × ':'')+String(a.image_height||''))+' px · '+esc(source)+'</figcaption></figure>':'<div class="detail-no-image">IMMAGINE NON DISPONIBILE O NON VERIFICATA</div>';
const summary=a.excerpt?'<section class="detail-section"><p class="eyebrow">IL RACCONTO DELLA FONTE</p><p class="detail-excerpt">'+esc(a.excerpt)+'</p></section>':'<section class="detail-section"><p class="eyebrow">SINTESI FORNITA DALLA FONTE</p><p class="detail-muted">La fonte non mette a disposizione una descrizione più ampia. ATELIER non aggiunge dettagli non verificati.</p></section>';
const sourceUrl=url(a.url);
const articleId=String(a.id||a.url||'');
content.innerHTML='<button type="button" class="save-article" data-save-article="'+esc(articleId)+'">♡ SALVA NEI PREFERITI</button><div class="detail-topline"><span>'+esc(category.toLocaleUpperCase('it'))+'</span><span>'+esc(published)+'</span></div><h1 class="detail-title">'+esc(a.title||'Senza titolo')+'</h1>'+(a.author?'<p class="detail-byline">A cura di '+esc(a.author)+'</p>':'')+photo+summary+'<div class="detail-metadata"><span>EDITORE</span><strong>'+esc(source)+'</strong><span>DATA DI PUBBLICAZIONE</span><strong>'+esc(published)+'</strong><span>CATEGORIA</span><strong>'+esc(category)+'</strong>'+(a.language?'<span>LINGUA</span><strong>'+esc(String(a.language).toLocaleUpperCase('it'))+'</strong>':'')+'</div><section class="detail-sources"><p class="eyebrow">FONTI E ATTRIBUZIONI</p><p><strong>'+esc(source)+'</strong> · Fonte originale del contenuto e delle informazioni riportate in questa scheda.</p>'+(sourceUrl?'<a class="text-link" href="'+esc(sourceUrl)+'" target="_blank" rel="noopener noreferrer">CONSULTA LA FONTE ORIGINALE ↗</a>':'<p class="detail-muted">Collegamento alla fonte non disponibile.</p>')+'<p class="detail-muted">La fotografia, quando presente, è stata controllata tecnicamente per formato, accessibilità e risoluzione. L’attribuzione resta all’editore originale.</p></section>';
document.title=(a.title||'Articolo')+' — ATELIER';
document.querySelector('meta[name="description"]').content=(a.excerpt||a.title||'Articolo ATELIER').slice(0,155);
document.getElementById('article-number').textContent=category.toLocaleUpperCase('it');
}
async function init(){
const id=new URLSearchParams(location.search).get('id');
if(!id){fail('Apri un articolo dalla homepage o dalla ricerca.');return;}
try{const r=await fetch('./data/articles.json',{cache:'no-store'});if(!r.ok)throw new Error('Archivio momentaneamente non raggiungibile.');const data=await r.json();const a=(data.articles||[]).find(item=>(item.id||item.url)===id);if(!a)throw new Error('Questo contenuto potrebbe essere stato rimosso o aggiornato.');render(a);}
catch(e){fail(e.message||'Errore durante il caricamento.');}
}
init();
})();