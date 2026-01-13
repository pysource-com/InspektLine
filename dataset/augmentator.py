import torch
from torchvision import transforms
from torch.utils.data import Dataset
from typing import Optional, List, Tuple, Callable, Any
from enum import Enum


class AugmentationType(Enum):
    """Enum for available augmentation types."""
    HORIZONTAL_FLIP = "horizontal_flip"
    VERTICAL_FLIP = "vertical_flip"
    ROTATION = "rotation"
    COLOR_JITTER = "color_jitter"
    AFFINE = "affine"
    PERSPECTIVE = "perspective"
    GAUSSIAN_BLUR = "gaussian_blur"
    RANDOM_CROP = "random_crop"
    RANDOM_ERASING = "random_erasing"


class DataAugmentator(Dataset):
    """
    A modular dataset wrapper for applying configurable augmentation transforms.
    """

    def __init__(
        self,
        dataset: Dataset,
        augmentations: Optional[List[AugmentationType]] = None,
        custom_transform: Optional[transforms.Compose] = None,
        normalize: bool = True,
        **augmentation_params
    ):
        """
        Initialize the augmentator with specific augmentations.

        Args:
            dataset: The base dataset to augment
            augmentations: List of augmentation types to apply
            custom_transform: Custom transform pipeline (overrides augmentations if provided)
            normalize: Whether to normalize the output tensors
            **augmentation_params: Custom parameters for specific augmentations
        """
        self.dataset = dataset
        self.augmentation_params = augmentation_params

        if custom_transform is not None:
            self.transform = custom_transform
        else:
            self.transform = self._build_transform_pipeline(
                augmentations or [],
                normalize
            )

    def _build_transform_pipeline(
        self,
        augmentations: List[AugmentationType],
        normalize: bool
    ) -> transforms.Compose:
        """
        Build a transform pipeline from selected augmentations.

        Args:
            augmentations: List of augmentation types to include
            normalize: Whether to add normalization

        Returns:
            Composed transform pipeline
        """
        transform_list = []

        for aug in augmentations:
            transform_list.append(self._get_augmentation(aug))

        transform_list.append(transforms.ToTensor())

        if normalize:
            transform_list.append(self._get_normalization())

        return transforms.Compose(transform_list)

    def _get_augmentation(self, aug_type: AugmentationType) -> Any:
        """
        Get a specific augmentation transform with parameters.

        Args:
            aug_type: Type of augmentation

        Returns:
            Configured transform
        """
        if aug_type == AugmentationType.HORIZONTAL_FLIP:
            p = self.augmentation_params.get('horizontal_flip_p', 0.5)
            return transforms.RandomHorizontalFlip(p=p)

        elif aug_type == AugmentationType.VERTICAL_FLIP:
            p = self.augmentation_params.get('vertical_flip_p', 0.3)
            return transforms.RandomVerticalFlip(p=p)

        elif aug_type == AugmentationType.ROTATION:
            degrees = self.augmentation_params.get('rotation_degrees', 15)
            return transforms.RandomRotation(degrees=degrees)

        elif aug_type == AugmentationType.COLOR_JITTER:
            brightness = self.augmentation_params.get('brightness', 0.2)
            contrast = self.augmentation_params.get('contrast', 0.2)
            saturation = self.augmentation_params.get('saturation', 0.2)
            hue = self.augmentation_params.get('hue', 0.1)
            return transforms.ColorJitter(
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                hue=hue
            )

        elif aug_type == AugmentationType.AFFINE:
            degrees = self.augmentation_params.get('affine_degrees', 0)
            translate = self.augmentation_params.get('translate', (0.1, 0.1))
            scale = self.augmentation_params.get('scale', (0.9, 1.1))
            shear = self.augmentation_params.get('shear', 0)
            return transforms.RandomAffine(
                degrees=degrees,
                translate=translate,
                scale=scale,
                shear=shear
            )

        elif aug_type == AugmentationType.PERSPECTIVE:
            distortion_scale = self.augmentation_params.get('distortion_scale', 0.2)
            p = self.augmentation_params.get('perspective_p', 0.5)
            return transforms.RandomPerspective(
                distortion_scale=distortion_scale,
                p=p
            )

        elif aug_type == AugmentationType.GAUSSIAN_BLUR:
            kernel_size = self.augmentation_params.get('blur_kernel_size', 3)
            sigma = self.augmentation_params.get('blur_sigma', (0.1, 2.0))
            return transforms.GaussianBlur(kernel_size=kernel_size, sigma=sigma)

        elif aug_type == AugmentationType.RANDOM_CROP:
            size = self.augmentation_params.get('crop_size', 224)
            padding = self.augmentation_params.get('crop_padding', 4)
            return transforms.RandomCrop(size=size, padding=padding)

        elif aug_type == AugmentationType.RANDOM_ERASING:
            p = self.augmentation_params.get('erasing_p', 0.5)
            scale = self.augmentation_params.get('erasing_scale', (0.02, 0.33))
            ratio = self.augmentation_params.get('erasing_ratio', (0.3, 3.3))
            return transforms.RandomErasing(p=p, scale=scale, ratio=ratio)

        else:
            raise ValueError(f"Unknown augmentation type: {aug_type}")

    @staticmethod
    def _get_normalization() -> transforms.Normalize:
        """Returns ImageNet normalization."""
        return transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )

    def __len__(self) -> int:
        """Returns the length of the dataset."""
        return len(self.dataset)

    def __getitem__(self, idx: int) -> Tuple:
        """
        Get an augmented item from the dataset.

        Args:
            idx: Index of the item

        Returns:
            Tuple of (augmented_data, label)
        """
        data, label = self.dataset[idx]

        if self.transform:
            data = self.transform(data)

        return data, label


class AugmentationPresets:
    """Predefined augmentation presets for common use cases."""

    @staticmethod
    def light() -> List[AugmentationType]:
        """Light augmentation for simple datasets."""
        return [
            AugmentationType.HORIZONTAL_FLIP,
            AugmentationType.ROTATION,
        ]

    @staticmethod
    def medium() -> List[AugmentationType]:
        """Medium augmentation for standard training."""
        return [
            AugmentationType.HORIZONTAL_FLIP,
            AugmentationType.ROTATION,
            AugmentationType.COLOR_JITTER,
            AugmentationType.AFFINE,
        ]

    @staticmethod
    def strong() -> List[AugmentationType]:
        """Strong augmentation for challenging datasets."""
        return [
            AugmentationType.HORIZONTAL_FLIP,
            AugmentationType.VERTICAL_FLIP,
            AugmentationType.ROTATION,
            AugmentationType.COLOR_JITTER,
            AugmentationType.AFFINE,
            AugmentationType.PERSPECTIVE,
            AugmentationType.GAUSSIAN_BLUR,
        ]

    @staticmethod
    def all() -> List[AugmentationType]:
        """All available augmentations."""
        return list(AugmentationType)

# Example usage:
if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image
    import matplotlib.pyplot as plt
    from torchvision.datasets import ImageFolder
    import os

    # Define paths
    input_dir = Path("../samples/disks_defects")
    output_dir = Path("../samples/dataset_augmented")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple dataset from the folder
    # Assuming structure: dataset_captured/class_name/image.jpg
    try:
        base_dataset = ImageFolder(root=str(input_dir))
        print(f"Found {len(base_dataset)} images in {len(base_dataset.classes)} classes")
        print(f"Classes: {base_dataset.classes}")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("Make sure images are organized in subfolders by class")
        exit(1)

    # Create augmented dataset with medium preset
    augmented_dataset = DataAugmentator(
        dataset=base_dataset,
        augmentations=AugmentationPresets.light(),
        rotation_degrees=20,
        brightness=0.3,
        contrast=0.3
    )

    # Generate augmented samples
    num_augmentations_per_image = 5

    for idx in range(len(base_dataset)):
        original_img, label = base_dataset[idx]
        class_name = base_dataset.classes[label]

        # Create class directory in output
        class_output_dir = output_dir / class_name
        class_output_dir.mkdir(exist_ok=True)

        # Get original filename
        img_path = base_dataset.imgs[idx][0]
        img_name = Path(img_path).stem

        # Save original
        original_img.save(class_output_dir / f"{img_name}_original.jpg")

        # Generate augmented versions
        for aug_idx in range(num_augmentations_per_image):
            aug_img, _ = augmented_dataset[idx]

            # Convert tensor back to PIL Image
            aug_img_pil = transforms.ToPILImage()(aug_img)

            # Save augmented image
            output_path = class_output_dir / f"{img_name}_aug_{aug_idx + 1}.jpg"
            aug_img_pil.save(output_path)

        print(f"Processed {idx + 1}/{len(base_dataset)}: {class_name}/{img_name}")

    print(f"\nAugmentation complete! Augmented images saved to: {output_dir}")

    # Visualize a sample with its augmentations
    sample_idx = 0
    original_img, label = base_dataset[sample_idx]

    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    fig.suptitle(f'Original and Augmented Samples - Class: {base_dataset.classes[label]}')

    # Show original
    axes[0, 0].imshow(original_img)
    axes[0, 0].set_title('Original')
    axes[0, 0].axis('off')

    # Show 5 augmented versions
    for i in range(5):
        row = (i + 1) // 3
        col = (i + 1) % 3
        aug_img, _ = augmented_dataset[sample_idx]
        aug_img_pil = transforms.ToPILImage()(aug_img)
        axes[row, col].imshow(aug_img_pil)
        axes[row, col].set_title(f'Augmented {i + 1}')
        axes[row, col].axis('off')

    plt.tight_layout()
    plt.savefig(output_dir / 'augmentation_preview.png')
    print(f"Preview saved to: {output_dir / 'augmentation_preview.png'}")
    plt.show()

