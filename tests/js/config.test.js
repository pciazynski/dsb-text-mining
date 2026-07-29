const test = require('node:test');
const assert = require('node:assert/strict');

const { withDom, loadScript } = require('./helpers');

test('stringToColour returns a stable six-digit hex colour', () => {
  const dom = withDom();
  try {
    const config = loadScript('config.js');

    const colour = config.stringToColour('woda');

    assert.match(colour, /^#[0-9a-f]{6}$/);
    assert.equal(colour, config.stringToColour('woda'));
  } finally {
    dom.restore();
  }
});

test('getColor maps different codes to different colours', () => {
  const dom = withDom();
  try {
    const config = loadScript('config.js');

    assert.notEqual(config.getColor('woda'), config.getColor('luft'));
  } finally {
    dom.restore();
  }
});
