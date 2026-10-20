const { knownBug, loadPage } = require('./helpers');

const EVALUATIONS = ['lemmaeval', 'normeval'];

for (const evaluation of EVALUATIONS) {
  describe(evaluation, () => {
    knownBug(
      'labels both uniqueness metrics in the zero-one graph',
      'the graph and hover text expose only an ambiguous single uniqueness metric',
      () => {
        const page = loadPage('vis/' + evaluation + '/zeroone.html');
        const source = page.documentElement.textContent;

        expect((source.match(/mapping-record uniqueness/gi) || []).length).toBeGreaterThanOrEqual(
          2,
        );
        expect(
          (source.match(/occurrence-weighted uniqueness/gi) || []).length,
        ).toBeGreaterThanOrEqual(2);
      },
    );

    knownBug(
      'summarizes both uniqueness metrics in basics',
      'the basics view calculates summary statistics for only one uniqueness ratio',
      () => {
        const page = loadPage('vis/' + evaluation + '/basics.html');
        const source = page.documentElement.textContent;

        expect(source).toMatch(/mapping-record uniqueness/i);
        expect(source).toMatch(/occurrence-weighted uniqueness/i);
      },
    );

    knownBug(
      'names target categories in the pie chart',
      'the pie chart uses ambiguous abbreviated category labels',
      () => {
        const page = loadPage('vis/' + evaluation + '/piechart.html');
        const source = page.documentElement.textContent;

        expect(source).toMatch(/unique target/i);
        expect(source).toMatch(/ambiguous target/i);
        expect(source).toMatch(/mixed target/i);
      },
    );
  });
}
