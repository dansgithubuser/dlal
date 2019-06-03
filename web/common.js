var gSocket;
var gPromiseResolvers = {};

function e(name){ return document.getElementById(name) }
function v(name){ return e(name).value }

function getUrlParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

// Math.random is probably good enough for this...
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.floor(Math.random() * 16), v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function socketConnect(options = {}) {
  const host = options.host || getUrlParam('host');
  const port = options.port || getUrlParam('port');
  gSocket = new WebSocket(`ws:${host}:${port}`);
  if (options.onOpen) gSocket.onopen = options.onOpen;
  gSocket.onmessage = (event) => {
    response = JSON.parse(event.data);
    gPromiseResolvers[response.uuid].resolve(response);
  };
}

function socketSend(path, options = {}) {
  if (!gSocket) return;
  const uuid = options.uuid || uuidv4();
  gSocket.send(JSON.stringify({
    uuid,
    path: path.split('.'),
    args: options.args,
    kwargs: options.kwargs,
    op: options.op,
  }));
  return new Promise(function (resolve, reject) {
    gPromiseResolvers[uuid] = { resolve, reject };
  });
}

function free(uuid) {
  return socketSend('free', { op: 'store', uuid });
}

function context(element) {
  contextDismiss();
  const dropdown = document.createElement('div');
  dropdown.className = 'dropdown';
  element.appendChild(dropdown);
  return dropdown;
}

function contextOption(dropdown, name, onClick, arg) {
  const option = document.createElement('div');
  option.className = 'option';
  option.onclick = () => onClick(arg);
  option.innerText = name;
  dropdown.appendChild(option);
}

function contextDismiss() {
  const dropdowns = document.getElementsByClassName('dropdown');
  while (dropdowns.length) {
    dropdowns[0].parentElement.removeChild(dropdowns[0]);
  }
}

async function component(name) {
  const r = await socketSend(`system.${name}`, { op: 'store' });
  return r.uuid;
}

function clone(x) {
  return JSON.parse(JSON.stringify(x));
}
