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


## Installation


### Install Packages and Environments

#### Install Node.js and npm
Ensure you have Node.js installed on your machine. If not, follow these steps:
1. Visit the [Node.js Official Site](https://nodejs.org/).
2. Download and install the appropriate version for your operating system.

#### Install Mineflayer
1. Open your terminal or command prompt.
2. Run the following command to install Mineflayer:
   ```bash
   npm install mineflayer

For more information, you can find the detailed tutorial at the [Mineflayer GitHub Repository](https://github.com/PrismarineJS/mineflayer).

### Install Minecraft 

#### Requirements
- Minecraft Java Edition
- A valid Mojang or Microsoft account

#### Steps to set up Minecraft

1. Visit the [Minecraft Official Website](https://www.minecraft.net/).
2. Navigate to the **"Get Minecraft"** section.
3. Select your platform (Windows, macOS, or Linux) and choose **Java Edition**.
4. Follow the instructions to purchase (if you don't already own it) and download the launcher.
5. Install the launcher and log in using your Mojang or Microsoft account.
6. Start the launcher, select the release version compatible with Mineflayer. For our test setup, we used version `1.17`. Then click **Play** to load the game.
7. Create a new world and ensure the following settings are applied:
   - Set the game mode to **Creative**.
   - Enable **Cheats** to allow command usage required for our package.
8. Once the world loads, open the **Pause Menu**, click **Open to LAN**, and take note of the **Port Number** displayed. This will be required for later usage.

For more detailed instructions, visit the [Minecraft Help Center](https://help.minecraft.net/).



## User Guide
1. For convenient usage, refer to the `APTAgent.ipynb` file for detailed demo instructions. This notebook provides step-by-step guidance to experiment with our agent framework.  
2. Please ensure you use your own OpenAI API key for authentication.


## Citation
If you find our agent framework or benchmark meaningful, please consider citing us!
```bibtex
@misc{chen2024aptarchitecturalplanningtexttoblueprint,
      title={APT: Architectural Planning and Text-to-Blueprint Construction Using Large Language Models for Open-World Agents}, 
      author={Jun Yu Chen and Tao Gao},
      year={2024},
      eprint={2411.17255},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2411.17255}, 
}
```


