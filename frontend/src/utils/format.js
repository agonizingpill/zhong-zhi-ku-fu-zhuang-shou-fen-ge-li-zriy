export const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function data(form,numbers=[]){let d=Object.fromEntries(new FormData(form));for(let k of numbers)d[k]=Number(d[k]);return d}
export const number=x=>Number(x??0).toLocaleString('zh-CN');
