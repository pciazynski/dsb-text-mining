const { withDom, loadScript } = require('./helpers');

describe('autocomplete', () => {
  it('keeps the input enabled without fetching or showing suggestions when disabled', () => {
    const dom = withDom({
      html: '<div><input id="searchinput" type="text"></div>',
    });
    const savedReadPHP = globalThis.readPHP;
    globalThis.readPHP = jest.fn(() => 'drjewo\nbom');

    try {
      const { autocomplete } = loadScript('autocomplete.js');
      const searchInput = dom.document.getElementById('searchinput');

      expect(typeof autocomplete).toBe('function');
      autocomplete('searchinput', 'prefixlemmasearch.php?lemma=', '', true);
      autocomplete('searchinput', 'prefixlemmasearch.php?lemma=', '', false);
      searchInput.value = 'dr';
      searchInput.dispatchEvent(new dom.window.Event('input', { bubbles: true }));

      expect(searchInput.disabled).toBe(false);
      expect(globalThis.readPHP).not.toHaveBeenCalled();
      expect(dom.document.querySelector('#searchinputautocomplete-list')).toBeNull();
    } finally {
      if (savedReadPHP === undefined) {
        delete globalThis.readPHP;
      } else {
        globalThis.readPHP = savedReadPHP;
      }
      dom.restore();
    }
  });

  it('removes visible suggestions and prevents further fetches when disabled', () => {
    const dom = withDom({
      html: '<div><input id="searchinput" type="text"></div>',
    });
    const savedReadPHP = globalThis.readPHP;
    globalThis.readPHP = jest.fn(() => 'drjewo\nbom');

    try {
      const { autocomplete } = loadScript('autocomplete.js');
      const searchInput = dom.document.getElementById('searchinput');

      autocomplete('searchinput', 'prefixlemmasearch.php?lemma=', '', true);
      searchInput.value = 'dr';
      searchInput.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
      expect(globalThis.readPHP).toHaveBeenCalledTimes(1);
      expect(dom.document.querySelector('#searchinputautocomplete-list')).not.toBeNull();

      autocomplete('searchinput', 'prefixlemmasearch.php?lemma=', '', false);
      expect(dom.document.querySelector('#searchinputautocomplete-list')).toBeNull();

      searchInput.value = 'drj';
      searchInput.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
      expect(globalThis.readPHP).toHaveBeenCalledTimes(1);
      expect(dom.document.querySelector('#searchinputautocomplete-list')).toBeNull();
    } finally {
      if (savedReadPHP === undefined) {
        delete globalThis.readPHP;
      } else {
        globalThis.readPHP = savedReadPHP;
      }
      dom.restore();
    }
  });
});
