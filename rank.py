import json
import random
import math
import os

def compute_sos(ranking, games):
    """Compute strength of schedule for each competitor based on the ranking."""
    n = len(ranking)
    # Create mapping from competitor to actual rank (1-indexed)
    rank_map = {team: i + 1 for i, team in enumerate(ranking)}
    sos = {team: 0.0 for team in ranking}
    opponent_counts = {team: 0 for team in ranking}
    
    # Count opponents for each competitor
    for game in games:
        winner = game["winner"]
        loser = game["loser"]
        # Use actual ranks: (n - rank_j) / n
        sos[winner] += (n - rank_map[loser]) / n
        sos[loser] += (n - rank_map[winner]) / n
        opponent_counts[winner] += 1
        opponent_counts[loser] += 1
    
    # Normalize by number of opponents
    for team in sos:
        if opponent_counts[team] > 0:
            sos[team] /= opponent_counts[team]
        else:
            sos[team] = 0.5  # Neutral value for competitors with no games
    
    return sos

def ranking_loss(order, games, include_sos=True):
    """Compute the total ranking inconsistency loss for a given order."""
    n = len(order)
    index = {team: i for i, team in enumerate(order)}
    inconsistency_loss = 0
    
    # Primary inconsistency loss
    for game in games:
        winner_idx = index[game["winner"]]
        loser_idx = index[game["loser"]]
        inconsistency_loss += max(0, 1 + winner_idx - loser_idx)
    
    if not include_sos or n <= 1:
        return inconsistency_loss
    
    # Strength of schedule tie-breaker
    sos = compute_sos(order, games)
    sos_penalty = 0
    for i, competitor in enumerate(order):
        # Use actual rank (i+1) not index (i) for SOS penalty
        sos_penalty += sos[competitor] * (i + 1)
    
    # Apply the bounded coefficient to ensure tie-breaker < 1
    epsilon = 2 / (n * (n + 1))
    total_loss = inconsistency_loss + epsilon * sos_penalty
    
    return total_loss

def optimize_ranking(games, competitors_file=None, max_iter=100000, seed=42):
    """Use simulated annealing to find a near-optimal ranking."""
    random.seed(seed)
    competitors = list({g["winner"] for g in games} | {g["loser"] for g in games})
    random.shuffle(competitors)
    
    best_order = competitors[:]
    best_loss = ranking_loss(best_order, games)
    current_order = best_order[:]
    current_loss = best_loss

    temperature = 1.0

    for step in range(max_iter):
        # Randomly swap two competitors
        i, j = random.sample(range(len(competitors)), 2)
        new_order = current_order[:]
        new_order[i], new_order[j] = new_order[j], new_order[i]

        new_loss = ranking_loss(new_order, games)
        delta = new_loss - current_loss

        # Accept new order if better or probabilistically if worse
        if delta < 0 or random.random() < math.exp(-delta / temperature):
            current_order = new_order
            current_loss = new_loss
            if new_loss < best_loss:
                best_loss = new_loss
                best_order = new_order

        # Gradually cool temperature
        if step % 1000 == 0:
            temperature *= 0.98

    # Sliding optimization
    max_total_passes = 1000
    total_passes = 0
    max_slide_distance = 3
    
    while total_passes < max_total_passes:
        total_passes += 1
        improved = False
        
        for current_pos, competitor in enumerate(best_order):
            best_slide_pos = current_pos
            best_slide_loss = best_loss
            
            # Try sliding up (to lower rank numbers)
            for slide_up in range(1, max_slide_distance + 1):
                new_pos = current_pos - slide_up
                if new_pos < 0:
                    break
                
                new_order = best_order[:]
                # Remove competitor from current position and insert at new position
                new_order.pop(current_pos)
                new_order.insert(new_pos, competitor)
                
                new_loss = ranking_loss(new_order, games)
                if new_loss < best_slide_loss:
                    best_slide_loss = new_loss
                    best_slide_pos = new_pos
            
            # Try sliding down (to higher rank numbers)  
            for slide_down in range(1, max_slide_distance + 1):
                new_pos = current_pos + slide_down
                if new_pos >= len(best_order):
                    break
                
                new_order = best_order[:]
                new_order.pop(current_pos)
                new_order.insert(new_pos, competitor)
                
                new_loss = ranking_loss(new_order, games)
                if new_loss < best_slide_loss:
                    best_slide_loss = new_loss
                    best_slide_pos = new_pos
            
            # If we found a better position for this competitor
            if best_slide_pos != current_pos:
                new_order = best_order[:]
                new_order.pop(current_pos)
                new_order.insert(best_slide_pos, competitor)
                
                best_order = new_order
                best_loss = best_slide_loss
                improved = True
                break  # Restart from the beginning after any change
        
        if not improved:
            break
    
    print(f"Sliding optimization completed in {total_passes} passes")
    print(f"Final loss: {best_loss:.4f}")

    if competitors_file:
        with open(competitors_file, "r", encoding="utf-8") as f:
            specified_competitors = json.load(f)
        best_order = [c for c in best_order if c in specified_competitors]
    ranking = [{"rank": i + 1, "competitor": c} for i, c in enumerate(best_order)]

    return ranking, best_loss

if __name__ == "__main__":
    input_file = input("Enter input file with game results: ")
    competitors_file = input("Enter file with list of competitors to rank (optional, press enter to skip): ")
    output_file = input("Enter output file name (default: output.json): ")
    if not output_file:
        output_file = "output.json"
    output_file = "rankings/" + output_file

    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        games = json.load(f)

    print(f"Loaded {len(games)} games...")
    ranking, loss = optimize_ranking(games, competitors_file if competitors_file else None)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ranking, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(ranking)} competitor rankings to {output_file}")
    print("\nTop 10:")
    for r in ranking[:10]:
        print(f"{r['rank']:>2}. {r['competitor']}")