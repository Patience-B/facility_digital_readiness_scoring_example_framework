# 🏥 Digital Readiness Scoring Tool (DRS)

A configurable Python tool for computing a **Digital Readiness Score (DRS)** for health facilities using structured indicator data.

This tool helps assess how prepared facilities are to adopt and sustain digital health systems (e.g., EMRs) by transforming raw data into a transparent, weighted score.

---

## ✨ Features

* ⚙️ **Config-driven scoring** (YAML-based)
* 🧮 **Automatic normalization** (boolean, numeric, percentage, ordinal)
* 🔃 **Invertible indicators** (lower raw value → higher score, e.g. distance to referral)
* 📊 **Weighted scoring system (0–100)**
* 🔍 **Full transparency** (per-indicator contributions & statuses)
* 🧱 **Modular design** (easy to extend without code changes)
* 📁 **CSV in → CSV out pipeline**

---

## 📂 Repository Structure

```
.
├── score_facilities.py     # Main scoring script
├── config.yaml             # Indicator definitions & weights
├── input.csv               # Example input data
├── output.csv              # Example output
└── README.md
```

---

## ⚙️ Installation

No external dependencies required beyond Python standard library.

```bash
git clone https://github.com/Patience-B/facility_digital_readiness_scoring_example_framework.git
cd digital-readiness-score
```

---

## ▶️ Usage

```bash
python score_facilities.py <input.csv> <output.csv> [config.yaml]
```

### Example:

```bash
python score_facilities.py input.csv output.csv config.yaml
```

If `config.yaml` is not provided, the script defaults to:

```bash
config.yaml
```

---

## 📥 Input Format

* First column: **Facility ID**
* Remaining columns: **Indicator values**
* Column names must match indicator names in the config

### Example

```csv
facility_id,infrastructure_devices_functional_devices_available,infrastructure_power_hours_available_per_day
FAC001,true,12
FAC002,false,8
```

---

## 🧾 Configuration (YAML)

All scoring logic is defined in `config.yaml`.

### Structure

```yaml
domains:
  domain_name:
    name: Human readable name
    description: Description of domain
    subcategories:
      subcategory_name:
        indicators:
          indicator_name:
            type: boolean | numeric | percentage | ordinal
            weight: number
            invert: true          # optional — flip the scale
            fallback_weight: number  # optional — used when value is missing
            min: number           # numeric/percentage only
            max: number           # numeric/percentage only
            scale: [...]          # ordinal only — ordered list, low → high
```

---

## 🧮 Scoring Methodology

### 1. Normalization

All indicator values are scaled to **[0, 1]** before weighting. The method depends on the indicator type:

| Type | Method |
| --- | --- |
| Boolean | `True → 1.0`, `False → 0.0` |
| Numeric | Min-max scaling: `(value − min) / (max − min)`, clamped to [0, 1] |
| Percentage | Same as Numeric |
| Ordinal | `index_in_scale / (len(scale) − 1)` — assumes scale is ordered from lowest to highest |

**Out-of-range clamping:** For `numeric` and `percentage` types, values below `min` or above `max` are clamped to `0.0` or `1.0` respectively rather than exceeding the [0, 1] range.

**Inverted indicators (`invert: true`):** Some indicators are naturally "better when lower" (e.g. distance to a referral facility, patient wait time). Setting `invert: true` on any indicator flips its normalized score:

```
final_score = 1.0 − normalized_score
```

This means a shorter distance (lower raw value) yields a higher readiness contribution. The `invert` flag works with all indicator types.

---

### 2. Weighted Contribution

Each indicator contributes to the total score in proportion to its configured weight:

```
contribution = normalized_value × weight
```

---

### 3. Digital Readiness Score (DRS)

The DRS aggregates all indicator contributions into a single facility-level score:

```
DRS = (Σ contributions / Σ weights) × 100
```

Only indicators that are present and have a non-zero weight are included in this calculation. Missing indicators contribute `0` to `Σ contributions` but their weight is still counted in `Σ weights`, which penalizes incomplete data.

---

### 4. Domain Scores

Each domain is scored **independently** based on its own indicators only:

```
domain_score = (Σ domain contributions / Σ domain weights) × 100
```

`Σ domain weights` is the sum of weights for all non-zero-weight indicators within that domain — it is **not** a share of the global total. This means domain scores are self-contained and comparable across facilities regardless of other domains.

---

### 5. Handling Missing Data

* Missing values contribute **0** to weighted contributions.
* Their configured weight **is still counted** in `Σ weights`, reducing the overall DRS.
* Indicators may define a `fallback_weight` in the config. When a value is missing and a `fallback_weight` is provided, the fallback replaces the standard weight for that indicator in that facility's calculation.
* Indicators with `weight: 0` are excluded from all score calculations but are still tracked in the output with status `excluded (weight=0)`.

---

### 6. Indicator % Contribution

After the DRS is computed, a second pass calculates each included indicator's share of the raw total:

```
pct_of_final_score = (indicator contribution / Σ contributions) × 100
```

This is recorded in the output and helps identify which indicators drove a facility's score.

---

## 🔍 Type Coercion

CSV values are automatically converted based on the indicator type defined in the config:

| Input | Indicator Type | Parsed As |
| --- | --- | --- |
| `true`, `yes`, `1`, `y` | boolean | `True` |
| `false`, `no`, `0`, `n` | boolean | `False` |
| `12.5` | numeric / percentage | `float` |
| `"grid"` | ordinal | string (matched against scale) |
| empty cell | any | `None` |

Columns present in the CSV but not defined in `config.yaml` are **silently ignored** during scoring. They will not appear in the output, but no error is raised.

---

## 📊 Output Format

The output CSV includes:

### Core Fields

* `facility_id`
* `drs_score`
* `raw_total`
* `max_possible`

### Domain Scores

* `<domain>_score`

### Indicator-Level Fields

For each non-zero-weight indicator:

* `<indicator>_normalised`
* `<indicator>_pct_of_score`
* `<indicator>_status`

---

## 📌 Indicator Status Definitions

| Status | Description |
| --- | --- |
| `included` | Present in input and used in scoring |
| `missing` | Not provided in input; contributes 0 |
| `excluded (weight=0)` | Ignored by design; tracked but not scored |
| `not_in_config` | Present in CSV but not defined in config |

---

## 🧩 Extending the Framework

To add a new indicator:

1. Add it to `config.yaml`
2. Add the column to your CSV
3. Define:

   * `type`
   * `weight`
   * Optional: `min`, `max` (numeric/percentage), `scale` (ordinal), `invert`, `fallback_weight`

✅ No code changes required.

---

## 🧠 Example Domains

* Clinical Service Delivery
* Routine Health Information & Reporting
* Health Workforce
* Physical Infrastructure

---

## 📈 Use Cases

* Digital health readiness assessments
* EMR rollout prioritization
* Facility benchmarking
* Infrastructure gap analysis

---

## ⚠️ Important Notes

* Indicators with `weight: 0` are excluded from scoring
* Some indicators act as **gating signals** (e.g., power, connectivity)
* Unknown CSV columns are ignored silently
* Values outside the configured `min`/`max` range are clamped, not rejected

---

## 📊 Example Output

```csv
facility_id,drs_score,physical_infrastructure_score
FAC001,67.5,72.3
```

---

## 🛠️ Future Improvements

* Visualization dashboard (e.g., Streamlit)
* JSON output support
* API wrapper for integration
* Validation checks for config consistency

---

## 📄 License

MIT License (or specify your preferred license)

---

## 👩🏽‍💻 Author

Built for scalable, explainable **digital health system readiness assessments**, especially in low-resource settings.
