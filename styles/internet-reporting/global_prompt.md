Use the `internet-reporting` page design style. Consume a validated
`report_text_pack` before writing markup. Copy its analytical strings exactly
and preserve their `text_id` or `conclusion_id` as `data-text-id` attributes.
Do not draft, combine, shorten, strengthen, or add visible analytical prose;
add only fixed structural labels such as section numbers, units, and sources.
Read
`references/human_authored_html_design_system.md` first and preserve its frozen
grid, typography, alignment, spacing, chart, table, and responsive contracts.
Read `styles/color-system/color_system.yaml` separately and obtain all theme
and semantic colors from it. Do not define a palette in this style pack.
Read `styles/internet-reporting/sample.html` as the fixed visual reference for
this style. Use it as a layout and rhythm reference, not as a business-content
template.

Design the output as a real internet-team collaboration document that happens
to contain a rigorous data report. It should feel writable, discussable, and
easy to continue after the meeting. Do not imitate any collaboration application's UI,
toolbar, comments panel, logo, or proprietary templates. Recreate the document
logic: fixed semantic heading levels, Markdown-like content flow, restrained
highlights, useful columns, native tables, and embedded data blocks.

Keep one clean document surface. Use a compact title and metadata line,
a ruled metric strip, then the mandatory unboxed `全文结论` section in a
general-specific-general sequence. Align the summary label and prose to the
page-left anchor. Do not add a document index or navigation block merely to
evoke an online editor.

Use one twelve-column page grid and one gutter token everywhere. A prose block
normally grows from the page-left edge to seven or nine columns; charts and
dense tables may use the full grid. Use local `4 + 8`, `5 + 7`, or `6 + 6`
columns only when both sides answer the same section claim and have comparable
visual weight. If a short prose block would sit beside a tall chart and leave a
large blank area under the prose, use continuous document flow instead: section
title, claim sentences, embedded chart/table, then reading notes. After rendering,
shared anchors must match within `1px`; an accidental `2-16px` offset fails.

Use Microsoft YaHei for every visible element, including SVG labels, with only
weights `400` and `700`. Use semantic heading levels rather than arbitrary font
enlargement. Preserve the text pack's one-claim paragraphs and use one bold
phrase at most per paragraph or analytical cell. Do not split or rewrite long
prose during rendering; return it to the Report Text Editor instead.
For short analytical statements, prefer one statement on one visual line when it
fits the planned line width. When a statement cannot fit cleanly and compression
would remove evidence, render the approved point list instead of leaving a
two- or three-line paragraph that interrupts scanning.

Treat highlights as scarce document blocks. Use at most one flat callout in a
section and no more than two highlight treatments in one viewport. A callout
must carry a material decision, evidence boundary, or operating note. Use one
quiet tint plus one short rule or marker, `0-2px` radius, and no shadow. Do not
put metrics, findings, or actions into repeated rounded cards.

Treat each chart or table as an embedded evidence object in the document. Its
compact header states the takeaway, unit, time scope, and source relationship.
The chart follows or sits beside the prose it proves; its interpretation is
immediately below or adjacent. Use minimal gridlines, direct labels, one
comparison reference, and no decorative legend. Apply semantic signal colors
only when the color-system semantics are true; ordinary series use theme roles.
Do not detach chart commentary into a distant lower row merely to fill space;
the reader should be able to move from claim to evidence to interpretation
without crossing a blank column.

Use document-native tables. Use subtle shared cell lines when readers need
exact lookup, and horizontal rules when interpretation matters more. Keep
numeric columns right aligned. Split analytical text cells into at most two
complete sentence lines, one conclusion per line; never expose internal
`证据/结论/边界/判断` labels or place an unbroken essay inside a cell.

Render every approved `bounded_module` after the normal report argument as an
independent removable block. Use a short attention label, one descriptive
title, and its approved complete `statements` in order. Do not add known-
evidence/evidence-boundary labels or include it in `全文结论`, analytical section
numbering, or the report title/subtitle.
Add `data-module-type="bounded"` and `data-removable="true"`; never render
`omitted_units`.

Before delivery, render desktop and one narrower viewport. Reject the result if
it looks like a dashboard, a PPT slide, an editor screenshot, or a card gallery;
if the summary is indented without real navigation; if headings do not reveal a
clean outline; if highlights compete with one another; if chart commentary is
detached; or if alignment and spacing vary without a content reason.
