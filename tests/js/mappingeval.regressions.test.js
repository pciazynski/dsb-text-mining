const assert = require('node:assert/strict');

const { knownBug, loadPage } = require('./helpers');

const EVALUATIONS = ['lemmaeval', 'normeval'];

for (const evaluation of EVALUATIONS) {
  knownBug(
    evaluation + ' zero-one graph labels both uniqueness metrics',
    'the graph and hover text expose only an ambiguous single uniqueness metric',
    () => {
      const page = loadPage('vis/' + evaluation + '/zeroone.html');
      const source = page.documentElement.textContent;

      assert.ok(
        (source.match(/mapping-record uniqueness/gi) || []).length >= 2,
        'graph and hover text must name mapping-record uniqueness',
      );
      assert.ok(
        (source.match(/occurrence-weighted uniqueness/gi) || []).length >= 2,
        'graph and hover text must name occurrence-weighted uniqueness',
      );
    },
  );

  knownBug(
    evaluation + ' basics summarizes both uniqueness metrics',
    'the basics view calculates summary statistics for only one uniqueness ratio',
    () => {
      const page = loadPage('vis/' + evaluation + '/basics.html');
      const source = page.documentElement.textContent;

      assert.match(source, /mapping-record uniqueness/i);
      assert.match(source, /occurrence-weighted uniqueness/i);
    },
  );

  knownBug(
    evaluation + ' pie chart names target categories',
    'the pie chart uses ambiguous abbreviated category labels',
    () => {
      const page = loadPage('vis/' + evaluation + '/piechart.html');
      const source = page.documentElement.textContent;

      assert.match(source, /unique target/i);
      assert.match(source, /ambiguous target/i);
      assert.match(source, /mixed target/i);
    },
  );
}