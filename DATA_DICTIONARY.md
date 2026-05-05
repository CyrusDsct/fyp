# Fixopleth Data Dictionary

This dictionary reflects the current implementation in `prompt.txt`, `ui/sections/criteria.py`, and `ui/sections/evaluation.py`.

Current output structure:

- 39 structured analysis fields
- 19 metadata / non-scoring fields
- 20 map-related scoring criteria
- 3 narrative outputs: `explanation`, `map_quality`, `recommendations`

Quality score calculation:

```text
good = 1 point
neutral = 0.5 point
bad = 0 point

quality score = (good + 0.5 * neutral) / 20 * 100%
```

Metadata fields are displayed as supporting evidence, but they do not directly count toward the quality score.

## 19 Metadata / Non-Scoring Fields

| No. | JSON Key | Display Name | Definition | Expected Values |
| --- | --- | --- | --- | --- |
| 1 | `number_of_bins` | Number of bins | Number of divisions used in the legend, including No Data or Others if present. | Integer, or `not applicable` for continuous legends |
| 2 | `data_breaks` | Data breaks | Boundary values or categories extracted from the legend. | List of ranges, numeric breaks, or category labels |
| 3 | `data_contiguity` | Data contiguity | Whether the legend represents a continuous range or discrete categories. | `continuous`, `discrete`, `not applicable` |
| 4 | `number_of_variables` | Number of variables | Number of distinct variables represented in the map. | `univariate (1)`, `bivariate (2)`, `multivariate (3+)` |
| 5 | `region_count` | Region count | Number of distinctly divided and colored regions visible in the map. | Integer |
| 6 | `coverage_percentage` | Coverage percentage | Percentage of visible regions with known data represented in the legend. | `0-100%` |
| 7 | `color_scheme` | Color scheme | Type of color sequence used for the data, excluding background and No Data colors. | `Sequential Single-hue`, `Sequential Multi-hue`, `Categorical`, `Diverging`, `Cyclic`, `Other`, `Not Applicable` |
| 8 | `legend_colors` | Legend colors | Notable colors used in the legend, ordered left-to-right or top-to-bottom. | List of simple color names |
| 9 | `legend_presence` | Legend presence | Whether a legend exists on the map. | `yes`, `no` |
| 10 | `legend_orientation` | Legend orientation | Direction in which legend values are arranged. | `horizontal`, `vertical`, `other`, `not applicable` |
| 11 | `legend_placement` | Legend placement | Position of the legend relative to the whole map. | `top left`, `top center`, `top right`, `center left`, `center`, `center right`, `bottom left`, `bottom center`, `bottom right` |
| 12 | `frequency_labels` | Frequency labels | Whether counts/frequencies are shown beside legend categories or bins. | `yes`, `no`, `not applicable` |
| 13 | `title_presence` | Title presence | Whether the map has a title. | `yes`, `no` |
| 14 | `title_text` | Title text | Text content of the title if present. | Text, or `not applicable` |
| 15 | `subtitle_presence` | Subtitle presence | Whether the map has a subtitle. | `yes`, `no` |
| 16 | `subtitle_text` | Subtitle text | Text content of the subtitle if present. | Text, or `not applicable` |
| 17 | `map_projection` | Map projection | Map projection inferred from region shapes and distortion. | Projection name, or `unknown` |
| 18 | `background_color` | Background color | Color used for non-data areas such as oceans, empty space, or out-of-scope regions. | Color name |
| 19 | `source_citation` | Source citation | Data source names or links visible on the map. | Text, link, or `not applicable` |

## 20 Scoring Criteria

These fields are used by the UI to calculate the map quality score.

| No. | JSON Key | Display Name | Definition | Good / Neutral / Bad Logic |
| --- | --- | --- | --- | --- |
| 1 | `data_distribution` | Data distribution | Whether the visible binning reveals the underlying data pattern clearly. | Good if regions are meaningfully spread across bins. Neutral if partially visible. Bad if the pattern is hidden or distorted. |
| 2 | `classification_method` | Classification method | Binning method used to split values into classes. | Good if suitable for the detected distribution. Neutral if acceptable but not optimal. Bad if unsuitable or arbitrary. |
| 3 | `normalization_present` | Normalization present | Whether the mapped variable is normalized, such as rate, percent, index, or per capita. | Good if normalization is explicit or not applicable. Neutral if ambiguous. Bad if raw totals/counts are used or normalization is unclear. |
| 4 | `geographic_unit_homogeneous` | Geographic unit homogeneous | Whether all regions use the same geographic or administrative unit. | Good if all regions are comparable. Neutral if not applicable. Bad if mixed scales are used. |
| 5 | `administrative_level` | Administrative level | Primary geographic unit of analysis. | Good if suitable for purpose. Neutral if acceptable but not ideal. Bad if too coarse or too detailed for the purpose. |
| 6 | `legend_completeness` | Legend completeness | Whether every non-background map color is explained in the legend. | Good if all colors have clear labels. Neutral if not applicable. Bad if colors are missing, unreadable, cut off, or ambiguous. |
| 7 | `handling_no_missing_data` | Missing-data handling | Whether no-data regions have a distinct visual treatment and are labeled in the legend. | Good if no-data is distinct and labeled. Neutral if no missing-data regions are visible. Bad if no-data is ambiguous or unlabeled. |
| 8 | `source_recency` | Source recency | Whether the source appears recent enough for the topic. | Good if current enough. Neutral if unknown or not applicable. Bad if outdated for a time-sensitive topic. |
| 9 | `bin_count_appropriateness` | Bin count appropriateness | Whether the number of bins is suitable for interpretation. | Good if generally 3-7 bins. Bad if too few, too many, or unsuitable for the range. |
| 10 | `data_breaks_quality` | Data breaks quality | Whether breaks are continuous, non-overlapping, cover the range, and distribute regions meaningfully. | Good if complete and balanced. Bad if gaps, overlaps, incomplete coverage, or most regions cluster in one or two bins. |
| 11 | `classification_appropriateness` | Classification appropriateness | Whether the classification method matches the detected data distribution. | Good if method is listed as suitable. Neutral if distribution is ambiguous but bins are reasonable. Bad if method is unsuitable or cannot be validated. |
| 12 | `choropleth_suitability` | Choropleth suitability | Whether the variable is appropriate for a choropleth map. | Good if normalized quantitative data or inherently categorical. Neutral if evidence is inconclusive. Bad if raw totals/counts create area bias or variable type is unclear. |
| 13 | `region_hierarchy_consistency` | Region hierarchy consistency | Whether the map uses consistent region hierarchy. | Good if all regions are at the same scale. Bad if scales are mixed or inconsistently subdivided. |
| 14 | `data_coverage_adequacy` | Data coverage adequacy | Whether enough visible regions have data for meaningful analysis. | Good if more than 90% of visible regions have data represented. Bad if coverage is 90% or lower. |
| 15 | `color_scheme_appropriateness` | Color scheme appropriateness | Whether the color scheme matches data type and ordering. | Good if sequential/diverging/categorical use is appropriate. Bad if the scheme mismatches data type or creates misleading associations. |
| 16 | `color_distinguishability` | Color distinguishability | Whether adjacent legend colors are visually distinguishable. | Good if adjacent colors are easy to distinguish. Bad if colors blend, have uneven lightness, or rely only on red-green contrast. |
| 17 | `legend_placement_quality` | Legend placement quality | Whether the legend is visible and placed without obstructing the map. | Good if easy to find and unobstructive. Bad if cropped, too small, far away, or covering important regions. |
| 18 | `title_quality` | Title quality | Whether the title clearly identifies geographic scope, variable, and time period. | Good if clear and concise. Bad if missing, vague, too long, misleading, or missing key information. |
| 19 | `subtitle_quality` | Subtitle quality | Whether the subtitle adds useful context beyond the title. | Good if it adds useful context. Neutral if absent but title is already sufficient. Bad if redundant, misleading, or irrelevant. |
| 20 | `source_quality` | Source quality | Whether the source is cited, reputable, relevant, and current enough. | Good if source is cited and suitable. Bad if no source is cited or the source is unreliable, irrelevant, or outdated. |

## Narrative Outputs

| JSON Key | Definition | Expected Value |
| --- | --- | --- |
| `explanation` | Short factual explanation of what the map shows. | Up to 100 words, with meaningful key findings highlighted using `**...**` |
| `map_quality` | Overall quality reasoning based on the scoring criteria. | About 300 words, with meaningful quality judgments highlighted using `**...**` |
| `recommendations` | Suggested fixes based on criteria marked bad. | About 150 words, or exactly `none` if no criteria are bad |

## Classification Method Values

`Defined Interval` is intentionally excluded from the user-facing binning comparison diagram.

Current classification method values used by the prompt:

- `Unclassed`
- `Manual Interval`
- `Equal Interval`
- `Pretty Breaks`
- `Geometric Interval`
- `Exponential`
- `Logarithmic`
- `Quantile`
- `Percentile`
- `Standard Deviation`
- `Natural Breaks`
- `Head/Tail Breaks`
- `Maximum Breaks`

## Removed / Legacy Fields From Older Dictionary

The following fields appeared in older notes but are not part of the current 39-field output dictionary:

- `Explicit Others Category`
- `Incomplete Info`
- `Data Type`
- `Semantic Type`
- `Contiguity` as a separate old-name field; current key is `data_contiguity`
- `Colours` as a separate old-name field; current key is `legend_colors`
- `Border For Legend`
- `Defined Interval` in the user-facing binning comparison
