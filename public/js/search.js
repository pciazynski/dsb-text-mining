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

var searchQueryString = function (key, value, options) {
  var query = encodeURIComponent(key) + '=' + encodeURIComponent(value);
  Object.keys(options).forEach(function (option) {
    query += '&' + encodeURIComponent(option) + '=' + (options[option] ? '1' : '0');
  });
  return query;
};

var splitTerms = function (raw, opts) {
  var terms = opts.list ? raw.split(/[;,]/) : [raw];
  var result = [];

  terms.forEach(function (term) {
    if (opts.trim) {
      term = term.trim();
    }
    if (term !== '') {
      result.push(term);
    }
  });

  return result;
};

// Test hook only. Browsers load this file via <script src>, where `module` is undefined.
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { readSearchOptions, searchQueryString, splitTerms };
}
