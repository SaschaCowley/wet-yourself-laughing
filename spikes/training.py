import os

import matplotlib.pyplot as plt
import tensorflow as tf

# Diagnostics
print(f'Tensorflow version: {tf.__version__}')
print(f'Eager execution: {tf.executing_eagerly()}')


# Get training data
train_dataset_url = "http://storage.googleapis.com/asia_audioset/youtube_corpus/v1/features/features.tar.gz"
#train_dataset_fp = tf.keras.utils.get_file(
#    fname="audioset_v1_embeddings.tar.gz", origin=train_dataset_url, file_hash="cd95d500ab2422d4233cb822e25cf73033633e2068eab64d39024e85125cb760", extract=True)
#print(f'Training dataset: {train_dataset_fp}')
#print(os.path.join(os.path.dirname(train_dataset_fp), "audioset_v1_embeddings/bal_train"))

files = tf.io.matching_files("C:\\Users\\sasch\\.keras\\datasets\\audioset_v1_embeddings\\bal_train\\*.tfrecord")

train_dataset = tf.data.TFRecordDataset(filenames=files)

print(type(next(iter(train_dataset))))
