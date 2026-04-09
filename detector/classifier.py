import os
import json
import torch
from typing import List, Union, Optional
from PIL import Image
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification


class TimmImageClassifier:
    """Classifier for timm .pth checkpoints (e.g. ConvNeXt fine-tuned weights).

    Loads a PyTorch Image Models (timm) checkpoint and runs inference
    with the same ``predict()`` API as ``TransformerImageClassifier``.
    """

    # Map of architecture families to common timm model names.
    # Used for auto-detection from state-dict key patterns.
    _ARCH_HINTS = {
        "convnext": "convnext_tiny",
        "resnet": "resnet50",
        "efficientnet": "efficientnet_b0",
        "vit": "vit_base_patch16_224",
    }

    def __init__(
        self,
        checkpoint_path: str,
        model_name: Optional[str] = None,
        class_names: Optional[List[str]] = None,
        device: Optional[str] = None,
    ) -> None:
        import timm
        from timm.data import resolve_data_config
        from timm.data.transforms_factory import create_transform

        self.model_name = checkpoint_path  # exposed for external code
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Load raw checkpoint
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

        # Handle different save formats ({state_dict: ...}, {model: ...}, or plain dict)
        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
            model_name = model_name or checkpoint.get("arch") or checkpoint.get("model_name")
        elif isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
            model_name = model_name or checkpoint.get("arch") or checkpoint.get("model_name")
        elif isinstance(checkpoint, dict) and "model" in checkpoint:
            state_dict = checkpoint["model"]
            model_name = model_name or checkpoint.get("arch") or checkpoint.get("model_name")
        elif isinstance(checkpoint, dict) and "net" in checkpoint:
            state_dict = checkpoint["net"]
            model_name = model_name or checkpoint.get("arch") or checkpoint.get("model_name")
        elif isinstance(checkpoint, dict) and any(
            k.startswith(("head.", "stages.", "stem.", "features.", "classifier."))
            for k in checkpoint.keys()
        ):
            # Plain state dict with recognizable layer keys
            state_dict = checkpoint
        else:
            state_dict = checkpoint

        # Try to read model_name from a model_config.json next to the .pth
        if model_name is None:
            model_name = self._read_model_config(checkpoint_path)

        # Auto-detect architecture from state-dict keys as last resort
        if model_name is None:
            model_name = self._guess_arch(state_dict)

        # Detect num_classes from classifier head weights
        num_classes = self._detect_num_classes(state_dict)

        # Build the model and load weights
        self.model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
        self.model.load_state_dict(state_dict, strict=False)
        self.model.to(self.device)
        self.model.eval()

        # Build data transforms from the model's pretrained config
        data_config = resolve_data_config(self.model.pretrained_cfg)
        self.transform = create_transform(**data_config, is_training=False)

        # Class labels
        if class_names is None:
            class_names = self._discover_class_names(checkpoint_path)

        if class_names:
            self.id2label = {i: name for i, name in enumerate(class_names)}
        else:
            self.id2label = {i: str(i) for i in range(num_classes)}
        self.label2id = {v: k for k, v in self.id2label.items()}

        print(
            f"[TimmImageClassifier] Loaded {model_name} "
            f"({num_classes} classes) from {checkpoint_path}"
        )

    # ---- helpers -----------------------------------------------------------

    @staticmethod
    def _detect_num_classes(state_dict: dict) -> int:
        """Infer the number of output classes from the classifier head."""
        for key in ("head.fc.weight", "head.weight", "classifier.weight", "fc.weight"):
            if key in state_dict:
                return state_dict[key].shape[0]
        return 2  # sensible fallback for binary classification

    @staticmethod
    def _read_model_config(checkpoint_path: str) -> Optional[str]:
        """Read ``timm_model_name`` from a ``model_config.json`` next to the checkpoint."""
        cfg_path = os.path.join(os.path.dirname(checkpoint_path), "model_config.json")
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("timm_model_name") or data.get("model_name") or data.get("arch")
            except Exception:
                pass
        return None

    @classmethod
    def _guess_arch(cls, state_dict: dict) -> str:
        """Best-effort guess of the timm architecture from state-dict keys."""
        joined = " ".join(state_dict.keys())
        for family, default_name in cls._ARCH_HINTS.items():
            if family in joined.lower():
                return default_name
        return "convnext_tiny"  # project default

    @staticmethod
    def _discover_class_names(checkpoint_path: str) -> Optional[List[str]]:
        """Look for ``classes.txt`` or ``classes.json`` next to the checkpoint."""
        parent = os.path.dirname(checkpoint_path)
        txt = os.path.join(parent, "classes.txt")
        jsn = os.path.join(parent, "classes.json")

        if os.path.isfile(txt):
            with open(txt, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        if os.path.isfile(jsn):
            with open(jsn, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        return None

    # ---- inference ---------------------------------------------------------

    @torch.no_grad()
    def predict(
        self,
        images: List[Union[Image.Image, np.ndarray]],
        top_k: int = 1,
        return_probabilities: bool = True,
    ):
        """Run classification on a list of images.

        Returns the same format as ``TransformerImageClassifier.predict``.
        """
        if not images:
            return []

        tensors = []
        for img in images:
            if isinstance(img, np.ndarray):
                pil_img = Image.fromarray(img)
            elif isinstance(img, Image.Image):
                pil_img = img
            else:
                raise TypeError("Each image must be a PIL.Image or NumPy array.")
            tensors.append(self.transform(pil_img))

        batch = torch.stack(tensors).to(self.device)
        logits = self.model(batch)

        if return_probabilities:
            probs = torch.softmax(logits, dim=-1)
        else:
            probs = logits

        top_k = min(top_k, logits.shape[-1])
        scores, indices = torch.topk(probs, k=top_k, dim=-1)

        results = []
        for img_scores, img_indices in zip(scores, indices):
            img_results = []
            for score, idx in zip(img_scores, img_indices):
                idx_int = idx.item()
                img_results.append(
                    {
                        "id": idx_int,
                        "label": self.id2label.get(idx_int, str(idx_int)),
                        "score": float(score.item()),
                    }
                )
            results.append(img_results)

        return results


class TransformerImageClassifier:
    def __init__(
        self,
        model_name: str = "facebook/convnextv2-tiny-22k-224",
        device: Optional[str] = None,
    ) -> None:
        """
        Wrapper for Hugging Face transformers image classification models.

        - model_name: any vision classification checkpoint from Hugging Face hub.
        - device: "cuda", "cpu", or None to auto -select.
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Load processor and model
        self.processor = AutoImageProcessor.from_pretrained(self.model_name)
        self.model = AutoModelForImageClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

        # Label mapping
        self.id2label = self.model.config.id2label
        self.label2id = self.model.config.label2id

    @torch.no_grad()
    def predict(
        self,
        images: List[Union[Image.Image, np.ndarray]],
        top_k: int = 1,
        return_probabilities: bool = True,
    ):
        """
        Run classification on a list of images.

        - images: list of PIL.Image or NumPy arrays.
        - top_k: how many top predictions to return per image.
        - return_probabilities: if True, returns softmax probabilities.

        Returns a list (per image) of dicts:
            { "label": str, "score": float, "id": int }
        """
        if not images:
            return []

        # Convert NumPy arrays to PIL images if needed
        processed_images = []
        for img in images:
            if isinstance(img, np.ndarray):
                processed_images.append(Image.fromarray(img))
            elif isinstance(img, Image.Image):
                processed_images.append(img)
            else:
                raise TypeError("Each image must be a PIL.Image or NumPy array.")

        inputs = self.processor(
            images=processed_images,
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model(**inputs)
        logits = outputs.logits  # shape: (batch, num_classes)

        if return_probabilities:
            probs = torch.softmax(logits, dim=-1)
        else:
            probs = logits

        top_k = min(top_k, logits.shape[-1])
        scores, indices = torch.topk(probs, k=top_k, dim=-1)

        results = []
        for img_scores, img_indices in zip(scores, indices):
            img_results = []
            for score, idx in zip(img_scores, img_indices):
                idx_int = idx.item()
                img_results.append(
                    {
                        "id": idx_int,
                        "label": self.id2label.get(idx_int, str(idx_int)),
                        "score": float(score.item()),
                    }
                )
            results.append(img_results)

        return results

# Example usage:
if __name__ == "__main__":
    import cv2
    import os
    import sys

    if len(sys.argv) < 3:
        print("Usage: python classifier.py <model_path> <image_path>")
        sys.exit(1)

    model_path = sys.argv[1]
    image_path = sys.argv[2]

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image_bgr = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    classifier = TransformerImageClassifier(model_name=model_path)
    results = classifier.predict([image_rgb], top_k=1, return_probabilities=True)
    for res in results[0]:
        print(f"Label: {res['label']}, Score: {res['score']:.4f}, ID: {res['id']}")
