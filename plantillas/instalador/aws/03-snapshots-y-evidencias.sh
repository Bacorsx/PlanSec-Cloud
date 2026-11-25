#!/usr/bin/env bash
# Snapshots de los volúmenes de ambas instancias + salida de evidencias de la consola AWS.
# Uso: bash 03-snapshots-y-evidencias.sh [snapshots|ami|evidencias|todo]
#   ami: imagen de cada instancia ya endurecida, para relanzarla en minutos si falla (recuperación)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"; source "$DIR/infra-$NN.env"
export AWS_DEFAULT_REGION=$REGION
MODO="${1:-todo}"

if [[ "$MODO" == snapshots || "$MODO" == todo ]]; then
  for INST in "$WEB" "$BD"; do
    NOMBRE=$(aws ec2 describe-instances --instance-ids "$INST" --query 'Reservations[0].Instances[0].Tags[?Key==`Name`].Value|[0]' --output text)
    for VOL in $(aws ec2 describe-volumes --filters "Name=attachment.instance-id,Values=$INST" --query 'Volumes[].VolumeId' --output text); do
      SNAP=$(aws ec2 create-snapshot --volume-id "$VOL" --description "ti3062-$NN $NOMBRE $(date +%F)" \
        --tag-specifications "ResourceType=snapshot,Tags=[{Key=Name,Value=snap-$NOMBRE-$(date +%Y%m%d)},{Key=Proyecto,Value=ti3062-$NN}]" --query SnapshotId --output text)
      echo "Snapshot $SNAP de $VOL ($NOMBRE)"
    done
  done
fi

if [[ "$MODO" == ami || "$MODO" == todo ]]; then
  for INST in "$WEB" "$BD"; do
    NOMBRE=$(aws ec2 describe-instances --instance-ids "$INST" --query 'Reservations[0].Instances[0].Tags[?Key==`Name`].Value|[0]' --output text)
    AMI=$(aws ec2 create-image --instance-id "$INST" --no-reboot --name "ami-$NOMBRE-$(date +%Y%m%d-%H%M)" \
      --description "ti3062-$NN $NOMBRE endurecida (recuperacion)" \
      --tag-specifications "ResourceType=image,Tags=[{Key=Name,Value=ami-$NOMBRE},{Key=Proyecto,Value=ti3062-$NN}]" --query ImageId --output text)
    echo "AMI $AMI de $NOMBRE (relanzar: misma subred, IP privada $([[ $INST == "$WEB" ]] && echo "$WEB_IP" || echo "$BD_IP") y su SG)"
  done
fi

if [[ "$MODO" == evidencias || "$MODO" == todo ]]; then
  echo "== VPC";            aws ec2 describe-vpcs --vpc-ids "$VPC" --query 'Vpcs[].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table
  echo "== Subredes";       aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC" --query 'Subnets[].[Tags[?Key==`Name`].Value|[0],CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]' --output table
  echo "== Ruta pública";   aws ec2 describe-route-tables --route-table-ids "$RTPUB" --query 'RouteTables[0].Routes[].[DestinationCidrBlock,GatewayId]' --output table
  echo "== Ruta privada";   aws ec2 describe-route-tables --route-table-ids "$RTPRIV" --query 'RouteTables[0].Routes[].[DestinationCidrBlock,GatewayId,NatGatewayId]' --output table
  echo "== sg-web-$NN";     aws ec2 describe-security-groups --group-ids "$SGWEB" --query 'SecurityGroups[0].IpPermissions[].[FromPort,IpRanges[].CidrIp|join(`,`,@),UserIdGroupPairs[].GroupId|join(`,`,@)]' --output table
  echo "== sg-bd-$NN";      aws ec2 describe-security-groups --group-ids "$SGBD" --query 'SecurityGroups[0].IpPermissions[].[FromPort,IpRanges[].CidrIp|join(`,`,@),UserIdGroupPairs[].GroupId|join(`,`,@)]' --output table
  echo "== Instancias";     aws ec2 describe-instances --instance-ids "$WEB" "$BD" --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value|[0],PrivateIpAddress,PublicIpAddress,Placement.AvailabilityZone,State.Name]' --output table
  echo "== IP elástica";    aws ec2 describe-addresses --filters "Name=tag:Proyecto,Values=ti3062-$NN" --query 'Addresses[].[PublicIp,InstanceId,AllocationId]' --output table
  echo "== AMIs";           aws ec2 describe-images --owners self --filters "Name=tag:Proyecto,Values=ti3062-$NN" --query 'Images[].[ImageId,Name,State,CreationDate]' --output table
  echo "== Snapshots";      aws ec2 describe-snapshots --owner-ids self --filters "Name=tag:Proyecto,Values=ti3062-$NN" --query 'Snapshots[].[SnapshotId,VolumeId,StartTime,State]' --output table
fi
