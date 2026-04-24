import yaml
import csv
import sys
import ast
from pathlib import Path


# ─────────────────────────────────────────────────────────
# NORMALISATION
# ─────────────────────────────────────────────────────────

def normalize(value, indicator):
    """Map a raw indicator value to [0, 1]."""
    ind_type = indicator['type']

    if ind_type == 'boolean':
        return 1.0 if value else 0.0

    elif ind_type in ('numeric', 'percentage'):
        min_val = indicator.get('min', 0)
        max_val = indicator.get('max', 1)
        if max_val == min_val:
            return 0.0
        return max(0.0, min((value - min_val) / (max_val - min_val), 1.0))

    elif ind_type == 'ordinal':
        scale = indicator['scale']
        if value in scale:
            return scale.index(value) / (len(scale) - 1)
        return 0.0

    return 0.0


# ─────────────────────────────────────────────────────────
# COERCION
# ─────────────────────────────────────────────────────────

def coerce_value(raw, ind_cfg):
    """
    Convert a CSV string cell to the correct Python type based on indicator config.
    Empty / missing cells return None.
    """
    if raw is None or str(raw).strip() == '':
        return None

    raw = str(raw).strip()
    ind_type = ind_cfg['type']

    if ind_type == 'boolean':
        return raw.lower() in ('true', '1', 'yes', 'y')

    elif ind_type in ('numeric', 'percentage'):
        try:
            return float(raw)
        except ValueError:
            return None

    elif ind_type == 'ordinal':
        return raw  # keep as string; normalise() matches against scale

    # Fallback — try a literal eval, then string
    try:
        return ast.literal_eval(raw)
    except Exception:
        return raw


# ─────────────────────────────────────────────────────────
# SCORING  (flattened – no subcategory tier)
# ─────────────────────────────────────────────────────────

def compute_facility_score(data, config):
    """
    Compute the Digital Readiness Score (DRS) for one facility.

    The breakdown is keyed by domain → indicator (subcategories are
    collapsed; the indicator dicts in the config are iterated directly).

    Returns:
        drs          (float) – final score as a percentage (0–100)
        breakdown    (dict)  – {domain_name: {ind_name: record, ...}, ...}
        raw_total    (float)
        max_possible (float)
    """
    indicator_results = []
    breakdown = {}

    for domain_name, domain_cfg in config['domains'].items():
        domain_entry = {}
        breakdown[domain_name] = domain_entry

        # Walk every subcategory but expose only domain → indicator
        for sub_cfg in domain_cfg['subcategories'].values():
            for ind_name, ind_cfg in sub_cfg['indicators'].items():
                weight = ind_cfg.get('weight', 0)
                present = ind_name in data and data[ind_name] is not None

                # Apply fallback weight when indicator is missing and fallback exists
                if not present and 'fallback_weight' in ind_cfg:
                    weight = ind_cfg['fallback_weight']

                # Exclude zero-weight indicators
                if weight == 0:
                    domain_entry[ind_name] = {
                        'raw_value': data.get(ind_name),
                        'normalised': None,
                        'weight': 0,
                        'weighted_contribution': 0.0,
                        'pct_of_final_score': 0.0,
                        'status': 'excluded (weight=0)',
                    }
                    continue

                if not present:
                    domain_entry[ind_name] = {
                        'raw_value': None,
                        'normalised': None,
                        'weight': weight,
                        'weighted_contribution': 0.0,
                        'pct_of_final_score': 0.0,
                        'status': 'missing',
                    }
                    indicator_results.append({
                        'id': ind_name,
                        'weighted_contribution': 0.0,
                        'weight': weight,
                    })
                    continue

                normalised = normalize(data[ind_name], ind_cfg)
                contribution = normalised * weight

                domain_entry[ind_name] = {
                    'raw_value': data[ind_name],
                    'normalised': round(normalised, 4),
                    'weight': weight,
                    'weighted_contribution': round(contribution, 4),
                    'pct_of_final_score': 0.0,   # filled in second pass
                    'status': 'included',
                }
                indicator_results.append({
                    'id': ind_name,
                    'weighted_contribution': contribution,
                    'weight': weight,
                })

    raw_total    = sum(r['weighted_contribution'] for r in indicator_results)
    max_possible = sum(r['weight']                for r in indicator_results)
    drs = (raw_total / max_possible * 100) if max_possible > 0 else 0.0

    # Second pass: attach % contribution to final score
    for domain_entry in breakdown.values():
        for rec in domain_entry.values():
            if rec['status'] == 'included' and raw_total > 0:
                rec['pct_of_final_score'] = round(
                    rec['weighted_contribution'] / raw_total * 100, 2
                )

    return round(drs, 2), breakdown, round(raw_total, 4), round(max_possible, 4)


# ─────────────────────────────────────────────────────────
# CSV I/O
# ─────────────────────────────────────────────────────────

def load_facilities_csv(path, config):
    """
    Read the facilities CSV.  The first column is the facility identifier;
    every subsequent column is an indicator name.

    Returns:
        facilities  – list of dicts: {'_id': ..., ind_name: typed_value, ...}
        id_col      – name of the identifier column
    """
    # Build a flat lookup: ind_name → ind_cfg  (needed for type coercion)
    ind_lookup = {}
    for domain_cfg in config['domains'].values():
        for sub_cfg in domain_cfg['subcategories'].values():
            for ind_name, ind_cfg in sub_cfg['indicators'].items():
                ind_lookup[ind_name] = ind_cfg

    facilities = []
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        id_col = reader.fieldnames[0]   # first column = facility ID

        for row in reader:
            record = {'_id': row[id_col]}
            for col, raw in row.items():
                if col == id_col:
                    continue
                if col in ind_lookup:
                    record[col] = coerce_value(raw, ind_lookup[col])
                # Columns not in the config are silently ignored

            facilities.append(record)

    return facilities, id_col


def collect_output_columns(config):
    """
    Build the ordered list of output columns (beyond facility ID and DRS):
        <domain>_score  for each domain
        <ind_name>_norm, <ind_name>_pct  for every non-zero-weight indicator
    """
    domain_cols = []
    ind_cols    = []

    for domain_name, domain_cfg in config['domains'].items():
        domain_cols.append(f"{domain_name}_score")

        for sub_cfg in domain_cfg['subcategories'].values():
            for ind_name, ind_cfg in sub_cfg['indicators'].items():
                if ind_cfg.get('weight', 0) != 0:
                    ind_cols.append(ind_name)

    return domain_cols, ind_cols


def compute_domain_scores(breakdown, raw_total, max_possible, config):
    """
    Derive a 0–100 score per domain based on each domain's share of
    weighted contributions vs. its share of possible weight.
    """
    domain_scores = {}
    for domain_name, domain_entry in breakdown.items():
        dom_contrib  = sum(r['weighted_contribution'] for r in domain_entry.values())
        dom_max      = sum(r['weight']                for r in domain_entry.values()
                          if r['status'] != 'excluded (weight=0)')
        domain_scores[domain_name] = round((dom_contrib / dom_max * 100)
                                           if dom_max > 0 else 0.0, 2)
    return domain_scores


def score_facilities_to_csv(input_csv, output_csv, config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    facilities, id_col = load_facilities_csv(input_csv, config)
    domain_cols, ind_cols = collect_output_columns(config)

    header = (
        [id_col, 'drs_score', 'raw_total', 'max_possible']
        + domain_cols
        + [f"{c}_normalised" for c in ind_cols]
        + [f"{c}_pct_of_score" for c in ind_cols]
        + [f"{c}_status" for c in ind_cols]
    )

    with open(output_csv, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=header, extrasaction='ignore')
        writer.writeheader()

        for fac in facilities:
            fac_data = {k: v for k, v in fac.items() if k != '_id'}
            drs, breakdown, raw_total, max_possible = compute_facility_score(fac_data, config)
            domain_scores = compute_domain_scores(breakdown, raw_total, max_possible, config)

            row = {
                id_col:        fac['_id'],
                'drs_score':   drs,
                'raw_total':   raw_total,
                'max_possible': max_possible,
            }

            # Domain scores
            for domain_name in config['domains']:
                row[f"{domain_name}_score"] = domain_scores.get(domain_name, '')

            # Per-indicator columns (flat, across all domains)
            for ind_name in ind_cols:
                rec = None
                for domain_entry in breakdown.values():
                    if ind_name in domain_entry:
                        rec = domain_entry[ind_name]
                        break

                if rec:
                    row[f"{ind_name}_normalised"]    = rec['normalised'] if rec['normalised'] is not None else ''
                    row[f"{ind_name}_pct_of_score"]  = rec['pct_of_final_score']
                    row[f"{ind_name}_status"]        = rec['status']
                else:
                    row[f"{ind_name}_normalised"]    = ''
                    row[f"{ind_name}_pct_of_score"]  = ''
                    row[f"{ind_name}_status"]        = 'not_in_config'

            writer.writerow(row)

    print(f"✓  Scored {len(facilities)} facilities → {output_csv}")


# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python score_facilities.py <input.csv> <output.csv> [config.yaml]")
        print("       config.yaml defaults to 'config.yaml' in the current directory.")
        sys.exit(1)

    input_csv   = sys.argv[1]
    output_csv  = sys.argv[2]
    config_path = sys.argv[3] if len(sys.argv) > 3 else "config.yaml"

    score_facilities_to_csv(input_csv, output_csv, config_path)
