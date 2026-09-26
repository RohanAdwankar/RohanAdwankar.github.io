# Two fonts that do the parsing

The loudest complaint about [semfont](https://github.com/RohanAdwankar/semfont) was that it is a
JavaScript library and not a font. Fair. So I moved the work into the font file, the way
[fontemon](https://www.coderelay.io/fontemon.html) runs a whole game in there.

<style>
@font-face { font-family: "semfont ttf"; src: url("/fonts/semfont-proto.woff2") format("woff2"); font-display: swap; }
@font-face { font-family: "markfont"; src: url("/fonts/markfont.woff2") format("woff2"); font-display: swap; }
.fontbox { border: 1px solid #3a3a3a; border-radius: 8px; padding: 16px 18px; margin: 22px 0 0;
           font-size: 18px; line-height: 1.65; height: 6.2em; overflow-y: auto;
           background: #fff; color: #111; white-space: pre-wrap; }
body.light .fontbox { border-color: #d8d8d8; }
.sf { font-family: "semfont ttf", Georgia, serif; }
.mf { font-family: "markfont", "Liberation Sans", Arial, sans-serif; }
/* The left pane is the same typeface markfont is built from, so the only
   difference across the pair is the font feature. */
.raw { font-family: "Liberation Sans", Arial, sans-serif; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.pair .fontbox { margin-top: 0; height: 8.4em; }
@media (max-width: 640px) { .pair { grid-template-columns: 1fr; gap: 0; } }
.fontnote { display: flex; justify-content: space-between; align-items: baseline;
            font-size: 13px; opacity: 0.6; margin: 6px 0 26px; }
</style>

<div class="fontbox sf" contenteditable="true" spellcheck="false">The rollback should have helped, but instead it made things worse. We fixed the crash that was corrupting user data, and the team is genuinely proud of how quickly it shipped.</div>
<div class="fontnote"><span>semfont, 47 KB</span><span>type in it</span></div>

<div class="pair">
  <div>
    <div class="fontbox raw" id="md-src" contenteditable="true" spellcheck="false">## A heading
**bold**, *italic*, ~~struck~~, _under_, `code`.
Not a # heading. get_user_name is safe.</div>
    <div class="fontnote"><span>what you type</span><span>type in it</span></div>
  </div>
  <div>
    <div class="fontbox mf" id="md-out"></div>
    <div class="fontnote"><span>markfont, 26 KB</span></div>
  </div>
</div>

<script>
// The only job of this script is to copy the characters across. Nothing here
// styles anything; the right pane differs from the left by one font feature.
(function () {
  var src = document.getElementById('md-src'), out = document.getElementById('md-out');
  var mirror = function () { out.textContent = src.innerText; };
  src.addEventListener('input', mirror);
  mirror();
})();
</script>

All three boxes hold plain text, and the two above share one typeface. No stylesheet or script
sets any of that formatting; every colour, weight and rule is a substitution rule inside the font.
The one script on this page copies characters from the left pane to the right.

Spans work by propagation: one rule styles the glyph after a marker, a second styles whatever
follows a styled glyph. A lookup sees its own output as backtrack, so the style carries to the
closing marker. Underlines are drawn into each glyph and join up because glyphs sit flush.

Markdown's markers are symmetric, so a closing `**` reopened the span and bold ran to the end of
the line. Worse, prose got eaten: `C#` became a heading, `get_user_name` lost its underscores.
Four guards fix it. A closing marker has styled glyphs behind it. A heading has nothing to
backtrack over, which is the only line-start test OpenType offers. An underscore between
alphanumerics is literal, and a delimiter followed by a space opens nothing.

## What they get wrong

No dark mode. A `CPAL` palette is fixed colours, so the file cannot see what it is drawn on.

semfont's other three channels need passage context, and rules have neither memory nor unbounded
context. Headings are scaled outlines, so the metrics never learn they grew. Links, lists and
tables want indentation and click targets, which glyphs cannot make.

Prototypes. The library is still the thing that works:
[RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont).
