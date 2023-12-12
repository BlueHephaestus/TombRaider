#!/bin/bash

# Function to get devices
get_devices() {
  # Return all devices that are not loop devices, only returning the full device, i.e., sda, sdb, etc. not partitions.
  devices=()
  while read -r line; do
    if [[ $line == *'disk'* && $line != *'loop'* ]]; then
      devices+=($(echo "$line" | awk '{print $1}'))
    fi
  done < <(lsblk)
  echo "${devices[@]}"
}
get_device_name() {
  # Should be unqualified device name, i.e. sda1
  device="/dev/$(basename $1)"

  # Get device info using udevadm
  udev_output=$(udevadm info --query=all "$device")

  # Extract ID_BUS, ID_VENDOR, ID_MODEL, ID_SERIAL_SHORT
  bus=$(echo "$udev_output" | grep -oP 'E: ID_BUS=\K.*')
  vendor=$(echo "$udev_output" | grep -oP 'E: ID_VENDOR=\K.*')
  model=$(echo "$udev_output" | grep -oP 'E: ID_MODEL=\K.*')
  serial=$(echo "$udev_output" | grep -oP 'E: ID_SERIAL_SHORT=\K.*')
  #minor=$(echo "$udev_output" | grep -oP 'E: MINOR=\K.*')
  #usec=$(echo "$udev_output" | grep -oP 'E: USEC_INITIALIZED=\K.*')

  # Only reliable way to get an actual uuid when sd card is in usb adapter in a usb hub, afaik.
  uuid=$(head "$device" | md5sum | cut -c -16)

  # Get ID_FS_LABEL if exists
  label=$(echo "$udev_output" | grep -oP 'E: ID_FS_LABEL=\K.*')
  if [[ -n $label ]]; then
    # If it exists, use it as the device name
    echo "$label"
    return
  fi

  # Get the total size of the device
  size=$(lsblk -d -o SIZE -n "$device" )
  unit="${size: -1}"  # Get the last character (unit)
  value="${size:0:${#size}-1}"  # Get all characters except the last (numeric part)
  value=$(echo "($value+0.5)/1" | bc)
  # if unit is not terabyte, round the value up to nearest power of two and put back into size string
  # otherwise just round up and leave it
  if [[ $unit != "T" ]]; then
    power_of_2=1
    while [[ "$power_of_2" -lt "$value" ]]; do
      power_of_2=$((power_of_2 * 2))
    done
    value="$power_of_2"
  fi
  size="$value$unit"

  # Format the extracted values (only use 4 chars for serial to avoid too long)
  formatted_name="${bus^^}_${size}_${vendor}_${model}_${uuid}"

  # Remove spaces and special characters
  formatted_name=$(echo "$formatted_name" | sed 's/[^a-zA-Z0-9_]//g')

  # Return the formatted name
  echo "$formatted_name"
  return
}
done=()
excluded=("sda" "sdb" "sdc" "sdd" "nvme0n1")
try_main=$1

#      # Mount device
#      echo "Mounting /dev/$device"
#      mkdir -p "/mnt/$device"
#      mount "/dev/$device" "/mnt/$deviceo
alert() {
  ffplay -nodisp -hide_banner -loop 999999 -loglevel warning /home/blue/alarm.mp3 &
  ffplay_pid=$!
  read -r -s -n 1 -p "Press any key to continue..."
  echo ""

  kill $ffplay_pid
}

raid_device(){
  device=$1
  device_name=$2
  device_path=$3

  original_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  udev_output=$(udevadm info --query=all "/dev/$device")

  # Extract ID_PATH to use for getting device port
  id_path=$(echo "$udev_output" | grep -oP 'E: ID_PATH=\K.*')
  device_port=$(python3.9 $original_dir/parse_usb_hub_uuid.py $id_path)

  device_path="/dev/$device"
  echo "Port $device_port: Device Name: $device_name ($device_path)"



  # Get the number of partitions on this device
  fs_partitions=$(($(mmls -a "$device_path" | wc -l) - 5))
#      if [[ $fs_partitions -lt 0 ]]; then
#        echo "No Filesystem Partitions Found on $device_name. Skipping..."
#      fi
  echo "Port $device_port: Found $fs_partitions Possible Filesystem Partitions on $device_name."

  # Create target directory
  mkdir -p "./$device_name"
  cd "./$device_name"

  if [[ $fs_partitions -lt 0 ]]; then
      echo -e "\tPort $device_port: Running Testdisk to attempt to recover files on $device_name ($device_path)"
      testdisk /log /cmd "$device_path" advanced,list,filecopy &> /dev/null
  else
      partitions=$(sudo fdisk -l $device_path | grep -E '^/dev/' | awk '{print $1}')

    while IFS= read -r line; do
      # Create subdirectory for partition
      partition_name=$(get_device_name "$line")

      mkdir -p "./$partition_name"
      cd "./$partition_name"
      echo -e "\tPort $device_port: Running Testdisk to attempt to recover files on $device_name ($line: $partition_name)"

      # Copy from this partition to target directory (current directory)
      testdisk /log /cmd "$device_path" advanced,"${line: -1}",list,filecopy &> /dev/null
      cd ..
    done <<< "$partitions"
  fi
  echo "Port $device_port: Done with $device_name ($device_path)"
  cd ..
}
while true; do
  devices=($(get_devices))
  for device in "${devices[@]}"; do
    device_name=$(get_device_name $device)
    if [[ ! " ${excluded[@]} " =~ " $device " && ! " ${done[@]} " =~ "$device_name" ]]; then

      raid_device $device $device_name $device_path &
      # Don't do this device again
      done+=("$device_name")
      #echo "Done with $device_name"
      #alert
    fi
  done
  sleep 1
  # Wait for user to press enter to continue if there was a device found
#  if [[ $i -gt 1 ]]; then
#    read -r -s -n 1 -p "Press any key to continue..."
#    echo ""
#  fi
done
