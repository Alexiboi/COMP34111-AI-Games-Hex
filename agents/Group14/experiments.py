import subprocess
import os
import random
import time
import csv
from datetime import datetime
import argparse

parser = argparse.ArgumentParser(description="Run experiments for Hex agents")
parser.add_argument("-a", required=True, help="Player 1 agent name (e.g MyAgent)")
parser.add_argument("-o", required=True, help="Player 2 agent name (e.g MyAgentTerminal)")
parser.add_argument("-g", type=int, required=True, help="Number of games to play (even)")
args = parser.parse_args()

AGENTNAME = args.a
OPPONENTNAME = args.o
GAMES = args.g

if GAMES % 2 == 1:
    raise KeyError("Games must be even")

AGENT = f"agents.Group14.{AGENTNAME} {AGENTNAME}"
# OPPONENT = f"agents.Group14.{OPPONENTNAME} {OPPONENTNAME}"
OPPONENT = f"agents.Group14.{OPPONENTNAME} {OPPONENTNAME}"

LOG_DIR = "agents/Group14/logs"

os.makedirs(LOG_DIR, exist_ok=True)


def run_game(game_id: int, agentFirst):
    logfile = f"{LOG_DIR}/game_{game_id}.log"


    start_time = time.time()
    subprocess.run(
        [
            "python", "Hex.py",
            "-p1", AGENT if agentFirst else OPPONENT,
            "-p2", OPPONENT if agentFirst else AGENT,
            "-p1Name", AGENTNAME if agentFirst else OPPONENTNAME,
            "-p2Name", OPPONENTNAME if agentFirst else AGENTNAME,
            "-l", logfile
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
    game_time = time.time() - start_time
    
    # Extract winner from log file
    winner = None
    try:
        with open(logfile, 'r') as f:
            lines = f.readlines()
        
        # Find winner line (last line: "winner,{agent_name},WIN")
        if lines:
            winner_line = lines[-1].strip()
            if winner_line.startswith("winner,"):
                parts = winner_line.split(",")
                if len(parts) >= 2:
                    winner = parts[1]
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    return winner, game_time


def main():
    print("Running experiments...")
    print(f"Agent: {AGENT}")
    print(f"Opponent: {OPPONENT}")
    print("------------------------")

    total_games = 0
    total_wins = 0
    total_time = 0
    
    try:
        for game in range(1, GAMES + 1):

            winner, game_time = run_game(game, game <= GAMES/2)
            total_games += 1
            total_time += game_time
            
            if winner == AGENTNAME:
                total_wins += 1
                result = "WIN"
            else:
                result = "LOSS"
            
            print(f"  Game {game} done - {result} ({game_time:.2f}s)")
            
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received — stopping early.")

    win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    avg_game_time = total_time / total_games if total_games > 0 else 0
    
    # Write results to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"agents/Group14/logs/{AGENTNAME}vs{OPPONENTNAME}_results_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Agent', 'Opponent', 'Total Games', 'Total Wins', 'Win Rate (%)', 'Avg Game Time (s)'])
        writer.writerow([AGENTNAME, OPPONENTNAME, total_games, total_wins, f"{win_rate:.2f}", f"{avg_game_time:.2f}"])
    
    print("------------------------")
    print(f"All experiments finished.")
    print(f"Total Games: {total_games}")
    print(f"Total Wins: {total_wins}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Average Game Time: {avg_game_time:.2f}s")
    print(f"Results saved to: {csv_filename}")


if __name__ == "__main__":
    main()
