# ComfyUI-LumaAI-API
<p align="center">
  <img src="./assets/luma_logo.png" alt="LumaAI Logo" width="200">
</p>


This is a custom node for ComfyUI that allows you to use the Luma AI API directly in ComfyUI. Luma AI API is based on top of [Dream Machine](https://lumalabs.ai/dream-machine/api), which is a complete suite of models for image and video generation. For more information, see [Luma AI API Documentation](https://docs.lumalabs.ai/docs/api).

## Requirements

Before using this node, you need to have an LumaAI API key. Get one [here](https://lumalabs.ai/dream-machine/api). If you want to use images as input, you will need to host them. As a suggestion, you can use [ImgBB](https://api.imgbb.com/) to host your images.

## Installation

### Installing manually

1. Navigate to the `ComfyUI/custom_nodes` directory.

2. Clone this repository:
   ```
   git clone https://github.com/lumalabs/ComfyUI-LumaAI-API.git
   ```
   The path should be `ComfyUI/custom_nodes/ComfyUI-LumaAI-API/*`, where `*` represents all the files in this repo.
  
3. Install the dependencies:

  - If you are using Windows (ComfyUI portable) run: `.\python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\ComfyUI-LumaAI-API\requirements.txt`
  - If you are using Linux or MacOS, run: `cd ComfyUI-LumaAI-API && pip install -r requirements.txt` to install the dependencies.

4. If you don't want to expose your Luma API key, you can add it to the `config.ini` file and keep it empty in the node.

5. Start ComfyUI and enjoy using the LumaAI API node!

### Installing with ComfyUI-Manager

1. Open ComfyUI-Manager and install the LumaAI API node (ComfyUI-LumaAI-API).

### Installing with Comfy Registry

1. Run `comfy node registry-install comfyui-lumaai-api` to install the node.

## Nodes

Most of the nodes allow you to save locally the output video. If you keep the default `filename` (empty string), the video will be saved in the `outputs` folder using the `generation_id` as the name.

For images, the node will always save the image locally, but you can set the `filename` to save it with a custom name.

**Notes: Duration and resolution parameters are only supported for Ray 2 and Ray 2 Flash models.**

### LumaAIClient

This node is used to create a LumaAI client.

### LumaText2Video

This node is used to generate a video from a text prompt. You can now choose between different models and resolutions.

### LumaImage2Video

This node is used to generate a video from an image. The image can be used as the first or last frame. You can now choose between different models and resolutions.

### LumaInterpolateGenerations

This node is used to interpolate between two generations. You can now choose between different models and resolutions.

### LumaExtendGeneration

This node is used to extend a generation. You can choose to extend before or after the generation. You can now choose between different models and resolutions.

### LumaUpscaleGeneration

This node is used to upscale a generation.

### LumaAddAudio2Video

This node is used to add audio to a video. When using this node with `Preview Video` node, you will notice that the audio won't play in comfy. For that, right click on the video and select `Open Image`, which will open the video in a new tab and you will be able to hear the audio.

### LumaPreviewVideo

This node is used to preview a video. The video is resized to 768px to look better on ComfyUI.

### ImgBBUpload

This node is used to upload an image to ImgBB and return the URL. We need this because Luma API currently only supports image urls as input.
To use this node, you need to have an ImgBB API key. Create an account and get one [here](https://api.imgbb.com/).

### Reference

This node is used to create a reference from an image URL. It is used for style and image references.

### ConcatReferences

This node is used to concatenate a list of references.

### CharacterReference

This node is used to create a character reference from a list of image URLs.

### ImageGeneration

This node is used to generate an image from a prompt.

### ModifyImage

This node is used to modify an image.

## Examples

For examples, see [workflows folder](./workflows). To use, just download the workflow json and import it into ComfyUI.

## API Documentation

For more information about the Luma AI API, see [Luma AI API Documentation](https://docs.lumalabs.ai/docs/api).

## Pricing

For pricing, see [Luma AI Pricing](https://lumalabs.ai/dream-machine/api/pricing).
