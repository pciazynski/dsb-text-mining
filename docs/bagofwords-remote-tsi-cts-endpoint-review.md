# That's a verification of a remote endpoint TSI/CTS /tm/bagofwords.php

can be called (depending of the which instance is being used) like this:
https://tsi.daty.info/tm/bagofwords.php?urn=urn:cts:dsb:bramborske_nowiny_1882_32.20220129&sort=true&lowercase=true

**Verdict**

For the specific passage you supplied, the reported frequencies are correct **assuming punctuation, including the final `-`, is intentionally excluded**.

I independently counted the plain-text passage:

```text
Pſchiżo na ſtwortk kuždego tyžeṅa a płaſchi we tej ſchiẜchcżaṙni
na bėrtyl lėta 60 pſ . , na poſcże 75 pſ . , wot poſta do domu
pſchiṅaßony 90 pſ . -
```

After lowercasing and removing punctuation, there are:

- **26 total tokens**
- **22 unique tokens**
- `na`: 3 occurrences
- `pſ`: 3 occurrences
- Every other returned token: 1 occurrence

The endpoint’s counts sum to:

$$
3 + 3 + 20 \times 1 = 26
$$

So this example is internally consistent and correctly counted.

However, I would **not yet treat the endpoint as universally reliable for downstream linguistic processing**. Its counting loop is correct, but token creation has several significant assumptions.

**Verified Transformation**

The actual tokens are:

```text
1  pſchiżo
2  na
3  ſtwortk
4  kuždego
5  tyžeṅa
6  a
7  płaſchi
8  we
9  tej
10 ſchiẜchcżaṙni
11 na
12 bėrtyl
13 lėta
14 60
15 pſ
16 na
17 poſcże
18 75
19 pſ
20 wot
21 poſta
22 do
23 domu
24 pſchiṅaßony
25 90
26 pſ
```

Counting repeated values gives exactly:

```text
na    3
pſ    3
```

The remaining 20 tokens each appear once. That agrees with the production response.

Sorting at [tm/bagofwords.php:36](tm/bagofwords.php#L36) changes only output order. It does not alter frequencies.

**Reliability Risks**

1. **Unicode lowercasing is potentially incorrect**

The default configuration has:

```php
$multibyte = false;
```

See [config_default.php:5](config_default.php#L5).

That makes the endpoint use:

```php
strtolower($psg)
```

instead of:

```php
mb_strtolower($psg, 'UTF-8')
```

PHP’s `strtolower()` handles ASCII letters but does not reliably lowercase Unicode letters.

For example, hypothetical input:

```text
Žona žona
```

may remain:

```text
Žona žona
```

and produce:

```text
Žona    1
žona    1
```

instead of the probably intended:

```text
žona    2
```

Your example only visibly needs ASCII `P -> p`, so it happens to work.

For multilingual historical text, `$multibyte` should be enabled and the `mbstring` PHP extension must be available.

2. **The production punctuation configuration is unknown**

The repository default contains:

```php
$replacearr = array(".",",","!","?",'"');
```

See [config_default.php:9](config_default.php#L9).

But your input ends with:

```text
pſ . -
```

and production does not return:

```text
-    1
```

Therefore, production’s missing [config.php](config.php) must differ from [config_default.php](config_default.php), probably by adding `-` to `$replacearr`.

That means tokenization behavior depends on server configuration that is not versioned in the workspace. This is a reproducibility risk: development, production, and downstream reprocessing may produce different tokens.

3. **It is not a general whitespace tokenizer**

The implementation uses:

```php
$psgarr = explode(' ', $psg);
```

See [tm/bagofwords.php:26](tm/bagofwords.php#L26).

This splits only on the literal ASCII space. It does not generally split on:

- tabs;
- non-breaking spaces;
- Unicode spaces;
- internal newlines without surrounding spaces.

For example:

```text
foo<TAB>bar
```

could become one token:

```text
"foo\tbar" => 1
```

instead of two tokens.

Using a Unicode whitespace expression such as `preg_split('/\s+/u', ...)` would be more reliable.

4. **XML is removed with a regular expression**

[deletexml()](functions.php#L51) uses:

```php
preg_replace('/<[^>]+>/', ' ', $res);
```

That is acceptable for controlled, predictable TEI fragments, but it is not a proper XML parser.

It also ignores the semantic TEI token boundaries. Given:

```xml
<w>hello</w><w>world</w>
```

it happens to produce:

```text
hello world
```

But the endpoint does not explicitly read `<w>` elements. It strips every tag and then guesses tokens from spaces.

This can behave incorrectly when TEI markup occurs inside a word:

```xml
<w>some<hi>thing</hi></w>
```

The regex produces approximately:

```text
some thing
```

That counts two words even though the TEI `<w>` element represents one token.

5. **It counts displayed historical forms, not normalized words**

For this XML:

```xml
<w lemma="PŚIŚ" norm="pśiźo">Pſchiżo</w>
```

the endpoint counts:

```text
pſchiżo
```

It does not count:

```text
pśiźo
```

and does not count the lemma:

```text
PŚIŚ
```

This is correct only if your downstream project wants **surface-form frequencies**.

If the downstream project expects normalized lexical frequencies, this endpoint gives the wrong semantic data despite performing its arithmetic correctly.

6. **Unicode normalization is absent**

Visually identical Unicode strings can have different byte representations. For example, `ė` can theoretically be stored as either:

- one precomposed character;
- `e` plus a combining mark.

PHP array keys treat those as different strings:

```text
lėta    1
lėta    1
```

They may look identical but be counted separately. The endpoint does not apply NFC or NFKC Unicode normalization.

7. **XML entities may survive as tokens**

Because the implementation removes tags rather than parsing XML, encoded text such as:

```xml
<w>Tom</w> &amp; <w>Anna</w>
```

could result in:

```text
Tom
&amp;
Anna
```

The endpoint does not explicitly call `html_entity_decode()` or decode entities through an XML parser.

8. **Parameter values are not actual Booleans**

These all enable lowercasing:

```text
?lowercase
?lowercase=true
?lowercase=false
?lowercase=0
```

The code only checks whether the parameter exists:

```php
isset($_GET['lowercase'])
```

The same applies to `sort`.

A downstream caller that sends `lowercase=false` might reasonably expect lowercasing to be disabled, but it will be enabled.

**Can You Trust It?**

You can trust the endpoint for this specific passage under this narrow contract:

> Count whitespace-separated surface forms after removing TEI tags, lowercasing according to the server’s PHP configuration, and replacing punctuation listed in the server’s `$replacearr`.

You should not yet claim the stronger contract:

> This endpoint always returns linguistically correct, normalized word frequencies for arbitrary UTF-8 TEI documents.

The current implementation does not guarantee that.

**Recommendation Before Downstream Use**

At minimum, the endpoint needs a documented tokenization contract and automated fixtures covering:

```text
ASCII uppercase:          Word word
Unicode uppercase:        Žona žona
Tabs and newlines:        one<TAB>two
Unicode spaces:           one<NBSP>two
Hyphenated forms:         něnto-raz
Apostrophes:              word’s
Nested TEI:               <w>some<hi>thing</hi></w>
XML entities:             Tom &amp; Anna
Combining characters:     precomposed vs decomposed ė
Numbers:                  60, 75, 90
Empty passage
Passage range
```

The tests should assert:

$$
\sum_{\text{token}} \operatorname{frequency}(\text{token})
=
\text{expected token count}
$$

For your supplied fixture, the expected assertions are:

```text
total token count = 26
unique token count = 22
na = 3
pſ = 3
all other returned tokens = 1
```

So the immediate answer is: **the sample output is correct, but the endpoint’s broader correctness depends on undocumented configuration and fragile Unicode/tokenization behavior. I would harden and test it before making it a source of truth for another project.**

**Findings From Five Additional Production Texts**

The five tested documents confirm that the identified risks occur in real data. The endpoint emits standalone curly-apostrophe tokens, such as `’	359`, leaves some Unicode uppercase letters unchanged despite `lowercase`, preserves combining-character sequences without normalization, and counts numbers and numeric forms as ordinary tokens. Nested highlighting markup is generally removed, but TEI word boundaries and metadata such as `lemma`, `norm`, and `type="ignore"` are not used.

The frequency arithmetic appears consistent, but the output should be understood as counts of surface strings after limited normalization, not as linguistically normalized word frequencies. Empty passages, XML entities, unusual whitespace, and CTS ranges still require separate tests before using this endpoint as a downstream source of truth.

**Concrete Examples From Production Texts**

The following unusual tokens were observed in the five tested documents:

```text
’                  359    standalone curly apostrophe
ßeb́e              9      combining acute accent
muͤ                25     historical combining mark
Ẃedro              12     uppercase Unicode letter left unchanged
Łukow              9      uppercase L with stroke
Žěkowach           1      uppercase Z with caron
k’tim              9      curly apostrophe inside a token
ſ’jich             3      long s and curly apostrophe
42½                1      number with fraction character
20-25              1      numeric range
100lětnej          12     number attached to a word
g                  3      single-letter fragment
ъ                  1      Cyrillic character
```

These examples show why the output should be treated as surface-form counts, not as fully normalized words. Punctuation can become a token, uppercase and lowercase Unicode forms can remain separate, combining characters can affect token identity, and numbers or fragments are counted without using TEI metadata such as `lemma`, `norm`, or `type="ignore"`.
