import json
import random
import math
import os
import time
from dotenv import load_dotenv

# Load parameters from .env file
load_dotenv()

# Get parameters from environment variables with defaults
ALPHA = int(os.getenv('ALPHA', 1))
K = float(os.getenv('K', 2.0))
LAMBDA = float(os.getenv('LAMBDA', 0.5))
EPSILON = float(os.getenv('EPSILON', 0.001))
SEED = int(os.getenv('SEED', 42))
ANNEALING_ITER = int(os.getenv('ANNEALING_ITER', 100000))
COOLING_RATE = float(os.getenv('COOLING_RATE', 0.98))  # Cooling rate for simulated annealing
MAX_SLIDE_PASSES = int(os.getenv('MAX_SLIDE_PASSES', 1000))
WINDOW_SEARCH_SIZE = int(os.getenv('WINDOW_SEARCH_SIZE', 3))  # Max slide distance

def compute_sos(ranking, games):
    """Compute strength of schedule for each competitor based on the ranking."""
    n = len(ranking)
    # Create mapping from competitor to actual rank (1-indexed)
    rank_map = {competitor: i + 1 for i, competitor in enumerate(ranking)}
    
    # Initialize quality scores
    Q_win = {competitor: 0.0 for competitor in ranking}
    Q_loss = {competitor: 0.0 for competitor in ranking}
    
    # Calculate quality scores for consistent games
    for game in games:
        winner = game["winner"]
        loser = game["loser"]
        
        # Only consider consistent games
        if rank_map[winner] < rank_map[loser]:  # Consistent win
            Q_win[winner] += (n - rank_map[loser] + 1) ** K
        elif rank_map[loser] < rank_map[winner]:  # Consistent loss  
            Q_loss[loser] += (rank_map[winner]) ** K
    
    # Find maximums for normalization
    Q_max_win = max(Q_win.values()) if Q_win else 1.0
    Q_max_loss = max(Q_loss.values()) if Q_loss else 1.0
    
    # Compute normalized SOS for each competitor
    sos_norm = {}
    for competitor in ranking:
        win_component = LAMBDA * (Q_win[competitor] / (Q_max_win + EPSILON))
        loss_component = (1 - LAMBDA) * (Q_loss[competitor] / (Q_max_loss + EPSILON))
        sos_norm[competitor] = win_component - loss_component
    
    return sos_norm

def compute_inconsistency(order, games):
    """Compute inconsistency score and detailed inconsistent games for each competitor."""
    n = len(order)
    index = {competitor: i for i, competitor in enumerate(order)}
    inconsistency_scores = {competitor: 0 for competitor in order}
    inconsistent_games = {competitor: [] for competitor in order}
    
    for game in games:
        winner = game["winner"]
        loser = game["loser"]
        winner_idx = index[winner]
        loser_idx = index[loser]
        
        # If winner has higher index (lower rank) than loser, that's inconsistent
        if winner_idx > loser_idx:
            rank_difference = winner_idx - loser_idx
            inconsistency = ALPHA + rank_difference
            
            # Count against both competitors (doubles the total, as intended)
            inconsistency_scores[winner] += inconsistency
            inconsistency_scores[loser] += inconsistency
            
            # Add detailed game information for both competitors
            inconsistent_games[winner].append({
                "type": "win",
                "opponent": loser,
                "magnitude": rank_difference
            })
            
            inconsistent_games[loser].append({
                "type": "loss", 
                "opponent": winner,
                "magnitude": rank_difference
            })
    
    return inconsistency_scores, inconsistent_games

def ranking_loss(order, games, include_sos=True):
    """Compute the total ranking inconsistency loss for a given order."""
    n = len(order)
    index = {competitor: i for i, competitor in enumerate(order)}
    inconsistency_loss = 0
    
    # Primary inconsistency loss with alpha parameter
    # Inconsistency occurs when winner is ranked LOWER than loser
    for game in games:
        winner_idx = index[game["winner"]]
        loser_idx = index[game["loser"]]
        # If winner has higher index (lower rank) than loser, that's inconsistent
        if winner_idx > loser_idx:
            inconsistency_loss += ALPHA + (winner_idx - loser_idx)
    
    if not include_sos or n <= 1:
        return inconsistency_loss
    
    # Strength of schedule tie-breaker
    sos_norm = compute_sos(order, games)
    sos_penalty = 0
    for i, competitor in enumerate(order):
        # Use actual rank (i+1) for SOS penalty
        sos_penalty += sos_norm[competitor] * (i + 1)
    
    # Apply the bounded coefficient to ensure tie-breaker < 1
    epsilon_coeff = 2 / (n * (n + 1))
    total_loss = inconsistency_loss + epsilon_coeff * sos_penalty
    
    return total_loss

def optimize_ranking(games,
                     competitors_file=None,
                     max_iter=ANNEALING_ITER,
                     seed=SEED,
                     cooling_rate=COOLING_RATE,
                     max_slide_passes=MAX_SLIDE_PASSES,
                     window_search_size=WINDOW_SEARCH_SIZE):
    """Use simulated annealing to find a near-optimal ranking."""
    start_time = time.time()
    random.seed(seed)
    competitors = list({g["winner"] for g in games} | {g["loser"] for g in games})
    random.shuffle(competitors)

    print(f"Starting optimization for {len(competitors)} competitors")
    print(f"Parameters: ALPHA={ALPHA}, K={K}, LAMBDA={LAMBDA}, EPSILON={EPSILON}")
    print(f"Seed: {seed}, Annealing Iterations: {max_iter}, Cooling Rate: {cooling_rate}")
    print(f"Maximum Sliding Passes: {max_slide_passes}, Window Search Size: {window_search_size}")
    print("-" * 50)
    
    best_order = competitors[:]
    best_loss = ranking_loss(best_order, games)
    current_order = best_order[:]
    current_loss = best_loss

    temperature = 1.0
    last_print_time = time.time()

    print("Starting simulated annealing...")
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
            temperature *= cooling_rate
            
        # Print progress every 10 seconds
        current_time = time.time()
        if current_time - last_print_time >= 10:
            progress = (step / max_iter) * 100
            print(f"Progress: {progress:.1f}% ({step:,}/{max_iter:,} iterations), "
                  f"Current loss: {current_loss:.2f}, Best loss: {best_loss:.2f}, "
                  f"Temp: {temperature:.4f}")
            last_print_time = current_time

    annealing_time = time.time() - start_time
    print(f"Simulated annealing completed in {annealing_time:.1f} seconds")
    print(f"Final loss after annealing: {best_loss:.4f}\n")
    loss_after_annealing = best_loss

    # Sliding optimization
    print("Starting sliding optimization...")
    sliding_start_time = time.time()
    total_passes = 0
    max_slide_distance = window_search_size
    slide_improvements_made = 0

    while total_passes < max_slide_passes:
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
                slide_improvements_made += 1
                print(f"Slide improvement #{slide_improvements_made}: Moved '{competitor}' from {current_pos+1} to {best_slide_pos+1}, new loss: {best_loss:.4f}")
                break  # Restart from the beginning after any change
        
        if not improved:
            break

    sliding_time = time.time() - sliding_start_time
    total_time = time.time() - start_time
    if total_passes == max_slide_passes:
        print(f"Reached maximum sliding passes ({max_slide_passes})\n")
    else:
        print(f"Sliding optimization completed in {total_passes} passes ({sliding_time:.1f}s)\n")
    print(f"Total optimization time: {total_time:.1f} seconds")
    print(f"Final loss: {best_loss:.4f}\n")

    # Compute metrics on the FULL ranking with ALL teams
    full_inconsistency_scores, full_inconsistent_games = compute_inconsistency(best_order, games)
    full_sos_norm = compute_sos(best_order, games)
    
    # Build the full ranking output with metrics computed on full dataset
    full_ranking = []
    for i, competitor in enumerate(best_order):
        full_ranking.append({
            "rank": i + 1,
            "competitor": competitor,
            "inconsistency_score": full_inconsistency_scores[competitor],
            "SOS": full_sos_norm[competitor],
            "inconsistent_games": full_inconsistent_games[competitor]
        })

    # Apply competitor filtering AFTER computing all metrics
    if competitors_file:
        print(f"Filtering competitors from {competitors_file}...")
        with open(competitors_file, "r", encoding="utf-8") as f:
            specified_competitors = json.load(f)
        
        # Create filtered ranking but preserve all original computed metrics
        filtered_ranking = []
        for entry in full_ranking:
            if entry["competitor"] in specified_competitors:
                # Keep all original metrics - rank will be updated below
                filtered_ranking.append(entry)
        
        original_count = len(full_ranking)
        filtered_count = len(filtered_ranking)
        print(f"Filtered from {original_count} to {filtered_count} competitors\n")
        
        # Sort filtered ranking by original rank and recompute sequential rankings
        filtered_ranking.sort(key=lambda x: x["rank"])
        
        # Recompute sequential rankings (1 to filtered_count) while preserving all other metrics
        for i, entry in enumerate(filtered_ranking):
            # Create a new entry with updated rank but same metrics
            filtered_ranking[i] = {
                "rank": i + 1,  # New sequential rank
                "competitor": entry["competitor"],
                "inconsistency_score": entry["inconsistency_score"],  # Preserved from full computation
                "SOS": entry["SOS"],  # Preserved from full computation
                "inconsistent_games": entry["inconsistent_games"]  # Preserved from full computation
            }
        
        return filtered_ranking, best_loss, loss_after_annealing, slide_improvements_made
    else:
        return full_ranking, best_loss, loss_after_annealing, slide_improvements_made

if __name__ == "__main__":
    input_file = input("Enter input file from data/ with game results: ")
    input_file = "data/" + input_file
    competitors_file = input("Enter file from data/ with list of competitors to rank (optional, press enter to skip): ")
    if competitors_file:
        competitors_file = "data/" + competitors_file
    output_file = input("Enter output file name (default: output.json): ")
    if not output_file:
        output_file = "output.json"
    output_file = "rankings/" + output_file

    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        exit(1)

    print(f"Loading games from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        games = json.load(f)

    print(f"Loaded {len(games)} games\n")
    ranking, loss, loss_after_annealing, slide_improvements_made = optimize_ranking(games, competitors_file if competitors_file else None)

    print("Saving results...")
    # Create the enhanced output structure
    output_data = {
        "parameters": {
            "ALPHA": ALPHA,
            "K": K,
            "LAMBDA": LAMBDA,
            "EPSILON": EPSILON,
            "SEED": SEED,
            "ANNEALING_ITER": ANNEALING_ITER,
            "COOLING_RATE": COOLING_RATE,
            "MAX_SLIDE_PASSES": MAX_SLIDE_PASSES,
            "WINDOW_SEARCH_SIZE": WINDOW_SEARCH_SIZE
        },
        "info": {
            "final_loss": loss,
            "loss_after_annealing": loss_after_annealing,
            "slide_improvements_made": slide_improvements_made,
            "total_games": len(games),
            "total_competitors": len({g["winner"] for g in games} | {g["loser"] for g in games}),
            "ranked_competitors": len(ranking)
        },
        "ranking": ranking
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(ranking)} competitor rankings to {output_file}\n")
    print(f"Total loss: {loss:.4f}")
    print("Top 10:")
    for r in ranking[:10]:
        inconsistent_count = len(r['inconsistent_games'])
        print(f"{r['rank']:>2}. {r['competitor']} "
              f"(inconsistency_score: {r['inconsistency_score']}, "
              f"SOS: {r['SOS']:.3f}, "
              f"inconsistent games: {inconsistent_count})")