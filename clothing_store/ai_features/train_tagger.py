import os
import shutil
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator


CATEGORIES = ['Shirt', 'T-Shirt', 'Jacket', 'Pants', 'Suit', 'Shoes']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'dummy_dataset')
MODEL_PATH = os.path.join(BASE_DIR, 'menswear_tagger.h5')


def generate_dummy_data():
    """
    Creates a temporary dummy dataset so the user can test the training script
    without needing to download a real fashion dataset right away.
    """
    if os.path.exists(DATASET_DIR):
        shutil.rmtree(DATASET_DIR)
        
    print("Generating dummy training dataset for transfer learning...")
    for category in CATEGORIES:
        cat_dir = os.path.join(DATASET_DIR, category)
        os.makedirs(cat_dir, exist_ok=True)
        # Create 10 dummy images per category
        for i in range(10):
            # Create a simple colored square image
            color = tuple(np.random.randint(0, 255, 3))
            img = Image.new('RGB', (224, 224), color=color)
            img.save(os.path.join(cat_dir, f"{category.lower()}_{i}.jpg"))
            
    print(f"Dummy dataset created at {DATASET_DIR}")


def build_and_train_model():
    """
    Fine-tunes MobileNetV2 on our specific menswear classes.
    """
    print("Loading base MobileNetV2 model (without the ImageNet head)...")
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    
    # Freeze the base layers so we only train the new classification head
    print("Freezing base model weights...")
    base_model.trainable = False
    
    # Add our custom classification head
    print(f"Adding custom classification head for: {CATEGORIES}")
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    predictions = Dense(len(CATEGORIES), activation='softmax')(x)
    
    # Combine into our final custom model
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # Compile the model
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    
    # Load the data
    train_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
    
    print("Loading images from directory...")
    train_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(224, 224),
        batch_size=8,
        class_mode='categorical',
        shuffle=True
    )
    
    # Train the model (Using 5 epochs on the dummy data; for real dataset, you'd use 10-20)
    print("\n--- Starting Fine-Tuning Process ---")
    model.fit(
        train_generator,
        epochs=5,
        steps_per_epoch=max(1, train_generator.samples // 8)
    )
    
    print(f"\nTraining Complete! Saving custom model to {MODEL_PATH}")
    model.save(MODEL_PATH)


if __name__ == '__main__':
    generate_dummy_data()
    build_and_train_model()
    print("Successfully fine-tuned and saved the AI tagger model.")
