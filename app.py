import random
import copy
from flask import Flask, request, jsonify

app = Flask(__name__)

# Define the data
classes = [
    {"type": "course", "name": "DL"},
    {"type": "lab", "name": "DL LAB"},
    {"type": "course", "name": "BDA"},
    {"type": "lab", "name": "BDA LAB"},
    {"type": "course", "name": "NNFS"},
    {"type": "lab", "name": "NNFS LAB"},
    {"type": "course", "name": "BT"},
    {"type": "lab", "name": "BT LAB"},
    {"type": "course", "name": "CSL"},
    {"type": "course", "name": "DS"},
    {"type": "lab", "name": "DS LAB"},
    {"type": "course", "name": "PROJECT"},
]

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

time_slots = [
    "09:15-10:15",
    "10:15-11:15",
    "11:15-11:30 (Break)",
    "11:30-12:30",
    "12:30-13:30",
    "13:30-14:15 (Break)",
    "14:15-15:15",
    "15:15-16:15",
    "16:15-17:15",
]

# Define class requirements
COURSE_REQUIREMENTS = {}
LAB_REQUIREMENTS = {}
for cls in classes:
    if cls["type"] == "course":
        COURSE_REQUIREMENTS[cls["name"]] = 3  # Each course taught 3 times a week
    elif cls["type"] == "lab":
        LAB_REQUIREMENTS[cls["name"]] = 1  # Each lab taught once a week

# Define a timetable structure (empty initially)
def create_empty_timetable():
    return {day: [""] * len(time_slots) for day in days}

# Fitness function to evaluate a timetable
def fitness(timetable):
    score = 0

    # Initialize counters
    course_counter = {cls["name"]: 0 for cls in classes if cls["type"] == "course"}
    lab_counter = {cls["name"]: 0 for cls in classes if cls["type"] == "lab"}

    # Check breaks are respected
    for day in days:
        if timetable[day][2] != "Break" or timetable[day][5] != "Break":
            return 0  # Breaks not respected

    # Check labs: only one lab per day and occupies two consecutive slots
    for day in days:
        lab_slots = []
        for idx, slot in enumerate(timetable[day]):
            if "LAB" in slot:
                lab_slots.append(idx)
        if len(lab_slots) > 2:
            return 0  # More than two lab slots in a day
        if len(lab_slots) == 2:
            if lab_slots[1] - lab_slots[0] != 1:
                return 0  # Lab slots are not consecutive
        elif len(lab_slots) == 1:
            return 0  # Lab should occupy two slots

    # Check course and lab frequencies and duplicates
    for day in days:
        classes_scheduled = set()
        for slot in timetable[day]:
            if slot == "" or slot == "Break":
                continue
            cls_name = slot.split(" - ")[0]
            cls_type = next(
                (cls["type"] for cls in classes if cls["name"] == cls_name), None
            )
            if cls_type == "course":
                course_counter[cls_name] += 1
                if cls_name in classes_scheduled:
                    return 0  # Duplicate course in the same day
                classes_scheduled.add(cls_name)
            elif cls_type == "lab":
                lab_counter[cls_name] += 1

    # Check if all courses are taught required number of times
    for course, count in COURSE_REQUIREMENTS.items():
        if course_counter.get(course, 0) != count:
            return 0

    # Check if all labs are taught required number of times
    for lab, count in LAB_REQUIREMENTS.items():
        if lab_counter.get(lab, 0) != count:
            return 0

    # If all constraints are satisfied
    score += 1
    return score

# Generate a random timetable
def generate_random_timetable():
    timetable = create_empty_timetable()

    # Shuffle courses and labs
    courses = [cls for cls in classes if cls["type"] == "course"]
    labs = [cls for cls in classes if cls["type"] == "lab"]

    # Schedule labs first
    for lab in labs:
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            day = random.choice(days)
            # Check if lab already scheduled on this day
            lab_present = any("LAB" in slot for slot in timetable[day])
            if lab_present:
                attempts += 1
                continue
            # Choose a starting slot for 2-hour lab
            possible_slots = [i for i in range(len(time_slots) - 1) if i not in [2, 5]]
            random.shuffle(possible_slots)
            for slot in possible_slots:
                if timetable[day][slot] == "" and timetable[day][slot + 1] == "":
                    timetable[day][slot] = lab["name"]
                    timetable[day][slot + 1] = lab["name"]
                    placed = True
                    break
            attempts += 1

    # Schedule courses
    for course in courses:
        times_scheduled = 0
        attempts = 0
        while times_scheduled < COURSE_REQUIREMENTS[course["name"]] and attempts < 100:
            day = random.choice(days)
            # Avoid duplicate courses in the same day
            if any(course["name"] in slot for slot in timetable[day]):
                attempts += 1
                continue
            # Choose a random slot excluding breaks and lab slots
            possible_slots = [i for i in range(len(time_slots)) if i not in [2, 5]]
            random.shuffle(possible_slots)
            for slot in possible_slots:
                # Check if slot is free and not part of a lab
                if timetable[day][slot] == "":
                    # Ensure not overlapping with lab slots
                    if slot > 0 and "LAB" in timetable[day][slot - 1]:
                        continue
                    if slot < len(time_slots) - 1 and "LAB" in timetable[day][slot + 1]:
                        continue
                    timetable[day][slot] = course["name"]
                    times_scheduled += 1
                    break
            attempts += 1

    # Add breaks
    for day in days:
        timetable[day][2] = "Break"
        timetable[day][5] = "Break"

    return timetable

# Crossover between two timetables
def crossover(timetable1, timetable2):
    child = copy.deepcopy(timetable1)
    crossover_day = random.choice(days)
    child[crossover_day] = copy.deepcopy(timetable2[crossover_day])
    return child

# Mutation to introduce variability
def mutate(timetable):
    mutated = copy.deepcopy(timetable)
    day = random.choice(days)
    slot = random.choice(range(len(time_slots)))

    # Skip break slots
    if slot in [2, 5]:
        return mutated

    current_class = mutated[day][slot]
    if current_class == "Break" or current_class == "":
        return mutated

    cls_name = current_class.split(" - ")[0]
    cls = next((c for c in classes if c["name"] == cls_name), None)
    if not cls:
        return mutated

    if cls["type"] == "course":
        # Try to replace with another course
        possible_courses = [
            c for c in classes if c["type"] == "course" and c["name"] != cls["name"]
        ]
        if possible_courses:
            new_cls = random.choice(possible_courses)
            mutated[day][slot] = new_cls["name"]
    elif cls["type"] == "lab":
        # Mutate both slots of the lab
        if slot < len(time_slots) - 1 and mutated[day][slot + 1] == current_class:
            # Replace with another lab if possible
            possible_labs = [
                c for c in classes if c["type"] == "lab" and c["name"] != cls["name"]
            ]
            if possible_labs:
                new_lab = random.choice(possible_labs)
                mutated[day][slot] = new_lab["name"]
                mutated[day][slot + 1] = new_lab["name"]
    return mutated

# Run the genetic algorithm
def run_genetic_algorithm(population_size=50, generations=1000):
    population = [generate_random_timetable() for _ in range(population_size)]
    for generation in range(generations):
        # Evaluate fitness
        population = sorted(population, key=lambda x: fitness(x), reverse=True)

        if fitness(population[0]) == 1:
            print(f"Optimal timetable found at generation {generation}")
            return population[0]

        # Selection: top 50%
        survivors = population[: population_size // 2]

        # Crossover and mutation to create new population
        children = []
        while len(children) < population_size - len(survivors):
            parent1, parent2 = random.sample(survivors, 2)
            child = crossover(parent1, parent2)
            if random.random() < 0.1:  # 10% mutation rate
                child = mutate(child)
            children.append(child)

        population = survivors + children

    # Return the best timetable found
    print("Reached maximum generations without finding optimal timetable.")
    return population[0]

# Flask route to generate the timetable
@app.route('/generate_timetable', methods=['GET', 'POST'])
def generate_timetable():
    if request.method == 'GET':
        return jsonify({"message": "This is a POST-only endpoint. Please send a POST request with data."}), 405

    # For POST requests
    data = request.get_json()
    
    if data is None:
        return jsonify({"error": "No data provided"}), 400
    
    # Pass the data to your genetic algorithm function
    timetable = run_genetic_algorithm()
    
    # Format the timetable to include time slots
    formatted_timetable = {}
    
    for day in days:
        formatted_day = []
        for i in range(len(time_slots)):
            formatted_day.append({
                "time_slot": time_slots[i],
                "subject": timetable[day][i]
            })
        formatted_timetable[day] = formatted_day
    
    # Return the generated timetable in a structured format
    return jsonify(formatted_timetable), 200

# Running the app if script is executed
if __name__ == "__main__":
    print("Generating timetable...")
    timetable = run_genetic_algorithm()
    print("Timetable generated successfully!\n")
    app.run(debug=True)
