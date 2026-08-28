# Human-authored HTML data-report format contract

Status: frozen structural baseline. Change it only through an explicit format
review. Use this reference for every HTML or React data-analysis report.

This contract owns hierarchy, grid, alignment, typography, spacing, container
fit, chart anatomy, table structure, and responsive behavior. A selected style
pack may change document character but must not weaken these rules. This file
does not own colors. Read `../styles/color-system/color_system.yaml` as the only
authority for palette choice and color usage.

This contract also does not own analytical wording. Before using it, require a
validated `report_text_pack` from `report_text_pack_contract.md`. The HTML or
React renderer may arrange approved strings and add fixed structural labels,
but it may not draft, rewrite, shorten, strengthen, or recommend through prose.

## Contents

1. Design objective
2. Start from the reading path
3. Grid and content measure
4. Container and card rules
5. Typography, title breaks, and spacing
6. Designed accents and markers
7. Analytical chart design
8. Relationship between prose and visuals
9. Tables, actions, and evidence notes
10. Responsive and print behavior
11. Anti-patterns
12. Visual review gate

## 1. Design objective

Make the page feel edited by a human information designer:

- Let hierarchy come from content order, typography, alignment, whitespace,
  and rules before adding surfaces.
- Make one management claim dominant in each viewport or report section.
- Use asymmetry when content importance or length differs. Equal visual weight
  is reserved for genuinely equal evidence.
- Optimize for comparison and interpretation, not for component count.
- Keep the evidence dense enough that a reader can inspect the claim without
  opening another view.

The report is a document with analytical exhibits, not a collection of UI
widgets. Do not imitate a SaaS dashboard unless the user explicitly requests an
interactive monitoring product.

## 2. Start from the reading path

Before writing markup, classify every content unit as one of:

| Unit | Reader question | Default treatment |
|---|---|---|
| claim | What should I believe? | Sentence headline on the main grid |
| metric | How large is the issue? | Ruled metric line or compact inline value |
| comparison | What differs from what? | Chart, table, or aligned number row |
| explanation | Why might this be happening? | Short prose beside the evidence |
| boundary | What can the evidence not establish? | Small note adjacent to the affected claim |
| decision | What should happen next? | Decision line or action register |
| source | Can I verify it? | Figure footer or end notes |

Then write a one-line reading path, for example:

`claim -> scale -> whole-report summary -> time pattern -> decomposition -> decision -> boundary`

Do not start from a component inventory. Start from the reading path, group
only units that readers need to interpret together, and remove repeated labels.

### Whole-report summary contract

Place one full-report summary immediately after the opening fact/metric strip
and before the first analytical section. Do not float the decision summary in a
right-side callout beside the title.

Write the summary as unboxed prose using a progressive sequence:

1. **Overall judgement:** one short paragraph that answers the report question.
2. **Supporting findings:** use only the short paragraphs needed to preserve the
   verified logic, one finding per paragraph, ordered by decision importance.
3. **Closing synthesis:** close the verified argument without importing text
   from detachable `bounded_modules`.

Use a small report-native label such as `全文结论`, then one readable prose
column. Do not use a card background, icon grid, side rail, or equal summary
tiles. Keep each paragraph to one claim and normally one or two sentences.

Render `bounded_modules` after the normal report argument as independent,
removable evidence-boundary modules. Do not number them as analytical sections,
and do not reuse their title or text in the full-report summary.

## 3. Grid and content measure

Use one explicit 12-column page grid at desktop widths.

### Global alignment contract

Alignment is a page-level contract, not a local styling preference. Before
writing CSS, create a private alignment ledger for every structural block:

| Block | Start anchor | End anchor | Internal split |
|---|---|---|---|
| title and standfirst | page start | declared text measure | none |
| metric rail | page start | page end | integer column groups |
| full-report summary | page start | declared reading measure | none |
| section evidence | page start | page end | declared column spans |
| full-width table | page start | page end | table column contract |

Use one source of truth for the page column count and gutter. Reuse the same
CSS custom properties or layout tokens in the masthead, title, metric rail,
summary, sections, figures, tables, and notes. Do not redefine a visually
similar 12-column grid with a different gap inside one section.

The canonical horizontal anchors are the page start, page end, declared column
starts and ends, and the center of a declared gutter. Structural text, rules,
plot frames, table edges, and separators must land on one of those anchors.
Elements that claim the same anchor may differ by at most `1px` after rendering.
An accidental near miss of `2-16px` fails review; either snap the edge to the
anchor or make the inset clearly intentional and record it in the ledger.

For a rail of comparable items, use integer column groups. Four comparable
metrics normally use `3 + 3 + 3 + 3` columns when their content fits. Equal
widths are appropriate here because the items share one semantic role; use
unequal integer spans only when content or decision importance materially
differs. Default to no vertical separator. If a separator is necessary, place
it in the center of the shared gutter and run it for the full declared rail
height. Never attach a border to the edge of a gapped grid item and then add
left padding to the next item: this creates a false double gutter and breaks
the shared alignment.

The full-report summary defaults to the page-left anchor. Put its label above
the prose and start both on the same left edge. Do not reserve a label column or
indent the prose merely to create an editorial side rail. A summary may use a
narrower reading measure, but that measure must grow rightward from the page
start unless a real navigation or annotation structure justifies an inset.

Nested grids are allowed only for internal systems such as chart axes, table
cells, or a compact number-title cluster. Their outer edges must still snap to
the parent page grid, and their internal tracks must not masquerade as page
anchors.

- Page width: `1120-1240px`; use `1200px` as the general default.
- Outer margin: at least `40px` on desktop and `20px` below `760px`.
- Column gap: `20-24px`.
- Body text measure: `24-38` Chinese characters per line; do not stretch prose
  across the full page.
- Dominant analytical visual: normally `7-9` columns.
- Interpretation rail: normally `3-5` columns.
- Dense table or multi-series exhibit: `12` columns.
- Short metric: `2-3` columns only when the value and label fit naturally.
- A sentence or short list does not receive a wider container merely to fill a row.

Use these span rules as defaults, not fixed templates:

| Content shape | Recommended span | Pairing |
|---|---:|---|
| one value + short label | 2-3 columns | place in a ruled metric rail |
| 2-4 sentence explanation | 4-5 columns | pair with a 7-8 column visual |
| ranked bars or time series | 7-9 columns | pair with reading notes |
| comparison matrix | 12 columns | put implication in the last column |
| two related small multiples | 6 + 6 columns | share scale, title logic, and baseline |
| action register | 12 columns | use a table, not action cards |

Align section titles, chart plotting areas, table edges, sources, and adjacent
prose to the same grid lines. A nearly aligned edge looks less intentional than
an obviously different inset.

Use one repeatable vertical rhythm unless the content gives a clear reason to
change it:

- fact strip to full-report summary: `28-36px`;
- summary to first section: `44-56px`;
- section header to evidence: `18-24px`;
- prose column to chart: `28-36px` horizontal gap;
- figure to source: `8-12px`;
- section to next section: `48-56px`.

Do not create spacing by leaving an unused grid column. Empty space must belong
to a declared margin, gutter, reading measure, or hierarchy break.
Do not combine a parent grid gap with ad hoc child `padding-left` or
`margin-left` to simulate another gutter between comparable siblings.

## 4. Container and card rules

Default to no card. Use a container only when it communicates one of these:

1. an interaction boundary;
2. an independent state;
3. an evidence group that must stay together when printed;
4. an exception that needs contrast from the surrounding report.

If none applies, use whitespace, a thin rule, indentation, or column position.

When a container is justified:

- Size it to its content and role; do not force unrelated containers to equal
  height.
- Use at most one separation device: background, border, or shadow. The default
  report styles use a background or a rule and no shadow.
- Keep corner radius between `0-3px`. Avoid floating rounded rectangles.
- Keep internal padding proportional to content: `12-16px` for a compact note,
  `20-24px` for a major evidence group.
- Do not nest cards. An inset note inside an exhibit should use a rule or tint,
  not another floating panel.
- Do not create three equal cards merely because there are three findings.
  Use rank, sequence, or a ruled list so importance remains visible.

Large empty cards, soft shadows, decorative outlines, and generous padding
around short text are failure conditions.

## 5. Typography, title breaks, and spacing

Use Microsoft YaHei as the report typeface for Chinese, Latin text, and
numbers. Use this local-only stack and do not depend on a remote font:

```css
font-family: "Microsoft YaHei", "Microsoft YaHei UI", Arial, sans-serif;
font-synthesis: none;
```

Use only weights that are reliably available on the workstation:

- `400`: paragraphs, descriptions, chart labels, table cells, and notes;
- `700`: report title, section claims, key values, short action labels, and
  the single phrase that needs emphasis.

Do not request `500`, `600`, `620`, `650`, `750`, or `800`. Synthetic or rounded
weights collapse hierarchy differently across browsers. Create intermediate
emphasis through size, spacing, or position instead of another weight.

Use no more than four visible text levels on a page:

1. report claim/title;
2. section claim;
3. body/analytical text;
4. source/caption.

Recommended desktop ranges:

- Report title: `36-40px`, weight `700`, line height `1.16-1.22`, maximum two
  lines.
- Section claim: `22-25px`, weight `700`, line height `1.28-1.36`, maximum two
  lines.
- Deck/standfirst: `16px`, weight `400`, line height `1.65-1.75`.
- Body: `15px`, weight `400`, line height `1.6-1.72`.
- Key metric: `28-32px`, weight `700`, line height `1.0-1.1`.
- Table and chart labels: `12-13px`, line height `1.35-1.55`.
- Source and notes: `11-12px`, line height `1.5-1.65`. Never render report text
  below `11px` at a desktop viewport.

Break a two-line title at a semantic boundary such as conclusion/reason or
problem/implication. Use explicit line spans or a controlled break after
checking the rendered width. Do not break inside a number, unit, date, proper
noun, or a tightly bound phrase. Do not allow a one- or two-character orphan on
the second line. At mobile widths, remove the forced break and let the title
wrap naturally.

Use a compact spacing scale such as `4, 8, 12, 16, 24, 32, 48, 64`.
Repeated elements must share a baseline and spacing rhythm. Vary section gaps to
show hierarchy; do not wrap every block in identical `24px` padding.

Use bold weight sparingly. Outside headings and table headers, allow at most one
bold phrase in a paragraph or cell and one dominant bold statement in a
highlight block. In one viewport, aim for no more than three bold reading
anchors excluding the report title and column headings. A page where every
label, number, and conclusion is bold has no hierarchy. Avoid all-caps English
micro-labels in Chinese reports.

## 6. Designed accents and markers

Use emphasis to encode meaning, not to decorate empty space. This section owns
the geometry and frequency of emphasis devices; all palette roles and color
behavior come from `../styles/color-system/color_system.yaml`.

Pair every emphasis treatment with a label, shape, position, or line style so
the meaning does not depend on appearance alone.

### Highlight blocks

Use a flat highlight block for a decision, material exception, or evidence
boundary that must be read with the surrounding claim.

- Use at most one primary highlight block above the fold and one per analytical
  section.
- Fit the block to its text. Do not equalize it with neighboring content.
- Use one background treatment plus one `2-3px` rule or geometric marker; no shadow.
- Use `12-16px` vertical and `14-18px` horizontal padding.
- Keep radius at `0-2px` and never nest a highlight block inside a card.
- Start with a short semantic label; do not fill the block with a long essay.

### Geometric markers

Use simple CSS or SVG geometry instead of generic icon libraries:

- circle, `6-8px`: a data point, current state, or numbered reading anchor;
- triangle, `8-10px`: direction, material change, or attention requiring action;
- short vertical bar, `3-5px`: selected row, quoted finding, or boundary;
- reference line or band: target, benchmark, event window, or confidence range.

Keep non-chart geometric markers to roughly three per viewport. Repeat a shape
only when its meaning stays the same. Every marker must sit beside a human-
readable label; mark purely visual shapes `aria-hidden="true"`.

### Mini charts

Use a sparkline, compact comparison bar, or tiny range plot inside a metric rail
only when it adds information that the headline value cannot carry.

- Sparkline: use for at least six ordered observations; show the relevant
  exception point/window and the last value.
- Compact bar: use for a part-to-whole or two-value comparison; show the numeric
  value in adjacent text.
- Size: approximately `90-170px` wide and `24-40px` high.
- Omit axes and legends; retain a reference line, endpoint, or highlighted
  point when it affects interpretation.
- Use one context treatment plus one focus treatment. Do not add a mini chart to every
  metric.
- Remove a mini chart if it only repeats the large number or acts as decoration.

## 7. Analytical chart design

Treat each chart as an argument, not an illustration. Before choosing a chart,
write:

- the question it answers;
- the comparison the reader must perform;
- the message to prove;
- the focus mark or interval;
- the decision or next question it informs.

### Required chart anatomy

Every decision-relevant chart includes:

1. a full-sentence takeaway title;
2. visible unit and time scope;
3. an honest baseline or clearly declared truncated scale;
4. a comparison reference such as prior period, target, benchmark, or total;
5. direct labels for the focus and endpoints;
6. one visually distinct focus treatment and context marks;
7. a source/note line;
8. an adjacent implication or reading note when interpretation is not obvious.

Use no more than two simultaneous focus treatments in one chart: normally one
primary focus treatment plus one reference treatment. Approved focus treatments
are an interval band, a direct annotation, a halo/ring around one point, a
reference line, a faded context series, or a business-impact marker. Do not use
all of them at once.

Dense does not mean crowded. Increase information density through useful
comparisons, shared scales, annotations, reference lines, and compact multiples,
not through more labels.

### Chart selection

- Trend over time: line, column, or small multiples. Show meaningful reference
  periods and annotate the exception window.
- Ranked contribution: sorted horizontal bar, lollipop, or waterfall. Keep the
  value and contribution direction visible.
- Composition: stacked bar or table. Avoid doughnuts when precise comparison is
  needed.
- Relationship: scatterplot with a reference band and named exceptions.
- Before/after or two-point movement: slope chart or delta table.
- Many categories with exact values: a well-designed table is often better than
  a chart.

Avoid gauges, decorative rings, 3D charts, legends that force eye travel, and
full value labels on every mark when only a few marks matter.

### Density targets

For a dominant desktop exhibit, aim for at least two of these:

- `8+` comparable marks;
- a target or benchmark;
- a highlighted interval or cohort;
- a delta or contribution label;
- a direct annotation that explains the focus;
- a small supporting comparison sharing the same scale.

A chart containing only one big number and a decorative shape should become a
metric line or prose.

## 8. Relationship between prose and visuals

Do not put a chart in a generic full-width card and explain it several screens
later. Use one of these exhibit relationships:

### Dominant exhibit with interpretation rail

- Chart: `8` columns.
- Reading notes: `4` columns.
- Align note numbers or headings with the vertical regions they explain.
- Put the management implication at the bottom of the rail, separated by a
  thin rule.

### Claim-evidence row

- Claim and reasoning: `4-5` columns.
- Chart or table: `7-8` columns.
- Keep the claim headline aligned with the exhibit title.
- Use for analytical sections, not for every paragraph.

### Full-width evidence table

- Put the takeaway above the table.
- Reserve the last column for interpretation, confidence, or decision use.
- Do not repeat the table in prose; call out only the pattern and exceptions.

Each section should answer, in order: `what the evidence says -> how to read it
-> what it changes`. If prose and chart make unrelated points, split them into
separate sections.

### Section header contract

Use the same header structure for every analytical section:

1. a compact sequence number;
2. the sentence-style section claim immediately beside it.

Do not put the sequence number in a separate wide grid column. Do not float the
internal validation question into the visible header or body. The visual gap
between number and title should be `8-12px`. The complete header should read as
one unit before the chart or table begins.

### Editorial writing and segmentation

- Write one conclusion per complete sentence and normally one or two sentences
  per paragraph. Put the next conclusion in the next sentence in reading order.
- Keep fact selection, evidence lineage, interpretation checks, and boundary
  classification internal. Visible prose must combine the necessary data and
  conclusion naturally instead of exposing `证据/结论/边界/判断` answer labels.
- Keep a section introduction to at most three short paragraphs.
- Keep a reading-rail note to one complete sentence; do not use a heading as a
  substitute for a conclusion.
- Remove repeated phrases already visible in the chart title, axis, or table.
- If a paragraph exceeds roughly four rendered lines in its assigned column,
  shorten it or divide it by analytical role.

Use the same prose-to-chart pattern, gap, top alignment, and source treatment
for comparable sections. Variation must reflect different content, not ad hoc
CSS per section.

## 9. Tables, actions, and evidence notes

- Use horizontal rules and alignment before cell fills.
- Keep numeric columns right-aligned and comparable units consistent.
- Highlight a row only when it changes the decision.
- Add an upward or downward triangle only when the direction itself matters.
- Use short labels in the first column and interpretation in the last column.
- Structure analytical text cells as at most two short complete sentences.
- Keep one conclusion per line. Use block-level spans or paragraphs with
  `4-6px` internal separation; do not expose internal evidence or boundary
  labels as cell headings.
- Keep comparable rows structurally identical. If the first row uses
  two sentence lines, every comparable row should use the same order.
- Let row height grow with content, but align numeric values and the first text
  line to the top. Do not vertically center long prose against short numbers.
- Prefer `12-16px` cell padding and a line height of `1.5-1.65` for text-heavy
  analytical tables.
- Use zebra striping only for long tables where row tracking is difficult.
- Turn repeated action cards into one action register with owner, time window,
  dependency, evidence needed, and next check.
- Put decision-critical boundaries next to the affected claim. Move ordinary
  definitions and sources to figure footers or end notes.

## 10. Responsive and print behavior

- At `900px`, allow a dominant exhibit and interpretation rail to stack.
- At `760px`, collapse to one column, but keep metric labels next to values and
  preserve table readability with horizontal scrolling where required.
- Do not turn every section into a card on mobile.
- Use `break-inside: avoid` for figures, action rows, and evidence groups.
- Remove decorative backgrounds in print only when contrast remains clear.
- Verify that takeaway titles, units, source notes, and emphasis meaning survive
  grayscale printing.
- Let forced desktop title lines reflow naturally below `760px`.
- Keep mini charts attached to their metric label/value when the rail stacks.

## 11. Anti-patterns

Reject or revise the page when any of these appear without a strong reason:

- three or four equal-width KPI cards as the first screen;
- a large gradient hero, glow, glass panel, or soft shadow;
- repeated rounded cards with identical padding regardless of content length;
- centered text used for analytical paragraphs;
- icons or pills that merely decorate section names;
- a decision summary floating to the right of the report title;
- a section number isolated in a wide empty column;
- an internal validation question exposed in a section header or body;
- visible prose divided into `证据/结论/边界/判断` answer blocks;
- a full-report summary whose prose is indented by a decorative label column;
- metric or card separators that do not land on the page grid or a declared
  gutter center;
- a local section grid that almost, but not exactly, matches the page grid;
- a doubled gap created by grid spacing plus sibling padding or margin;
- long semicolon chains or unsegmented prose beside a chart;
- table cells containing multiple unlabeled conclusions in one paragraph;
- circles, triangles, or mini charts repeated without a stable semantic role;
- more than one primary highlight block competing inside the same section;
- five or more requested font weights, synthetic font weight, or mixed Chinese
  typefaces in one report;
- a full-width chart with large unused margins and fewer than three useful data
  comparisons;
- a chart title that names the chart type instead of stating the finding;
- a detached legend, detached commentary, or source several sections away;
- all sections having the same visual weight;
- English template labels in an otherwise Chinese report;
- a decorative closing card instead of a decision, action, or evidence gap.

## 12. Visual review gate

Render the report before delivery. Review at desktop width and one narrower
width. The report fails if any answer below is no.

### Five-second scan

- Can the reader identify the main claim, the scale of the issue, and the
  dominant evidence without reading body copy?
- Is there one obvious entry point rather than a grid of equal choices?

### Alignment and fit

- Do titles, plot areas, tables, notes, and adjacent prose share deliberate grid
  lines?
- Does every structural block use the same page-grid column count and gutter
  tokens?
- Do elements assigned to the same anchor render within `1px` of each other,
  with no accidental `2-16px` near misses?
- Do comparable metric cells start on declared integer columns, with no local
  padding that creates a second gutter?
- Are vertical separators absent by default, or centered in a declared gutter
  and extended for the full group height?
- Do the full-report summary label and prose share the page-left anchor?
- Does every container fit its content without large dead space?
- Are unequal content lengths allowed to produce unequal spans or heights?
- Does the full-report summary follow the metric strip in a single prose flow?
- Do all section numbers sit directly beside their titles, without exposing
  internal validation questions?
- Are comparable sections using the same header-to-content and prose-to-chart
  gaps?
- Does the title use no more than two intentional lines without an orphan?
- Is every visible text element at least `11px` at desktop width?

### Chart quality

- Does each chart support a named claim and show a meaningful comparison?
- Are unit, baseline, focus, direct labels, and source visible?
- Is the chart information-dense without becoming label-dense?
- Do mini charts add trend or comparison information instead of decoration?
- Is each chart using no more than two focus treatments?

### Page composition

- Are chart and prose close enough to be read as one argument?
- Does the page alternate between dominant evidence, explanation, and compact
  supporting material instead of repeating the same component row?
- Does emphasis reveal exceptions rather than decorate the page?

### Human-authored finish

- Could each major layout choice be explained by content length, importance, or
  comparison need?
- After removing backgrounds and borders, would the page hierarchy still work?
- Is Microsoft YaHei used consistently with only `400` and `700` weights?
- Can every highlight block, circle, triangle, and mark be explained by
  a stable semantic role?
- Does every paragraph carry one claim, and does every analytical table cell
  expose its internal structure instead of hiding it in continuous prose?
