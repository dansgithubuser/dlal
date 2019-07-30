import {
  getUrlParam,
  uuidv4,
} from './../deps/obvious/obvious.js';

var gSocket;
var gPromiseResolvers = {};

export function socketConnect(options = {}) {
  gSocket = new WebSocket(options.url || getUrlParam('ws-url'));
  if (options.onOpen) gSocket.onopen = options.onOpen;
  gSocket.onmessage = (event) => {
    const response = JSON.parse(event.data);
    if ('result' in response) gPromiseResolvers[response.uuid].resolve(response);
  };
}

export function socketSend(path, options = {}) {
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

export function free(uuid) {
  return socketSend('free', { op: 'store', uuid });
}

export function context(element) {
  contextDismiss();
  const dropdown = document.createElement('div');
  dropdown.className = 'dropdown';
  element.appendChild(dropdown);
  return dropdown;
}

export function contextOption(dropdown, name, onClick, arg) {
  const option = document.createElement('div');
  option.className = 'option';
  option.onclick = () => onClick(arg);
  option.innerHTML = name.replace(' ', '&nbsp;');
  dropdown.appendChild(option);
}

export function contextSpace(dropdown) {
  const space = document.createElement('div');
  space.className = 'option';
  space.innerHTML = '&nbsp;';
  dropdown.appendChild(space);
}

export function contextDismiss() {
  const dropdowns = document.getElementsByClassName('dropdown');
  while (dropdowns.length) {
    dropdowns[0].parentElement.removeChild(dropdowns[0]);
  }
}

export async function component(name) {
  const r = await socketSend(`system.${name}`, { op: 'store' });
  return r.uuid;
}
