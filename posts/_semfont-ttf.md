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
*italic holding **bold ~~struck~~** inside*, _under_, `code`.
Not a # heading. get_user_name is safe.</div>
    <div class="fontnote"><span>what you type</span><span>type in it</span></div>
  </div>
  <div>
    <div class="fontbox mf" id="md-out"></div>
    <div class="fontnote"><span>markfont, 60 KB</span></div>
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

Every letter has a copy per state, and there are thirty-two states. Only eight sets of those are
real outlines, one per Liberation face; the rest are components pointing at one of the eight,
plus a one-em bar scaled to the letter's width for underline and strikethrough. Colour is a
`COLR` record and a `CPAL` entry, so it costs no drawing at all.

A closing `**` does not have to be matched with the `**` that opened it. It turns bold off
because bold was on. So emphasis is a set of flags, not a bracket, and five flags is
thirty-two states. Every glyph carries the state it is in:

```
lookup TOGGLE {
  sub @S0 asterisk.s0' lookup NULL_s1 asterisk.s0' lookup NULL_s1 @Open;  # bold on
  sub @S1 @Any.s0' lookup TO_s1;                                          # carry it
  sub @S1nonspace asterisk.s0' lookup NULL_s0 asterisk.s0' lookup NULL_s0; # bold off
}
```

A delimiter becomes a zero-width glyph carrying the state after the flip, and a lookup walks
left to right seeing its own output as backtrack, so one pass runs the whole machine. Depth
never comes up, which is why the four nested spans in the box above come out right.

The guards are the rest. An opener needs a non-space after it and a closer needs a non-space
before it, so `2 * 3 * 4` survives. An underscore after a word character opens nothing, so
`get_user_name` survives. A heading only fires with nothing to backtrack over, which is the
only line-start test OpenType offers, so `C#` survives.

[RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont).
