# Two fonts that do the parsing

The loudest complaint about [semfont](https://github.com/RohanAdwankar/semfont) was that it is a
JavaScript library and not a font. Fair. So I moved the work into the font file.

<style>
@font-face { font-family: "semfont ttf"; src: url("/fonts/semfont-proto.woff2") format("woff2"); font-display: swap; }
@font-face { font-family: "markfont"; src: url("/fonts/markfont.woff2") format("woff2"); font-display: swap; }
.fontbox { border: 1px solid #3a3a3a; border-radius: 8px; padding: 16px 18px; margin: 22px 0 0;
           font-size: 18px; line-height: 1.65; height: 6.2em; overflow-y: auto;
           background: #fff; color: #111; white-space: pre-wrap; }
body.light .fontbox { border-color: #d8d8d8; }
/* The fonts bake absolute colours into CPAL, so they can only be read on a
   light background. This page has no theme to switch. */
.theme-switch { display: none; }
/* "2 * 3" broke across a line and read as two fragments */
article :not(pre) > code { white-space: nowrap; }
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

<script>document.body.classList.add('light');</script>

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

## How it works

Every letter has a copy per style. A `COLR` record points the copy back at the original outline
and paints it from a `CPAL` palette entry, so colour costs no new drawing. Bold and italic are
real Liberation Sans outlines. Underline and strikethrough are a bar drawn into each glyph, which
joins up into one rule because glyphs sit flush.

Then one rule seeds a span and a second carries it:

```
lookup CLRb { sub a by a.b; sub b by b.b; ... } CLRb;

sub asterisk asterisk a' lookup CLRb;   # after **, embolden the next glyph
sub @Anyb @Any' lookup CLRb;            # and the one after that, and so on
```

A lookup walks left to right and sees its own output as backtrack, so the second rule keeps
firing until the class stops matching. The closing marker is where it stops.

Four `ignore` rules keep it off ordinary prose. A closing marker is one with styled glyphs behind
it. A heading has nothing to backtrack over, which is the only line-start test OpenType offers,
so `C#` survives. An underscore between alphanumerics is literal, so `get_user_name` survives. A
delimiter followed by a space opens nothing, so `2 * 3` survives.

A marker is then hidden only once a styled glyph ends up beside it. One that styled nothing stays
on the page.

[RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont).
