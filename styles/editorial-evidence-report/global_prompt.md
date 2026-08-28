Use the `editorial-evidence-report` page design style. Consume a validated
`report_text_pack` before writing markup. Copy its analytical strings exactly
and preserve their `text_id` or `conclusion_id` as `data-text-id` attributes.
Do not draft, combine, shorten, strengthen, or add visible analytical prose;
add only fixed structural labels such as section numbers, units, and sources.
Before writing markup,
read `references/human_authored_html_design_system.md` and write a private
one-line reading path, content-to-grid map, and alignment ledger.
Read `styles/color-system/color_system.yaml` separately and take every color
token and color-usage rule from that module; do not define a palette here.

Design the report as a continuous editorial evidence document, not a dashboard
or a card gallery. Build hierarchy with sentence headlines, a twelve-column
grid, aligned rules, compact spacing, and deliberately unequal spans. Default
to no card. Add a background or border only when it communicates an independent
state, print group, interaction boundary, or exception; never use a shadow and
never nest cards.

Treat alignment as a page-level contract. Define the page column count and
gutter once, then reuse those exact tokens for the masthead, title, metric rail,
summary, analytical sections, figures, tables, and notes. Assign every
structural edge to the page start, page end, a declared column edge, or the
center of a declared gutter. After rendering, edges assigned to the same anchor
must be within `1px`; an accidental `2-16px` near miss fails review. Local chart
and table grids may differ internally, but their outer edges must snap to the
page grid.

For four comparable opening metrics, use `3 + 3 + 3 + 3` page columns when the
content fits. Default to no vertical separators. If one is analytically
necessary, center it in the shared gutter and run it for the full rail height.
Never combine the page gutter, a cell-edge border, and extra left padding on the
next item. That creates a false double gutter and visibly breaks alignment.

Fit layout to content. Short metrics belong in a ruled inline rail, two to four
sentences normally occupy four or five columns, a dominant chart normally uses
seven to nine columns, and dense tables use the full grid. Do not make panels
equal height or width when their content length, importance, or comparison role
differs. Do not create three equal cards simply because there are three
findings.

After the metric rail, render one unboxed section named `全文结论` or an
equivalent report-native label. Preserve the approved progressive prose sequence:
one overall judgement, only the supporting paragraphs required by verified
logic, and one closing synthesis. Keep one claim per paragraph and exclude all
detachable bounded modules. Never float the report decision in a right-side block beside the
title and never replace the full summary with cards. Put the summary label
above the prose and align both to the page-left anchor. Do not reserve a
decorative label column or indent the prose merely to create a side rail.

Use `"Microsoft YaHei", "Microsoft YaHei UI", Arial, sans-serif` for every
visible element, including SVG labels. Use only weights `400` and `700`, and
disable font synthesis. Use `36-40px/700` for the report title, `22-25px/700`
for section claims, `16px/400` for the standfirst, `15px/400` for body text,
`28-32px/700` for key metrics, `12-13px` for table/chart labels, and at least
`11px` for sources. Keep the report title to at most two lines and break it at a
semantic boundary; remove the forced break on mobile. Outside headings and
table headers, bold no more than one phrase per paragraph or cell.

Treat every chart as an argument. Give it a full-sentence takeaway title,
visible unit and time scope, an honest baseline or declared scale, a comparison
reference, direct labels for the focus and endpoints, a clear focus treatment, and a
source line. Prefer an eight-column exhibit paired with a four-column
interpretation rail. Align numbered reading notes with the chart regions they
explain, and end the rail with the decision implication or evidence boundary.

Use designed emphasis with a fixed semantic grammar. Pair emphasis with a
label, circle, triangle, short bar, band, or line style. A circle marks a state or data point; a triangle
marks direction or attention; a short vertical bar marks a selected row or
boundary. Keep non-chart markers to roughly three per viewport.

Allow one primary flat highlight block above the fold and at most one per
analytical section. Use one background treatment plus one rule or geometric marker, with no
shadow and no nested surface. Use a sparkline only for six or more ordered
observations and a compact bar only for a useful part-to-whole or two-value
comparison. Do not put a mini chart in every metric. Keep mini charts attached
to their number, and highlight only the exception window, relevant endpoint, or
reference.

Make charts information-dense through comparison, shared scales, reference
lines, exception windows, and annotations. Do not label every
mark. If a visual contains only one number and decorative geometry, replace it
with a metric line or prose. Use a table when exact comparison across many
categories is more important than shape.

Use no more than two focus treatments in one chart: normally one primary
treatment such as an interval band or point halo plus one reference treatment
such as a benchmark line or faded context. Do not combine every possible
annotation effect.

Use report-native Chinese labels for Chinese reports. Avoid gradients, glass effects,
rounded floating surfaces, decorative icon libraries, badges, generic section
microcopy, and oversized empty hero areas.

Before delivery, inspect computed or rendered geometry, not only the CSS source.
Reject any page where shared left or right edges drift, horizontal rules start
from inconsistent anchors, comparable metric cells use arbitrary fractional
splits, the full-report summary is offset from the page-left anchor, or one
section silently redefines the page gutter.

The reading order should normally be: claim -> scale -> whole-report summary ->
time pattern -> decomposition -> decision -> boundary.
Each analytical section must keep its
claim, evidence, reading notes, implication, and source close enough to be read
as one unit. Finish with a ruled action register, decision record, or evidence
gap table rather than a decorative summary card.

Build every analytical section header from one compact sequence number followed
immediately by the sentence-style claim. Use an `8-12px` number-title gap. Do
not reserve a wide column for the number, and never expose the Agent's internal
validation question in the visible header or body.

Use a repeatable editorial rhythm: `22px` from section header to evidence,
`32px` between prose and chart, and about `52px` between sections. Write no more
than three short introductory paragraphs per section. Render one complete
conclusion per sentence in reading order; do not expose `证据/结论/边界/判断`
answer labels. If prose exceeds roughly four rendered lines in its column,
return it to the writer for sentence-level compression or paragraphing.

Inside analytical tables, use at most two complete sentence lines and one
conclusion per line. Keep the same order for comparable rows. Top-align numeric
values and the first text line. Do not expose internal evidence labels or place
a paragraph containing several conclusions into one table cell.

Render the page at desktop width and at one narrower width. Reject the design if
the main claim and dominant evidence are not clear in five seconds, if container
sizes are not explained by content, if alignment drifts, or if chart commentary
is detached from the chart. Also reject it if Microsoft YaHei is not actually
used, any text is below `11px`, a title exceeds two lines at desktop width, or a geometric marker or
mini chart has no explainable semantic role.
Reject it as well if the summary is floating beside the title, section numbers
are separated from claims by unused grid space, comparable sections use
different spacing without a content reason, or chart/table prose is not visibly
segmented.
