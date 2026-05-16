import json, sys

unis     = json.load(open("universities.json"))
lag      = json.load(open("lag_model.json"))
affinity = json.load(open("affinity_matrix.json"))

lag_field_ids      = {entry["field_id"] for entry in lag}
affinity_field_ids = {entry["field_id"] for entry in affinity}
lag_degree_ids     = set()
for field in lag:
    lag_degree_ids.update(field.get("associated_degrees", []))

errors = []

for uni in unis:
    for degree in uni["degrees"]:
        if degree["degree_id"] not in lag_degree_ids:
            errors.append(
                f"ORPHANED degree_id: '{degree['degree_id']}' in {uni['name']} "
                f"has no lag_model entry"
            )

for uni in unis:
    for degree in uni["degrees"]:
        if degree["field_id"] not in lag_field_ids:
            errors.append(
                f"MISSING field_id: '{degree['field_id']}' on degree "
                f"'{degree['degree_id']}' not found in lag_model.json"
            )

for uni in unis:
    for degree in uni["degrees"]:
        if degree["field_id"] not in affinity_field_ids:
            errors.append(
                f"MISSING field_id: '{degree['field_id']}' on degree "
                f"'{degree['degree_id']}' not found in affinity_matrix.json"
            )

for entry in affinity:
    if entry["field_id"] not in lag_field_ids:
        errors.append(
            f"ORPHANED affinity field_id: '{entry['field_id']}' "
            f"not found in lag_model.json"
        )

for uni in unis:
    for degree in uni["degrees"]:
        cond  = degree["eligibility"].get("conditionally_eligible_streams", [])
        notes = degree["eligibility"].get("eligibility_notes", {})
        for stream in cond:
            if stream not in notes:
                errors.append(
                    f"MISSING eligibility_note: stream '{stream}' in "
                    f"'{degree['degree_id']}' has no entry in eligibility_notes "
                    f"— FilterNode will crash with KeyError at runtime"
                )

if errors:
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("All integrity checks passed.")
