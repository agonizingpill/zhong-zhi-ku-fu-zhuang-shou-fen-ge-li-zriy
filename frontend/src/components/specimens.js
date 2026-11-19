import{esc,number}from'../utils/format.js';
export const title=(tag,heading,desc)=>`<div class="pagehead"><div class="eyebrow">QINGHE FIELD BOOK / ${tag}</div><h1>${heading}</h1><p>${desc}</p></div>`;
export const specimen=(lot,d)=>{let a=d.accessions.find(a=>a.id===lot.accession_id);return `<div class="specimen"><span class="seedmark">◒</span><div><b>${esc(a.code)} · ${esc(a.name)}</b><small>${esc(lot.code)} / G${lot.generation} / ${number(lot.available)} 粒</small></div></div>`};
export const reserve=(a,d)=>{let total=d.lots.filter(l=>l.accession_id===a.id).reduce((n,l)=>n+l.available,0);return `<div class="reserve"><span>活种保底 / ${esc(a.code)}</span><b>${number(total)} <small>/ 最低 ${number(a.minimum)} 粒</small></b><div class="reserve-track"><i style="width:${Math.min(100,a.minimum/Math.max(total,1)*100)}%"></i></div><small>保底量按同种质全部种批合计，抽样 / 复壮 / 共享共同扣用。</small></div>`};
export const lotOptions=d=>d.lots.map(l=>`<option value="${l.id}">${esc(l.code)} / G${l.generation} / ${l.available}粒</option>`).join('');
export const regenOptions=(d,states=['issued'])=>d.regenerations.filter(r=>states.includes(r.state)).map(r=>`<option value="${r.id}">${esc(r.code)} / ${r.issued}粒</option>`).join('');
export const empty=text=>`<div class="empty">${esc(text)}</div>`;
export const flowerBand=(f,d)=>{let p=d.plots.find(p=>p.id===f.plot_id),r=d.regenerations.find(r=>r.id===f.regeneration_id);return `<div class="flowerband"><strong>${esc(p.code)}</strong><span>${esc(r.code)}</span><i></i><b>${f.start} → ${f.end}</b><small>${esc(f.state)}</small></div>`};
