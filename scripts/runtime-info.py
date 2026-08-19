import importlib.metadata as metadata
import json
import platform

import torch


print(
    json.dumps(
        {
            "python": platform.python_version(),
            "unimernet": metadata.version("unimernet"),
            "pyside6": metadata.version("PySide6"),
            "torch": metadata.version("torch"),
            "torchvision": metadata.version("torchvision"),
            "transformers": metadata.version("transformers"),
            "torch_cuda_version": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
        }
    )
)
