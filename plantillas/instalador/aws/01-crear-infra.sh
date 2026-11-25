#!/usr/bin/env bash
# Crea en AWS (receptor del despliegue) toda la red y las dos instancias del proyecto.
# Ejecutar en AWS CloudShell o en un PC con AWS CLI y las credenciales de AWS Academy (AWS Details).
# Uso: bash 01-crear-infra.sh <TU_IP_PUBLICA>      (ej: 190.20.30.40)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
ADMIN_IP="${1:?Uso: $0 <tu IP pública de administración, ej 190.20.30.40>}"
ADMIN_CIDR="${ADMIN_IP%/*}/32"
export AWS_DEFAULT_REGION=$REGION
ESTADO="$DIR/infra-$NN.env"
tag() { echo "ResourceType=$1,Tags=[{Key=Name,Value=$2},{Key=Proyecto,Value=ti3062-$NN}]"; }
paso() { echo -e "\n\033[1;36m▶ $*\033[0m"; }

if [[ -f "$ESTADO" ]]; then echo "Ya existe $ESTADO (infraestructura creada). Bórralo solo si eliminaste los recursos."; exit 1; fi

paso "VPC $VPC_NOMBRE $VPC_CIDR"
VPC=$(aws ec2 create-vpc --cidr-block "$VPC_CIDR" --tag-specifications "$(tag vpc "$VPC_NOMBRE")" --query Vpc.VpcId --output text)
aws ec2 modify-vpc-attribute --vpc-id "$VPC" --enable-dns-support '{"Value":true}'
aws ec2 modify-vpc-attribute --vpc-id "$VPC" --enable-dns-hostnames '{"Value":true}'
echo "VPC=$VPC" > "$ESTADO"

paso "Subredes en $ZONA"
PUB=$(aws ec2 create-subnet --vpc-id "$VPC" --cidr-block "$PUB_CIDR" --availability-zone "$ZONA" --tag-specifications "$(tag subnet "subred-publica-$NN")" --query Subnet.SubnetId --output text)
PRIV=$(aws ec2 create-subnet --vpc-id "$VPC" --cidr-block "$PRIV_CIDR" --availability-zone "$ZONA" --tag-specifications "$(tag subnet "subred-privada-$NN")" --query Subnet.SubnetId --output text)
aws ec2 modify-subnet-attribute --subnet-id "$PUB" --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id "$PRIV" --no-map-public-ip-on-launch
echo -e "PUB=$PUB\nPRIV=$PRIV" >> "$ESTADO"

paso "Internet Gateway IGW-$NN"
IGW=$(aws ec2 create-internet-gateway --tag-specifications "$(tag internet-gateway "IGW-$NN")" --query InternetGateway.InternetGatewayId --output text)
aws ec2 attach-internet-gateway --internet-gateway-id "$IGW" --vpc-id "$VPC"
echo "IGW=$IGW" >> "$ESTADO"

paso "Tablas de rutas"
RTPUB=$(aws ec2 create-route-table --vpc-id "$VPC" --tag-specifications "$(tag route-table "rt-publica-$NN")" --query RouteTable.RouteTableId --output text)
aws ec2 create-route --route-table-id "$RTPUB" --destination-cidr-block 0.0.0.0/0 --gateway-id "$IGW" >/dev/null
aws ec2 associate-route-table --route-table-id "$RTPUB" --subnet-id "$PUB" >/dev/null
RTPRIV=$(aws ec2 create-route-table --vpc-id "$VPC" --tag-specifications "$(tag route-table "rt-privada-$NN")" --query RouteTable.RouteTableId --output text)
aws ec2 associate-route-table --route-table-id "$RTPRIV" --subnet-id "$PRIV" >/dev/null
echo -e "RTPUB=$RTPUB\nRTPRIV=$RTPRIV" >> "$ESTADO"

paso "Security Groups (mínimo privilegio)"
SGWEB=$(aws ec2 create-security-group --vpc-id "$VPC" --group-name "sg-web-$NN" --description "Web $NN: 80/443 publico, SSH solo admin" --tag-specifications "$(tag security-group "sg-web-$NN")" --query GroupId --output text)
SGBD=$(aws ec2 create-security-group --vpc-id "$VPC" --group-name "sg-bd-$NN" --description "BD $NN: motor y SSH solo desde sg-web" --tag-specifications "$(tag security-group "sg-bd-$NN")" --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id "$SGWEB" --ip-permissions \
  "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0,Description=HTTP}]" \
  "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0,Description=HTTPS}]" \
  "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=$ADMIN_CIDR,Description=SSH-admin}]" >/dev/null
aws ec2 authorize-security-group-ingress --group-id "$SGBD" --ip-permissions \
  "IpProtocol=tcp,FromPort=$DB_PORT,ToPort=$DB_PORT,UserIdGroupPairs=[{GroupId=$SGWEB,Description=BD-desde-web}]" \
  "IpProtocol=tcp,FromPort=22,ToPort=22,UserIdGroupPairs=[{GroupId=$SGWEB,Description=SSH-bastion-web}]" >/dev/null
echo -e "SGWEB=$SGWEB\nSGBD=$SGBD\nADMIN_CIDR=$ADMIN_CIDR" >> "$ESTADO"

paso "Par de llaves ED25519 (cuenta ubuntu inicial)"
KEY="llave-ti3062-$NN"
aws ec2 create-key-pair --key-name "$KEY" --key-type ed25519 --query KeyMaterial --output text > "$DIR/$KEY.pem"
chmod 400 "$DIR/$KEY.pem"
echo "KEY=$KEY" >> "$ESTADO"

paso "AMI Ubuntu Server 24.04"
AMI=$(aws ssm get-parameters --names /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id --query 'Parameters[0].Value' --output text 2>/dev/null || true)
if [[ -z "$AMI" || "$AMI" == "None" ]]; then
  AMI=$(aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)
fi
echo "AMI=$AMI"

paso "Instancia $WEB_HOST ($WEB_IP)"
WEB=$(aws ec2 run-instances --image-id "$AMI" --instance-type "$TIPO_INSTANCIA" --key-name "$KEY" --subnet-id "$PUB" \
  --private-ip-address "$WEB_IP" --security-group-ids "$SGWEB" --associate-public-ip-address \
  --user-data "$(printf '#!/bin/bash\nhostnamectl set-hostname %s\necho "127.0.1.1 %s" >> /etc/hosts\n' "$WEB_HOST" "$WEB_HOST")" \
  --tag-specifications "$(tag instance "$WEB_HOST")" "$(tag volume "vol-$WEB_HOST")" --query 'Instances[0].InstanceId' --output text)
echo "WEB=$WEB" >> "$ESTADO"

paso "Instancia $BD_HOST ($BD_IP) + volumen extra de 2 GB para LUKS"
BD=$(aws ec2 run-instances --image-id "$AMI" --instance-type "$TIPO_INSTANCIA" --key-name "$KEY" --subnet-id "$PRIV" \
  --private-ip-address "$BD_IP" --security-group-ids "$SGBD" --no-associate-public-ip-address \
  --block-device-mappings '[{"DeviceName":"/dev/sdf","Ebs":{"VolumeSize":2,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
  --user-data "$(printf '#!/bin/bash\nhostnamectl set-hostname %s\necho "127.0.1.1 %s" >> /etc/hosts\n' "$BD_HOST" "$BD_HOST")" \
  --tag-specifications "$(tag instance "$BD_HOST")" "$(tag volume "vol-$BD_HOST")" --query 'Instances[0].InstanceId' --output text)
echo "BD=$BD" >> "$ESTADO"

aws ec2 wait instance-running --instance-ids "$WEB" "$BD"

paso "IP elástica para $WEB_HOST (AWS Academy detiene las instancias al cerrar la sesión y la IP automática cambia)"
WEB_EIP=$(aws ec2 allocate-address --domain vpc --tag-specifications "$(tag elastic-ip "eip-$WEB_HOST")" --query AllocationId --output text)
aws ec2 associate-address --instance-id "$WEB" --allocation-id "$WEB_EIP" >/dev/null
WEB_PUB=$(aws ec2 describe-addresses --allocation-ids "$WEB_EIP" --query 'Addresses[0].PublicIp' --output text)
echo -e "WEB_EIP=$WEB_EIP\nWEB_PUB=$WEB_PUB" >> "$ESTADO"

cat <<EOF

✅ Infraestructura creada. IDs guardados en $ESTADO
   $WEB_HOST  pública $WEB_PUB (IP elástica, no cambia entre sesiones)  privada $WEB_IP
   $BD_HOST   privada $BD_IP (sin IP pública)
Llave inicial: $DIR/$KEY.pem  (descárgala de CloudShell: Actions → Download file)

Siguiente: bash $DIR/02-nat-temporal.sh crear   (salida temporal para instalar paquetes en $BD_HOST)
EOF
