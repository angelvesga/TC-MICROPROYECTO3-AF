"use strict";
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const list = text => text.trim() ? text.split(",").map(x => x.trim()) : [];
let mode = "regex", result = null, stageIndex = 0, editorSignature = "", zoom = 1;
let processing = false, simulationRequest = 0;

function setMode(next) {
  invalidate();
  mode = next;
  for (const name of ["regex", "manual"]) {
    $(name + "-pane").hidden = name !== next;
    $(name + "-tab").classList.toggle("active", name === next);
    $(name + "-tab").setAttribute("aria-selected", String(name === next));
    $(name + "-tab").tabIndex = name === next ? 0 : -1;
  }
  if (next === "manual" && !editorSignature) buildEditor();
}
for (const name of ["regex", "manual"]) {
  $(name + "-tab").onclick = () => setMode(name);
  $(name + "-tab").onkeydown = e => {
    if (["ArrowLeft", "ArrowRight"].includes(e.key)) {
      e.preventDefault(); const next = mode === "regex" ? "manual" : "regex";
      setMode(next); $(next + "-tab").focus();
    }
  };
}
function error(message) { $("error").textContent = message; $("error").hidden = !message; }
function signature() { return JSON.stringify([list($("states").value), list($("alphabet").value)]); }
function editorData() {
  const edges = Object.create(null);
  document.querySelectorAll("#transition-editor input").forEach(input => {
    (edges[input.dataset.state] ||= {})[input.dataset.symbol] = list(input.value);
  });
  return edges;
}
function buildEditor(edges = null) {
  const states = list($("states").value), alphabet = list($("alphabet").value);
  if (!states.length || states.length > 80 || !alphabet.length || alphabet.length > 12) {
    error("Para crear la tabla, ingresa entre 1 y 80 estados y entre 1 y 12 símbolos."); return;
  }
  edges ||= editorData();
  const symbols = [...alphabet, "ε"];
  $("transition-editor").innerHTML = `<table><thead><tr><th>Estado</th>${symbols.map(s=>`<th>${esc(s)}</th>`).join("")}</tr></thead><tbody>${states.map(q=>`<tr><th>${esc(q)}</th>${symbols.map(s=>`<td><input aria-label="Destinos de ${esc(q)} con ${esc(s)}" data-state="${esc(q)}" data-symbol="${esc(s)}" value="${esc((edges[q]?.[s] || []).join(", "))}"></td>`).join("")}</tr>`).join("")}</tbody></table>`;
  editorSignature = signature(); error("");
}
$("build-table").onclick = () => buildEditor();

const examples = {
  suffix: {mode:"regex", alphabet:["a","b"], expression:"(a|b)*abb"},
  nfa: {mode:"manual", automaton:{states:["q0","q1","q2"], alphabet:["a","b"], initial:"q0", finals:["q2"], transitions:{q0:{a:["q0","q1"],b:["q0"]},q1:{b:["q2"]},q2:{}}}},
  dfa: {mode:"manual", automaton:{states:["A","B","C","X"], alphabet:["a","b"], initial:"A", finals:["B","C"], transitions:{A:{a:["B"],b:["C"]},B:{a:["B"],b:["C"]},C:{a:["B"],b:["C"]},X:{a:["X"],b:["X"]}}}}
};
document.querySelectorAll("[data-example]").forEach(button => button.onclick = () => {
  const data = examples[button.dataset.example];
  setMode(data.mode);
  $("alphabet").value = (data.alphabet || data.automaton.alphabet).join(", ");
  if (data.mode === "regex") $("expression").value = data.expression;
  else {
    $("states").value = data.automaton.states.join(", ");
    $("initial").value = data.automaton.initial;
    $("finals").value = data.automaton.finals.join(", ");
    buildEditor(data.automaton.transitions);
  }
  $("word").value = button.dataset.example === "suffix" ? "aabb" : "ab";
  invalidate(); $("process-button").focus();
});
function invalidate() {
  result = null; simulationRequest++;
  $("results").hidden = true; $("classification").hidden = true; $("empty-state").hidden = false;
  error("");
}
$("process-form").addEventListener("input", invalidate);
async function post(url, data) {
  const response = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)});
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "No se pudo completar la operación.");
  return body;
}
$("process-form").onsubmit = async event => {
  event.preventDefault(); if (processing) return;
  error("");
  if (mode === "manual" && signature() !== editorSignature) {error("Cambiaste estados o alfabeto. Pulsa «Actualizar tabla de entrada» y revisa sus destinos."); return;}
  const payload = mode === "regex" ? {mode, alphabet:list($("alphabet").value), expression:$("expression").value} :
    {mode, automaton:{states:list($("states").value),alphabet:list($("alphabet").value),initial:$("initial").value.trim(),finals:list($("finals").value),transitions:editorData()}};
  processing = true; $("process-button").disabled = true; $("process-button").textContent = "Procesando…";
  // Bloquear la entrada impide asociar un resultado con datos editados durante la petición.
  const controls = document.querySelectorAll(".input-panel input, .input-panel button");
  controls.forEach(c=>c.disabled = true);
  try {
    result = await post("/api/process", payload);
    $("empty-state").hidden = true; $("results").hidden = false;
    $("classification").textContent = result.classification; $("classification").hidden = false;
    $("metrics").innerHTML = [["original_states","Originales"],["reachable_states","Accesibles"],["dfa_states","AFD completo"],["minimal_states","AFD mínimo"]].map(([key,label])=>`<div class="metric"><b>${result.summary[key]}</b><span>${label}</span></div>`).join("");
    $("stage-nav").innerHTML = ["Entrada","Accesibles","AFD","Mínimo"].map((name,i)=>`<button type="button" data-stage="${i}">${i+1}. ${name}</button>`).join("");
    $("stage-nav").querySelectorAll("button").forEach(b=>b.onclick=()=>showStage(Number(b.dataset.stage)));
    showStage(3);
  } catch (e) {invalidate(); error(e.message || "No hay conexión con el servidor.");}
  finally {processing=false; controls.forEach(c=>c.disabled=false); $("process-button").innerHTML="Construir y minimizar <span>→</span>";}
};
function table(a) {
  const symbols = [...a.alphabet];
  if (a.states.some(q=>a.transitions[q]?.["ε"]?.length)) symbols.push("ε");
  return `<table><thead><tr><th>Estado</th>${symbols.map(s=>`<th>${esc(s)}</th>`).join("")}</tr></thead><tbody>${a.states.map(q=>`<tr><td class="${a.finals.includes(q)?"final":""}">${q===a.initial?"→ ":""}${a.finals.includes(q)?"* ":""}${esc(q)}</td>${symbols.map(s=>`<td>${esc(a.transitions[q]?.[s]?.join(", ") || "∅")}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
function showStage(index) {
  stageIndex=index; const stage=result.stages[index]; zoom=1; simulationRequest++;
  $("simulation").innerHTML="";
  $("stage-nav").querySelectorAll("button").forEach((b,i)=>{b.classList.toggle("active",i===index); b.setAttribute("aria-current",i===index?"step":"false");});
  $("stage-counter").textContent=`ETAPA ${index+1} DE 4`;
  $("stage-title").textContent=stage.title;
  $("transition-result").innerHTML=table(stage.automaton);
  $("mapping-result").innerHTML=Object.entries(stage.mapping).map(([q,members])=>`<p><b>${esc(q)}</b> = ${esc(members.length ? `{${members.join(", ")}}` : "∅ (sumidero)")}${stage.original_mapping?`<small>En la entrada: ${esc(stage.original_mapping[q].join(", ") || "∅")}</small>`:""}</p>`).join("");
  $("step-list").innerHTML=stage.steps.map(step=>`<li>${esc(step)}</li>`).join("");
  $("step-count").textContent=`${stage.steps.length} operaciones`;
  const min=result.stages[3].automaton;
  $("comparison-result").innerHTML=`<p>Etapa seleccionada: <b>${stage.automaton.states.length}</b> estados. AFD mínimo: <b>${min.states.length}</b> estados. Ambos reconocen el mismo lenguaje.</p><h4>Tabla del AFD mínimo</h4>${table(min)}`;
  drawDiagram(stage.automaton);
}
for (const name of ["table","mapping"]) $(name+"-tab").onclick=()=>{
  for (const other of ["table","mapping"]) {
    $(other+"-tab").classList.toggle("active",other===name);
    $(other+"-tab").setAttribute("aria-pressed",String(other===name));
  }
  $("transition-result").hidden=name!=="table"; $("mapping-result").hidden=name!=="mapping";
};

function drawDiagram(a) {
  const n=a.states.length, radius=n===1?0:Math.max(115,n*22);
  const size=Math.max(350, radius*2+180), center=size/2;
  const pos=Object.create(null);
  a.states.forEach((q,i)=>{const angle=-Math.PI/2+i*2*Math.PI/n; pos[q]=[center+radius*Math.cos(angle),center+radius*Math.sin(angle)];});
  const grouped=new Map();
  for(const q of a.states) for(const [s,targets] of Object.entries(a.transitions[q] || {})) for(const t of targets){
    const key=JSON.stringify([q,t]); if(!grouped.has(key))grouped.set(key,[]); grouped.get(key).push(s);
  }
  let paths="", labels="", nodes="";
  for(const [key,symbols] of grouped){
    const [q,t]=JSON.parse(key), [x,y]=pos[q], [tx,ty]=pos[t];
    let d,lx,ly;
    if(q===t){d=`M ${x-18} ${y-22} C ${x-68} ${y-88}, ${x+68} ${y-88}, ${x+18} ${y-22}`;lx=x;ly=y-70;}
    else {
      const dx=tx-x,dy=ty-y,length=Math.hypot(dx,dy),ux=dx/length,uy=dy/length;
      const bend=grouped.has(JSON.stringify([t,q]))?48:Math.min(28,length*.07);
      const cx=(x+tx)/2-uy*bend,cy=(y+ty)/2+ux*bend;
      const startLen=Math.hypot(cx-x,cy-y),endLen=Math.hypot(tx-cx,ty-cy);
      d=`M ${x+(cx-x)/startLen*30} ${y+(cy-y)/startLen*30} Q ${cx} ${cy} ${tx-(tx-cx)/endLen*34} ${ty-(ty-cy)/endLen*34}`;
      lx=(x+2*cx+tx)/4;ly=(y+2*cy+ty)/4-5;
    }
    paths+=`<path d="${d}" fill="none" stroke="#73958b" stroke-width="1.5" marker-end="url(#arrow)"/>`;
    labels+=`<text x="${lx}" y="${ly}" text-anchor="middle" font-size="12" fill="#335e54" stroke="#f8faf7" stroke-width="4" paint-order="stroke" font-family="Consolas,monospace">${esc(symbols.join(","))}</text>`;
  }
  for(const q of a.states){
    const [x,y]=pos[q],final=a.finals.includes(q);
    if(q===a.initial)nodes+=`<path d="M ${x-75} ${y} L ${x-34} ${y}" stroke="#087d70" stroke-width="2" marker-end="url(#arrow)"/>`;
    nodes+=`<g><title>${esc(q)}${final?" (final)":""}</title><circle cx="${x}" cy="${y}" r="29" fill="${final?"#e3f3e9":"#ffffff"}" stroke="#087d70" stroke-width="1.8"/>${final?`<circle cx="${x}" cy="${y}" r="24" fill="none" stroke="#087d70"/>`:""}<text x="${x}" y="${y+4}" text-anchor="middle" font-family="Consolas,monospace" font-size="${q.length>5?9:12}" fill="#174b42">${esc(q.length>9?q.slice(0,7)+"…":q)}</text></g>`;
  }
  $("diagram").innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="${Math.max(350,Math.min(size,680))}" height="${Math.max(350,Math.min(size,680))}" role="img" aria-label="Autómata de ${n} estados" data-size="${Math.max(350,Math.min(size,680))}"><title>Autómata con ${n} estados; inicial ${esc(a.initial)}; finales ${esc(a.finals.join(", ") || "ninguno")}</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L7,3 z" fill="#73958b"/></marker></defs>${paths}${labels}${nodes}</svg>`;
}
function changeZoom(factor){const svg=$("diagram").querySelector("svg");if(!svg)return;zoom=Math.max(.5,Math.min(6,zoom*factor));svg.setAttribute("width",svg.dataset.size*zoom);svg.setAttribute("height",svg.dataset.size*zoom);}
$("zoom-in").onclick=()=>changeZoom(1.3);$("zoom-out").onclick=()=>changeZoom(1/1.3);
function download(content,type,name){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement("a");a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$("download-json").onclick=()=>result&&download(JSON.stringify(result,null,2),"application/json","resultado-automata.json");
$("download-svg").onclick=()=>download($("diagram").querySelector("svg").outerHTML,"image/svg+xml",`automata-${result.stages[stageIndex].id}.svg`);
$("simulate-form").onsubmit=async event=>{
  event.preventDefault();if(!result)return;const id=++simulationRequest;
  $("simulate-button").disabled=true;
  try{
    const data=await post("/api/simulate",{automaton:result.stages[stageIndex].automaton,word:$("word").value});
    if(id!==simulationRequest)return;
    $("simulation").innerHTML=`<p class="verdict ${data.accepted?"":"rejected"}">${data.accepted?"✓ Cadena aceptada":"× Cadena rechazada"} · ${esc(data.word||"ε")}</p><div class="path">${data.path.map((step,i)=>`${i?`<i>—${esc(step.symbol)}→</i>`:""}<span>${esc(step.states.length?`{${step.states.join(", ")}}`:"∅")}</span>`).join("")}</div>`;
  }catch(e){if(id===simulationRequest)$("simulation").innerHTML=`<p class="error">${esc(e.message)}</p>`;}
  finally{$("simulate-button").disabled=false;}
};
