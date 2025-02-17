
import tensorflow as tf
import glob
import os, os.path
import cv2
import time
import numpy as np
import itertools
import matplotlib.pyplot as plt
from google.colab import files
from google.colab import drive
from sklearn.preprocessing import LabelEncoder
from tensorflow.python import keras
from tensorflow.python.keras.models import Sequential, load_model
from sklearn.model_selection import train_test_split
from tensorflow.python.keras.layers import Dense, Flatten, Conv2D, Dropout, MaxPooling2D
from tensorflow.python.keras.preprocessing.image import ImageDataGenerator
from keras.utils.np_utils import to_categorical
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
sns.set()
from keras.utils import print_summary
from datetime import datetime
from pathlib import Path

"""Checking tensorflow version and gpu device name"""

device_name = tf.test.gpu_device_name()
print(device_name)
print(tf.__version__)

"""Mounting google drive"""

# drive.mount('/content/drive/')

"""unzipping asl-alphabet.zip folder"""

# !unzip drive/My\ Drive/asl-alphabet.zip

"""Setting up global variables"""

TRAIN_DIR = "asl_alphabet_train/asl_alphabet_train"
TEST_DIR = "asl_alphabet_test/asl_alphabet_test"
CATEGORIES = os.listdir(TRAIN_DIR) # dir is your directory path
CATEGORIES.sort()
# CATEGORIES will be like that ['A', 'B', 'C', 'D',..............., 'del', 'nothing', 'space']
TEST_DATA = os.listdir(TEST_DIR)
TEST_DATA.sort()
# ['A_test.jpg', 'B_test.jpg', 'C_test.jpg', ..................., 'nothing_test.jpg', 'space_test.jpg']
# In the testing data the is no image for the del category
CATEGORY_NO = len(CATEGORIES)
IMAGE_SIZE = 50
ENCODER = LabelEncoder()
ENCODED_CATEGORIES = ENCODER.fit_transform(CATEGORIES)

MODEL_DIR = "model"
MODEL_PATH = MODEL_DIR + "/cnn-model.h5"
MODEL_WEIGHTS_PATH = MODEL_DIR + "/cnn-model.weights.h5"
MODEL_CHECKPOINTS= MODEL_DIR + "/checkpoints/cp.ckpt"
os.mkdir(MODEL_DIR)

"""Read and create Trainging labels along with its labels"""

def preprocessing(img):
  laplacian_imange = cv2.Laplacian(img, cv2.CV_64F)
  return img

def create_training_data():
  X_train_data = []
  Y_train_data = []
  X_train = []
  Y_train = []
  for index, category in enumerate(CATEGORIES):
    path = os.path.join(TRAIN_DIR,category)
    category_number = ENCODED_CATEGORIES[index]
    for img in os.listdir(path):
      try:
        img_array = cv2.imread(os.path.join(path,img), cv2.IMREAD_GRAYSCALE)
        new_array  = cv2.resize(img_array, (IMAGE_SIZE, IMAGE_SIZE))
        preprocessed_image = preprocessing(new_array)
        X_train_data.append(preprocessed_image)
        Y_train_data.append(category_number)
      except Exception as e:
        pass
  X_train = np.array(X_train_data).reshape(-1, IMAGE_SIZE, IMAGE_SIZE, 1)
  Y_train = np.array(Y_train_data)
  return X_train, Y_train

"""Building the model"""

def build_model(save=False):
  print('Building model ....')
  model = Sequential()
    
  model.add(Conv2D(64, kernel_size=3, strides=1, activation='relu', input_shape=(IMAGE_SIZE, IMAGE_SIZE, 1)))
  model.add(Conv2D(64, kernel_size=3, strides=2, activation='relu'))
  model.add(Dropout(0.25))
  model.add(Conv2D(128, kernel_size=3, strides=1, activation='relu'))
  model.add(Conv2D(128, kernel_size=3, strides=2, activation='relu'))
  model.add(Dropout(0.25))
  model.add(Conv2D(256, kernel_size=3, strides=1, activation='relu'))
  model.add(Conv2D(256, kernel_size=3, strides=2, activation='relu'))
  model.add(Flatten())
  model.add(Dropout(0.25))
  model.add(Dense(512, activation='relu'))
  model.add(Dense(CATEGORY_NO, activation='softmax'))

  model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

  if save: model.save(MODEL_PATH)
   
  return model

"""Fitting the model"""

def fit_model(model, train_generator, validation_data, epochs_number, save=False):

  cp_callback = keras.callbacks.ModelCheckpoint(filepath=MODEL_CHECKPOINTS,
                                                 save_weights_only=True,
                                                 verbose=1)
  
  logdir= MODEL_DIR + "logs/fit/" + datetime.now().strftime("%Y%m%d-%H%M%S")
  tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir)

  fit = model.fit_generator(train_generator,
                            epochs = epochs_number,
                            validation_data = validation_data,
                            callbacks = [cp_callback, tensorboard_callback])
  
  if save: model.save_weights(MODEL_WEIGHTS_PATH)

  return fit

def split_data_to_train_and_validation(X_train, Y_train, val_size):
  X_train, X_val, Y_train, Y_val = train_test_split(X_train, Y_train, test_size = val_size, random_state=2)
  return X_train, X_val, Y_train, Y_val

"""Training the Model"""

print("reading data and preproccessing")
X_train, Y_train = create_training_data()
print ('reading and preproccessing finished')
X_train, X_val, Y_train, Y_val = split_data_to_train_and_validation(X_train, Y_train, 0.1)
print('starting data augmentation')
data_generator_with_aug = ImageDataGenerator(
                                   horizontal_flip=False,
                                   vertical_flip=False,
                                   width_shift_range = 0.1,
                                   height_shift_range = 0.1,
                                   rotation_range=5
                                  )

data_generator_with_aug.fit(X_train)

cnn_model = build_model(save=True)
History = fit_model(cnn_model, data_generator_with_aug.flow(X_train,Y_train, batch_size=64), (X_val,Y_val), 5, save=True )

"""Read and create Test data along with its labels"""

def create_testing_data():
  X_test = []
  Y_test = []
  for test in TEST_DATA:
    data = test.split("_")
    category_number = CATEGORIES.index(data[0])
    try:
      img_array = cv2.imread(os.path.join(TEST_DIR,test), cv2.IMREAD_GRAYSCALE)
      new_array  = cv2.resize(img_array, (IMAGE_SIZE, IMAGE_SIZE))
      laplacian_image = preprocessing(new_array)
      X_test.append(laplacian_image)
      Y_test.append(category_number)
    except Exception as e:
      pass
  X_test1 = np.array(X_test).reshape(-1, IMAGE_SIZE, IMAGE_SIZE, 1)
  print(X_test1.shape)
  return X_test1, Y_test

"""Plot Confusion matrix (This code is from sklearn documentation)"""

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')


    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

"""Method for testing already preproccessed data"""

def test_preproccessed_data(model, X_test, Y_test):
  start_time = time.time()
  y = model.predict(X_test)
  print('Took {:.0f} seconds to get predictions on this set.'.format(
        time.time() - start_time))
  results = np.argmax(y, axis=1)
  accuracy_test = accuracy_score(results, Y_test)
  print('accuracy_score:', accuracy_test)
  cm = confusion_matrix(Y_test, results)
  with sns.axes_style('ticks'):
      plt.figure(figsize=(16, 16))
      plot_confusion_matrix(cm, CATEGORIES)
      plt.show()
  return results

"""Testing Both asl_alphabet_test images and validation Images"""

print_summary(cnn_model)
X_test, Y_test = create_testing_data()
y_pred_test = test_preproccessed_data(cnn_model, X_test, Y_test)
y_pred_val = test_preproccessed_data(cnn_model, X_val, Y_val)
print(classification_report(Y_val, y_pred_val, target_names=CATEGORIES))

"""Loading Model and its weights from local files you need to change the MODEL_PATH and MODEL_WEIGHTS_PATH in global variable to the path where these data are stored in"""

def load_model_and_weights_from_disk():
  model_file = Path(MODEL_PATH)
  model_weights_file = Path(MODEL_WEIGHTS_PATH)
  if model_file.is_file() and model_weights_file.is_file():
    print('Retrieving model from disk...')
    model = load_model(model_file.__str__())
                
    print('Loading CNN model weights from disk...')
    model.load_weights(model_weights_file.__str__())
    return model
    
  return None

"""Method for testing extrenal images, Here preproccessing is applied first then the model make its prediction"""

def test_data(model, images):
  X_test = []
  for img in images:
    try:
      img_array = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
      new_array  = cv2.resize(img_array, (IMAGE_SIZE, IMAGE_SIZE))
      laplacian_image = preprocessing(new_array)
      X_test.append(laplacian_image)
    except Exception as e:
      pass
  test_data = np.array(X_test).reshape(-1, IMAGE_SIZE, IMAGE_SIZE, 1)
  y_test_data = model.predict(test_data)
  results = np.argmax(y_test_data, axis=1)

  for y, index in enumerate(results):
    print(images[index] + " --> "+ CATEGORIES[y])
  return results

"""Testing on extrenal images, for this just put the path to the image in the images array"""

# Uncomment the line below if you want to load_model and its weight 
# cnn_model = load_model_and_weights_from_disk()
images = ["asl_alphabet_test/asl_alphabet_test/A_test.jpg", "asl_alphabet_test/asl_alphabet_test/B_test.jpg"]
test_data(cnn_model, images )
