import torch
from typing import List, Union, Optional
from PIL import Image
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification


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
    from datasets import load_dataset
    import cv2
    import numpy as np

    dataset = load_dataset("huggingface/cats-image")
    image = dataset["test"]["image"][0]

    # show the image with opencv
    image_np = np.array(image)
    cv2.imshow("Cat Image", cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR))
    cv2.waitKey(1)

    classifier = TransformerImageClassifier(
        model_name="facebook/convnextv2-base-22k-224"
    )

    predictions = classifier.predict([image], top_k=1)
    predicted_label = predictions[0][0]["label"]
    print(predicted_label)

    cv2.waitKey(0)