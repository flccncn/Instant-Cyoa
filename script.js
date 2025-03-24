let resources = {};
let tags = [];
let realTags = [];

const container = document.getElementById('game-container');

async function loadJSON(path) {
  const response = await fetch(path + '?v=' + Date.now());
  return await response.json();
}

async function startGame() {
  const intro = await loadJSON('./data/intro.json');
  resources = await loadJSON('./data/resource.json');
  addElements(intro);
}

let activeToggles = [];
let buttonIdCounter = 0;

function generateId() {
  return 'btn_' + (buttonIdCounter++);
}

function addElements(data) {
  const row = document.createElement('div');
  row.className = 'flex-row';
  container.appendChild(row);

  let currentWidth = 0;
  let currentLine = createFlexLine();
  row.appendChild(currentLine);

  for (const item of data) {
    const width = item.width ?? 100;
    if (currentWidth + width > 100) {
      currentLine = createFlexLine();
      row.appendChild(currentLine);
      currentWidth = 0;
    }

    const element = createElement(item, width);
    currentLine.appendChild(element);
    currentWidth += width;
  }
}

function createFlexLine() {
  const line = document.createElement('div');
  line.className = 'flex-line';
  return line;
}

function formatText(text) {
  const trimmed = text.trim();
  const withLineBreaks = trimmed.replace(/\n/g, "<br>");
  const withQuotes = withLineBreaks.replace(/'([^']+)'/g, `<span class="quote">“$1”</span>`);
  return withQuotes;
}

const pastelBackgrounds = [
  '#fff7f7'
];

function createElement(item, width) {
  const wrapper = document.createElement('div');
  wrapper.className = 'intro-item';
  wrapper.style.flexBasis = `${width}%`;

  if (item.type !== 'line' && item.type !== 'image') {
    const randomBg = pastelBackgrounds[Math.floor(Math.random() * pastelBackgrounds.length)];
    wrapper.style.setProperty('--item-bg', randomBg);
  }

  if (item.type === 'textbox') {
    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'textbox-content';

    const textBlock = document.createElement('div');
    textBlock.className = 'textbox-text';

    if (item.title) {
      const title = document.createElement('h3');
      title.textContent = item.title;
      textBlock.appendChild(title);
    }

    if (item.text) {
      const text = document.createElement('p');
      text.innerHTML = formatText(item.text);
      textBlock.appendChild(text);
    }

    contentWrapper.appendChild(textBlock);

    if (item.image) {
      const img = document.createElement('img');
      img.src = `./image/${item.image}`;
      img.alt = '';
      img.className = 'textbox-image';
      contentWrapper.appendChild(img);
    }

    wrapper.appendChild(contentWrapper);
  }


  else if (item.type === 'button') {
    const id = item.id ?? generateId();
    const btn = document.createElement('button');
    btn.className = 'fancy-button';
    btn.style.flexBasis = `${width}%`;
    btn.id = id;

    if (item.image) {
      const img = document.createElement('img');
      img.src = `./image/${item.image}`;
      img.alt = '';
      img.className = 'button-image';
      contentWrapper.appendChild(img);
    }

    if (item.title) {
      const title = document.createElement('div');
      title.className = 'button-title';
      title.textContent = item.title;
      btn.appendChild(title);
    }

    if (item.text) {
      const text = document.createElement('div');
      text.className = 'button-text';
      text.textContent = item.text;
      btn.appendChild(text);
    }

    const eventList = item.events ?? [];

    if (item.actionType === 'toggle') {
      btn.dataset.active = "false";
      btn.addEventListener('click', () => {
        const isActive = btn.dataset.active === "true";
        btn.dataset.active = (!isActive).toString();
        if (isActive) {
          activeToggles = activeToggles.filter(e => e._btnId !== id);
          btn.classList.remove('active');
        } else {
          const wrapped = eventList.map(e => ({ ...e, _btnId: id }));
          activeToggles.push(...wrapped);
          btn.classList.add('active');
        }
        updateValues();
      });
    } else {
      btn.addEventListener('click', () => {
        executeEvents(eventList);
        updateValues();
      });
    }

    return btn;
  }

  else if (item.type === 'image') {
    const img = document.createElement('img');
    img.src = `./image/${item.image}`;
    img.alt = "";
    img.className = 'intro-img';
    img.style.flexBasis = `${width}%`;
    return img;
  }

  else if (item.type === 'line') {
    const hr = document.createElement('hr');
    hr.className = 'full-line';
    return hr;
  }


  return wrapper;
}

function executeEvents(events) {
  for (const e of events) {
    if (e.type === 'cyoaStart') {
      startCustomization();
    }
    if (e.type === 'setValue') {
      handleSetValue(e, 'realValue')
    }
  }
}

async function startCustomization() {
  document.getElementById('startButton').style.display = 'none';
  document.getElementById('status-bar').style.display = 'flex';
  addElements([{ "type":"line" }])
  const data = await loadJSON('./data/custom.json');

  for (const categoryName in data) {
    const category = data[categoryName];

    const title = document.createElement('h2');
    title.textContent = categoryName;
    title.className = 'category-title';
    container.appendChild(title);

    if (category.description) {
      const desc = document.createElement('p');
      desc.textContent = category.description;
      desc.className = 'category-desc';
      container.appendChild(desc);
    }

    if (Array.isArray(category.elements)) {
      addElements(category.elements);
    }
  }

  updateValues();

}

function returnValue(expr) {
  const tokens = tokenize(expr);
  console.log("Tokens:", tokens);

  const replaced = replaceTokens(tokens);
  console.log("Replaced:", replaced);

  const postfix = toPostfix(replaced);
  console.log("Postfix:", postfix);

  const result = evaluatePostfix(postfix);
  return typeof result === 'number' ? Math.floor(result) : result;
}

function tokenize(expr) {
  const pattern = /(==|!=|>=|<=|<<|>>|\|\||&&|\^\^|[+\-*/%()<>]|\d+\.?\d*|".*?"|[가-힣\w]+)/g;
  return [...expr.matchAll(pattern)].map(m => m[0].replace(/\s/g, ''));
}


function replaceTokens(tokens) {
  return tokens.map(tok => {
    if (tok === 'true') return true;
    if (tok === 'false') return false;

    if (['(', ')'].includes(tok)) return tok;

    if (tok === 'tags' || tok === '태그') return tags;

    const resource = Object.entries(resources).find(([id, val]) =>
      id === tok || val.name === tok
    );
    if (resource) return resource[1].value;

    if (/^".*"$/.test(tok)) return tok.slice(1, -1);
    if (!isNaN(tok)) return Number(tok);

    return tok;
  });
}


const precedence = {
  '||': 2,
  '^^': 3,
  '&&': 4,
  '<<': 5, '>>': 5,
  '==': 6, '!=': 6, '>': 6, '<': 6, '>=': 6, '<=': 6,
  '+': 7, '-': 7,
  '*': 8, '/': 8, '%': 8
};



function isOperator(token) {
  return ['(', ')'].includes(token) || Object.prototype.hasOwnProperty.call(precedence, token);
}

function toPostfix(tokens) {
  const output = [];
  const opStack = [];

  for (const tok of tokens) {
    if (typeof tok === 'number' || typeof tok === 'boolean' || Array.isArray(tok)) {
      output.push(tok);
    } else if (typeof tok === 'string' && !isOperator(tok)) {
      output.push(tok);
    } else if (tok === '(') {
      opStack.push(tok);
    } else if (tok === ')') {
      while (opStack.length && opStack[opStack.length - 1] !== '(') {
        output.push(opStack.pop());
      }
      opStack.pop();
    } else if (isOperator(tok)) {
      while (
        opStack.length &&
        isOperator(opStack[opStack.length - 1]) &&
        precedence[opStack[opStack.length - 1]] >= precedence[tok]
      ) {
        output.push(opStack.pop());
      }
      opStack.push(tok);
    } else {
      console.warn(`Unknown token encountered during toPostfix: ${tok}`);
    }
  }

  while (opStack.length) output.push(opStack.pop());

  return output;
}


function evaluatePostfix(postfix) {
  const stack = [];

  for (const token of postfix) {
    if (
      typeof token === 'number' ||
      typeof token === 'boolean' ||
      Array.isArray(token) ||
      (typeof token === 'string' && !isOperator(token))
    ) {
      stack.push(token);
    } else {
      const b = stack.pop();
      const a = stack.pop();
      stack.push(applyOperator(a, b, token));
    }
  }

  return stack[0];
}


function applyOperator(a, b, op) {
  switch (op) {
    case '+': return a + b;
    case '-': return a - b;
    case '*': return a * b;
    case '/': return Math.floor(a / b);
    case '%': return a % b;
    case '==': return a == b;
    case '!=': return a != b;
    case '>': return a > b;
    case '<': return a < b;
    case '>=': return a >= b;
    case '<=': return a <= b;
    case '<<': return Array.isArray(b) && b.includes(a);
    case '>>': return Array.isArray(a) && a.includes(b);
    case '&&': return a && b;
    case '||': return a || b;
    case '^^': return (!!a) !== (!!b);
    default: throw new Error(`Unknown operator: ${op}`);
  }
}

function handleSetValue(event, field = 'value') {
  const { target, operation, value } = event;
  const evaluated = returnValue(value);

  if (target === 'tags' || target === '태그') {
    console.log(target, operation, evaluated)
    let tagList = (field === 'realValue') ? realTags : tags;

    if (operation === 'add') {
      if (!tagList.includes(evaluated)) tagList.push(evaluated);
    } else if (operation === 'remove') {
      tagList = tagList.filter(t => t !== evaluated);
    }

    if (field === 'realValue') realTags = tagList;
    else tags = tagList;

    return;
  }

  const res = resources[target];
  if (!res || !(field in res)) {
    console.warn(`잘못된 setValue 대상: ${target} / 필드: ${field}`);
    return;
  }

  const current = res[field];
  switch (operation) {
    case '=':
      res[field] = Math.floor(evaluated);
      break;
    case '+':
      res[field] = Math.floor(current + evaluated);
      break;
    case '-':
      res[field] = Math.floor(current - evaluated);
      break;
    case '*':
      res[field] = Math.floor(current * evaluated);
      break;
    case '/':
      res[field] = Math.floor(current / evaluated);
      break;
    default:
      console.warn(`알 수 없는 연산: ${operation}`);
  }
}

function updateValues() {
  for (const key in resources) {
    const res = resources[key];
    res.value = res.realValue;
  }
  tags = [...realTags];
  for (const ev of activeToggles) {
    if (ev.type == "setValue") {
      handleSetValue(ev);
    }
  }
  updateStatusBar();
}

function updateStatusBar() {
  const bar = document.getElementById('status-bar');
  bar.innerHTML = '';

  for (const key in resources) {
    const res = resources[key];
    if (!res.show) continue;

    const el = document.createElement('div');
    el.className = 'status-box';
    el.textContent = `${res.name}: ${res.value}`;
    bar.appendChild(el);
  }
}

function fixValue(targetKey = null) {
  if (targetKey === 'tags' || targetKey === '태그') {
    realTags = [...tags];

    activeToggles = activeToggles.filter(ev => {
      return !(ev.type === "setValue" && (ev.target === "tags" || ev.target === "태그"));
    });

    updateValues();
    return;
  }

  const res = resources[targetKey];

  if (!targetKey) {
    for (const key in resources) {
      fixValue(key);
    }
    fixValue("tags");
    return;
  } else if (!res) {
    console.warn(`존재하지 않는 자원: ${targetKey}`);
    return;
  }

  res.realValue = res.value;

  activeToggles = activeToggles.filter(ev => {
    return !(ev.type === "setValue" && ev.target === targetKey);
  });

  updateValues();
}




window.onload = startGame;
