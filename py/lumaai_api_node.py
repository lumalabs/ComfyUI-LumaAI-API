import configparser
import os
import requests
import time
from lumaai import LumaAI

import folder_paths
import nodes

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_path = os.path.join(parent_dir, "config.ini")

config = configparser.ConfigParser()
config.read(config_path)

try:
    luma_api_key = config["API"]["LUMAAI_API_KEY"]
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


def wait_for_generation(client, generation_id, save, filename, output_dir):
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
        download_file(
            video_url, os.path.join(output_dir, directory, filename + ".mp4")
        )
    return video_url


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
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "model": (["ray-flash-2", "ray-2", "ray-1.6"],),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "duration": (["5s", "9s"],),
                "loop": ("BOOLEAN", {"default": False}),
                "aspect_ratio": (["9:16", "3:4", "1:1", "4:3", "16:9", "21:9"],),
                "resolution": (["540p", "720p"],),
                "save": ("BOOLEAN", {"default": True}),
            },
            "optional": {"filename": ("STRING", {"default": ""})},
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "LumaAI/Ray"

    def run(self, client, model, prompt, duration, loop, aspect_ratio, resolution, save, filename):
        """
        Generate a video from a text prompt.
        """
        if prompt == "":
            raise ValueError("Prompt is required")

        generation = client.generations.create(
            prompt=prompt,
            model=model,
            loop=loop,
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution,
        )
        generation_id = generation.id
        video_url = wait_for_generation(client, generation_id, save, filename, self.output_dir)

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
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "model": (["ray-flash-2", "ray-2", "ray-1.6"],),
                "duration": (["5s", "9s"],),
                "loop": ("BOOLEAN", {"default": False}),
                "resolution": (["540p", "720p"],),
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
    CATEGORY = "LumaAI/Ray"

    def run(
        self,
        client,
        model,
        prompt,
        duration,
        loop,
        resolution,
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
            prompt=prompt,
            model=model,
            loop=loop,
            duration=duration,
            resolution=resolution,
            keyframes=keyframes,
        )
        generation_id = generation.id
        video_url = wait_for_generation(client, generation_id, save, filename, self.output_dir)

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
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "model": (["ray-flash-2", "ray-2", "ray-1.6"],),
                "resolution": (["540p", "720p"],),
                "save": ("BOOLEAN", {"default": True}),
                "generation_id_1": ("STRING", {"default": "", "forceInput": True}),
                "generation_id_2": ("STRING", {"default": "", "forceInput": True}),
            },
            "optional": {"filename": ("STRING", {"default": ""})},
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    FUNCTION = "run"
    CATEGORY = "LumaAI/Ray"

    def run(
        self,
        client,
        model,
        prompt,
        resolution,
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
            model=model,
            resolution=resolution,
        )
        generation_id = generation.id
        video_url = wait_for_generation(client, generation_id, save, filename, self.output_dir)

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
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "model": (["ray-flash-2", "ray-2", "ray-1.6"],),
                "loop": ("BOOLEAN", {"default": False}),
                "resolution": (["540p", "720p"],),
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
    CATEGORY = "LumaAI/Ray"

    def run(
        self,
        client,
        model,
        prompt,
        loop,
        resolution,
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

        generation = client.generations.create(
            prompt=prompt,
            model=model,
            loop=loop,
            resolution=resolution,
            keyframes=keyframes,
        )
        generation_id = generation.id
        video_url = wait_for_generation(client, generation_id, save, filename, self.output_dir)

        return {
            "ui": {"text": [generation_id]},
            "result": (
                video_url,
                generation_id,
            ),
        }


class UpscaleGeneration:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "generation_id": ("STRING", {"default": "", "forceInput": True}),
                "resolution": (["540p", "720p", "1080p", "4k"],),
                "save": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "filename": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    FUNCTION = "run"
    CATEGORY = "LumaAI/Upscale"

    def run(
        self,
        client,
        generation_id,
        resolution,
        save,
        filename="",
    ):
        """
        Upscale a generation.
        """
        generation = client.generations.upscale(id=generation_id, resolution=resolution)
        upscaled_generation_id = generation.id
        video_url = wait_for_generation(client, upscaled_generation_id, save, filename, self.output_dir)

        return {
            "ui": {"text": [upscaled_generation_id]},
            "result": (
                video_url,
                upscaled_generation_id,
            ),
        }


class AddAudio2Video:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
    
    @classmethod
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "generation_id": ("STRING", {"default": "", "forceInput": True}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "save": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "filename": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "generation_id")
    FUNCTION = "run"
    CATEGORY = "LumaAI/Audio"

    def run(
        self,
        client,
        generation_id,
        prompt,
        negative_prompt,
        save,
        filename="",
    ):
        """
        Upscale a generation.
        """
        generation = client.generations.audio(id=generation_id, prompt=prompt, negative_prompt=negative_prompt)
        with_audio_generation_id = generation.id
        video_url = wait_for_generation(client, with_audio_generation_id, save, filename, self.output_dir)

        return {
            "ui": {"text": [with_audio_generation_id]},
            "result": (
                video_url,
                with_audio_generation_id,
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

    @classmethod
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "LumaAI/Utils"
    RETURN_TYPES = ()

    def run(self, video_url):
        return {"ui": {"video_url": [video_url]}}


class Reference:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_url": ("STRING", {"forceInput": True}),
                "weight": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
            }
        }

    RETURN_TYPES = ("REFERENCE",)
    RETURN_NAMES = ("reference",)
    FUNCTION = "run"
    CATEGORY = "LumaAI/Photon"

    def run(self, image_url, weight):
        """
        Create a reference from an image URL and a weight.
        """
        return ({"url": image_url, "weight": weight},)


class ConcatReferences:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "reference_1": ("REFERENCE", {"forceInput": True}),
                "reference_2": ("REFERENCE", {"forceInput": True}),
                "reference_3": ("REFERENCE", {"forceInput": True}),
                "reference_4": ("REFERENCE", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("CONCAT_REFERENCES",)
    RETURN_NAMES = ("concat_references",)
    FUNCTION = "run"
    CATEGORY = "LumaAI/Photon"

    def run(
        self, reference_1=None, reference_2=None, reference_3=None, reference_4=None
    ):
        """
        Concatenate a list of references.
        """
        references = []
        for reference in [reference_1, reference_2, reference_3, reference_4]:
            if reference is not None:
                references.append(reference)
        if len(references) == 0:
            raise ValueError("You must provide at least one reference")
        return (references,)


class CharacterReference:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "character_image_url_1": ("STRING", {"forceInput": True}),
                "character_image_url_2": ("STRING", {"forceInput": True}),
                "character_image_url_3": ("STRING", {"forceInput": True}),
                "character_image_url_4": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("CHARACTER_REFERENCE",)
    RETURN_NAMES = ("character_reference",)
    FUNCTION = "run"
    CATEGORY = "LumaAI/Photon"

    def run(
        self,
        character_image_url_1=None,
        character_image_url_2=None,
        character_image_url_3=None,
        character_image_url_4=None,
    ):
        """
        Create a character reference from a list of image URLs.
        """
        urls = []
        for url in [
            character_image_url_1,
            character_image_url_2,
            character_image_url_3,
            character_image_url_4,
        ]:
            if url is not None:
                urls.append(url)
        if len(urls) == 0:
            raise ValueError("You must provide at least one character image URL")

        character_reference = {"identity0": {"images": urls}}
        return (character_reference,)


class ImageGeneration:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
    
    @classmethod
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "model": (["photon-1", "photon-flash-1"],),
                "prompt": ("STRING", {"forceInput": True, }),
                "aspect_ratio": (["9:16", "3:4", "1:1", "4:3", "16:9", "21:9"],),
            },
            "optional": {
                "image_ref": ("CONCAT_REFERENCES", {"forceInput": True}),
                "style_ref": ("REFERENCE", {"forceInput": True}),
                "character_ref": ("CHARACTER_REFERENCE", {"forceInput": True}),
                "filename": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("image_url", "generation_id", "image")
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "LumaAI/Photon"

    def run(
        self,
        client,
        model,
        prompt,
        aspect_ratio,
        image_ref=None,
        style_ref=None,
        character_ref=None,
        filename="",
    ):
        """
        Generate an image from a text prompt and optional references.
        """
        if style_ref is not None:
            style_ref = [style_ref]

        generation = client.generations.image.create(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            image_ref=image_ref,
            style_ref=style_ref,
            character_ref=character_ref,
        )

        generation_id = generation.id
        completed = False
        while not completed:
            generation = client.generations.get(id=generation_id)
            if generation.state == "completed":
                completed = True
            elif generation.state == "failed":
                raise ValueError(f"Generation failed: {generation.failure_reason}")
            time.sleep(1)

        image_url = generation.assets.image
        directory, filename = parse_filename(filename)
        if filename == "":
            filename = generation_id
        download_file(
            image_url, os.path.join(self.output_dir, directory, filename + ".jpg")
        )

        image, _ = nodes.LoadImage().load_image(
            os.path.join(self.output_dir, directory, filename + ".jpg")
        )

        return {
            "ui": {"text": [generation_id]},
            "result": (image_url, generation_id, image),
        }


class ModifyImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
    
    @classmethod
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("LUMACLIENT", {"forceInput": True}),
                "model": (["photon-1", "photon-flash-1"],),
                "prompt": ("STRING", {"forceInput": True, }),
                "modify_image_ref": ("REFERENCE", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("image_url", "generation_id", "image")
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "LumaAI/Photon"

    def run(self, client, model, prompt, modify_image_ref, filename=""):
        """
        Modify an image.
        """
        generation = client.generations.image.create(
            prompt=prompt,
            model=model,
            modify_image_ref=modify_image_ref,
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

        image_url = generation.assets.image
        directory, filename = parse_filename(filename)
        if filename == "":
            filename = generation_id
        download_file(
            image_url, os.path.join(self.output_dir, directory, filename + ".jpg")
        )

        image, _ = nodes.LoadImage().load_image(
            os.path.join(self.output_dir, directory, filename + ".jpg")
        )

        return {
            "ui": {"text": [generation_id]},
            "result": (image_url, generation_id, image),
        }
