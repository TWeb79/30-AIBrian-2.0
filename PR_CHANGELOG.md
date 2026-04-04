Changelog for feature work (April 2026)

Summary
-------
- Implemented theta→gamma coupling and a scalar GammaOscillator (brain/oscillations/gamma.py).
- Added ThetaGammaCoupler to compute phase-amplitude coupling.
- Implemented simple PING-style gamma scaffold (brain/oscillations/gamma_ping.py) and optional runtime integration via USE_PING_GAMMA.
- Wired gamma gain into STDP LTP scaling inside OSCENBrain.step().
- Added hippocampus_full (memory/hippocampus_full.py) and hippocampus_spiking (memory/hippocampus_spiking.py) scaffolds; OSCENBrain can select backends with USE_FULL_HIPPOCAMPUS / USE_SPIKING_HIPPOCAMPUS.
- Implemented laminar-inspired PV + SST inhibitory subpopulations per region (brain/regions/cortical_regions.py).
- Tightened Ollama model selection in config.py to avoid registering unknown models automatically.
- Added unit tests for gamma, gamma_ping, and hippocampus_spiking; total test count now 39 and all pass.

Files added
 - brain/oscillations/gamma.py
 - brain/oscillations/gamma_ping.py
 - memory/hippocampus_full.py
 - memory/hippocampus_spiking.py
 - tests/test_gamma.py
 - tests/test_gamma_ping.py
 - tests/test_hippocampus_spiking.py
 - PR_CHANGELOG.md

Files modified
 - brain/__init__.py (integration, STDP modulation, env flags)
 - brain/regions/cortical_regions.py (PV+SST)
 - config.py (LLM model selection)
 - ASSESSMENT1750.md (updated)

Notes
-----
The scaffolds aim to be safe, incremental, and unit-testable. They are not yet full biological implementations — further tuning and more detailed spiking models are future work.
