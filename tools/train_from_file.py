"""CLI helper: train brain vocabulary from TrainingFile.md

Usage: python tools/train_from_file.py --batch 200
"""
import argparse
import os
from api.config import brain


def main(batch_size: int = 200):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'TrainingFile.md'))
    if not os.path.exists(path):
        print("TrainingFile.md not found at", path)
        return
    with open(path, 'r', encoding='utf-8') as f:
        chunk = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunk.append(line)
            if len(chunk) >= batch_size:
                brain.process_input_v01(" ".join(chunk))
                chunk = []
        if chunk:
            brain.process_input_v01(" ".join(chunk))
    # Persist vocabulary so trained words reload on next start
    if hasattr(brain, 'persist_vocabulary'):
        brain.persist_vocabulary()
    print("Training run completed")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, default=200)
    args = parser.parse_args()
    main(args.batch)
