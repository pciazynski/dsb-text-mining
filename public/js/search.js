var searchDefaults = {
  ci: true,
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
  var timelineData = focus === 3 ? 'lemmacountperyear.php' : 'lemmasumperyear.php';
  var timelinePage = searchOptions.list ? 'timelinesumlist.html' : 'timeline.html';

  return {
    timeline: timelinePage + '?data=' + timelineData + '&' + query + '&sort&focus=' + focus,
    group: 'lemmalist.html?data=lemmagroup.php&' + query + '&sort',
    tokens: 'tokenlist.html?data=lemmatoken.php&' + query + '&sort',
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

var splitTerms = function (raw, opts) {
  var terms = opts.list ? raw.split(/[;,]/) : [raw];

  return terms
    .map(function (term) {
      return opts.trim ? term.trim() : term;
    })
    .filter(function (term) {
      return term !== '';
    });
};

var searchControlState = function (options) {
  var enabled = !options.regex && !options.list;
  return { autocomplete: enabled, alphabetSort: enabled };
};

var applySearchControlState = function (doc, options) {
  var state = searchControlState(options);
  var alphabetSort = doc.getElementById('prefixsearchCheckBox');
  var searchInput = doc.getElementById('searchinput');
  if (alphabetSort) {
    alphabetSort.disabled = !state.alphabetSort;
  }
  if (searchInput) {
    searchInput.disabled = !state.autocomplete;
  }
};

var restoreSearchFromLocation = function (doc, search) {
  var params = new URLSearchParams(search || '');
  if (!params.has('lemma')) {
    return;
  }

  var options = readSearchOptions(search);
  var searchInput = doc.getElementById('searchinput');
  if (searchInput) {
    searchInput.value = params.get('lemma');
  }

  Object.keys(options).forEach(function (option) {
    var checkbox = doc.getElementById(option + 'CheckBox');
    if (checkbox) {
      checkbox.checked = options[option];
    }
  });

  applySearchControlState(doc, options);
};

// Test hook only. Browsers load this file via <script src>, where `module` is undefined.
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    readSearchOptions,
    searchOptionsFromForm,
    searchQueryString,
    buildVisUrls,
    phpUrlFromLocation,
    splitTerms,
    searchControlState,
    applySearchControlState,
    restoreSearchFromLocation,
  };
}
