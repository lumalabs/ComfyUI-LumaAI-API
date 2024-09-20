import configparser
import os
import requests
import time
from lumaai import LumaAI

import folder_paths

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_path = os.path.join(parent_dir, "config.ini")

config = configparser.ConfigParser()
config.read(config_path)

try:
    luma_api_key = config['API']['LUMAAI_API_KEY']
    if luma_api_key != "":
        os.environ["LUMAAI_API_KEY"] = luma_api_key
    else:
        print("Warning: LUMAAI_API_KEY is empty in config.ini")
except KeyError:
    print("Error: LUMAAI_API_KEY not found in config.ini")


def download_file(url, file_name):
    response = requests.get(url, stream=True)
    with open(file_name, "wb") as file:
        file.write(response.content)
    print(f"File downloaded as {file_name}")

def parse_filename(filename):
    # Remove file extension if present
    filename = os.path.splitext(filename)[0]

    # Check if the filename ends with a directory separator
    if filename.endswith(os.path.sep):
        # If it does, we'll use the generation_id as the filename later
        directory = filename
        filename = ""
    else:
        # Otherwise, split the path into directory and filename
        directory, filename = os.path.split(filename)

    # Create directories if they don't exist
    output_path = folder_paths.get_output_directory()
    full_directory = os.path.join(output_path, directory)
    if directory and not os.path.exists(full_directory):
        os.makedirs(full_directory)

    return directory, filename


class LumaAIClient:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": (
                    "STRING",
                    {
                        "default": "",
                    },
                )
            },
        }

    RETURN_TYPES = ("LUMACLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "run"
    CATEGORY = "LumaAI"

    def run(self, api_key):
        """
        Create a LumaAI client with the provided API key.
        """
        api_key = api_key if api_key != "" else os.environ.get("LUMAAI_API_KEY", "")

        if api_key == "":
            raise ValueError("API Key is required")

        client = LumaAI(
            auth_token=api_key,
        )

        return (client,)


class Text2Video:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "loop": ("BOOLEAN", {"default": False}),
                "aspect_ratio": (["9:16", "3:4", "1:1", "4:3", "16:9", "21:9"],),
                "save": ("BOOLEAN", {"default": True}),
            },
            "optional": {"filename": ("STRING", {"default": ""})},
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "LumaAI"

    def run(self, client, prompt, loop, aspect_ratio, save, filename):
        """
        Generate a video from a text prompt.
        """
        if prompt == "":
            raise ValueError("Prompt is required")

        generation = client.generations.create(
            prompt=prompt, loop=loop, aspect_ratio=aspect_ratio
        )
        generation_id = generation.id
        completed = False
        while not completed:
            generation = client.generations.get(id=generation_id)
            if generation.state == "completed":
                completed = True
            elif generation.state == "failed":
                raise ValueError(f"Generation failed: {generation.failure_reason}")
            time.sleep(3)

        video_url = generation.assets.video
        if save:
            directory, filename = parse_filename(filename)
            if filename == "":
                filename = generation_id
            download_file(video_url, os.path.join(self.output_dir, directory, filename + ".mp4"))

        return {
            "ui": {"text": [generation_id]},
            "result": (
                video_url,
                generation_id,
            ),
        }


class Image2Video:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "loop": ("BOOLEAN", {"default": False}),
                "save": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "init_image_url": ("STRING", {"default": "", "forceInput": True}),
                "final_image_url": ("STRING", {"default": "", "forceInput": True}),
                "filename": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    FUNCTION = "run"
    CATEGORY = "LumaAI"

    def run(
        self,
        client,
        prompt,
        loop,
        save,
        init_image_url="",
        final_image_url="",
        filename="",
    ):
        """
        Generate a video from an image prompt.
        """
        if init_image_url == "" and final_image_url == "":
            raise ValueError("At least one image URL is required")

        keyframes = {}
        if init_image_url != "":
            keyframes["frame0"] = {"type": "image", "url": init_image_url}
        if final_image_url != "":
            keyframes["frame1"] = {"type": "image", "url": final_image_url}

        generation = client.generations.create(
            prompt=prompt, loop=loop, keyframes=keyframes
        )
        generation_id = generation.id
        completed = False
        while not completed:
            generation = client.generations.get(id=generation_id)
            if generation.state == "completed":
                completed = True
            elif generation.state == "failed":
                raise ValueError(f"Generation failed: {generation.failure_reason}")
            time.sleep(3)

        video_url = generation.assets.video
        if save:
            directory, filename = parse_filename(filename)
            if filename == "":
                filename = generation_id
            download_file(video_url, os.path.join(self.output_dir, directory, filename + ".mp4"))

        return {
            "ui": {"text": [generation_id]},
            "result": (
                video_url,
                generation_id,
            ),
        }


class InterpolateGenerations:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "save": ("BOOLEAN", {"default": True}),
                "generation_id_1": ("STRING", {"default": "", "forceInput": True}),
                "generation_id_2": ("STRING", {"default": "", "forceInput": True}),
            },
            "optional": {"filename": ("STRING", {"default": ""})},
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    FUNCTION = "run"
    CATEGORY = "LumaAI"

    def run(
        self,
        client,
        prompt,
        save,
        generation_id_1,
        generation_id_2,
        filename="",
    ):
        """
        Generate a video by interpolating between two existing generations.
        """
        if not generation_id_1 or not generation_id_2:
            raise ValueError("Both generation IDs are required")

        generation = client.generations.create(
            prompt=prompt,
            keyframes={
                "frame0": {"type": "generation", "id": generation_id_1},
                "frame1": {"type": "generation", "id": generation_id_2},
            },
        )
        generation_id = generation.id
        completed = False
        while not completed:
            generation = client.generations.get(id=generation_id)
            if generation.state == "completed":
                completed = True
            elif generation.state == "failed":
                raise ValueError(f"Generation failed: {generation.failure_reason}")
            time.sleep(3)

        video_url = generation.assets.video
        if save:
            directory, filename = parse_filename(filename)
            if filename == "":
                filename = generation_id
            download_file(video_url, os.path.join(self.output_dir, directory, filename + ".mp4"))

        return {
            "ui": {"text": [generation_id]},
            "result": (
                video_url,
                generation_id,
            ),
        }


class ExtendGeneration:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "save": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "init_image_url": ("STRING", {"default": "", "forceInput": True}),
                "final_image_url": ("STRING", {"default": "", "forceInput": True}),
                "init_generation_id": ("STRING", {"default": "", "forceInput": True}),
                "final_generation_id": ("STRING", {"default": "", "forceInput": True}),
                "filename": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    FUNCTION = "run"
    CATEGORY = "LumaAI"

    def run(
        self,
        client,
        prompt,
        save,
        init_image_url="",
        final_image_url="",
        init_generation_id="",
        final_generation_id="",
        filename="",
    ):
        """
        Generate a video by extending from an image to an existing generation.
        """
        if not init_generation_id and not final_generation_id:
            raise ValueError("You must provide at least one generation id")
        if init_image_url and init_generation_id:
            raise ValueError(
                "You cannot provide both an init image and a init generation"
            )
        if final_image_url and final_generation_id:
            raise ValueError(
                "You cannot provide both a final image and a final generation"
            )

        keyframes = {}
        if init_image_url != "":
            keyframes["frame0"] = {"type": "image", "url": init_image_url}
        if final_image_url != "":
            keyframes["frame1"] = {"type": "image", "url": final_image_url}
        if init_generation_id != "":
            keyframes["frame0"] = {"type": "generation", "id": init_generation_id}
        if final_generation_id != "":
            keyframes["frame1"] = {"type": "generation", "id": final_generation_id}

        generation = client.generations.create(prompt=prompt, keyframes=keyframes)
        new_generation_id = generation.id
        completed = False
        while not completed:
            generation = client.generations.get(id=new_generation_id)
            if generation.state == "completed":
                completed = True
            elif generation.state == "failed":
                raise ValueError(f"Generation failed: {generation.failure_reason}")
            time.sleep(3)

        video_url = generation.assets.video
        if save:
            directory, filename = parse_filename(filename)
            if filename == "":
                filename = new_generation_id
            download_file(video_url, os.path.join(self.output_dir, directory, filename + ".mp4"))

        return {
            "ui": {"text": [new_generation_id]},
            "result": (
                video_url,
                new_generation_id,
            ),
        }


class PreviewVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"forceInput": True}),
            }
        }

    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "LumaAI"
    RETURN_TYPES = ()

    def run(self, video_url):
        return {"ui": {"video_url": [video_url]}}
