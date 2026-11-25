#!/usr/bin/env bash
# Cifrado en reposo: volumen LUKS2 montado en /respaldos (destino de los respaldos de la BD).
# Uso: sudo bash 02-luks-respaldos.sh [dispositivo]      (por defecto detecta el disco extra de 2 GB)
#      sudo bash 02-luks-respaldos.sh abrir | cerrar     (tras un reinicio hay que abrirlo a mano)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/../config.env"
[[ $EUID -eq 0 ]] || { echo "Ejecuta con sudo"; exit 1; }
MAP="respaldos_$NN"; ESTADO=/etc/ti3062-luks-dispositivo
mkdir -p /etc/ti3062 2>/dev/null || true

case "${1:-}" in
  abrir)  DEV=$(cat $ESTADO); cryptsetup open "$DEV" "$MAP"; mount /dev/mapper/$MAP /respaldos; df -h /respaldos; exit 0 ;;
  cerrar) umount /respaldos; cryptsetup close "$MAP"; echo "Volumen cerrado"; lsblk -f; exit 0 ;;
esac

DEV="${1:-}"
if [[ -z "$DEV" ]]; then
  RAIZ=$(lsblk -no PKNAME "$(findmnt -no SOURCE /)")
  DEV=$(lsblk -dpno NAME,TYPE,SIZE | awk -v r="/dev/$RAIZ" '$2=="disk" && $1!=r {print $1}' | head -1)
fi
if [[ -z "$DEV" ]]; then
  echo "No hay disco extra; se usará un contenedor cifrado en archivo (1 GB)."
  mkdir -p /var/lib/ti3062; DEV=/var/lib/ti3062/respaldos.luks
  [[ -f $DEV ]] || fallocate -l 1G $DEV
fi
if [[ -b "$DEV" ]]; then
  if [[ -n "$(lsblk -no FSTYPE "$DEV" | tr -d '[:space:]')" || $(lsblk -no NAME "$DEV" | wc -l) -gt 1 ]] || findmnt -S "$DEV" >/dev/null; then
    echo "⛔ $DEV ya tiene datos, particiones o está montado. Usa el disco vacío de 2 GB (lsblk -f)."; exit 1
  fi
fi
lsblk -f; echo; echo "Se cifrará: $DEV  (se BORRARÁ su contenido)"
read -rp "Escribe SI para continuar: " OK; [[ $OK == SI ]] || exit 1

echo "Define la frase de paso del volumen (guárdala en un lugar seguro; NO la captures):"
cryptsetup luksFormat -q --verify-passphrase --type luks2 --cipher aes-xts-plain64 --key-size 512 --hash sha256 "$DEV"
cryptsetup open "$DEV" "$MAP"
mkfs.ext4 -q -L respaldos /dev/mapper/$MAP
mkdir -p /respaldos && mount /dev/mapper/$MAP /respaldos
chown root:root /respaldos && chmod 700 /respaldos
echo "$DEV" > $ESTADO
echo "== Evidencia"; cryptsetup luksDump "$DEV" | head -20; lsblk -f; df -h /respaldos
echo -e "\n✅ /respaldos cifrado con LUKS2. Tras reiniciar: sudo bash $0 abrir"
