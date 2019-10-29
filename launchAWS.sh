#!/bin/bash
#launch cluster
aws emr create-cluster --applications Name=Spark Name=Hadoop Name=TensorFlow \
--ec2-attributes '{"KeyName":"keyAWS","InstanceProfile":"EMR_EC2_DefaultRole","SubnetId":"subnet-2059dd7a","EmrManagedSlaveSecurityGroup":"sg-1ebbe66a","EmrManagedMasterSecurityGroup":"sg-1ebbe66a"}' \
--release-label emr-5.25.0 \
--log-uri 's3n://aws-logs-455260197376-eu-west-3/elasticmapreduce/' \
--steps '[{"Args":["spark-submit","--deploy-mode","cluster","--master","yarn","--num-executors","3","--executor-cores","3","--executor-memory","10G","--driver-memory","10G","--conf","spark.rpc.message.maxSize=1024","s3://oc-datascience-p2/extract-featuresAws.py","aws"],"Type":"CUSTOM_JAR","ActionOnFailure":"CONTINUE","Jar":"command-runner.jar","Properties":"","Name":"Spark application"},{"Args":["spark-submit","--deploy-mode","cluster","--master","yarn","--num-executors","3","--executor-cores","3","--executor-memory","10G","--driver-memory","10G","--conf","spark.rpc.message.maxSize=1024","s3://oc-datascience-p2/classificationRaceAws.py","aws","wheaten_terrier","yorkshire_terrier"],"Type":"CUSTOM_JAR","ActionOnFailure":"CONTINUE","Jar":"command-runner.jar","Properties":"","Name":"Spark application"}]' \
--instance-groups '[{"InstanceCount":3,"EbsConfiguration":{"EbsBlockDeviceConfigs":[{"VolumeSpecification":{"SizeInGB":32,"VolumeType":"gp2"},"VolumesPerInstance":2}]},"InstanceGroupType":"CORE","InstanceType":"m5.xlarge","Name":"Core - 2"},{"InstanceCount":1,"EbsConfiguration":{"EbsBlockDeviceConfigs":[{"VolumeSpecification":{"SizeInGB":32,"VolumeType":"gp2"},"VolumesPerInstance":2}]},"InstanceGroupType":"MASTER","InstanceType":"m5.xlarge","Name":"Master Instance Group"}]' \
--bootstrap-actions '[{"Path":"s3://oc-datascience-p2/bootstrapAWS.sh","Name":"Custom action"}]' \
--ebs-root-volume-size 10 \
--service-role EMR_DefaultRole \
--enable-debugging \
--name 'Azadeh cluster OC -extract features' \
--scale-down-behavior TERMINATE_AT_TASK_COMPLETION \
--region eu-west-1