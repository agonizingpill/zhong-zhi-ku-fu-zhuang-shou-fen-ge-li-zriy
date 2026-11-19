import{api}from'../api.js';
export function toast(message){let x=document.querySelector('#toast');x.textContent=message;x.classList.add('show');clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>x.classList.remove('show'),5500)}
export async function perform(path,method,payload,reload,message,after){try{let value=await api(path,method,payload);if(after)after(value);await reload();toast(message);return value}catch(e){toast(e.message)}}
export function bindActions(reload){document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>perform(b.dataset.action,'POST',{},reload,b.dataset.message||'业务记录已更新'))}
