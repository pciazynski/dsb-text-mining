var searchDefaults = {
  cs: false,
  regex: false,
  list: false,
  trim: true,
  ambig: true,
};

var searchBoolean = function (value) {
  var normalized = String(value).trim().toLowerCase();
  if (normalized === '' || normalized === '0' || normalized === 'false') {
    return false;
  }
  if (normalized === '1' || normalized === 'true') {
    return true;
  }
  return null;
};

var readSearchOptions = function (query) {
  var params = new URLSearchParams(query || '');
  var options = {};

  Object.keys(searchDefaults).forEach(function (key) {
    options[key] = searchDefaults[key];
    if (!params.has(key)) {
      return;
    }
    var parsed = searchBoolean(params.get(key));
    if (parsed !== null) {
      options[key] = parsed;
    }
  });

  if (!params.has('ambig') && params.has('exact')) {
    var exact = searchBoolean(params.get('exact'));
    if (exact !== null) {
      options.ambig = !exact;
    }
  }

  return options;
};

var searchOptionsFromForm = function (doc) {
  var options = {};
  Object.keys(searchDefaults).forEach(function (key) {
    var checkbox = doc.getElementById(key + 'CheckBox');
    options[key] = checkbox ? checkbox.checked : searchDefaults[key];
  });
  return options;
};

var searchQueryString = function (key, value, options) {
  var query = encodeURIComponent(key) + '=' + encodeURIComponent(value);
  Object.keys(options).forEach(function (option) {
    query += '&' + encodeURIComponent(option) + '=' + (options[option] ? '1' : '0');
  });
  return query;
};

var buildVisUrls = function (kind, term, options, focus) {
  if (String(term).trim() === '') {
    return null;
  }

  var searchOptions = Object.assign({}, searchDefaults, options || {});
  var query = searchQueryString(kind, term, searchOptions);

  if (kind === 'token') {
    return {
      timeline: 'timeline.html?data=tokencountperyear.php&' + query + '&sort&focus=' + focus,
      wordinfo:
        searchOptions.regex || searchOptions.list
          ? 'error_token.html'
          : 'wordinfo.html?data=token2lemma.php&token=' + encodeURIComponent(term),
    };
  }

  var timelineData =
    kind === 'norm'
      ? focus === 3
        ? 'normcountperyear.php'
        : 'normsumperyear.php'
      : focus === 3
        ? 'lemmacountperyear.php'
        : 'lemmasumperyear.php';
  var timelinePage = searchOptions.list ? 'timelinesumlist.html' : 'timeline.html';
  var groupPage = kind === 'norm' ? 'normlist.html' : 'lemmalist.html';
  var groupData = kind === 'norm' ? 'normgroup.php' : 'lemmagroup.php';
  var tokenData = kind === 'norm' ? 'normtoken.php' : 'lemmatoken.php';

  return {
    timeline: timelinePage + '?data=' + timelineData + '&' + query + '&sort&focus=' + focus,
    group: groupPage + '?data=' + groupData + '&' + query + '&sort',
    tokens: 'tokenlist.html?data=' + tokenData + '&' + query + '&sort',
  };
};

var phpUrlFromLocation = function (dataKey, termKey, search) {
  var params = new URLSearchParams(search || '');
  var data = params.get(dataKey);
  if (!data || !/^[A-Za-z0-9_-]+\.php$/.test(data)) {
    return null;
  }

  var term = params.get(termKey);
  if (term === null) {
    return null;
  }

  var options = readSearchOptions(search);
  var query = searchQueryString(termKey, term, options);
  return data + '?' + query + (params.has('sort') ? '&sort' : '');
};

var listPlotUrlsFromLocation = function (dataKey, termKey, search) {
  var params = new URLSearchParams(search || '');
  var term = params.get(termKey);
  if (term === null) {
    return null;
  }

  return listTermsFromLocation(search, termKey).map(function (item) {
    var itemSearch = new URLSearchParams(search || '');
    itemSearch.set(termKey, item);
    return phpUrlFromLocation(dataKey, termKey, '?' + itemSearch.toString());
  });
};

var listPlotTraces = function (rawData, separator) {
  var traces = [];
  var traceByName = Object.create(null);
  var rows = String(rawData || '').split('\n');

  rows.forEach(function (row) {
    if (row.trim() === '') {
      return;
    }

    var cells = row.split(separator);
    var name = cells[0];
    var year = cells[1];
    var count = parseInt(cells[2], 10);
    if (!name || !year || Number.isNaN(count)) {
      return;
    }

    var trace = traceByName[name];
    if (!trace) {
      trace = { x: [], y: [], name: name, mode: 'markers' };
      traceByName[name] = trace;
      traces.push(trace);
    }

    var yearIndex = trace.x.indexOf(year);
    if (yearIndex === -1) {
      trace.x.push(year);
      trace.y.push(count);
    } else {
      trace.y[yearIndex] += count;
    }
  });

  return traces;
};

var splitTerms = function (raw, opts) {
  var separator = opts.regex ? ';' : /[;,]/;
  var terms = opts.list ? raw.split(separator) : [raw];

  return terms
    .map(function (term) {
      return opts.trim ? term.trim() : term;
    })
    .filter(function (term) {
      return term !== '';
    });
};

var listTermsFromLocation = function (search, termKey) {
  termKey = termKey || 'lemma';
  var params = new URLSearchParams(search || '');
  var term = params.get(termKey);
  if (term === null) {
    return [];
  }

  return splitTerms(term, readSearchOptions(search));
};

var searchControlState = function (options) {
  var enabled = !options.regex && !options.list;
  return { autocomplete: enabled, alphabetSort: enabled };
};

var applySearchControlState = function (doc, options) {
  var state = searchControlState(options);
  var alphabetSort = doc.getElementById('prefixsearchCheckBox');
  if (alphabetSort) {
    alphabetSort.disabled = !state.alphabetSort;
    var alphabetSortLabel = alphabetSort.closest('label');
    if (alphabetSortLabel) {
      alphabetSortLabel.style.color = alphabetSort.disabled ? 'gray' : 'black';
    }
  }
};

var languageLabel = function (name, fallback) {
  return typeof globalThis !== 'undefined' && globalThis[name] ? globalThis[name] : fallback;
};

var showTruncationNotice = function (doc, xhr) {
  if (!xhr || xhr.getResponseHeader('X-Dsb-Result-Truncated') !== '1') {
    return false;
  }

  if (doc.querySelector('[data-result-truncated]')) {
    return true;
  }

  var notice = doc.createElement('p');
  notice.dataset.resultTruncated = 'true';
  notice.textContent = languageLabel(
    'lang_error_resultset_too_large',
    'Resultset too large. Please refine query.',
  );
  doc.body.insertBefore(notice, doc.body.firstChild);
  return true;
};

var readPHPChecked = function (doc, url) {
  var body = readPHP(url);
  var xhr = typeof globalThis === 'undefined' ? null : globalThis.rawFile;
  if (showTruncationNotice(doc, xhr)) {
    return null;
  }
  return body;
};

var ambigButtonLabel = function (ambig) {
  var searchLabel = languageLabel('lang_searchitem', 'Suche');
  var ambigLabel = languageLabel('lang_ambigsearch', 'Suche inkl Ambig');
  return ambig ? ambigLabel : searchLabel;
};

var applyAmbigButtonLabel = function (doc) {
  var checkbox = doc.getElementById('ambigCheckBox');
  var button = doc.getElementById('ambigSearchButton');
  if (!button) {
    return;
  }

  var checked = checkbox ? checkbox.checked : true;
  button.textContent = ambigButtonLabel(checked);
};

var searchExample = function (options, kind) {
  var resolved = Object.assign({}, searchDefaults, options || {});
  var examples = {
    lemma: {
      literal: resolved.cs ? 'DRJEWO' : 'drjewo',
      regex: resolved.cs ? 'TE(J|N)' : 'te(j|n)',
      listItem: resolved.cs ? 'BOM' : 'bom',
    },
    norm: {
      literal: 'Chóśebuz',
      regex: 'te(j|n)',
      listLiteral: 'tej',
      listItem: 'ten',
      regexListItem: 'Chóśebuz',
    },
    token: {
      literal: 'woni',
      regex: 'w(o|a)n(a|i)',
      listLiteral: 'druge',
      listItem: 'woni',
      regexListItem: 'druge',
    },
  };
  var example = examples[kind] || examples.lemma;
  var separator = resolved.trim ? '; ' : ';';

  if (resolved.regex && resolved.list) {
    return example.regex + separator + (example.regexListItem || example.listItem);
  }
  if (resolved.regex) {
    return example.regex;
  }
  if (resolved.list) {
    return (example.listLiteral || example.literal) + separator + example.listItem;
  }
  return example.literal;
};

var applySearchExample = function (doc, kind) {
  var example = doc && doc.getElementById ? doc.getElementById('searchexample') : null;
  if (!example) {
    return;
  }

  example.textContent = searchExample(searchOptionsFromForm(doc), kind);
};

var restoreSearchFromLocation = function (doc, search, kind) {
  kind = kind || 'lemma';
  var params = new URLSearchParams(search || '');
  var searchInput = doc.getElementById('searchinput');
  var term = params.get(kind);
  if (term === null && kind === 'token') {
    term = params.get('word');
  }
  if (searchInput) {
    searchInput.value = term || '';
  }

  if (term === null) {
    applySearchControlState(doc, searchOptionsFromForm(doc));
    applySearchExample(doc, kind);
    return;
  }

  var options = readSearchOptions(search);
  Object.keys(options).forEach(function (option) {
    var checkbox = doc.getElementById(option + 'CheckBox');
    if (checkbox) {
      checkbox.checked = options[option];
    }
  });

  applySearchControlState(doc, options);
  applySearchExample(doc, kind);
};

// Test hook only. Browsers load this file via <script src>, where `module` is undefined.
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    readSearchOptions,
    searchOptionsFromForm,
    searchQueryString,
    buildVisUrls,
    phpUrlFromLocation,
    listPlotUrlsFromLocation,
    listPlotTraces,
    splitTerms,
    listTermsFromLocation,
    searchControlState,
    applySearchControlState,
    ambigButtonLabel,
    applyAmbigButtonLabel,
    searchExample,
    applySearchExample,
    restoreSearchFromLocation,
    showTruncationNotice,
    readPHPChecked,
  };
}
