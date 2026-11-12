import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

possible_paths = [
    BASE_DIR / "knowledge_base.json",
    PROJECT_DIR / "knowledge_base.json",
]

KB_PATH = next((path for path in possible_paths if path.exists()), None)

if KB_PATH is None:
    raise FileNotFoundError(
        "Knowledge base JSON was not found."
    )

with KB_PATH.open("r", encoding="utf-8") as file:
    knowledge_base = json.load(file)

if not isinstance(knowledge_base, list):
    raise ValueError(
        "The knowledge base must be a JSON list of problem records."
    )

print(f"Knowledge base loaded from: {KB_PATH}")

DEVICES = {
    "1": "PC/Laptop",
    "2": "Smartphone/iPad",
    "3": "Monitor",
    "4": "Printer",
    "5": "Router / Wi-Fi",
}

DEVICE_ID_RANGES = {
    "1": range(1, 31),
    "2": range(31, 54),
    "3": range(54, 61),
    "4": range(61, 64),
    "5": range(64, 70),
}

FOLLOW_UP_RULES = {
    "Power": [
        "Does the device show any power or charging indicator?",
        "Is the power cable or charger connected properly?",
        "Does the device respond when you press the power button?",
    ],
    "Overheating": [
        "Does the device feel unusually hot?",
        "Are the cooling fans spinning normally, if the device has fans?",
        "Are the air vents blocked by dust?",
        "Does the device become hot during light use?",
    ],
    "Display": [
        "Is the monitor or display turned on?",
        "Is the display cable connected properly, if applicable?",
        "Does the screen show 'No Signal'?",
    ],
    "Blue Screen & Crashes": [
        "Does an error message or blue screen appear?",
        "Does the device restart, freeze, or shut down by itself?",
        "Did the problem begin after an update or software installation?",
    ],
    "Slow Performance": [
        "Does the device take a long time to start?",
        "Do applications respond slowly?",
        "Are many applications running in the background?",
    ],
    "I/O Devices": [
        "Is the keyboard, mouse, or touchscreen connected or enabled properly, if applicable?",
        "Does the input device respond at all?",
        "Does the problem affect all keys or touch areas, or only some?",
    ],
    "Internet & Wi-Fi": [
        "Is the router powered on?",
        "Can other devices connect to the internet?",
        "Is the connection slow, unavailable, or disconnecting frequently?",
        "Does the problem affect Wi-Fi, mobile data, or both?",
    ],
    "Software & Applications": [
        "Does the application close unexpectedly or fail to open?",
        "Does an error message appear?",
        "Is the problem happening with one application or several?",
        "Did the problem start after an update or installation?",
    ],
    "Storage": [
        "Does the device report that storage is full?",
        "Can you save new files?",
        "Is the problem happening with internal storage or an external drive?",
    ],
    "Battery": [
        "Does the battery drain quickly?",
        "Does the device lose charge even when not in use?",
        "Does the device become hot while charging?",
    ],
    "Display Quality": [
        "Is the screen flickering, too dark, stretched, or unclear?",
        "Did the issue start after changing display settings or updating a driver?",
        "Does the issue happen all the time?",
    ],
    "Audio": [
        "Is the volume turned up and unmuted?",
        "Is the problem with the microphone or the speaker?",
        "Does the issue happen with every application?",
    ],
    "Printer": [
        "Is the printer powered on and connected to the computer or network?",
        "Is there a paper jam?",
        "Does the printer show an ink or toner warning?",
    ],
    "Device Connection": [
        "Is Bluetooth enabled, if applicable?",
        "Is the device connected to the correct port or network?",
        "Does the device work when connected to another port or paired again?",
    ],
}

GROUP_ALIASES = {
    "power": "Power",
    "charging": "Power",
    "battery": "Battery",
    "battery issues": "Battery",
    "overheating": "Overheating",
    "overheat": "Overheating",
    "display": "Display",
    "no display": "Display",
    "screen": "Display",
    "blue screen": "Blue Screen & Crashes",
    "crashes": "Blue Screen & Crashes",
    "slow": "Slow Performance",
    "slow performance": "Slow Performance",
    "input/output": "I/O Devices",
    "i/o devices": "I/O Devices",
    "internet": "Internet & Wi-Fi",
    "wifi": "Internet & Wi-Fi",
    "wi-fi": "Internet & Wi-Fi",
    "software": "Software & Applications",
    "applications": "Software & Applications",
    "software & applications": "Software & Applications",
    "sotware & applications": "Software & Applications",
    "storage": "Storage",
    "display quality": "Display Quality",
    "audio": "Audio",
    "printer": "Printer",
    "connection": "Device Connection",
    "device connection": "Device Connection",
}

def infer_follow_up_group(record):
    """Infer a group from the problem name if the JSON group is missing."""
    problem = str(record.get("problem", "")).casefold()

    # Printer problems
    if any(word in problem for word in (
        "printer", "paper jam", "ink", "toner", "printing"
    )):
        return "Printer"

    # Router and internet problems
    if any(word in problem for word in (
        "router", "internet", "wi-fi", "wifi",
        "mobile data", "network", "signal is weak"
    )):
        return "Internet & Wi-Fi"

    # Audio problems
    if any(word in problem for word in (
        "no sound", "audio", "speaker", "microphone"
    )):
        return "Audio"

    # Battery and charging problems
    if any(word in problem for word in (
        "battery", "does not charge", "cannot charge",
        "not charging", "cannot charge"
    )):
        return "Battery"

    # Overheating problems
    if any(word in problem for word in (
        "overheating", "overheats", "overheat"
    )):
        return "Overheating"

    # Display problems
    if any(word in problem for word in (
        "no display", "no signal", "screen flicker",
        "screen is flickering", "too dark",
        "screen resolution", "displayport", "hdmi"
    )):
        return "Display Quality" if any(
            word in problem for word in (
                "flicker", "too dark", "resolution"
            )
        ) else "Display"

    # Input and Output devices
    if any(word in problem for word in (
        "keyboard", "mouse", "touchpad", "touchscreen",
        "keys not responding", "usb port"
    )):
        return "I/O Devices"

    # Storage problems
    if "storage" in problem or "storage is full" in problem:
        return "Storage"

    # Software and applications
    if any(word in problem for word in (
        "application", "apps", "software",
        "update stuck", "cannot install", "camera not working"
    )):
        return "Software & Applications"

    # Device connection problems
    if any(word in problem for word in (
        "bluetooth", "not detecting", "not connecting",
        "cannot connect"
    )):
        return "Device Connection"

    # Blue screens and crashes
    if any(word in problem for word in (
        "blue screen", "crash", "freezes", "freezing",
        "system freezes"
    )):
        return "Blue Screen & Crashes"

    # Slow performance and startup
    if any(word in problem for word in (
        "very slow", "running slowly", "too long to boot",
        "too long to start", "takes too long"
    )):
        return "Slow Performance"

    # Power problems
    if any(word in problem for word in (
        "turn on", "power", "shuts down", "restart"
    )):
        return "Power"

    return None

def get_device_problems(selected_device):
    """Return records belonging to the selected device."""
    valid_ids = DEVICE_ID_RANGES.get(selected_device)

    if valid_ids is None:
        return []

    problems = []

    for item in knowledge_base:
        raw_id = str(item.get("id", "")).strip()
        match = re.search(r"\d+", raw_id)

        if not match:
            continue

        record_id = int(match.group())

        if record_id in valid_ids:
            problems.append(item)

    return problems

def get_follow_up_questions(record):
    raw_group = record.get("follow_up_group")

    if isinstance(raw_group, list):
        group_names = raw_group
    elif raw_group:
        group_names = re.split(
            r"\s+or\s+", str(raw_group), flags=re.IGNORECASE
        )
    else:
        inferred_group = infer_follow_up_group(record)
        group_names = [inferred_group] if inferred_group else []

    normalized_rules = {
        " ".join(name.casefold().split()): questions
        for name, questions in FOLLOW_UP_RULES.items()
    }

    normalized_aliases = {
        " ".join(name.casefold().split()):
        " ".join(alias.casefold().split())
        for name, alias in GROUP_ALIASES.items()
    }

    questions = []

    for name in group_names:
        if not name:
            continue

        group = " ".join(str(name).casefold().split())
        group = normalized_aliases.get(group, group)

        questions.extend(normalized_rules.get(group, []))

    return list(dict.fromkeys(questions))

def ask_yes_no(question):
    while True:
        answer = input(f"{question} (Y/N): ").strip().casefold()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please enter Y for Yes or N for No.")

def refine_result(record, answers):
    """Return the cause and solution stored in the knowledge base."""
    possible_cause = record.get(
        "possible_cause", "Not available"
    )
    solution = record.get(
        "solution", "Not available"
    )

    # Answers are collected for display and future diagnosis rules.
    answer_map = dict(answers)

    return possible_cause, solution


def main():
    print("\n=== Computer Troubleshooting Expert System ===")
    print("\nWhat device are you having a problem with?")

    for number, device_name in DEVICES.items():
        print(f"{number}. {device_name}")

    choice = input("\nChoose a device (1-5): ").strip()

    if choice not in DEVICES:
        print("Invalid choice. Please select a number from 1 to 5.")
        return

    device_name = DEVICES[choice]
    print(f"\nSelected device: {device_name}")

    available_problems = get_device_problems(choice)

    if not available_problems:
        print("No problems are listed for this device in the knowledge base.")
        return

    print("\nChoose the problem that best matches what you are experiencing:")

    for index, item in enumerate(available_problems, start=1):
        print(f"{index}. {item.get('problem', 'Unknown problem')}")

    problem_choice = input("\nChoose a problem number: ").strip()

    if not problem_choice.isdigit():
        print("Invalid choice. Please enter a number from the list.")
        return

    problem_index = int(problem_choice)

    if not 1 <= problem_index <= len(available_problems):
        print("Invalid choice. Please select a number from the list.")
        return

    item = available_problems[problem_index - 1]

    print(f"\nSelected problem: {item.get('problem', 'Not available')}")

    group = item.get("follow_up_group") or infer_follow_up_group(item)

    if group:
        print("Troubleshooting category:", group)

    questions = get_follow_up_questions(item)
    answers = []

    if questions:
        print("\nLet's check a few follow-up questions.")

        for question in questions:
            answer = ask_yes_no(question)
            answers.append((question, answer))
    else:
        print(
            "\nNo follow-up questions could be matched to this problem."
        )

    possible_cause, solution = refine_result(item, answers)

    print("\n=== Troubleshooting Result ===")
    print("Device Category:", device_name)
    print("Exact Problem:", item.get("problem", "Not available"))
    print("Possible Cause:", possible_cause)
    print("Recommended Solution:", solution)
    print("Severity:", item.get("severity", "Not specified"))

if __name__ == "__main__":
    main()
