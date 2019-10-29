# coding=utf-8
# ! /usr/bin/env python2
import sys
import boto3
import pyspark
from pyspark.mllib.classification import SVMWithSGD
from pyspark.mllib.regression import LabeledPoint
from pyspark.sql import SparkSession

sc = pyspark.SparkContext()


# cette fonction permet de se connecter au bucket et enregistrer toutes les fichier json dans un rdd
def s3ToRdd():
    s3 = boto3.resource('s3')
    bucket = "oc-datascience-p2"  # nom de ma bucket
    bucketObj = s3.Bucket(bucket)

    key_list = []

    spark = SparkSession.builder.getOrCreate()
    spark.sparkContext.setLogLevel('ERROR')

    for my_bucket_object in bucketObj.objects.filter(Prefix='features/'):
        if my_bucket_object.key != "features/":
            # mettre le nom de fichier dans name
            name = my_bucket_object.key
            # mettre les données dans data et changer les byte en str pour pouvoir le mettre dans un tuple.
            # Pour ressembler au rdd qu'on peut manipuler.
            response = my_bucket_object.get()
            data = response['Body'].read().decode("utf-8")
            key_list.append((name, data))

    rdd = sc.parallelize(key_list)
    return rdd




# cette fonction permet de trouver le nom de la race par rapport au nom complet de l'image
# val: est le nom de fichier (image)
# return : nom de la race
def race(val):
    return '_'.join(val.split('/')[-1].split('_')[:-1])


# cette fonction nettoie le format des valeurs de RDD d'entrée
# data: RDD qui doit être nettoyer
# return : RDD propre, sans espace, split sur les ","
def format_data(data):
    return list(map(lambda x: float(x), data.strip("[]").replace(' ', '').split(",")))


# fonction qui renvoie 1 si une chaine de charactère donnée, est dans une autre chaine. Sinon 0.
# cela permet de distinguer le race que l'ont souhaite de tester
# label : race qu'on test
# x: dans la chaine qu'on test
# return : 1 si la label est dans x, sinon 0
def put_label(label, x):
    if (label.lower() in x.lower()):
        return 1
    else:
        return 0


# fonction qui filtre 2 races dans toutes les races
# x : la chaine dans la quelle on cherche
# label1: la 1ere valeur qu'on cherche dans x
# label2: la 2eme valeur qu'on cherche dans x
# return : vrai si label1 ou label2 existe dans la chaine x
def filter_labels(x, label1, label2):
    return ((label1.lower() in x.lower()) | (label2.lower() in x.lower()))


# dans le cas de 1 vs 1, filtre 2 races dans toutes les races. par exemple Abyssinian et American_pit_bull_terrier
# rdd1Label1 : la 1ere race à filtrer dans rddToFilter
# rdd1Label2 : la 2eme race à filtrer dans rddToFilter
# rddToFilter : RDD qui contient la totalité des races
# return : un RDD avec les 2 races recherché.
def filter1(rdd1Label1, rdd2Label0, rddToFilter):
    return rddToFilter.filter(lambda f: filter_labels(f[0], rdd1Label1, rdd2Label0))


# dans le cas de 1 vs tous, filtre sur Abyssinian et ensuite met le label = 1 les autres = 0
# change le nom de la race qu'on test en 1 et tous les autres en 0
# rdd1Label1 : la race qu'on test
# rddToChange : RDD dans la quelle on va changer le nom des race
# return : un nouveau RDD qu'à la place des nom des race contient 1 si c'est la race qu'on cherche ou 0 si ce n'est pas la race qu'on cherche.
def changeLabel(rdd1Label1, rddToChange):
    return rddToChange.map(lambda y: (put_label(rdd1Label1, y[0]), y[1]))


# Cette fonction est l'intelligence metier du programe, il lance tout le programme
# sc : pyspark.SparkContext()
# path :
#   en mode local : chemin de fichier des images transformé en json
#   en mode aws : on met aws, il prend le repertoire de "features" dans S3
# race1 : la 1ere race qu'on test
# race2 :
#   pour 1 vs 1: la 2eme race qu'on test
#   pour 1 vs tous : None
# return : le pourcentage de bonne classification du model
def process(sc, path, race1, race2):
    # 1 Charger tous les images dans un RDD
    if (path == 'aws'):
        toutRDD = s3ToRdd()
    else:
        toutRDD = sc.wholeTextFiles(path + "/*.json")

    # 2 retravailler les données des deux colonnes (nom de fichier et les valeurs)
    toutRDDPropre = toutRDD.map(lambda x: (race(x[0]), format_data(x[1])))

    # 3

    #  1 vs tous changer le nom de la race en 1 et les autres races en 0
    if (race2 == 'None'):
        labelRDD = changeLabel(race1, toutRDDPropre)

    #  1 vs 1  filtrer les 2 races et changer le nom de la race1 en 1 et le race2 en 0
    else:
        labelRDDFilter = filter1(race1, race2, toutRDDPropre)
        labelRDD = changeLabel(race1, labelRDDFilter)

    # 4 couper en 2 dataframes d'apprentissage et test

    #  1 vs tous
    apprentissageRDD, testRDD = labelRDD.randomSplit(weights=[0.7, 0.3], seed=20)

    # 5 transformer en labelpoint le RDD d'apprentissage (1, 0000011 (touts les chiffres))
    apprentissageLabelPoint = apprentissageRDD.map(lambda x: LabeledPoint(x[0], x[1]))

    # 6 creer le model
    model = SVMWithSGD.train(apprentissageLabelPoint, iterations=100)

    # 7 appliquer le model sur l echantillon de test
    resultat = testRDD.map(lambda x: (x[0], model.predict(x[1])))

    # 8 calculer la precision, calculer le taux de succès du modèle (le pourcentage de bonnes classifications)
    test_accuracy = float(resultat.filter(lambda a: a[0] == a[1]).count()) / float(testRDD.count())

    return test_accuracy


# Cette méthode nous permet d'enregistrer le résultat dans un fichier nommé resultat.txt
def resultat(path,race1, race2, test_accuracy):
    if (path == 'aws'):
        # information pour la connexion au bucket d'aws
        s3 = boto3.resource('s3')
        s3c = boto3.client('s3')
        bucket = "oc-datascience-p2"  # nom de ma bucket
        bucketObj = s3.Bucket(bucket)

        keyJ = "resultat.txt"
        if (race2 == 'None'):
            data = race1+ ' --->  '+ str(test_accuracy)
        else:
            data = race1 + '  -  ' + race2 + ' ----->  '+ str(test_accuracy)

        s3c.put_object(Body=data, Bucket=bucket, Key=keyJ)

    else:
        fichier = open("resultat.txt", "w")
        if (race2 == 'None'):
            fichier.write("\n local 1 vs tous")
            fichier.write(race1 + '\t  --->  \t' + str(test_accuracy))
            fichier.write('\n' + str(test_accuracy))
            fichier.close()

        else:
            fichier.write("\n local 1 vs 1")
            fichier.write(race1 + '   -   \t' + race2 + ' --->  \t' + str(test_accuracy))
            fichier.write('\n' + str(test_accuracy))
            fichier.close()


def main(path, race1, race2):
    test_accuracy = process(sc, path, race1, race2)
    resultat( path, race1, race2, test_accuracy)


if __name__ == '__main__':
    if (len(sys.argv) == 4):
        main(*sys.argv[1:4])
    else:
        print("nombre argument incorrect")
        print("si vous voulez lancer avec les données de S3, mettez aws après le nom de programme ensuite les 1/2 races")
        print("si vous voulez lancer 1 vs tous il faut mettre None pour le race 2")