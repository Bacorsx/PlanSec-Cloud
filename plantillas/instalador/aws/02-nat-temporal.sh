#!/usr/bin/env bash
# Salida TEMPORAL a Internet para la subred privada (solo para instalar paquetes en bd-NN).
# Uso: bash 02-nat-temporal.sh crear | eliminar | estado
# El estado final evaluado debe quedar SIN salida: ejecuta "eliminar" apenas termines de instalar.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"; source "$DIR/infra-$NN.env"
export AWS_DEFAULT_REGION=$REGION

case "${1:-}" in
  crear)
    EIP=$(aws ec2 allocate-address --domain vpc --query AllocationId --output text)
    NAT=$(aws ec2 create-nat-gateway --subnet-id "$PUB" --allocation-id "$EIP" \
      --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=nat-temporal-$NN}]" --query NatGateway.NatGatewayId --output text)
    echo "Esperando NAT $NAT (1-3 min)..."; aws ec2 wait nat-gateway-available --nat-gateway-ids "$NAT"
    aws ec2 create-route --route-table-id "$RTPRIV" --destination-cidr-block 0.0.0.0/0 --nat-gateway-id "$NAT" >/dev/null
    echo -e "NAT=$NAT\nEIP=$EIP" >> "$DIR/infra-$NN.env"
    echo "✅ Salida temporal activa. Instala paquetes en $BD_HOST y luego: bash $0 eliminar" ;;
  eliminar)
    aws ec2 delete-route --route-table-id "$RTPRIV" --destination-cidr-block 0.0.0.0/0 2>/dev/null && echo "Ruta 0.0.0.0/0 eliminada de rt-privada-$NN" || echo "rt-privada-$NN ya no tenía ruta a Internet"
    if [[ -n "${NAT:-}" ]]; then
      aws ec2 delete-nat-gateway --nat-gateway-id "$NAT" >/dev/null; echo "Eliminando NAT $NAT..."
      aws ec2 wait nat-gateway-deleted --nat-gateway-ids "$NAT"
      aws ec2 release-address --allocation-id "$EIP" && echo "IP elástica liberada"
      sed -i '/^NAT=/d;/^EIP=/d' "$DIR/infra-$NN.env"
    fi
    echo "✅ Subred privada sin salida a Internet. Evidencia:"; bash "$0" estado ;;
  estado)
    aws ec2 describe-route-tables --route-table-ids "$RTPRIV" --query 'RouteTables[0].Routes[].[DestinationCidrBlock,GatewayId,NatGatewayId,State]' --output table ;;
  *) echo "Uso: $0 crear|eliminar|estado"; exit 1 ;;
esac
