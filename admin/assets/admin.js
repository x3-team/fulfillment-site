// Админка: добавить/удалить/переставить строки, счётчики знаков, подтверждения, «есть несохранённые изменения».
(() => {
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Списки строк (операции калькулятора, вопросы). Индексы в name переписываются перед отправкой.
  const renumber = (list) => {
    $$('[data-row]', list.querySelector('.rows')).forEach((row, i) => {
      $$('[name]', row).forEach((el) => { el.name = el.name.replace(/^(\w+\[(?:\w+\]\[)?)(?:\d+|__i__)\]/, `$1${i}]`); });
      const no = row.querySelector('[data-no]');
      if (no) no.textContent = String(i + 1).padStart(2, '0');
    });
    const rows = $$('[data-row]', list.querySelector('.rows'));
    rows.forEach((row, i) => {
      const [up, down] = $$('[data-move]', row);
      if (up) up.disabled = i === 0;
      if (down) down.disabled = i === rows.length - 1;
    });
  };
  const changed = () => document.dispatchEvent(new Event('tvd:dirty'));

  $$('[data-list]').forEach((list) => {
    const rows = list.querySelector('.rows');
    list.addEventListener('click', (e) => {
      const b = e.target.closest('button');
      if (!b) return;
      const row = b.closest('[data-row]');
      if (b.hasAttribute('data-add')) {
        rows.insertAdjacentHTML('beforeend', list.querySelector('template').innerHTML);
        const added = rows.lastElementChild;
        renumber(list);
        grow(added);
        added.querySelector('input:not([type=hidden]),textarea')?.focus();
        changed();
      } else if (b.hasAttribute('data-remove') && row) {
        const name = row.querySelector('input:not([type=hidden])')?.value.trim();
        if (!name || confirm(`Удалить «${name}»?`)) { row.remove(); renumber(list); changed(); }
      } else if (b.hasAttribute('data-move') && row) {
        const sib = +b.dataset.move < 0 ? row.previousElementSibling : row.nextElementSibling;
        if (sib) { +b.dataset.move < 0 ? sib.before(row) : sib.after(row); renumber(list); changed(); b.focus(); }
      }
    });
    renumber(list);
  });

  // Подтверждение для опасных кнопок
  $$('form[data-confirm]').forEach((f) => f.addEventListener('submit', (e) => { if (!confirm(f.dataset.confirm)) e.preventDefault(); }));

  // Высота текстовых полей по содержимому
  const grow = (root = document) => $$('textarea[data-grow]', root).forEach((t) => { t.style.height = 'auto'; t.style.height = t.scrollHeight + 2 + 'px'; });
  document.addEventListener('input', (e) => { if (e.target.matches('textarea[data-grow]')) grow(e.target.parentElement); });
  grow();

  // Счётчики знаков в SEO
  const count = (c) => {
    const f = c.closest('div').querySelector('.inp');
    const n = f.value.length, max = +c.dataset.count;
    c.textContent = `· ${n}`;
    c.classList.toggle('over', n > max);
  };
  $$('[data-count]').forEach((c) => { count(c); c.closest('div').querySelector('.inp').addEventListener('input', () => count(c)); });

  // Несохранённые изменения: подсказка и предупреждение при уходе со страницы
  const form = document.querySelector('form[data-track]');
  if (form) {
    let dirty = false, sending = false;
    const mark = () => { dirty = true; const d = document.querySelector('.dirty'); if (d) d.hidden = false; };
    form.addEventListener('input', mark);
    document.addEventListener('tvd:dirty', mark);
    form.addEventListener('submit', () => { sending = true; });
    addEventListener('beforeunload', (e) => { if (dirty && !sending) { e.preventDefault(); e.returnValue = ''; } });
  }
})();
