python
import os
from typing import Optional, Dict, Any

import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoImageProcessor,
    AutoModelForImageClassification,
    TrainingArguments,
    Trainer,
)


class ImageClassificationTrainer:
    def __init__(
        self,
        model_name: str = "facebook/convnextv2-tiny-22k-224",
        num_labels: Optional[int] = None,
        id2label: Optional[Dict[int, str]] = None,
        label2id: Optional[Dict[str, int]] = None,
        device: Optional[str] = None,
    ) -> None:
        """
        Simple training wrapper for image classification models.

        \- model_name: model checkpoint name.
        \- num_labels/id2label/label2id: label config (if None, taken from checkpoint).
        \- device: "cuda", "cpu" or None for auto.
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Load processor and model
        self.processor = AutoImageProcessor.from_pretrained(self.model_name)

        model_kwargs: Dict[str, Any] = {}
        if num_labels is not None:
            model_kwargs["num_labels"] = num_labels
        if id2label is not None and label2id is not None:
            model_kwargs["id2label"] = id2label
            model_kwargs["label2id"] = label2id

        self.model = AutoModelForImageClassification.from_pretrained(
            self.model_name, **model_kwargs
        )
        self.model.to(self.device)

    def _build_transform(self):
        """
        Returns a function that maps a batch with an 'image' column to model inputs.
        """

        def transform(batch):
            # Expect batch["image"] to be a list of PIL images
            inputs = self.processor(
                images=batch["image"],
                return_tensors="pt",
            )
            # Trainer expects tensors, not lists of tensors
            return inputs

        return transform

    def prepare_dataset(
        self,
        dataset: Dataset | DatasetDict,
        image_column: str = "image",
        label_column: str = "label",
    ) -> DatasetDict:
        """
        Prepares a Dataset or DatasetDict for training.

        \- dataset: Hugging Face Dataset or DatasetDict containing images and labels.
        \- image_column: column name that holds the images (PIL or arrays).
        \- label_column: column name with integer labels.
        """
        if isinstance(dataset, Dataset):
            dataset = DatasetDict({"train": dataset})

        # Rename to expected names, if needed
        def _rename_columns(ds: Dataset) -> Dataset:
            cols_to_rename = {}
            if image_column != "image":
                cols_to_rename[image_column] = "image"
            if label_column != "labels":
                cols_to_rename[label_column] = "labels"
            if cols_to_rename:
                ds = ds.rename_columns(cols_to_rename)
            return ds

        dataset = DatasetDict(
            {split: _rename_columns(ds) for split, ds in dataset.items()}
        )

        transform = self._build_transform()

        # Set transform – only on splits that exist
        for split, ds in dataset.items():
            dataset[split] = ds.with_transform(
                lambda batch, t=transform: {
                    **t(batch),
                    "labels": batch["labels"],
                }
            )

        return dataset

    def train(
        self,
        dataset: Dataset | DatasetDict,
        output_dir: str = "./outputs",
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 8,
        per_device_eval_batch_size: int = 8,
        learning_rate: float = 5e-5,
        weight_decay: float = 0.01,
        logging_steps: int = 50,
        eval_steps: int = 500,
        save_steps: int = 500,
        evaluation_strategy: str = "steps",
        save_total_limit: int = 2,
        load_best_model_at_end: bool = True,
        metric_for_best_model: Optional[str] = "accuracy",
    ):
        """
        Runs training using Hugging Face Trainer.

        Expect dataset to have at least a 'train' split, optionally 'validation'.
        """

        os.makedirs(output_dir, exist_ok=True)

        dataset = self.prepare_dataset(dataset)

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            per_device_eval_batch_size=per_device_eval_batch_size,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            logging_steps=logging_steps,
            evaluation_strategy=evaluation_strategy
            if "validation" in dataset
            else "no",
            eval_steps=eval_steps,
            save_steps=save_steps,
            save_total_limit=save_total_limit,
            load_best_model_at_end=load_best_model_at_end
            if "validation" in dataset
            else False,
            metric_for_best_model=metric_for_best_model
            if "validation" in dataset
            else None,
            remove_unused_columns=False,
        )

        train_dataset = dataset["train"]
        eval_dataset = dataset.get("validation", None)

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
        )

        trainer.train()
        trainer.save_model(output_dir)
        self.processor.save_pretrained(output_dir)

        return trainer
