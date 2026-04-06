# Model Tree Snapshot

This document is meant to be published as a reference example, not just kept as a private snapshot.

It documents the currently observed model tree structure used in the reference stack because the tree shape itself is useful:

- it shows how LLM, diffusion, and cache assets are separated
- it shows that some model families are single files while others are small directories
- it shows where multimodal layouts use both `model.gguf` and `mmproj.gguf`
- it shows where placeholder directories are intentionally kept for future assets
- it shows where symlinks are used to preserve compatibility without storing duplicate large files

It does not contain secrets, credentials, or private endpoints.

It also shows a useful operational pattern:

- active assets can coexist with archived assets
- symlinks can preserve compatibility while avoiding duplicate large files

Read this tree as a concrete example of a workable layout, not as a required universal standard.

```text
/mnt/ai-models/
├── cache
│   ├── hf
│   │   ├── hub
│   │   └── transformers
│   └── llama.cpp
├── llm
│   ├── gemma-4-26B-A4B-it-UD-Q5_K_XL.gguf
│   ├── GLM-4.7-Flash-UD-Q6_K_XL.gguf
│   ├── nomic-embed-text-v1.5.Q4_K_M.gguf
│   ├── nomic-embed-text-v2-moe.Q8_0.gguf
│   ├── nvidia_Nemotron-3-Nano-30B-A3B-Q5_K_L.gguf
│   ├── O-Researcher-72B-rl.i1-Q4_K_M.gguf
│   ├── Qwen3.5-27B-UD-Q6_K_XL.gguf
│   ├── Qwen3.5-35B-A3B-UD-Q6_K_XL.gguf
│   ├── Qwen3.5-9B-UD-Q6_K_XL.gguf
│   ├── Qwen3-Coder-Next-UD-Q4_K_XL.gguf
│   ├── Qwen3-Embedding-8B-Q6_K.gguf
│   ├── Qwen3-Embedding-8B-Q8_0.gguf
│   ├── Qwen3-VL-30B-A3B-Instruct-Q4_K_M
│   │   ├── mmproj.gguf
│   │   └── model.gguf
│   ├── Qwen3-VL-8B-Instruct-abliterated-v2
│   │   ├── mmproj.gguf
│   │   └── model.gguf
│   ├── Qwen3-VL-Embedding-8B-Q8_0
│   │   ├── mmproj.gguf -> /mnt/ai-models/llm/Qwen3-VL-8B-Instruct-abliterated-v2/mmproj.gguf
│   │   └── model.gguf
│   ├── Qwen3-VL-Reranker-8B
│   │   ├── mmproj.gguf
│   │   └── model.gguf
│   ├── speakleash_Bielik-11B-v3.0-Instruct-Q8_0.gguf
│   └── tinyllama-1.1b-chat-v1.0.Q4_0.gguf
└── sd
    ├── archive
    │   ├── 2026-04-05-manifest
    │   │   └── model-cleanup.txt
    │   ├── 2026-04-05-optional-image-assets
    │   │   ├── ARCHIVE-MANIFEST.txt
    │   │   └── checkpoints
    │   │       └── Animagine_XL_3.1.safetensors
    │   └── 2026-04-05-video-assets
    │       ├── ARCHIVE-MANIFEST.txt
    │       ├── checkpoints
    │       ├── clip
    │       ├── unet
    │       └── vae
    ├── checkpoints
    │   ├── Juggernaut_XL_Lightning.safetensors
    │   ├── ltx-2.3-22b-dev-fp8.safetensors
    │   ├── put_checkpoints_here
    │   └── RealVisXL_V4.0_Lightning.safetensors
    ├── clip
    │   ├── mistral_3_small_flux2_bf16.safetensors -> mistral_3_small_flux2_fp8.safetensors
    │   ├── mistral_3_small_flux2_fp8.safetensors
    │   ├── put_clip_or_text_encoder_models_here
    │   ├── qwen_3_8b_fp4mixed.safetensors -> ../text_encoders/qwen_3_8b_fp4mixed.safetensors
    │   └── t5xxl_fp8_e4m3fn.safetensors
    ├── controlnet
    │   └── put_controlnets_and_t2i_here
    ├── custom_nodes_models
    ├── embeddings
    │   └── put_embeddings_or_textual_inversion_concepts_here
    ├── latent_upscale_models
    ├── loras
    │   ├── Flux2TurboComfyv2.safetensors -> Flux_2-Turbo-LoRA_comfyui.safetensors
    │   ├── Flux_2-Turbo-LoRA_comfyui.safetensors
    │   ├── ltxv
    │   │   └── ltx2
    │   │       └── ltx-2.3-22b-distilled-lora-384.safetensors
    │   └── put_loras_here
    ├── text_encoders
    │   ├── gemma_3_12B_it_fp4_mixed.safetensors
    │   ├── mistral_3_small_flux2_bf16.safetensors -> /mnt/ai-models/sd/clip/mistral_3_small_flux2_bf16.safetensors
    │   ├── mistral_3_small_flux2_fp8.safetensors -> ../clip/mistral_3_small_flux2_fp8.safetensors
    │   └── qwen_3_8b_fp4mixed.safetensors
    ├── unet
    │   ├── flux2_dev_fp8mixed.safetensors
    │   └── flux-2-klein-9b-Q5_K_M.gguf
    ├── upscale_models
    │   ├── 4x-UltraSharp.pth
    │   └── put_esrgan_and_other_upscale_models_here
    └── vae
        ├── flux2-vae.safetensors
        └── put_vae_here
```
