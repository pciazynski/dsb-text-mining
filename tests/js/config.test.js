const { withDom, loadScript } = require('./helpers');

describe('stringToColour', () => {
  it('returns a stable six-digit hex colour', () => {
    const dom = withDom();
    try {
      const config = loadScript('config.js');

      const colour = config.stringToColour('woda');

      expect(colour).toMatch(/^#[0-9a-f]{6}$/);
      expect(colour).toBe(config.stringToColour('woda'));
    } finally {
      dom.restore();
    }
  });
});

describe('getColor', () => {
  it('maps different codes to different colours', () => {
    const dom = withDom();
    try {
      const config = loadScript('config.js');

      expect(config.getColor('woda')).not.toBe(config.getColor('luft'));
    } finally {
      dom.restore();
    }
  });
});
