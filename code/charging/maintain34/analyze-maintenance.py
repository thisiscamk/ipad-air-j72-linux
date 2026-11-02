#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Analyze fresh gauge vectors across charging and protective holds."""
import argparse
import json
from pathlib import Path


def analyze(capture):
    capture = Path(capture)
    final = json.loads((capture / 'final.json').read_text())
    assert final['ended_by'] == 'host_deadline' and final['observed_controller_s'] >= 3600
    state = final['worker']
    assert all(state[k] == v for k, v in {'enabled': '0', 'active': '0', 'armed': '0',
                                         'restore_failed': '0', 'fault': '0', 'restored': '1'}.items())
    assert final['independent']['reg_04c0'] == '02'
    rows = [json.loads(line) for line in (capture / 'samples.jsonl').read_text().splitlines()]
    assert len(rows) > 100
    unique = {}
    resume_events = []
    previous = None
    for row in rows:
        value = row['worker']
        assert value['fault'] == '0' and value['restore_failed'] == '0'
        if previous:
            assert row['elapsed_s'] > previous['elapsed_s']
            old = previous['worker']
            if old['active'] == '0' and value['active'] == '1' and int(value['cycles']) > int(old['cycles']):
                resume_events.append({'host_elapsed_s': row['elapsed_s'], 'cycle': int(value['cycles']),
                                      'soc': int(value['guard_soc']), 'temperature_tenthC': int(value['guard_temp_tenthC']),
                                      'voltage_uV': int(value['guard_voltage_uV'])})
        stamp = int(value['guard_at_ms'])
        if stamp:
            vector = tuple(int(value['guard_' + name]) for name in
                           ('present', 'soc', 'temp_tenthC', 'voltage_uV', 'current_uA'))
            assert vector[0] == 1 and 10 <= vector[1] <= 100
            assert 200 <= vector[2] <= 500 and 3500000 <= vector[3] <= 4400000
            assert abs(vector[4]) <= 1500000
            if value['active'] == '1':
                assert vector[1] <= 95 and vector[2] <= 380 and vector[3] <= 4200000
            if stamp in unique:
                assert unique[stamp] == vector, 'Conflicting duplicate gauge timestamp'
            unique[stamp] = vector
        previous = row
    data = sorted(unique.items())
    gaps = [(b[0] - a[0]) / 1000 for a, b in zip(data, data[1:])]
    span = (data[-1][0] - data[0][0]) / 1000
    assert span >= final['observed_controller_s'] - 10
    assert all(0 < gap <= 4.5 for gap in gaps), 'Incomplete fresh-vector coverage'
    area = sum((b[0] - a[0]) / 1000 * (a[1][4] + b[1][4]) / 2
               for a, b in zip(data, data[1:]))
    mean = area / span
    return {'status': 'COMPLETE_FAULT_FREE_RESTORATION_PASS',
            'observation_s': final['observed_controller_s'], 'fresh_vectors': len(data),
            'coverage_s': round(span, 3), 'max_sample_gap_s': max(gaps),
            'time_weighted_current_uA': round(mean, 3),
            'estimated_net_mAh_over_coverage': round(area / 3600000, 6),
            'net_positive_50mA_margin': mean >= 50000,
            'current_min_uA': min(v[4] for _, v in data), 'current_max_uA': max(v[4] for _, v in data),
            'max_temperature_tenthC': max(v[2] for _, v in data),
            'soc_first': data[0][1][1], 'soc_last': data[-1][1][1],
            'cycles': int(state['cycles']), 'pauses': int(state['pauses']),
            'automatic_restarts': resume_events,
            'final_input_limit_baseline': final['independent']['reg_04c0'],
            'source_scope': 'Pi-supervised owner-qualified JCH377 only',
            'unattended_or_general_charger_qualified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    print(json.dumps(analyze(parser.parse_args().capture), indent=2))
