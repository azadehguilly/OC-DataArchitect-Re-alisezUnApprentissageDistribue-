# coding=utf-8
# ! /usr/bin/env python2

import json
import sys
from io import BytesIO

import boto3
import numpy as np
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input
from keras.models import Model
from keras.preprocessing import image


def extract_features(model, image_path):
    img = image.load_img(image_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    features = model.predict(x)
    return features.tolist()[0]


# extraction des features sur aws
def extract_all_features():
    # information pour la connexion au bucket d'aws
    s3 = boto3.resource('s3')
    s3c = boto3.client('s3')
    bucket = "oc-datascience-p2"  # nom de ma bucket

    base_model = VGG16(weights='imagenet')
    model = Model(input=base_model.input, output=base_model.get_layer('fc2').output)

    bucketObj = s3.Bucket(bucket)

    # extraction des information de toutes les images contenant dans le repertoire images et les mettre dans le repertoir features
    for my_bucket_object in bucketObj.objects.filter(Prefix='images/'):
        if my_bucket_object.key != "images/":
            response = my_bucket_object.get()
            data = BytesIO(response['Body'].read())
            features = extract_features(model, data)
            keyJ = my_bucket_object.key
            path = keyJ.split("images/")
            keyJ = "features/" + path[1] + ".json"
            s3c.put_object(Body=json.dumps(features), Bucket=bucket, Key=keyJ)


def main():
    # si l'extraction est pour aws
    if (sys.argv[1] == 'aws'):
        extract_all_features()

    # si l'extraction est en local
    else:
        # Load model VGG16 as described in https://arxiv.org/abs/1409.1556
        # This is going to take some time...
        base_model = VGG16(weights='imagenet')
        # Model will produce the output of the 'fc2'layer which is the penultimate neural network layer
        # (see the paper above for mode details)
        model = Model(input=base_model.input, output=base_model.get_layer('fc2').output)

        # For each image, extract the representation
        for image_path in sys.argv[1:]:
            features = extract_features(model, image_path)
            # J'enregistre l'extraction dans le repertoire features
            splitImage = image_path.split("/")
            with open("features/" + splitImage[1] + ".json",
                      "w") as out:  # @TODO si le repertoire features n'existe pas le crééer !
                json.dump(features, out)


if __name__ == "__main__":
    main()