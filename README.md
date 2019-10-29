# Open Classrooms, formation Data Architect
# Projet : Réalisez un apprentissage distribué

**Mission:**

J'ai créé une application permettant de de faire une classification d’image. Pour cela j’ai séparé les images en jeux d'apprentissage et de test, d'extraire les features des images en provenance de deux classes différentes, d'apprendre un modèle sur les données d'apprentissage et de mesurer les performances du modèle sur les données de test. 
J’ai fait la classification "1 vs 1" et la classification "1 vs All".
Le programme peut se lancer en local ou déployé sur un cluster de calcul sur Amazon Web Services EMR. Les données peuvent être enregistrer en local ou sur S3 de AWS.


**Contexte :**
* Utilisation du modèle de classification SVMWithSGD du package spark MLlib.
* Utilisation de library keras pour pouvoir utiliser les images. (Obtenir une représentation d'images sous la forme d'un tableau de 4096 valeurs flottantes.)
* Une Dataset de 37 classes différents de chiens et de chats. Chaque classe a environs 200 images.


## inclus :

**extract-featuresAws.py :** programme qui extrait les features des images en local ou sur AWS 
**classificationRaceAws.py :** programme principal de classification d'image. Il peut être lancé en local ou sur EMR d'AWS
**images/ :** répertoire qui contient les images en format jpeg
**bootstrapAWS.sh :** script d'installation des library nécessaires
**launchAWS.sh :** script de création de cluster EMR en lançant les programmes suivant:
    - bootstrapAWS.sh
    - extract-featuresAws.py
    - classificationRaceAws.py
**resultat.txt :** fichier de résultat qui contient la performance du model
**features/ :** répertoire des features des images. Chaque feature d'image est un fichier en format json.
**preformance.pdf :** Un pdf représentant l'évolution des performances du modèle en fonction du nombre d'images d'apprentissage.

## note
Pour chacune des images, il faut d’abord produire une représentation de l’image sous la forme d’un tableau de 4096 valeurs flottantes, ce qui permettra de réaliser des calculs sur cette représentation. Transformation de fichier jpeg en fichier json et ensuite sauvegarder tout dans un RDD.


## Usage
Les programmes peuvent se lancer en local ou sur AWS.
* En local : 
    * programme d'extraction des features:
        ```
        python [nom du programme] [répertoire des fichiers jpeg]
        
        Par exemple: 
            python extract-featuresAws.py images/*.jpg
        ```
    * programme principal:
        ```
        spark-submit [nom du programme] [repertoire des fichiers json]  [race 1] [race 2]

        Par exemple: 
            spark-submit classificationRaceAws.py ~/Documents/dev/datascience/features  wheaten_terrier yorkshire_terrier
        ```
        Si c'est une classification 1 vs tous mettre **None** à la place de [race 2]
        
    Je lance le programme dans un virtual machine avec 1 processeur de 8G et 15 Mo de mémoire vive: j'ai donc 2 configurations que j'ai testé qui améliore mon programme.
    ```
    spark-submit --num-executors 2 --executor-cores 1 --executor-memory 1G --driver-memory 2G classificationRaceAws.py ~/Documents/dev/datascience/features  wheaten_terrier yorkshire_terrier
    
    Le 2eme est beaucoup pour ce que je fais.
    
    spark-submit --num-executors 1 --executor-cores 4 --executor-memory 6G --driver-memory 4G classificationRaceAws.py ~/Documents/dev/datascience/features  wheaten_terrier yorkshire_terrier
    ```
    
* Sur AWS, les paramètres sont en dur dans le programe. En cas de besoin changez le code. 
        - données sont enregistré sur S3
        - bucket = oc-datascience-p2
        - répertoire des images jpeg = images
        - répertoire des features json : features

    Je lance le programme dans un cluster EMR avec :
    Master : 1 instance de m5 xlarge, 4 vCore, 16G mémoire
    Nœuds d’executeurs (machines) : 3 instances de m5 xlarge, 4 vCore, 16G mémoire chacun

    Pour les 4 instances 64G de mémoire disque mais je n’utilise pas car je n’ai pas fait de persistance de données. J’utilise que la mémoire vive dans le programme. 

    Donc je lance le programme avec les paramètres suivant :
    spark.rpc.message.maxSize=1024 : la taille maximum des messages qui sont utilisés entre les processus des executors
    num-executors  = 3 (1 par machine)
    executor-cores  = 3 (1 executor-core par executor)
    executor-memory = 10G (J’ai enlevé 6G pour d’autre traitements)
    driver-memory = 10G memoire de Master
 

* programe d'extraction des features:
    
    ```
    spark-submit [nom du programme] aws
    Par exemple: 
        spark-submit extract-featuresAws.py aws
        
    ```
    * programme principal:
    ```
    spark-submit [nom du programme] aws  [race 1] [race 2]
    Par exemple: 
        spark-submit classificationRaceAws.py aws  wheaten_terrier yorkshire_terrier
    ```
    Si c'est une classification 1 vs tous mettre **None** à la place de [race 2]

    Quand le lance le programme sur AWS et mes données sont sur S3:  
    ```
    spark-submit --deploy-mode cluster --master yarn --num-executors 3 --executor-cores 3 --executor-memory 10G --driver-memory 10G --conf spark.rpc.message.maxSize=1024 s3://oc-datascience-p2/classificationRaceAws.py aws wheaten_terrier yorkshire_terrier

    ```
    
    Quand le lance le programme en local et mes données sont sur S3:  
    ```
    spark-submit --num-executors 1   --executor-cores 4    --executor-memory 6G   --driver-memory 4G classificationRaceAws.py aws  wheaten_terrier yorkshire_terrier
    ```
    
    Le nombre d'itérations = 100 et la proportion de cas d'entrainement = 7 et cas de test = 3 est en dure dans le code. 
    Vous pouvez le modifiez en cas de besoin.


## Prérequis

* Spark 2.4.4 et python  2
* package et library a installé : boto, boto3, keras, tensorflow, h5py, pillow, pyspark, mllib
En plus sur AWS : Hadoop 2.8.5, Spark 2.4.3 et TensorFlow 1.13.1 

## Installation sur EMR d'AWS
Lancer launchAWS.sh sur aws-cli:
    Bootstrap.sh va installer les packages nécessaires
    Une fois fini on aura 2 étapes :
        -changer les images en fichiers json (extract-featuresAws.py) 
        -lancer le programme principal (classificationRaceAws.py)
    N'oubliez pas de mettre le répertoire des images en local ou sur S3 sur AWS


## Le résultat : 

Est la performance de modèle par rapport à l'image testé

### wheaten_terrier vs yorkshire_terrier :

La performance du modèle est de **98%** avec les options ci-dessous :
    - 200 images dans chaque race
    - Proportion de cas d’entrainement = 7 et cas de test = 3
    - Nombre d’itérations = 100
    - seed fixe (= 20)

Voir performance.pdf

### wheaten_terrier vs tous

La performance du modèle est de **98%** avec les options ci-dessous :
    - 200 images dans chaque race
    - Proportion de cas d’entrainement = 7 et cas de test = 3
    - Nombre d’itérations = 100
    - seed fixe (= 20)
    
La performance du modèle est de **97%** avec les options ci-dessous :
    - 200 images dans chaque race
    - Proportion de cas d’entrainement = 1 et cas de test = 9
    - Nombre iterations = 100
    - seed fixe (=20)

Voir performance.pdf

### Résultat des différents tests effectués :

8 images de performance de modèle : 4 --> 1 vs 1 et 4 --> 1 vs tous
Pour les 1 vs tous, la performance du modèle reste toujours au-dessus de 97%.
Pour les 1 vs 1 : cela dépend des 2 races choisi. Plus ils se ressemblent, moins est la performance du model. Donc il faut augmenter la proportion d’entrainement.

Dès fois quand on pousse les proportions, jusqu'au extrémités, 1, 9 ou 9, 1, nous avons des résultats pas corrects. Donc à éviter

Pour moi les propositions le plus stable est la proportion de cas d’entrainement = 7 et cas de test = 3 avec le nombre d’itérations à 100 pour notre projet.


## performances du programme :

En local :
* 1 vs 1 : environ 2 minutes 20 secondes
* 1 vs tous : environ 2 minutes 30 secondes

Sur AWS:
* 1 vs 1 : environ 9 minutes 
* 1 vs tous : environ 9 minutes

## Todo :

Dans le programme j’amène les données de S3 en une fois et ensuite je parallélise. 
Il faut améliorer cela avec spark pour amener les données en parallèle et non pas en une fois pour utiliser la puissance de spark. C’est la partie avec boto où je n’ai pas trouvé beaucoup de documentation.

Pour améliorer les performance de programme et réduire le temps de traitement sur les fonction de pyspark, j'ai augmenté le driver-memory à 4G (2G), j'ai dit num-executors 1 (2) pour les traitement en parallèle chacun avec 4 executor-core(1 executor-core) dont le driver-memory de chaque executor-core est 6G (2G)
Il faut encore chercher pour trouver les meilleur options en local.