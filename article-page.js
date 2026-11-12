(() => {
'use strict';
const content=document.getElementById('article-content');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const url=v=>{try{const u=new URL(String(v||''),location.href);return ['http:','https:'].includes(u.protocol)&&String(v||'').trim()!=='#'?u.href:'';}catch(_){return '';}};
const cat=v=>({'Fashion':'Moda','Streetwear':'Streetwear','Design':'Design','Art & Culture':'Arte e cultura','Technology':'Tecnologia','Architecture':'Architettura','Business':'Impresa','Lifestyle':'Stili di vita','Journal':'Rivista'})[v]||v||'Rivista';
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
const imageFor=a=>{
const original=url(a.image);
if(original)return {url:original,verified:a.image_verified===true,sourceImage:true};
const choices=fallbackPhotos[a.category]||fallbackPhotos.Fashion;
const seed=String(a.title||a.id||'ATELIER').split('').reduce((n,c)=>n+c.charCodeAt(0),0);
return {url:'https://images.unsplash.com/'+choices[seed%choices.length]+'?auto=format&fit=crop&w=1600&q=85',verified:false,sourceImage:false};
};
const date=v=>{const d=new Date(v);return v&&!Number.isNaN(d.getTime())?d.toLocaleDateString('it-IT',{day:'2-digit',month:'long',year:'numeric'}).toUpperCase():'DATA NON DISPONIBILE';};
function compactText(value,maxWords=105){
const clean=String(value||'').replace(/\s+/g,' ').trim();if(!clean)return '';
const sentences=clean.match(/[^.!?]+[.!?]+|[^.!?]+$/g)||[clean];const chosen=[];let count=0;
for(const sentence of sentences){const words=sentence.trim().split(/\s+/);if(count&&count+words.length>maxWords)break;chosen.push(sentence.trim());count+=words.length;if(count>=maxWords)break;}
let result=chosen.join(' ');if(result.length<clean.length)result=result.replace(/[,:;\s]+$/,'')+'…';return result;
}
function editorialParagraphs(value){
const parts=String(value||'').trim().split(/\n\s*\n/).map(part=>part.trim()).filter(Boolean);
const highlightIndex=parts.length>=3?2:Math.max(0,parts.length-1);
return parts.map((part,index)=>{
if(index!==highlightIndex)return '<p>'+esc(part)+'</p>';
const match=part.match(/^(.+?[.!?])(?=\s|$)([\s\S]*)$/);
if(!match)return '<p><strong>'+esc(part)+'</strong></p>';
return '<p><strong>'+esc(match[1])+'</strong>'+esc(match[2])+'</p>';
}).join('');
}
function fail(msg){content.innerHTML='<p class="eyebrow">ATELIER / ARCHIVIO</p><h1 class="detail-title">Articolo non disponibile.</h1><p class="detail-excerpt">'+esc(msg)+'</p><a class="text-link" href="./">TORNA ALLA RIVISTA ↗</a>';}
function render(a){
const source=a.source||'Editore non identificato', category=cat(a.category), published=date(a.date), imageInfo=imageFor(a), image=imageInfo.url;
const photo=image?'<figure class="detail-figure"><img src="'+esc(image)+'" alt="'+esc(a.title||'Immagine editoriale ATELIER')+'" referrerpolicy="no-referrer" onerror="this.closest(\'.detail-figure\').classList.add(\'image-unavailable\');this.remove()"><figcaption>'+(imageInfo.verified?'Immagine verificata tecnicamente · ':imageInfo.sourceImage?'Immagine della fonte, non verificata · ':'Immagine illustrativa · ')+esc(source)+'</figcaption></figure>':'<div class="detail-no-image">IMMAGINE EDITORIALE NON DISPONIBILE</div>';
const editorial=String(a.editorial_summary||'').trim();
const sourceText=String(a.excerpt||'').trim();
const mainText=editorial?editorialParagraphs(editorial):'<p>'+esc(compactText(sourceText,170))+'</p>';
const summary=mainText?'<section class="detail-section editorial-summary"><p class="eyebrow">'+(editorial?'ATELIER · LA NOTIZIA':'IN BREVE · DALLA FONTE')+'</p><div class="detail-excerpt">'+mainText+'</div></section>':'<p class="detail-muted">La fonte non mette a disposizione una sintesi più ampia.</p>';
const sourceUrl=url(a.url);
const articleId=String(a.id||a.url||'');
content.innerHTML='<button type="button" class="like-article" data-like-article="'+esc(articleId)+'" aria-pressed="false">♡ <span data-like-count="'+esc(articleId)+'">0</span> MI PIACE</button><button type="button" class="save-article" data-save-article="'+esc(articleId)+'" aria-label="Salva articolo nei preferiti" aria-pressed="false">♡ SALVA NEI PREFERITI</button><div class="detail-topline"><span>'+esc(category.toLocaleUpperCase('it'))+'</span><span>'+esc(published)+'</span></div><h1 class="detail-title">'+esc(a.title||'Senza titolo')+'</h1>'+(a.author?'<p class="detail-byline">A cura di '+esc(a.author)+'</p>':'')+photo+summary+'<div class="detail-metadata"><span>EDITORE</span><strong>'+esc(source)+'</strong><span>DATA DI PUBBLICAZIONE</span><strong>'+esc(published)+'</strong><span>CATEGORIA</span><strong>'+esc(category)+'</strong>'+(a.language?'<span>LINGUA</span><strong>'+esc(String(a.language).toLocaleUpperCase('it'))+'</strong>':'')+'</div><section class="detail-sources"><p class="eyebrow">FONTI E ATTRIBUZIONI</p><p><strong>'+esc(source)+'</strong> · Fonte originale del contenuto e delle informazioni riportate in questa scheda.</p>'+(sourceUrl?'<a class="text-link" href="'+esc(sourceUrl)+'" target="_blank" rel="noopener noreferrer">CONSULTA LA FONTE ORIGINALE ↗</a>':'<p class="detail-muted">Collegamento alla fonte non disponibile.</p>')+'<p class="detail-muted">Le fotografie contrassegnate come verificate provengono dai metadati della fonte e hanno superato i controlli tecnici. Le immagini illustrative sono alternative visive e non documentano necessariamente il fatto narrato.</p></section>';
document.title=(a.title||'Articolo')+' — ATELIER';
document.querySelector('meta[name="description"]').content=(a.excerpt||a.title||'Articolo ATELIER').slice(0,155);
document.getElementById('article-number').textContent=category.toLocaleUpperCase('it');
document.dispatchEvent(new Event('atelier:article-rendered'));
}
async function init(){
const id=new URLSearchParams(location.search).get('id');
if(!id){fail('Apri un articolo dalla homepage o dalla ricerca.');return;}
try{const r=await fetch('./data/articles.json',{cache:'no-store'});if(!r.ok)throw new Error('Archivio momentaneamente non raggiungibile.');const data=await r.json();const a=(data.articles||[]).find(item=>(item.id||item.url)===id);if(!a)throw new Error('Questo contenuto potrebbe essere stato rimosso o aggiornato.');render(a);}
catch(e){fail(e.message||'Errore durante il caricamento.');}
}
init();
})();