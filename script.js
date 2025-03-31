let customData = {};
let resources = {};
let scene = [];
let endings = {};
let setting = {};
let tags = [];
let realTags = [];
let items = [];
let realItems = [];

let phase = 'intro';

let eventCount = 0;
let currentEvent = null;

const eventHistory = [];
let currentLog = {
    title: '',
    summary: [],
    choices: [],
    scene: [[]]
}

let DEV_MODE = false;

function toggleDevMode() {
    DEV_MODE = !DEV_MODE;
    document.body.classList.toggle("dev-mode", DEV_MODE);
    document.getElementById("dev-toggle").textContent = DEV_MODE ? "🛠 Dev ON" : "🚫 Dev OFF";
    console.log("개발자 모드:", DEV_MODE);

    updateValues();
    updateStatusBar();
}

function insertDevToggleButton() {
    const btn = document.createElement("button");
    btn.id = "dev-toggle";
    btn.textContent = "🚫 Dev OFF";
    btn.onclick = toggleDevMode;
    btn.style.cssText = `
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 9999;
        background: rgba(0,0,0,0.7);
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
    `;
    document.body.appendChild(btn);
}

function detectInitialDevMode() {
    const host = location.hostname;
    return (
        host === "localhost" ||
        host === "127.0.0.1" ||
        host === "0.0.0.0" ||
        host === "" ||
        location.protocol === "file:"
    );
}

function saveData(key, value) {
    try {
        localStorage.setItem('DD_' + key, JSON.stringify(value));
    } catch (e) {
        console.error('로컬스토리지 저장 실패:', e);
    }
}

function loadData(key, defaultValue = null) {
    try {
        const stored = localStorage.getItem('DD_' + key);
        return stored ? JSON.parse(stored) : defaultValue;
    } catch (e) {
        console.error('로컬스토리지 불러오기 실패:', e);
        return defaultValue;
    }
}

if (detectInitialDevMode()) {
    window.addEventListener("DOMContentLoaded", () => {
        insertDevToggleButton();
    });
}


const container = document.getElementById('game-container');

async function loadJSON(path) {
    const response = await fetch(path + '?v=' + Date.now());
    return await response.json();
}

async function startGame() {
    const intro = await loadJSON('./data/intro.json');
    customData = await loadJSON('./data/custom.json');
    resources = await loadJSON('./data/resource.json');
    scene = await loadJSON('./data/scenes.json');
    endings = await loadJSON('./data/endings.json');
    setting = await loadJSON('./data/setting.json');
    addElements(intro);
}

let activeToggles = [];
let buttonIdCounter = 0;

function generateId(type = 'btn') {
    return type + '_' + (buttonIdCounter++);
}

function addElements(data, category = null) {
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

        const element = createElementItem(item, category);
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
    return text.trim()
        .replace(/\n/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
        .replace(/(['"])([^'"“”]+?)\1/g, `<span class="quote">“$2”</span>`);
}

function getEffectColor(target, operation) {
    const res = resources[target];
    const positive = res?.positive;

    if (!res || positive === undefined) return "";

    const direction = operation === '+' || operation === '*' ? 1
    : operation === '-' || operation === '/' ? -1
    : 0;

    if (direction === 0) return "";

    const isGood = (positive && direction > 0) || (!positive && direction < 0);
    return isGood ? "good-effect" : "bad-effect";
}

function generateButtonEffects(events, { asElements = true } = {}) {
    const tags = [];
    const effects = [];

    for (const ev of events) {
        if (ev.type !== "setValue" || ev.hidden) continue;
        const valStr = returnValue(ev.value);
        const op = ev.operation;

        if ((ev.target === "tags") && ev.operation == 'add' && asElements) {
            tags.push(`${valStr.replace('_', ' ')}`);
        } else {
            const colorClass = getEffectColor(ev.target, ev.operation);
            const res = resources[ev.target];
            const name = res?.name ?? ev.target;
            const val = returnValue(ev.value);
            const count = returnValue(ev.count ?? 1);
            let line = "";

            if (ev.conditionText) {
                line += `${ev.conditionText} `.replace(/</g, '《 ').replace(/>/g, ' 》');
            }

            switch (ev.operation) {
            case '+': line += `${name} +${val}`; break;
            case '-': line += `${name} -${val}`; break;
            case '*': line += `${name} ${val}배로`; break;
            case '/': line += `${name} ${val}로 나눔`; break;
            case '=': line += `${name}을(를) ${typeof valStr === 'boolean'?(valStr?"얻음":"잃음"):`${val}으로 만듦`}`; break;
            case 'add': line += `${val}을(를) ${ev.target == 'items'?count+"개 ":""}얻음`; break;
            case 'remove': line += `${val}을(를) ${ev.target == 'items'?(count == 0?"전부":count+"개 "):""}잃음`; break;
            }

            if (asElements) {
              const lineEl = document.createElement('div');
              lineEl.textContent = line;
              if (colorClass) lineEl.classList.add(colorClass);
              effects.push(lineEl);
            } else {
              effects.push({ line, colorClass });
            }
        }
    }

    return {
        tagsLines: tags,
        effectLines: effects
    };
}

function createButton(item, type = 'button', parentId = null) {
    const id = item.id ?? generateId('btn');
    const btn = document.createElement('button');
    btn.className = 'fancy-button';
    btn.style.flexBasis = `calc(${item.width ?? 100}% - 1rem)`;
    btn.id = id;
    btn.condition = item.condition ?? true;
    btn.hidden = item.hidden ?? false;
    btn.lockReasons = new Set();

    if (type == 'button' && parentId) {
        btn.dataset.category = parentId;
    }

    if (item.image) {
        const img = document.createElement('img');
        img.src = `./image/${item.image}`;
        img.alt = '';
        img.className = 'button-image';
        btn.appendChild(img);
    }

    if (item.title) {
        const title = document.createElement('div');
        title.className = 'button-title';
        title.textContent = `《 ${item.title} 》`;
        btn.appendChild(title);
    }

    const eventList = item.events ?? [];
    const { tagsLines, effectLines } = generateButtonEffects(eventList);

    if (tagsLines.length > 0 || item.conditionText || effectLines.length > 0) {
        const desc = document.createElement('div');
        desc.className = 'button-effect-desc';

        if (tagsLines.length > 0) {
            const tagLine = document.createElement('div');
            tagLine.innerHTML = tagsLines.map(tag => `<span class="effect-tag">${tag}</span>`).join('');
            desc.appendChild(tagLine);
        }

        if (item.conditionText) {
            const condLine = document.createElement('div');
            condLine.textContent = item.conditionText.replace(/</g, '《 ').replace(/>/g, ' 》');
            condLine.classList.add("value-neutral");
            desc.appendChild(condLine);
        }

        for (let line of effectLines) {
            desc.appendChild(line);
        }

        btn.appendChild(desc);
    }

    if (item.title && item.text) {
        const hr = document.createElement('hr');
        hr.className = 'text-line';
        btn.appendChild(hr);
    }

    if (item.text) {
        const text = document.createElement('div');
        text.className = 'button-text';
        text.innerHTML = formatText(item.text);
        btn.appendChild(text);
    }

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
            if (phase == 'event') {
                currentLog.choices.push(item.title);
            }
            executeEvents(eventList);

            if (type == 'choice' && parentId) {
                btn.classList.add('active');
                const parent = document.getElementById(parentId);
                if (parent) {
                    const buttons = parent.querySelectorAll('button');
                    buttons.forEach(b => {
                        b.lockReasons.add('choice');
                        b.disabled = true;
                        b.classList.add('disabled');
                    });
                }
            }

            if (item.branch) {
                handleBranchTo(item.branch);
            }

            updateValues();
        });
    }

    return btn;
}

function createElementItem(item, category = null) {
    const wrapper = document.createElement('div');
    wrapper.className = 'info-box';
    wrapper.style.flexBasis = `calc(${item.width ?? 100}% - 1rem)`;

    if (item.type === 'textbox') {
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'textbox-content';

        const textBlock = document.createElement('div');
        textBlock.className = 'textbox-text';

        if (item.title) {
            const title = document.createElement('h3');
            title.textContent = `${item.title}`;
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

    else if (item.type === 'titlebox') {
        const box = document.createElement('div');
        box.className = 'title-box';
        box.textContent = item.title ?? '';
        box.style.flexBasis = `calc(${item.width ?? 100}% - 1rem)`;
        return box;
    }

    else if (item.type === 'button') {
        return createButton(item, 'button', category);
    }

    else if (item.type === 'image') {
        const img = document.createElement('img');
        img.src = `./image/${item.image}`;
        img.alt = "";
        img.className = 'info-img';
        img.style.flexBasis = `calc(${item.width ?? 100}% - 1rem)`;
        return img;
    }

    else if (item.type === 'line') {
        const hr = document.createElement('hr');
        hr.className = 'full-line';
        return hr;
    }

    else if (item.type === 'choice') {
        const container = document.createElement('div');
        const choiceId = generateId('choice');
        container.id = choiceId;
        container.className = 'choice-group';
        container.style.flexBasis = `calc(${item.width ?? 100}% - 1rem)`;

        for (const option of item.elements ?? []) {
            const btn = createButton(option, 'choice', choiceId);
            container.appendChild(btn);
        }

        return container;
    }

    else if (item.type === 'spacer') {
        const space = document.createElement('div');
        space.className = 'spacer';
        space.style.height = `${item.height}px` ?? '16px';
        return space;
    }

    return wrapper;
}

function executeEvents(events, log = true) {
    for (const e of events) {
        if (e.type === 'cyoaStart') {
            if (!isBgmPlaying) {
                if (loadData('bgm', true)) {
                    toggleBGM();
                }
            }
            startCustomization();
        }
        if (e.type === 'eventStart') {
            startEvent();
        }
        if (e.type === 'setValue') {
            handleSetValue(e, 'realValue', log);
            updateValues();
        }
        if (e.type === 'viewSummary') {
            showSummary();
        }
    }
}

let categoryLimits = {};

async function startCustomization() {
    phase = 'custom';
    document.getElementById('status-bar').style.display = 'flex';
    addElements([{ "type":"line" }])

    let _first = true;

    for (const categoryId in customData) {
        const category = customData[categoryId];

        const box = document.createElement('div');
        box.className = 'info-box';

        const title = document.createElement('h2');
        title.textContent = `${category.name}`;
        title.className = 'info-title';
        box.appendChild(title);

        if (category.description) {
            const desc = document.createElement('p');
            desc.innerHTML = formatText(category.description);
            box.appendChild(desc);
        }

        container.appendChild(box);

        const rules = [];
        if (category.maxSelect) rules.push(`최대 ${category.maxSelect}개 선택`);
        if (category.required) rules.push(`필수 ${category.required}개 선택`);
        if (rules.length > 0) {
            const ruleText = document.createElement('p');
            ruleText.textContent = rules.join(' / ');
            ruleText.className = 'info-rules';
            container.appendChild(ruleText);
        }


        if (Array.isArray(category.elements)) {
            addElements(category.elements, categoryId);
        }

        categoryLimits[categoryId] = {
            maxSelect: category.maxSelect ?? Infinity,
            required: category.required ?? 0
        };

        const hr = document.createElement('hr');
        hr.className = 'full-line';
        container.appendChild(hr);
    }


    addElements(
        [{
            "type": "choice",
            "elements":[
                {
                    "type": "button",
                    "condition": "required",
                    "title": "결정",
                    "actionType": "once",
                    "events": [
                        {
                            "type": "eventStart"
                        }
                    ],
                    "width":100
                }
            ],
            "width":80
        }]
    );

    updateValues();

}

function startEvent() {
    phase = 'event';
    const buttons = document.querySelectorAll('.fancy-button');

    for (const btn of buttons) {
        if (!btn.lockReasons) {
            btn.lockReasons = new Set();
        }

        btn.lockReasons.add('custom');
        btn.disabled = true;
        btn.classList.add('disabled');
    }

    fixValue();

    newEvent();
}

function newEvent() {
    eventCount++;

    const candidates = Object.values(scene).filter(ev => {
        if (ev.repeatable === false && ev._completed) return false;
        return ev.condition === undefined || returnValue(ev.condition);
    });

    if ((setting.maxRound != 0 && eventCount > setting.maxRound) || candidates.length === 0) {
        startEnding();
        return;
    }

    const maxPriority = Math.max(...candidates.map(ev => ev.priority ?? 0));
    const topCandidates = candidates.filter(ev => (ev.priority ?? 0) === maxPriority);

    const totalWeight = topCandidates.reduce((sum, ev) => sum + (ev.weight ?? 1), 0);
    let r = Math.random() * totalWeight;
    for (const ev of topCandidates) {
        r -= (ev.weight ?? 1);
        if (r <= 0) {
            currentEvent = ev;
            break;
        }
    }

    if (!currentEvent) currentEvent = topCandidates[0]; // fallback

    if (currentEvent.repeatable === false) {
        currentEvent._completed = true;
    }

    const startIndex = currentEvent.start ?? 'start';
    const page = currentEvent.pages[startIndex];

    if (!page) {
        console.error(`시작 페이지 "${startId}"가 존재하지 않음`);
        return;
    }

    currentLog.title = currentEvent.title;
    currentLog.summary.push(page.summary);

    const spacer = {
        type: "spacer",
        height: 80
    };

    const titleBox = {
        type: "titlebox",
        title: `${eventCount}일차: ${currentEvent.title}`,
        width: 80
    };

    addElements([ spacer, { type: "line" }, titleBox, ...page.elements ]);
}

function addEventLog() {
    eventHistory.push(currentLog);
    currentLog = {
        title: '',
        summary: [],
        choices: [],
        scene: [[]]
    }
}

function handleBranchTo(branches) {
    const valid = branches.filter(b => !b.condition || returnValue(b.condition));

    if (valid.length === 0) {
        executeEvents(setting.events, false);
        addEventLog();
        newEvent();
        return;
    }

    const maxPriority = Math.max(...valid.map(b => b.priority ?? 0));
    const topBranches = valid.filter(b => (b.priority ?? 0) === maxPriority);

    const totalWeight = topBranches.reduce((sum, b) => sum + (b.weight ?? 1), 0);
    let r = Math.random() * totalWeight;

    let selected = null;
    for (const b of topBranches) {
        r -= (b.weight ?? 1);
        if (r <= 0) {
            selected = b;
            break;
        }
    }

    if (!selected) selected = topBranches[0];

    switch (selected.type) {
    case "page":
        currentLog.summary.push(currentEvent.pages[selected.value].summary);
        currentLog.scene.push([]);
        const spacer = {
            type: "spacer",
            height: 80
        };
        addElements([ spacer, ...currentEvent.pages[selected.value].elements ]);
        break;
    case "ending":
        addEventLog();
        startEnding(selected.value);
        break;
    case "next":
    default:
        executeEvents(setting.events, false);
        addEventLog();
        newEvent();
        break;
    }
}

function startEnding(endingId = null) {
    phase = 'ending';
    let selected = null;

    if (endingId) {
        selected = endings[endingId];
    } else {
        const candidates = Object.values(endings).filter(e => !e.condition || returnValue(e.condition));

        if (candidates.length === 0) {
            console.warn("조건을 만족하는 엔딩이 없습니다.");
            return;
        }

        const maxPriority = Math.max(...candidates.map(e => e.priority ?? 0));
        const top = candidates.filter(e => (e.priority ?? 0) === maxPriority);

        selected = top[0];
    }

    if (!selected) {
        console.error("해당하는 엔딩이 없습니다.");
        return;
    }

    console.log(`🎬 엔딩 진입: ${selected.title}`);


    const spacer = {
        type: "spacer",
        height: 80
    };

    const titleBox = {
        type: "titlebox",
        title: `엔딩: ${selected.title}`,
        width: 80
    };

    addElements([ spacer, { type: "line" }, titleBox, ...selected.elements ]);


    addElements(
        [{
            "type": "choice",
            "elements":[
                {
                    "type": "button",
                    "title": "결과 보기",
                    "actionType": "once",
                    "events": [
                        {
                            "type": "viewSummary"
                        }
                    ],
                    "width":100
                }
            ],
            "width":80
        }]
    );
}



function returnValue(expr) {
    const tokens = tokenize(expr);
//console.log("Tokens:", tokens);

    const replaced = replaceTokens(tokens);
//console.log("Replaced:", replaced);

    const postfix = toPostfix(replaced);
//console.log("Postfix:", postfix);

    const result = evaluatePostfix(postfix);
    return typeof result === 'number' ? Math.floor(result) : result;
}

function tokenize(expr) {
    expr = String(expr);
    const pattern = /(==|!=|>=|<=|<<|>>|\|\||&&|\^\^|[+\-*/%()<>]|\d+\.?\d*|".*?"|[가-힣\w]+)/g;
    return [...expr.matchAll(pattern)].map(m => m[0]);
}



function replaceTokens(tokens) {
    return tokens.map(tok => {
        if (tok === 'true') return true;
        if (tok === 'false') return false;

        if (['(', ')'].includes(tok)) return tok;

        if (tok === 'tags') return tags;
        if (tok === 'items') return items;
        if (tok === 'random') return Math.random();
        if (tok === 'required') {
            return isAllRequirementsMet();
        }

        const resource = Object.entries(resources).find(([id, val]) =>
            id === tok
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
    case '<<': return Array.isArray(a) && a.includes(b);
    case '>>': return Array.isArray(b) && b.includes(a);
    case '&&': return a && b;
    case '||': return a || b;
    case '^^': return (!!a) !== (!!b);
    default: throw new Error(`Unknown operator: ${op}`);
    }
}

function handleSetValue(event, field = 'value', log = true) {
    const { target, operation, value, count } = event;
    const evaluated = returnValue(value);

    if (event.condition === undefined || returnValue(event.condition)) {
        if (field == 'realValue' && phase == 'event' && log) {
            currentLog.scene[currentLog.scene.length - 1].push(event);
        }
    } else {
        return;
    }

    if (target === 'tags') {
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
    if (target === 'items') {
        let itemList = (field === 'realValue') ? realItems : items;
        let _count = count ?? 1;

        if (operation === 'add') {
            for (let i=0; i<_count; i++) {
                itemList.push(evaluated.value ?? evaluated);
            }
        } else if (operation === 'remove') {
            const value = evaluated.value ?? evaluated;
            for (let i=0; i<_count; i++) {
                const idx = itemList.indexOf(value);
                if (idx != -1) {
                    itemList.splice(idx, 1);
                } else {
                    break;
                }
            }
        }

        if (field === 'realValue') realItems = itemList;
        else items = itemList;

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
        res[field] = evaluated;
        break;
    case '+':
        res[field] = current + evaluated;
        break;
    case '-':
        res[field] = current - evaluated;
        break;
    case '*':
        res[field] = current * evaluated;
        break;
    case '/':
        res[field] = current / evaluated;
        break;
    default:
        console.warn(`알 수 없는 연산: ${operation}`);
    }
    if (res.maxValue !== undefined) {
        res[field] = Math.min(res[field], returnValue(res.maxValue));
    }
    if (res.minValue !== undefined) {
        res[field] = Math.max(res[field], returnValue(res.minValue));
    }
}

function updateValues() {
    if (phase == 'ending') {
        return;
    }
    for (const key in resources) {
        const res = resources[key];
        res.value = res.realValue;
    }

    tags = [...realTags];
    items = [...realItems];

    for (const ev of activeToggles) {
        if (ev.type == "setValue") {
            handleSetValue(ev);
        }
    }

    for (const key in resources) {
        const res = resources[key];
        if (res.maxValue !== undefined) {
            res.value = Math.min(res.value, returnValue(res.maxValue));
        }
        if (res.minValue !== undefined) {
            res.value = Math.max(res.value, returnValue(res.minValue));
        }
    }

    const allButtons = document.querySelectorAll('.fancy-button');
    let _deactive = false;
    for (const btn of allButtons) {
        const condition = btn.condition ?? true;
        const hidden = btn.hidden ?? false;
        const result = returnValue(condition);

        if (hidden && !result) {
            if (!DEV_MODE) {
                btn.classList.add('hidden');
            } else {
                btn.classList.remove('hidden');
                btn.lockReasons.add('devMode');
            }

            if (btn.dataset.active === "true") {
                btn.dataset.active = "false";
                activeToggles = activeToggles.filter(e => e._btnId !== btn.id);
                btn.classList.remove('active');
                _deactive = true;
            }

            continue;
        }

        if (hidden && result) {
            btn.classList.remove('hidden');
            btn.lockReasons.delete('devMode');
        }

        if (btn.dataset.active === "true") continue;

        if (result) {
            if (btn.lockReasons.has('condition')) {
                btn.lockReasons.delete('condition');
            }
        } else {
            btn.lockReasons.add('condition');
        }

        if (btn.lockReasons.size === 0) {
            btn.disabled = false;
            btn.classList.remove('disabled');
        } else {
            btn.disabled = true;
            btn.classList.add('disabled');
        }
    }

    if (_deactive) {
        updateValues();
        return;
    }

    applyCategoryLimits();
    updateStatusBar();
}

function applyCategoryLimits() {
    const buttons = document.querySelectorAll('.fancy-button');

    const categoryMap = {};

    for (const btn of buttons) {
        const cat = btn.dataset.category;
        if (!cat) continue;
        if (!categoryMap[cat]) categoryMap[cat] = [];
        categoryMap[cat].push(btn);
    }

    for (const category in categoryMap) {
        const group = categoryMap[category];
        const limit = categoryLimits[category];
        if (!limit) continue;

        const activeCount = group.filter(b => b.dataset.active === "true").length;

        if (limit.maxSelect) {
            for (const btn of group) {
                if (btn.dataset.active !== "true") {
                    if (activeCount >= limit.maxSelect) {
                        btn.lockReasons.add('limit');
                    } else {
                        btn.lockReasons.delete('limit');
                    }
                }
            }
        }

        for (const btn of group) {
            if (btn.lockReasons?.size > 0) {
                btn.disabled = true;
                btn.classList.add('disabled');
            } else {
                btn.disabled = false;
                btn.classList.remove('disabled');
            }
        }
    }
}

function isAllRequirementsMet() {
    for (const category in categoryLimits) {
        const required = categoryLimits[category]?.required;
        if (!required) continue;

        const buttons = document.querySelectorAll(`.fancy-button[data-category="${category}"]`);
        const activeCount = [...buttons].filter(b => b.dataset.active === "true").length;

        if (activeCount < required) return false;
    }
    return true;
}


function updateStatusBar() {
    const bar = document.getElementById('status-bar');
    bar.innerHTML = '';

    for (const key in resources) {
        const res = resources[key];
        if ((!res.show || (res.showIfPositive && !returnValue(res.value))) && !DEV_MODE) continue;

        const el = document.createElement('div');
        el.className = 'status-box';
        el.textContent = `${res.name}` + (!DEV_MODE && typeof returnValue(res.value) === 'boolean' ? "" : `: ${res.value}${res.maxValue ? `/${returnValue(res.maxValue)}` : ``}`);

        if (res.description) {
            el.title = res.description;
        }

        if ((!res.show || (res.showIfPositive && !returnValue(res.value))) && DEV_MODE) {
            el.disabled = true;
            el.classList.add("disabled");
        }

        bar.appendChild(el);
    }

    if (Array.isArray(items) && items.length > 0) {
        const countMap = {};
        for (const item of items) {
            countMap[item] = (countMap[item] || 0) + 1;
        }

        for (const name in countMap) {
            const el = document.createElement('div');
            el.className = 'item-box';
            el.textContent = `${name} × ${countMap[name]}`;
            bar.appendChild(el);
        }
    }
}

function fixValue(targetKey = null) {
    if (targetKey === 'tags') {
        realTags = [...tags];

        activeToggles = activeToggles.filter(ev => {
            return !(ev.type === "setValue" && (ev.target === "tags"));
        });

        updateValues();
        return;
    }
    if (targetKey === 'items') {
        realItems = [...items];

        activeToggles = activeToggles.filter(ev => {
            return !(ev.type === "setValue" && (ev.target === "items"));
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
        fixValue("items");
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

function showSummary() {
    const container = document.getElementById("game-container");

    const spacer = {
        type: "spacer",
        height: 80
    };

    addElements([ spacer ]);

    const summaryResources = Object.entries(resources)
    .filter(([_, val]) => val.summary)
    .map(([id, val]) => ({ name: val.name, value: val.value }));

    const profileBox = document.createElement('div');
    profileBox.className = 'info-box summary-part profile-summary';
    profileBox.innerHTML = '<h2>최종 상태</h2>';
    summaryResources.forEach(r => {
        const line = document.createElement('div');
        line.className = 'resource-line';

        const label = document.createElement('span');
        label.className = 'resource-label';
        label.textContent = `${r.name}`;

        const value = document.createElement('span');
        value.className = 'resource-value';
        value.textContent = r.value;

        // 긍정/부정에 따라 색상 부여
        const resourceObj = Object.entries(resources).find(([_, val]) => val.name === r.name)?.[1];
        if (resourceObj?.positive !== undefined) {
            const isPositive = resourceObj.positive;
            /*if ((isPositive && r.value > r.realValue) || (!isPositive && r.value < r.realValue)) {
                value.classList.add('value-positive');
            } else if ((isPositive && r.value < r.realValue) || (!isPositive && r.value > r.realValue)) {
                value.classList.add('value-negative');
            } else {*/
                value.classList.add('value-neutral');
            //}
        }

        line.appendChild(label);
        line.appendChild(value);
        profileBox.appendChild(line);
    });
    container.appendChild(profileBox);

    const chosenCustoms = {};
    document.querySelectorAll('.fancy-button').forEach(btn => {
        if (btn.dataset.active === "true" && btn.dataset.category) {
            if (!chosenCustoms[btn.dataset.category]) chosenCustoms[btn.dataset.category] = [];
            chosenCustoms[btn.dataset.category].push(btn);
        }
    });

    const customBox = document.createElement('div');
    customBox.className = 'info-box summary-part custom-summary';
    customBox.innerHTML = '<h2 style="width: 100%">시작 상태</h2>';
    for (const category in chosenCustoms) {
        chosenCustoms[category].forEach(btn => {
            const clone = btn.cloneNode(true);
            clone.disabled = false;
            clone.removeAttribute('disabled');
            clone.style.pointerEvents = 'none';
            customBox.appendChild(clone);
        });
    }
    container.appendChild(customBox);

    const eventBox = document.createElement('div');
    eventBox.className = 'info-box summary-part event-summary';
    eventBox.innerHTML = '<h2>이야기 요약</h2>';

    eventHistory.forEach(e => {
      const block = document.createElement('div');
      block.className = 'event-block styled-block';

      // 이벤트 제목
      const title = document.createElement('div');
      title.className = 'event-title styled-title';
      title.textContent = e.title;
      block.appendChild(title);

      for (let i = 0; i < e.summary?.length; i++) {
        const group = document.createElement('div');
        group.className = 'event-segment';

        // 요약 라인
        const summaryLine = document.createElement('div');
        summaryLine.className = 'event-summary-line styled-summary';
        summaryLine.textContent = e.summary[i];
        group.appendChild(summaryLine);

        // 선택지 라인
        if (e.choices[i]) {
          const choiceLine = document.createElement('div');
          choiceLine.className = 'event-choice-line styled-choice';
          choiceLine.textContent = `→ ${e.choices[i]}`;
          group.appendChild(choiceLine);
        }

        const { tagsLines, effectLines } = generateButtonEffects(e.scene[i], { asElements: false });
        for (const fx of effectLines) {
            const fxLine = document.createElement('div');
            fxLine.textContent = fx.line;
            if (fx.colorClass) fxLine.classList.add(fx.colorClass);
            group.appendChild(fxLine);
        }

        block.appendChild(group);
      }

      eventBox.appendChild(block);
    });

    container.appendChild(eventBox);

    document.querySelectorAll('.summary-part').forEach((part, i) => {
        const icon = document.createElement('button');
        icon.innerHTML = '💾';
        icon.className = 'save-icon-button';
        icon.title = '이미지로 저장';
        icon.style.position = 'absolute';
        icon.style.top = '8px';
        icon.style.right = '8px';

        icon.addEventListener('click', () => {
          icon.style.display = 'none';

          part.classList.add('capture-clean');

          downloadElementAsImage(part, `summary_part${i + 1}.png`, () => {
            part.classList.remove('capture-clean');
            icon.style.display = '';
          });
        });

        part.style.position = 'relative';
        part.appendChild(icon);
    });
}

async function downloadElementAsImage(element, filename, callback) {
    const canvas = await html2canvas(element);
    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL();
    link.click();

    if (typeof callback === 'function') {
        callback();
    }
}

window.onload = startGame;
