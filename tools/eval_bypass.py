import json
import os
import sys
# Ensure project root is on sys.path so `from brain import OSCENBrain` works when
# running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from brain import OSCENBrain

def run_evaluation(total=200):
    b = OSCENBrain(scale=0.001, seed=1)
    inputs = [
        'hello',
        'how are you?',
        'what is the weather?',
        'tell me a joke',
        'remind me of our last topic',
    ]
    counts = {'local':0,'llm':0,'cached':0}
    non_neonatal = 0
    for i in range(total):
        text = inputs[i % len(inputs)]
        res = b.process_input_v01(text)
        p = res.get('path')
        if not isinstance(p, str):
            p = 'unknown'
        counts[p] = counts.get(p, 0) + 1
        if p == 'local' and res.get('response') not in ('[silence]', '[unknown]'):
            non_neonatal += 1
    out = {
        'counts': counts,
        'non_neonatal_local': non_neonatal,
        'total': total,
        'local_rate': counts.get('local',0)/total
    }
    print(json.dumps(out))

if __name__ == '__main__':
    run_evaluation(total=200)
