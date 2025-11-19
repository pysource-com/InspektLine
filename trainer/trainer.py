# python
import os
from typing import Optional, Iterable
import torch
from torch.utils.data import DataLoader
from tqdm.auto import tqdm
from transformers import (
    AutoConfig,
    AutoImageProcessor,
    AutoModelForImageClassification,
    get_scheduler,
)


class Trainer:
    """
    Simple trainer for Hugging Face image classification models.

    Usage:
      trainer = Trainer(model_name="facebook/convnextv2-tiny-22k-224", device="cuda")
      trainer.train(train_loader, val_loader, epochs=3)
      trainer.save("outputs/checkpoint")
    """

    def __init__(
            self,
            model_name: str = "facebook/convnextv2-tiny-22k-224",
            num_labels: Optional[int] = None,
            device: Optional[str] = None,
            lr: float = 5e-5,
            weight_decay: float = 0.0,
            output_dir: str = "outputs",
            mixed_precision: bool = False,
            id2label: Optional[dict] = None,
            label2id: Optional[dict] = None,
    ) -> None:
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.lr = lr
        self.weight_decay = weight_decay
        self.output_dir = output_dir
        self.mixed_precision = mixed_precision

        # Load processor
        self.processor = AutoImageProcessor.from_pretrained(self.model_name)

        # Load model with updated labels
        config = AutoConfig.from_pretrained(self.model_name)
        if num_labels is not None:
            config.num_labels = num_labels
        if id2label is not None:
            config.id2label = id2label
        if label2id is not None:
            config.label2id = label2id

        self.model = AutoModelForImageClassification.from_pretrained(
            self.model_name, config=config, ignore_mismatched_sizes=True
        )

        self.model.to(self.device)
        self.scaler = torch.cuda.amp.GradScaler() if self.mixed_precision and torch.cuda.is_available() else None

    def _prepare_batch(self, batch: dict):
        """
        Ensure batch contains 'pixel_values' tensor on device and 'labels' if present.
        Accepts batches with 'image' or 'images' list/array of PIL/numpy.
        """
        if "pixel_values" not in batch:
            images = batch.get("image") or batch.get("images")
            if images is None:
                raise ValueError("Batch must contain 'pixel_values' or 'image'/'images'.")
            processed = self.processor(images=images, return_tensors="pt")
            pixel_values = processed["pixel_values"]
        else:
            pixel_values = batch["pixel_values"]

        pixel_values = pixel_values.to(self.device)
        prepared = {"pixel_values": pixel_values}
        if "labels" in batch:
            prepared["labels"] = batch["labels"].to(self.device)
        return prepared

    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        epochs: int = 3,
        max_grad_norm: float = 1.0,
        lr_scheduler_type: str = "linear",
        warmup_steps: int = 0,
        save_every_epoch: bool = False,
    ):
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        total_steps = epochs * len(train_loader)
        scheduler = get_scheduler(
            name=lr_scheduler_type,
            optimizer=optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps,
        )

        self.model.train()
        for epoch in range(1, epochs + 1):
            pbar = tqdm(train_loader, desc=f"Train epoch {epoch}/{epochs}")
            running_loss = 0.0
            for batch in pbar:
                prepared = self._prepare_batch(batch)

                optimizer.zero_grad()
                if self.scaler:
                    with torch.cuda.amp.autocast():
                        outputs = self.model(**prepared)
                        loss = outputs.loss
                    self.scaler.scale(loss).backward()
                    if max_grad_norm > 0:
                        self.scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_grad_norm)
                    self.scaler.step(optimizer)
                    self.scaler.update()
                else:
                    outputs = self.model(**prepared)
                    loss = outputs.loss
                    loss.backward()
                    if max_grad_norm > 0:
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_grad_norm)
                    optimizer.step()
                    scheduler.step()

                scheduler.step()
                running_loss += loss.item()
                pbar.set_postfix({"loss": running_loss / (pbar.n + 1)})

            if val_loader is not None:
                val_metrics = self.evaluate(val_loader)
                tqdm.write(f"Epoch {epoch} validation: {val_metrics}")

            if save_every_epoch:
                self.save(os.path.join(self.output_dir, f"epoch-{epoch}"))

        # final save
        self.save(os.path.join(self.output_dir, "final"))

    def evaluate(self, dataloader: Iterable):
        """
        Evaluate loss and accuracy. Expects batches convertible by _prepare_batch.
        Returns dict with mean loss and accuracy.
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for batch in tqdm(dataloader, desc="Evaluating", leave=False):
                prepared = self._prepare_batch(batch)
                if self.scaler:
                    with torch.cuda.amp.autocast():
                        outputs = self.model(**prepared)
                else:
                    outputs = self.model(**prepared)

                loss = outputs.loss
                logits = outputs.logits
                total_loss += loss.item() * logits.size(0)
                preds = torch.argmax(logits, dim=-1)
                if "labels" in prepared:
                    labels = prepared["labels"]
                    correct += (preds == labels).sum().item()
                    total += labels.size(0)
        self.model.train()
        mean_loss = total_loss / (total if total > 0 else len(dataloader.dataset))
        accuracy = correct / total if total > 0 else 0.0
        return {"loss": mean_loss, "accuracy": accuracy}

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        self.model.save_pretrained(path)
        self.processor.save_pretrained(path)

    def load(self, path: str):
        self.processor = AutoImageProcessor.from_pretrained(path)
        self.model = AutoModelForImageClassification.from_pretrained(path)
        self.model.to(self.device)

# Example usage:
if __name__ == "__main__":
    from datasets import load_dataset
    from torch.utils.data import DataLoader

    dataset = load_dataset("imagefolder", data_dir="../samples/splitted_dataset")

    # Extract label names from dataset
    label_names = dataset["train"].features["label"].names
    id2label = {i: label for i, label in enumerate(label_names)}
    label2id = {label: i for i, label in enumerate(label_names)}

    trainer = Trainer(
        model_name="facebook/convnextv2-tiny-22k-224",
        device="cuda",
        mixed_precision=True,
        num_labels=len(label_names),
        id2label=id2label,
        label2id=label2id
    )


    def collate_fn(examples):
        batch = {
            "image": [e["image"].convert("RGB") for e in examples],
        }
        if "label" in examples[0]:
            batch["labels"] = torch.tensor([e["label"] for e in examples])
        return batch


    train_loader = DataLoader(dataset["train"], batch_size=64, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(dataset["test"], batch_size=64, collate_fn=collate_fn)

    trainer.train(train_loader, val_loader, epochs=25, save_every_epoch=True)

