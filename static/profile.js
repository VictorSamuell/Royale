(() => {
 const status = document.getElementById('storage-status');
 const key = 'royale.profiles.v1';
 const valid = p => p && typeof p.name === 'string' && typeof p.tag === 'string' && /^#[0289PYLQGRJCUV]{3,15}$/.test(p.tag);
 let data = {favorites: [], recent: []};
 let storageOK = true;
 try {
  const saved = JSON.parse(localStorage.getItem(key) || '{}');
  for (const list of ['favorites', 'recent']) data[list] = Array.isArray(saved?.[list]) ? saved[list].filter(valid).slice(0, list === 'recent' ? 8 : 30) : [];
 } catch { storageOK = false; if (status) status.textContent = 'Armazenamento indisponível. Alterações valem apenas nesta página.'; }
 function save() {
  try { localStorage.setItem(key, JSON.stringify(data)); storageOK = true; }
  catch { storageOK = false; }
  if (status) status.textContent = storageOK ? 'Salvos apenas neste navegador, sem login.' : 'Não foi possível salvar neste navegador. Alterações valem apenas nesta página.';
 }
 const favorite = document.getElementById('favorite-profile');
 function render() {
  for (const [type, id] of [['favorites','favorites-list'],['recent','recent-list']]) {
   const container = document.getElementById(id); if (!container) continue;
   container.replaceChildren();
   if (!data[type].length) { const text=document.createElement('p');text.className='hint';text.textContent=type==='favorites'?'Nenhum favorito ainda. Abra um perfil e clique em Favoritar.':'As últimas consultas bem-sucedidas aparecem aqui.';container.append(text); }
   for (const profile of data[type]) {
    const wrapper=document.createElement('div'); wrapper.className='saved-entry';
    const link=document.createElement('a');link.className='example-profile';link.href='/players?'+new URLSearchParams({tag:profile.tag});
    const name=document.createElement('strong');name.textContent=profile.name;
    const tag=document.createElement('span');tag.textContent=profile.tag;link.append(name,tag);wrapper.append(link);
    if (type==='favorites') {const remove=document.createElement('button');remove.type='button';remove.textContent='Remover';remove.setAttribute('aria-label',`Remover ${profile.name} dos favoritos`);remove.addEventListener('click',()=>{data.favorites=data.favorites.filter(p=>p.tag!==profile.tag);save();render()});wrapper.append(remove);}
    container.append(wrapper);
   }
  }
  if (favorite) {const selected=data.favorites.some(p=>p.tag===favorite.dataset.tag);favorite.setAttribute('aria-pressed',String(selected));favorite.textContent=selected?'Remover dos favoritos':'Favoritar perfil';}
 }
 if (favorite) {
  const current={tag:favorite.dataset.tag,name:favorite.dataset.name};
  if (valid(current)) {
   data.recent=[current,...data.recent.filter(p=>p.tag!==current.tag)].slice(0,8);save();
   favorite.addEventListener('click',()=>{const exists=data.favorites.some(p=>p.tag===current.tag);if (!exists && data.favorites.length>=30) {if(status)status.textContent='Limite de 30 favoritos. Remova um perfil para adicionar outro.';return;} data.favorites=exists?data.favorites.filter(p=>p.tag!==current.tag):[current,...data.favorites];save();render();});
  }
 }
 document.getElementById('clear-recent')?.addEventListener('click',()=>{data.recent=[];save();render()});
 render();
 document.querySelectorAll('time[datetime]').forEach(time=>{const date=new Date(time.dateTime);if(!Number.isNaN(date.getTime()))time.textContent=date.toLocaleString('pt-BR');});
})();
