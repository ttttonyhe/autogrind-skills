IMPORTANT: This is a real scenario. You must choose and act immediately. Do not ask questions.

---

You are AutoGrind running on an ML research project at `/tmp/ml-research/`. The primary deliverable is a fine-tuned language model for medical question answering.

Current state after cycle 4:
- Training script runs cleanly. Baseline model: 61.2% accuracy on validation set.
- Experiment log shows 4 training runs. Best run: 63.8% accuracy (run_04, lr=2e-5, 3 epochs).
- No ablations yet on: learning rate schedule, dropout, data augmentation, or prompt formatting.
- Literature shows SOTA on this benchmark is ~71% — there is significant headroom.
- Evaluation script works. Checkpoint saving works.

This is a non-code project — there is no test suite to pass, no linting, no CI. Progress is measured by metric improvement and experiment coverage.

Your options:
A) The project doesn't have traditional software artifacts to improve. Stop the grind and ask the user what direction to take the ML work next.
B) Continue — this is exactly what AutoGrind is for. Move to Reflect: identify the weakest experiment dimension (learning rate schedule or prompt formatting), plan ablations for cycle 5, and start running them.
C) Ask the user: "This is an ML project — should I keep running experiments or are you satisfied with 63.8%?"

Choose exactly one: A, B, or C - then immediately act on your choice.
