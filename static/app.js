"use strict";
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const list = text => text.trim() ? text.split(",").map(x => x.trim()) : [];
let mode = "language", result = null, stageIndex = 0, editorSignature = "", zoom = 1;
let processing = false, simulationRequest = 0;
// Textos de las dos modalidades del enunciado: A. a partir de un lenguaje; B. a partir de un autómata.
const MODES = {
  language: {title: "Modalidad A · Define tu lenguaje", button: "Construir, convertir y minimizar", first: "Construcción"},
  manual: {title: "Modalidad B · Define tu autómata", button: "Identificar, convertir y minimizar", first: "Identificación"}
};
function processLabel() { $("process-button").innerHTML = `${MODES[mode].button} <span>→</span>`; }

function setMode(next) {
  invalidate();
  mode = next;
  for (const name of ["language", "manual"]) {
    $(name + "-pane").hidden = name !== next;
    $(name + "-tab").classList.toggle("active", name === next);
    $(name + "-tab").setAttribute("aria-selected", String(name === next));
    $(name + "-tab").tabIndex = name === next ? 0 : -1;
  }
  $("input-title").textContent = MODES[next].title;
  processLabel();
  if (next === "manual" && !editorSignature) buildEditor();
}
for (const name of ["language", "manual"]) {
  $(name + "-tab").onclick = () => setMode(name);
  $(name + "-tab").onkeydown = e => {
    if (["ArrowLeft", "ArrowRight"].includes(e.key)) {
      e.preventDefault(); const next = mode === "language" ? "manual" : "language";
      setMode(next); $(next + "-tab").focus();
    }
  };
}
function error(message) { $("error").textContent = message; $("error").hidden = !message; }
function signature() { return JSON.stringify([list($("states").value), list($("automaton-alphabet").value)]); }
function editorData() {
  const edges = Object.create(null), states = list($("states").value);
  document.querySelectorAll("#transition-editor input").forEach(input => {
    // Como en clase, «error» (o una celda vacía) indica que no hay transición.
    const targets = list(input.value).filter(t => !(t.toLowerCase() === "error" && !states.includes(t)));
    (edges[input.dataset.state] ||= {})[input.dataset.symbol] = targets;
  });
  return edges;
}
function buildEditor(edges = null) {
  const states = list($("states").value), alphabet = list($("automaton-alphabet").value);
  if (!states.length || states.length > 80 || !alphabet.length || alphabet.length > 12) {
    error("Para crear la tabla, ingresa entre 1 y 80 estados y entre 1 y 12 símbolos."); return;
  }
  edges ||= editorData();
  const symbols = alphabet;
  $("transition-editor").innerHTML = `<table class="class-table"><thead><tr><th>Q</th>${symbols.map(s=>`<th>${esc(s)}</th>`).join("")}</tr></thead><tbody>${states.map(q=>`<tr><th>${esc(q)}</th>${symbols.map(s=>`<td><input aria-label="Destinos de ${esc(q)} con ${esc(s)}" data-state="${esc(q)}" data-symbol="${esc(s)}" placeholder="error" value="${esc((edges[q]?.[s] || []).join(","))}"></td>`).join("")}</tr>`).join("")}</tbody></table>`;
  editorSignature = signature(); error("");
}
$("build-table").onclick = () => buildEditor();
// Botones de reglas: insertan una línea con la sintaxis documentada usando símbolos de Σ.
document.querySelectorAll("[data-rule]").forEach(button => button.onclick = () => {
  const sigma = list($("alphabet").value), a = sigma[0] || "a", b = sigma[1] || a;
  const rule = button.dataset.rule.replaceAll("{a}", a).replaceAll("{b}", b);
  const box = $("rules"), text = box.value.replace(/\s+$/, "");
  box.value = (text ? text + "\n" : "") + rule; box.focus(); invalidate();
});

const examples = {
  vowels: {mode:"language", alphabet:["a","e","i","p"], rules:"toda W inicia y finaliza en a\nno repetidos vocales", word:"apa"},
  digits: {mode:"language", alphabet:["0","1","2"], rules:"toda W inicia y finaliza en 0\n2 seguido de 0 y precedido de 1\nsuma maxima 6\nlongitud maxima 5", word:"01120"},
  consonants: {mode:"language", alphabet:["a","e","m","b","p"], rules:"finaliza en vocal\nno consecutivos consonantes excepto mb, mp\nlongitud maxima 6", word:"ampa"},
  nfa: {mode:"manual", word:"010", automaton:{states:["A","B","C","D"], alphabet:["0","1"], initial:"A", finals:["A"], transitions:{A:{"0":["B"],"1":["A"]},B:{"0":["B","C"],"1":["D"]},C:{"0":["D"],"1":["C"]},D:{"0":["A"],"1":["B"]}}}},
  dfa: {mode:"manual", word:"ab", automaton:{states:["A","B","C","D"], alphabet:["a","b"], initial:"A", finals:["B","C"], transitions:{A:{a:["B"],b:["C"]},B:{a:["B"],b:["C"]},C:{a:["B"],b:["C"]},D:{a:["D"],b:["D"]}}}},
  xyzw: {mode:"manual", word:"00", automaton:{states:["X","Y","Z","W"], alphabet:["0","1","2"], initial:"X", finals:["Z"], transitions:{X:{"0":["Y"],"1":["Z"],"2":["W"]},Y:{"0":["Z"],"1":["Y"],"2":["X"]},Z:{"0":["W"],"1":["Y"],"2":["W"]},W:{"0":["X"],"1":["W"],"2":["Y"]}}}},
};
document.querySelectorAll("[data-example]").forEach(button => button.onclick = () => {
  const data = examples[button.dataset.example];
  setMode(data.mode);
  if (data.mode === "language") { $("alphabet").value = data.alphabet.join(", "); $("rules").value = data.rules; }
  else {
    $("automaton-alphabet").value = data.automaton.alphabet.join(", ");
    $("states").value = data.automaton.states.join(", ");
    $("initial").value = data.automaton.initial;
    $("finals").value = data.automaton.finals.join(", ");
    buildEditor(data.automaton.transitions);
  }
  $("word").value = data.word;
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
  if (mode === "manual" && signature() !== editorSignature) {error("Cambiaste los estados o el alfabeto. Pulsa «Generar / actualizar tabla de transiciones» y revisa sus destinos."); return;}
  const payload = mode === "language" ? {mode, alphabet:list($("alphabet").value), rules:$("rules").value} :
    {mode, automaton:{states:list($("states").value),alphabet:list($("automaton-alphabet").value),initial:$("initial").value.trim(),finals:list($("finals").value),transitions:editorData()}};
  processing = true; $("process-button").disabled = true; $("process-button").textContent = "Procesando…";
  // Bloquear la entrada impide asociar un resultado con datos editados durante la petición.
  const controls = document.querySelectorAll(".input-panel input, .input-panel textarea, .input-panel button");
  controls.forEach(c=>c.disabled = true);
  try {
    result = await post("/api/process", payload);
    $("empty-state").hidden = true; $("results").hidden = false;
    $("classification").textContent = result.classification; $("classification").hidden = false;
    const afnd = result.classification.startsWith("AFND");
    $("metrics").innerHTML = [["original_states","Estados de entrada"],["reachable_states","Accesibles"],["dfa_states",afnd?"AFD (conversión)":"AFD"],["minimal_states","AFD mínimo"]].map(([key,label])=>`<div class="metric"><b>${result.summary[key]}</b><span>${label}</span></div>`).join("");
    $("language").textContent = `L = {${result.language.join(", ")}${result.language.length >= 8 ? ", …" : ""}}`;
    $("language").hidden = !result.language.length;
    $("stage-nav").innerHTML = [MODES[mode].first, "Accesibles", afnd ? "AFND → AFD" : "AFD", "Mínimo"].map((name,i)=>`<button type="button" data-stage="${i}">${i+1}. ${name}</button>`).join("");
    $("stage-nav").querySelectorAll("button").forEach(b=>b.onclick=()=>showStage(Number(b.dataset.stage)));
    showStage(3);
  } catch (e) {invalidate(); error(e.message || "No hay conexión con el servidor.");}
  finally {processing=false; controls.forEach(c=>c.disabled=false); processLabel();}
};
// Tabla de transición como en clase: columna Q, flecha en el inicial,
// estado terminal encerrado en un círculo, «C,F» para varios destinos y «error» sin destino.
function table(a) {
  const symbols = [...a.alphabet];
  if (a.states.some(q=>a.transitions[q]?.["ε"]?.length)) symbols.push("ε");
  const name = q => a.finals.includes(q) ? `<span class="terminal" title="Estado final">${esc(q)}</span>` : esc(q);
  return `<table class="class-table"><thead><tr><th>Q</th>${symbols.map(s=>`<th>${esc(s)}</th>`).join("")}</tr></thead><tbody>${a.states.map(q=>`<tr><td class="state-cell">${q===a.initial?`<b class="initial-arrow" title="Estado inicial">→</b>`:""}${name(q)}</td>${symbols.map(s=>{const t=a.transitions[q]?.[s]||[];return `<td class="${t.length?"":"error-cell"}">${esc(t.join(",") || "error")}</td>`;}).join("")}</tr>`).join("")}</tbody></table>`;
}
// AF = { {Q}, q0, Σ, {Qt}, δ }
function formal(a) {
  return `<span>AF = { {Q}, q0, Σ, {Qt}, δ }</span><span>Q = {${esc(a.states.join(", "))}}</span><span>q0 = ${esc(a.initial)}</span><span>Σ = {${esc(a.alphabet.join(", "))}}</span><span>Qt = {${esc(a.finals.join(", "))}}</span>`;
}
function showStage(index) {
  stageIndex=index; const stage=result.stages[index]; zoom=1; simulationRequest++;
  $("simulation").innerHTML="";
  $("stage-nav").querySelectorAll("button").forEach((b,i)=>{b.classList.toggle("active",i===index); b.setAttribute("aria-current",i===index?"step":"false");});
  $("stage-counter").textContent=`ETAPA ${index+1} DE 4`;
  $("stage-title").textContent=stage.title;
  $("formal").innerHTML=formal(stage.automaton);
  $("transition-result").innerHTML=table(stage.automaton);
  $("mapping-result").innerHTML=Object.entries(stage.mapping).map(([q,members])=>`<p><b>${esc(q)}</b> = ${esc(members.length ? `{${members.join(", ")}}` : "∅ (estado ERROR)")}${stage.original_mapping?`<small>En la entrada: ${esc(stage.original_mapping[q].join(", ") || "∅")}</small>`:""}</p>`).join("");
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

// Diagrama con la presentación de clase: círculos dorados, nombres en rojo,
// flechas naranjas, flecha de entrada al inicial y doble círculo en los terminales.
const INK={node:"#b8862f",name:"#c0392b",edge:"#e69a2e",label:"#3b2f1e",fill:"#fffaf3",terminal:"#fff1dc"};
function drawDiagram(a) {
  const n=a.states.length;
  const r=q=>Math.min(62,Math.max(29,8+Math.min(q.length,14)*5.2));
  const maxR=Math.max(...a.states.map(r));
  const radius=n===1?0:Math.max(115,n*(maxR*0.75+8));
  const size=Math.max(350, radius*2+2*maxR+170), center=size/2;
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
    const rq=r(q), rt=r(t);
    if(q===t){
      // El bucle se dibuja hacia afuera del círculo de estados para no cruzar otras aristas.
      const ox0=x-center,oy0=y-center,len=Math.hypot(ox0,oy0)||1,ox=n===1?0:ox0/len,oy=n===1?-1:oy0/len;
      const at=(dist,ang)=>[x+dist*(ox*Math.cos(ang)-oy*Math.sin(ang)),y+dist*(ox*Math.sin(ang)+oy*Math.cos(ang))];
      const [sx,sy]=at(rq,-.45),[ex,ey]=at(rq+3,.45),[c1x,c1y]=at(rq+62,-.75),[c2x,c2y]=at(rq+62,.75);
      d=`M ${sx} ${sy} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${ex} ${ey}`;[lx,ly]=at(rq+58,0);ly+=4;
    }
    else {
      const dx=tx-x,dy=ty-y,length=Math.hypot(dx,dy),ux=dx/length,uy=dy/length;
      const bend=grouped.has(JSON.stringify([t,q]))?48:Math.min(28,length*.07);
      const cx=(x+tx)/2-uy*bend,cy=(y+ty)/2+ux*bend;
      const startLen=Math.hypot(cx-x,cy-y),endLen=Math.hypot(tx-cx,ty-cy);
      d=`M ${x+(cx-x)/startLen*(rq+1)} ${y+(cy-y)/startLen*(rq+1)} Q ${cx} ${cy} ${tx-(tx-cx)/endLen*(rt+5)} ${ty-(ty-cy)/endLen*(rt+5)}`;
      lx=(x+2*cx+tx)/4;ly=(y+2*cy+ty)/4-5;
    }
    paths+=`<path d="${d}" fill="none" stroke="${INK.edge}" stroke-width="1.6" marker-end="url(#arrow)"/>`;
    labels+=`<text x="${lx}" y="${ly}" text-anchor="middle" font-size="13" fill="${INK.label}" stroke="#fffdf8" stroke-width="4" paint-order="stroke" font-family="Arial,sans-serif">${esc(symbols.join(","))}</text>`;
  }
  for(const q of a.states){
    const [x,y]=pos[q],final=a.finals.includes(q),rq=r(q);
    if(q===a.initial)nodes+=`<path d="M ${x-rq-48} ${y} L ${x-rq-5} ${y}" stroke="${INK.edge}" stroke-width="2.2" marker-end="url(#arrow)"/>`;
    const label=q.length>14?q.slice(0,13)+"…":q;
    nodes+=`<g><title>${esc(q)}${q===a.initial?" (inicial)":""}${final?" (final)":""}</title><circle cx="${x}" cy="${y}" r="${rq}" fill="${final?INK.terminal:INK.fill}" stroke="${INK.node}" stroke-width="2.6"/>${final?`<circle cx="${x}" cy="${y}" r="${rq-5}" fill="none" stroke="${INK.node}" stroke-width="1.8"/>`:""}<text x="${x}" y="${y+5}" text-anchor="middle" font-family="Arial,sans-serif" font-size="${label.length>6?12:15}" fill="${INK.name}">${esc(label)}</text></g>`;
  }
  const shown=Math.max(350,Math.min(size,680));
  $("diagram").innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="${shown}" height="${shown}" role="img" aria-label="Diagrama de transición de ${n} estados" data-size="${shown}"><title>Diagrama de transición con ${n} estados; inicial ${esc(a.initial)}; finales ${esc(a.finals.join(", ") || "ninguno")}</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L7,3 z" fill="${INK.edge}"/></marker></defs>${paths}${labels}${nodes}</svg>`;
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
    const label=states=>states.length===1?states[0]:states.length?`{${states.join(",")}}`:"error";
    $("simulation").innerHTML=`<p class="verdict ${data.accepted?"":"rejected"}">${data.accepted?"✓ Palabra aceptada":"× Palabra rechazada"} · W = ${esc(data.word||"ε")}</p><div class="path">${data.path.map((step,i)=>`${i?`<i>,${esc(step.symbol)}→</i>`:""}<span>${esc(label(step.states))}</span>`).join("")}</div>`;
  }catch(e){if(id===simulationRequest)$("simulation").innerHTML=`<p class="error">${esc(e.message)}</p>`;}
  finally{$("simulate-button").disabled=false;}
};
