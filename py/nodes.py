from .lumaai_api_node import (
    LumaAIClient,
    Text2Video,
    Image2Video,
    InterpolateGenerations,
    ExtendGeneration,
    PreviewVideo,
)
from .imgbb_node import ImgBBUpload

NODE_CLASS_MAPPINGS = {
    "LumaAIClient": LumaAIClient,
    "ImgBBUpload": ImgBBUpload,
    "LumaText2Video": Text2Video,
    "LumaImage2Video": Image2Video,
    "LumaInterpolateGenerations": InterpolateGenerations,
    "LumaExtendGeneration": ExtendGeneration,
    "LumaPreviewVideo": PreviewVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumaAIClient": "LumaAI Client",
    "ImgBBUpload": "ImgBB Upload",
    "LumaText2Video": "Text to Video",
    "LumaImage2Video": "Image to Video",
    "LumaInterpolateGenerations": "Interpolate Generations",
    "LumaExtendGeneration": "Extend Generation",
    "LumaPreviewVideo": "LumaAI Preview Video",
}
