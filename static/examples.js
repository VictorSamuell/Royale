const button = document.getElementById('load-top');
if (button) button.addEventListener('click', async () => {
 const status = document.getElementById('top-status');
 const list = document.getElementById('top-profiles');
 button.disabled = true;
 status.textContent = 'Buscando o ranking do Ranqueado…';
 try {
  const response = await fetch(button.dataset.url);
  if (!response.ok) throw new Error('unavailable');
  const data = await response.json();
  list.replaceChildren();
  for (const player of data.players) {
   const link = document.createElement('a'); link.className = 'example-profile'; link.href = player.url;
   const name = document.createElement('strong'); name.textContent = player.name;
   const rank = document.createElement('span'); rank.textContent = `#${player.rank} global · Ranqueado`;
   link.append(name, rank); list.append(link);
  }
  status.textContent = data.players.length ? 'Ranking consultado agora; pode ter até 5 minutos de cache.' : 'Nenhum jogador disponível no ranking neste momento.';
  button.hidden = data.players.length > 0;
 } catch {
  status.textContent = 'Não foi possível carregar o ranking. Você pode tentar novamente ou buscar uma tag.';
 } finally { button.disabled = false; }
});
