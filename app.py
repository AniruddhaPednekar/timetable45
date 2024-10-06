from flask import Flask, jsonify, request
import random
import copy

app = Flask(__name__)

# Define your data
subjects = [
    "Deep Learning", 
    "Big Data Analytics", 
    "Neural Network and Fuzzy System", 
    "Blockchain", 
    "CyberSecurity"
]
labs = [
    "Deep Learning Lab", 
    "Blockchain Lab", 
    "Neural Network and Fuzzy System Lab", 
    "Big Data Analytics Lab"
]
project_slot = "Major Project"
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Updated time slots to start at 9:15 and end at 5:15
time_slots = [
    "9:15-10:15", 
    "10:15-11:15", 
    "11:15-11:30 (Break)",
    "11:30-12:30", 
    "12:30-1:30", 
    "1:30-2:15 (Break)",
    "2:15-3:15", 
    "3:15-4:15", 
    "4:15-5:15"
]

# Define a timetable structure (empty initially)
def create_empty_timetable():
    return {day: [""] * len(time_slots) for day in days}

# Fitness function to evaluate a timetable
def fitness(timetable):
    score = 0
    # Check that breaks are respected
    for day in days:
        if timetable[day][2] != "Break" or timetable[day][5] != "Break":
            return 0  # Timetable doesn't respect break times
        
    # Check that there are no duplicate subjects in a day
    for day in days:
        subjects_scheduled = set()
        for slot in timetable[day]:
            if slot != "Break" and slot != "":
                if slot in subjects_scheduled:
                    return 0
                subjects_scheduled.add(slot)
        
    # Check that "Major Project" appears exactly 3 times per week
    major_project_count = sum([timetable[day].count(project_slot) for day in days])
    if major_project_count != 3:
        return 0
    
    # Check that every subject and lab appears at least once
    all_subjects = subjects + labs
    for item in all_subjects:
        if not any(item in timetable[day] for day in days):
            return 0
    
    # Each valid timetable gains a positive score
    score += 1
    return score

# Generate a random timetable
def generate_random_timetable():
    timetable = create_empty_timetable()
    
    # Fill in the subjects and labs randomly
    all_classes = subjects + labs
    for day in days:
        slots_filled = 0
        
        # Add project slots 3 times per week
        if sum([timetable[d].count(project_slot) for d in days]) < 3 and random.choice([True, False]):
            project_index = random.randint(0, len(time_slots) - 1)
            while timetable[day][project_index] != "":
                project_index = random.randint(0, len(time_slots) - 1)
            timetable[day][project_index] = project_slot
            slots_filled += 1
        
        # Fill other slots with classes
        for i in range(len(time_slots)):
            if timetable[day][i] == "" and time_slots[i] not in ["11:15-11:30 (Break)", "1:30-2:15 (Break)"]:
                timetable[day][i] = random.choice(all_classes)
                all_classes.remove(timetable[day][i])
                if not all_classes:
                    all_classes = subjects + labs  # Reset subjects/labs pool when exhausted
                
    # Add the breaks
    for day in days:
        timetable[day][2] = "Break"
        timetable[day][5] = "Break"
        
    return timetable

# Crossover between two timetables
def crossover(timetable1, timetable2):
    new_timetable = copy.deepcopy(timetable1)
    crossover_day = random.choice(days)
    new_timetable[crossover_day] = timetable2[crossover_day]
    return new_timetable

# Mutation to introduce variability
def mutate(timetable):
    day_to_mutate = random.choice(days)
    time_slot_to_mutate = random.choice(range(len(time_slots)))
    
    if time_slots[time_slot_to_mutate] not in ["11:15-11:30 (Break)", "1:30-2:15 (Break)"]:
        possible_classes = subjects + labs + [project_slot]
        timetable[day_to_mutate][time_slot_to_mutate] = random.choice(possible_classes)
    
    return timetable

# Main genetic algorithm function
def run_genetic_algorithm(data, population_size=20, generations=500):
    # Create initial population
    population = [generate_random_timetable() for _ in range(population_size)]
    
    for generation in range(generations):
        population = sorted(population, key=lambda x: fitness(x), reverse=True)
        
        if fitness(population[0]) == 1:
            return population[0]  # Found an optimal solution
        
        # Selection (top 50% will survive)
        population = population[:population_size // 2]
        
        # Crossover and mutation to create new offspring
        new_population = []
        while len(new_population) < population_size:
            parent1 = random.choice(population)
            parent2 = random.choice(population)
            
            child = crossover(parent1, parent2)
            if random.random() < 0.1:  # 10% mutation rate
                child = mutate(child)
            
            new_population.append(child)
        
        population = new_population
        
    # Return the best timetable found
    return sorted(population, key=lambda x: fitness(x), reverse=True)[0]

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
    timetable = run_genetic_algorithm(data)
    
    # Return the generated timetable as a JSON response
    return jsonify(timetable), 200



# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
