import random
import json

num_teams = 10
num_games = 1000

def does_a_beat_b(a_strength, b_strength):
    prob = a_strength / (a_strength + b_strength)
    return random.random() < prob

team_names = [ f"Team {x}" for x in range(1, num_teams+1) ]
strengths = [ random.random() for x in range(0, num_teams) ]
results = []

for i in range(num_teams):
    print(f"{team_names[i]}: {strengths[i]}")

for i in range(num_games):
    a = random.randint(0, 9)
    b = random.randint(0, 9)
    while b == a:
        b = random.randint(0, 9)
    
    a_beats_b = does_a_beat_b(strengths[a], strengths[b])
    if a_beats_b:
        results.append((team_names[a], team_names[b]))
    else:
        results.append((team_names[b], team_names[a]))

formatted_results = [ {"winner": game[0], "loser": game[1]} for game in results]

output_filename = input("Enter output filename (default: simulated_results.json): ")
if not output_filename:
    output_filename = "simulated_results.json"

with open(f"data/{output_filename}", "w", encoding="utf-8") as f:
    json.dump(formatted_results, f, indent=2)
    
    