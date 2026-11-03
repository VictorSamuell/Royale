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
 const share = document.getElementById('share-profile');
 share?.addEventListener('click', () => {
  const canvas = document.createElement('canvas');
  canvas.width = 1200; canvas.height = 630;
  const ctx = canvas.getContext('2d');
  if (!ctx) { const message=document.getElementById('share-status'); if(message) message.textContent='Seu navegador não conseguiu criar a imagem.'; return; }
  const background=ctx.createLinearGradient(0,0,1200,630);
  background.addColorStop(0,'#101720'); background.addColorStop(1,'#1b2a42');
  ctx.fillStyle=background;ctx.fillRect(0,0,1200,630);
  ctx.strokeStyle='#e4bd68';ctx.lineWidth=6;ctx.strokeRect(28,28,1144,574);
  ctx.fillStyle='#e4bd68';ctx.font='bold 30px Arial';ctx.fillText('ROYALE',72,94);
  ctx.fillStyle='#edf1f5';ctx.font='bold 62px Arial';
  let name=share.dataset.name || 'Jogador';
  while(ctx.measureText(name).width>1040 && name.length>3) name=name.slice(0,-2)+'…';
  ctx.fillText(name,72,210);
  ctx.fillStyle='#a7b4c3';ctx.font='30px Arial';ctx.fillText(share.dataset.tag || '',74,260);
  ctx.strokeStyle='#303e4d';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(72,310);ctx.lineTo(1128,310);ctx.stroke();
  const stats=[['MELHOR LIGA',share.dataset.league],['MAIOR CAMPEÃO',share.dataset.points+' pontos'],['TROFÉUS',share.dataset.trophies],['APROVEITAMENTO',share.dataset.winrate]];
  stats.forEach(([label,value],i)=>{
   const x=72+(i%2)*540,y=390+Math.floor(i/2)*112;
   ctx.fillStyle='#a7b4c3';ctx.font='bold 19px Arial';ctx.fillText(label,x,y);
   ctx.fillStyle='#edf1f5';ctx.font='bold 34px Arial';
   let display=String(value || '—');while(ctx.measureText(display).width>480 && display.length>4) display=display.slice(0,-2)+'…';
   ctx.fillText(display,x,y+42);
  });
  ctx.fillStyle='#a7b4c3';ctx.font='18px Arial';ctx.fillText('Perfil gerado em royale-5z0o.onrender.com',72,560);
  canvas.toBlob(blob=>{
   if(!blob){const message=document.getElementById('share-status');if(message)message.textContent='Não foi possível gerar o cartão. Tente novamente.';return;}
   const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=`royale-${(share.dataset.tag||'perfil').replace('#','')}.png`;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
   const message=document.getElementById('share-status');if(message)message.textContent='Cartão baixado em PNG, pronto para compartilhar.';
  },'image/png');
 });
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
