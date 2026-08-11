import importlib.metadata as metadata
import json
import platform

import torch


print(
    json.dumps(
        {
            "python": platform.python_version(),
            "pix2tex": metadata.version("pix2tex"),
            "pyside6": metadata.version("PySide6"),
            "torch": metadata.version("torch"),
            "torch_cuda_version": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
        }
    )
)
