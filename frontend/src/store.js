import{api}from'./api.js';
export const state={user:null,data:null};
export async function refresh(){state.data=await api('/archive');return state}
