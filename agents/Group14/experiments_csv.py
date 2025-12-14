import subprocess
import os
import random
import time
import csv
from datetime import datetime

AGENT = "agents.Group14.MyAgent MyAgent"
OPPONENT = "agents.Group14.MyAgentReroot MyAgentReroot"

SEEDS = [0, 1, 2]
GAMES_PER_SEED = 20
LOG_DIR = "agents/Group14/logs"

os.makedirs(LOG_DIR, exist_ok=True)


def run_game(seed: int, game_id: int):
    logfile = f"{LOG_DIR}/game_{game_id}.log"

    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    
    
    # Extract winner from log file
    try:
        with open(logfile, 'r') as f:
            lines = f.readlines()
        
        # Find winner line (last line: "winner,{agent_name},WIN")
        if lines:
            winner_line = lines[-1].strip()
            if winner_line.startswith("winner,"):
                parts = winner_line.split(",")
                if len(parts) >= 2:
                    return parts[1]
    except Exception as e:
        print(f"Error reading log file: {e}")
        
    return ""
    
    


def main():
    print("Running experiments...")
    print(f"Agent: {AGENT}")
    print(f"Opponent: {OPPONENT}")
    print("------------------------")

    total_games = 0
    total_wins = 0
    total_time = 0
    
    agent_name = AGENT.split()[-1]
    opponent_name = OPPONENT.split()[-1]

    for seed in SEEDS:
        print(f"Seed {seed}")
        for game in range(1, GAMES_PER_SEED + 1):
            winner = run_game(seed, game)
            total_games += 1
            
            if "reroot" not in winner.lower():
                total_wins += 1
               

    win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    avg_game_time = total_time / total_games if total_games > 0 else 0
    
    # Write results to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"agents/Group14/logs/results_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Agent', 'Opponent', 'Total Games', 'Total Wins', 'Win Rate (%)', 'Avg Game Time (s)'])
        writer.writerow([agent_name, opponent_name, total_games, total_wins, f"{win_rate:.2f}", f"{avg_game_time:.2f}"])
    
    print("------------------------")
    print(f"All experiments finished.")
    print(f"Total Games: {total_games}")
    print(f"Total Wins: {total_wins}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Average Game Time: {avg_game_time:.2f}s")
    print(f"Results saved to: {csv_filename}")


if __name__ == "__main__":
    main()
