Here’s a more polished, **GitHub-ready README.md** with cleaner formatting, badges, and a professional tone:

---

# 🏥 Digital Readiness Scoring Tool (DRS)

A configurable Python tool for computing a **Digital Readiness Score (DRS)** for health facilities using structured indicator data.

This tool helps assess how prepared facilities are to adopt and sustain digital health systems (e.g., EMRs) by transforming raw data into a transparent, weighted score.

---

## ✨ Features

* ⚙️ **Config-driven scoring** (YAML-based)
* 🧮 **Automatic normalization** (boolean, numeric, percentage, ordinal)
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
git clone https://github.com/your-username/digital-readiness-score.git
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
```

---

## 🧮 Scoring Methodology

### 1. Normalization

All indicator values are scaled to **[0, 1]**:

| Type       | Method                    |
| ---------- | ------------------------- |
| Boolean    | `True → 1`, `False → 0`   |
| Numeric    | Min-max scaling           |
| Percentage | Min-max scaling           |
| Ordinal    | Position in defined scale |

---

### 2. Weighted Contribution

```
contribution = normalized_value × weight
```

---

### 3. Digital Readiness Score (DRS)

```
DRS = (Σ contributions / Σ weights) × 100
```

---

### 4. Domain Scores

Each domain is scored independently:

```
domain_score = (domain contribution / domain max weight) × 100
```

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

For each indicator:

* `<indicator>_normalised`
* `<indicator>_pct_of_score`
* `<indicator>_status`

---

## 📌 Indicator Status Definitions

| Status                | Description                    |
| --------------------- | ------------------------------ |
| `included`            | Used in scoring                |
| `missing`             | Not provided in input          |
| `excluded (weight=0)` | Ignored by design              |
| `not_in_config`       | Present in CSV but not defined |

---

## 🔄 Handling Missing Data

* Missing values contribute **0**
* Indicators may define a `fallback_weight`
* Indicators with `weight = 0` are **excluded from scoring but tracked**

---

## 🔍 Type Coercion

CSV values are automatically converted:

| Input              | Parsed As |
| ------------------ | --------- |
| `true`, `yes`, `1` | Boolean   |
| `12.5`             | Float     |
| `"grid"`           | Ordinal   |
| empty cell         | `None`    |

---

## 🧩 Extending the Framework

To add a new indicator:

1. Add it to `config.yaml`
2. Add the column to your CSV
3. Define:

   * `type`
   * `weight`
   * Optional: `min`, `max`, or `scale`

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

---


