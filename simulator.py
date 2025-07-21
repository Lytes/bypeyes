import json
import time

REPLAY_FILE = "./replay_logs/game_XXXXXX.jsonl"  # <-- you replace XXXXXX

def run_simulation(filepath):
    print(f"\n[Agent Simulator]\nLoading replay: {filepath}\n")

    with open(filepath, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        data = json.loads(line)
        print(f"--- TURN {data['turn']} ---")
        print(f"Player: {data['player_input']}\n")

        for agent_name, agent_data in data['agents'].items():
            print(f"[{agent_name}]")
            print(f"  Note: {agent_data['note']}")
            print(f"  Reply: {agent_data['reply']}")
            print(f"  Guess: {agent_data['guess']}")
            print("")

        print(f"Outcome after turn: {data['outcome']}")
        print("\n" + "-"*50 + "\n")
        time.sleep(0.5)  # tiny delay for readability

    print("\n[Simulation Complete]")

if __name__ == "__main__":
    run_simulation(REPLAY_FILE)
