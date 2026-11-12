from flask import Flask, abort, jsonify, render_template, request

import main as expert  # existing expert system, unchanged

app = Flask(__name__)


def find_record(problem_id):
    for item in expert.knowledge_base:
        if str(item.get("id")) == str(problem_id):
            return item
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/devices")
def api_devices():
    devices = []
    for key, name in expert.DEVICES.items():
        devices.append({
            "id": key,
            "name": name,
            "count": len(expert.get_device_problems(key)),
        })
    return jsonify(devices)

CATEGORY_MAP = {
    "Power": "power", "Battery": "power",
    "Display": "display", "Display Quality": "display",
    "Internet & Wi-Fi": "network",
    "Audio": "audio",
    "Slow Performance": "performance", "Blue Screen & Crashes": "performance",
    "Overheating": "performance", "Storage": "performance",
    "Software & Applications": "performance",
    "I/O Devices": "peripheral", "Device Connection": "peripheral",
    "Printer": "printer",
}

CATEGORY_LABELS = {
    "power": "Power Issues",
    "display": "Display Issues",
    "network": "Network Issues",
    "audio": "Audio Issues",
    "performance": "Performance Issues",
    "peripheral": "Peripheral Issues",
    "printer": "Printer Issues",
}

CATEGORY_ORDER = list(CATEGORY_LABELS)


def record_group(item):
    raw = item.get("follow_up_group")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if raw:
        return str(raw).split(" or ")[0].strip()
    return expert.infer_follow_up_group(item)


def record_category(item):
    group = record_group(item)
    if group in CATEGORY_MAP:
        return CATEGORY_MAP[group]
    return group or "general" 


@app.route("/api/devices/<device_id>/problems")
def api_problems(device_id):
    if device_id not in expert.DEVICES:
        abort(404)

    problems, grouped = [], {}
    for item in expert.get_device_problems(device_id):
        cat = record_category(item)
        problems.append({
            "id": item.get("id"),
            "problem": item.get("problem", "Unknown problem"),
            "symptoms": item.get("symptoms", ""),
            "category": cat,
        })
        grouped.setdefault(cat, []).append(item)

    ordered = [c for c in CATEGORY_ORDER if c in grouped]
    ordered += [c for c in grouped if c not in ordered]

    categories = []
    for cat in ordered:
        symptoms = []
        for item in grouped[cat]:
            s = item.get("symptoms", "")
            if s and s not in symptoms:
                symptoms.append(s)
        categories.append({
            "id": cat,
            "label": CATEGORY_LABELS.get(cat, str(cat).title() + " Issues"),
            "subtitle": ", ".join(symptoms[:2]),
            "count": len(grouped[cat]),
        })

    return jsonify({
        "device": expert.DEVICES[device_id],
        "categories": categories,
        "problems": problems,
    })


@app.route("/api/problems/<problem_id>")
def api_problem(problem_id):
    item = find_record(problem_id)
    if item is None:
        abort(404)
    return jsonify({
        "id": item.get("id"),
        "problem": item.get("problem", "Not available"),
        "questions": expert.get_follow_up_questions(item),
    })


@app.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    data = request.get_json(silent=True) or {}
    item = find_record(data.get("problem_id"))
    if item is None:
        abort(404)
    answers = [
        (a.get("question", ""), bool(a.get("answer")))
        for a in data.get("answers", [])
    ]
    possible_cause, solution = expert.refine_result(item, answers)
    return jsonify({"possible_cause": possible_cause, "solution": solution})


if __name__ == "__main__":
    app.run(debug=False)
