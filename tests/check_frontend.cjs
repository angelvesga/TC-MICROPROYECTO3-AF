// Pruebas de contrato de presentación sin iniciar ni automatizar un navegador.
// El DOM mínimo solo permite ejecutar el código de formato real de la aplicación.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const nodes = new Map();
const element = id => {
  if (!nodes.has(id)) nodes.set(id, {
    value: '', innerHTML: '', textContent: '', hidden: false,
    addEventListener() {}, setAttribute() {}, focus() {},
    classList: { toggle() {} }, querySelectorAll() { return []; }
  });
  return nodes.get(id);
};
const context = vm.createContext({
  document: { getElementById: element, querySelectorAll: () => [] },
  console, setTimeout
});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8'), context);
const a = JSON.parse('{"states":["__proto__","constructor"],"alphabet":["&","<"],"initial":"__proto__","finals":["constructor"],"transitions":{"__proto__":{"&":["constructor"],"<":["__proto__"]},"constructor":{"&":["constructor"],"<":["__proto__"]}}}');
context.sample = a;
const html = vm.runInContext('table(sample)', context);
assert(html.includes('&amp;') && html.includes('&lt;'));
assert(html.includes('constructor'));
assert(html.includes('<th>Q</th>') && html.includes('class="terminal"'));
vm.runInContext('drawDiagram(sample)', context);
const svg = element('diagram').innerHTML;
assert(svg.includes('<svg') && svg.includes('</svg>'));
assert(!svg.includes('NaN') && !svg.includes('undefined'));
assert(svg.includes('&amp;') && svg.includes('&lt;'));
assert(!svg.includes('<script'));
element('states').value = '__proto__, constructor';
element('alphabet').value = '&, <';
vm.runInContext('buildEditor(sample.transitions)', context);
assert(element('transition-editor').innerHTML.includes('data-state="__proto__"'));
assert(element('transition-editor').innerHTML.includes('value="constructor"'));
vm.runInContext('setMode("manual")', context);
assert.equal(element('results').hidden, true);
assert.equal(element('manual-pane').hidden, false);
assert.equal(element('regex-pane').hidden, true);
console.log('4 comprobaciones correctas: tabla escapada, SVG, nombres especiales y cambio de modalidad.');
