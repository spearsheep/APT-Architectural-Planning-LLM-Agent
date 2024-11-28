# APT: Architectural Planning and Text-to-Blueprint Construction Using Large Language Models for Open-World Agents

**Authors**: Jun Yu Chen, Tao Gao

---

## Overview

APT is an advanced framework that leverages Large Language Models (LLMs) to enable autonomous agents to construct complex and creative structures within the Minecraft environment. Unlike previous approaches that focus on skill-based tasks or rely on image-based diffusion models for voxel structures, APT utilizes the intrinsic spatial reasoning capabilities of LLMs.

By employing **chain-of-thought decomposition** alongside **multimodal inputs**, the framework generates detailed architectural layouts and blueprints. This allows the agent to execute tasks under zero-shot or few-shot learning scenarios.

## Features

- **LLM-Driven Spatial Reasoning**: Utilizes GPT-based LLMs for advanced spatial planning.
- **Chain-of-Thought Decomposition**: Breaks down complex construction tasks into manageable steps.
- **Multimodal Input Integration**: Combines textual and visual instructions for comprehensive understanding.
- **Memory and Reflection Modules**: Facilitates lifelong learning, adaptive refinement, and error correction.
- **Zero-Shot/Few-Shot Learning**: Executes tasks without extensive pre-training.
- **Complex Structure Generation**: Builds intricate structures with functionalities like Redstone-powered systems.
- **Emergent Behaviors**: Exhibits unexpected behaviors such as scaffolding, showcasing advanced problem-solving techniques.

## Benchmark and Evaluation

We introduce a comprehensive benchmark comprising diverse construction tasks designed to test:

- Creativity
- Spatial reasoning
- Adherence to in-game rules
- Effective integration of multimodal instructions

Experimental results demonstrate the agent's ability to accurately interpret extensive instructions involving numerous items, positions, and orientations. A/B testing indicates that the inclusion of a memory module significantly enhances performance, emphasizing its role in continuous learning and experience reuse.
