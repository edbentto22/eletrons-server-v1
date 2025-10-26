#!/usr/bin/env python3
"""
Dataset Preparation Script for Projeto Classe Excluded
Prepares the dataset in YOLO format with proper train/val/test splits
"""

import os
import shutil
import random
from pathlib import Path
from typing import List, Tuple
import json

def create_directory_structure(base_path: Path) -> None:
    """Create the YOLO dataset directory structure"""
    directories = [
        "images/train",
        "images/val", 
        "images/test",
        "labels/train",
        "labels/val",
        "labels/test"
    ]
    
    for directory in directories:
        (base_path / directory).mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created directory structure at {base_path}")

def get_image_label_pairs(source_path: Path) -> List[Tuple[Path, Path]]:
    """Get matching image-label pairs"""
    images_dir = source_path / "images"
    labels_dir = source_path / "labels"
    
    pairs = []
    
    # Get all image files
    image_files = list(images_dir.glob("*.jpg"))
    print(f"📊 Found {len(image_files)} image files")
    
    # Find matching label files
    for img_file in image_files:
        # Try to find corresponding label file
        label_file = labels_dir / f"{img_file.stem}.txt"
        if label_file.exists():
            pairs.append((img_file, label_file))
    
    print(f"📊 Found {len(pairs)} matching image-label pairs")
    return pairs

def split_dataset(pairs: List[Tuple[Path, Path]], 
                 train_ratio: float = 0.7, 
                 val_ratio: float = 0.2, 
                 test_ratio: float = 0.1) -> Tuple[List, List, List]:
    """Split dataset into train/val/test sets"""
    
    # Shuffle the pairs
    random.shuffle(pairs)
    
    total = len(pairs)
    train_size = int(total * train_ratio)
    val_size = int(total * val_ratio)
    
    train_pairs = pairs[:train_size]
    val_pairs = pairs[train_size:train_size + val_size]
    test_pairs = pairs[train_size + val_size:]
    
    print(f"📊 Dataset split:")
    print(f"   Train: {len(train_pairs)} pairs ({len(train_pairs)/total*100:.1f}%)")
    print(f"   Val:   {len(val_pairs)} pairs ({len(val_pairs)/total*100:.1f}%)")
    print(f"   Test:  {len(test_pairs)} pairs ({len(test_pairs)/total*100:.1f}%)")
    
    return train_pairs, val_pairs, test_pairs

def copy_files(pairs: List[Tuple[Path, Path]], 
               dest_images_dir: Path, 
               dest_labels_dir: Path,
               split_name: str) -> None:
    """Copy image-label pairs to destination directories"""
    
    print(f"📁 Copying {len(pairs)} {split_name} files...")
    
    for i, (img_file, label_file) in enumerate(pairs):
        # Copy image
        dest_img = dest_images_dir / img_file.name
        shutil.copy2(img_file, dest_img)
        
        # Copy label
        dest_label = dest_labels_dir / label_file.name
        shutil.copy2(label_file, dest_label)
        
        if (i + 1) % 100 == 0:
            print(f"   Copied {i + 1}/{len(pairs)} files...")
    
    print(f"✅ Completed copying {split_name} files")

def validate_dataset(dataset_path: Path) -> None:
    """Validate the prepared dataset"""
    
    print("\n🔍 Validating dataset...")
    
    splits = ["train", "val", "test"]
    total_images = 0
    total_labels = 0
    
    for split in splits:
        images_dir = dataset_path / "images" / split
        labels_dir = dataset_path / "labels" / split
        
        img_count = len(list(images_dir.glob("*.jpg")))
        label_count = len(list(labels_dir.glob("*.txt")))
        
        total_images += img_count
        total_labels += label_count
        
        print(f"   {split.capitalize()}: {img_count} images, {label_count} labels")
        
        if img_count != label_count:
            print(f"   ⚠️  Warning: Mismatch in {split} - {img_count} images vs {label_count} labels")
    
    print(f"\n📊 Total: {total_images} images, {total_labels} labels")
    
    # Check data.yaml exists
    data_yaml = dataset_path / "data.yaml"
    if data_yaml.exists():
        print("✅ data.yaml configuration file found")
    else:
        print("❌ data.yaml configuration file missing")

def main():
    """Main function to prepare the dataset"""
    
    print("🚀 Starting dataset preparation for Projeto Classe Excluded")
    print("=" * 60)
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Define paths
    base_path = Path("/Volumes/SSD NVME - Backup/TRAINING SYSTEM YOLO/datasets")
    source_path = base_path / "project-1-at-2025-10-08-07-10-8b70e39d"
    dest_path = base_path / "projeto-classe-excluded"
    
    # Check if source exists
    if not source_path.exists():
        print(f"❌ Source dataset not found at {source_path}")
        return
    
    # Create destination directory structure
    create_directory_structure(dest_path)
    
    # Get image-label pairs
    pairs = get_image_label_pairs(source_path)
    
    if not pairs:
        print("❌ No matching image-label pairs found!")
        return
    
    # Split dataset
    train_pairs, val_pairs, test_pairs = split_dataset(pairs)
    
    # Copy files to respective directories
    copy_files(train_pairs, dest_path / "images/train", dest_path / "labels/train", "train")
    copy_files(val_pairs, dest_path / "images/val", dest_path / "labels/val", "val")
    copy_files(test_pairs, dest_path / "images/test", dest_path / "labels/test", "test")
    
    # Validate the prepared dataset
    validate_dataset(dest_path)
    
    print("\n🎉 Dataset preparation completed successfully!")
    print(f"📁 Dataset ready at: {dest_path}")
    print(f"📄 Configuration file: {dest_path / 'data.yaml'}")

if __name__ == "__main__":
    main()