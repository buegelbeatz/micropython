#!/bin/bash

subcommand="${1}"

check_installation(){
    missing=""
    
    [ "$(which mpy-cross 2>/dev/null)" == "" ] && \
      echo "Please install mpy-cross: https://ports.macports.org/port/mpy-cross/" && \
      missing="1"
    [ "$(which rshell 2>/dev/null)" == "" ] && \
      echo "Please install rshell: https://github.com/dhylands/rshell" && \
      missing="1"
    [ "$(which esptool.py 2>/dev/null)" == "" ] && \
      echo "Please install esptool.py: https://docs.espressif.com/projects/esptool/en/latest/esp32/installation.html" && \
      missing="1"
    [ "${missing}" != "" ] && \
    exit 1
}

help(){
    echo "
subcommands:
    ./mp.sh info [<usb-connection>] - try to connect to board and collect infos about the connected board
    ./mp.sh deploy <folder> [<usb-connection>] - rsync local files in ./src/<folder> to connected board
    ./mp.sh repl <usb-connection> - repl-connection to connected board
    ./mp.sh install <firmware> [<usb-connection>] - if url download first otherwise pick file from ./firmware/ and upload firmware
                                 checkout https://micropython.org/download/ for newest versions"
}

get_connected_devices(){
  device="${1}"
  [ ! -z "${device}" ] && \
    echo "${device}" && \
    return 0
  devices="$(rshell -l|grep "@/dev/cu."|grep '\(USB Serial Device\|usbserial\-\|SLAB_USBtoUART\)'|sed 's|^.*@||g;')"
  num_devices=$(echo "$devices"|wc -l | sed 's/[^0-9]//g;')
  if [ "$num_devices" != "1" ];then
    echo "Please select an usb connection:"
    echo "${devices}"
    exit 1
  else
    echo "$devices" | sed 's/\r//g;'
    return 0
  fi
}

get_processor(){
  device="${1}"
  device=$(get_connected_devices "${device}")
  result=$?
  [ ! -z "${device}" ] && \
    esptool.py --port ${device} flash_id 2>/dev/null | \
    grep 'chip type' | \
    grep -v 'Unsupported' | \
    sed 's/^.* //g;' | \
    tr '[:upper:]' '[:lower:]' && \
    return 0
  return 1
}

_firmware_error(){
  folder="${1}"
  previous_folder=$(pwd)
  mkdir -p ${folder}/firmware 2>/dev/null
  cd ${folder}/firmware
  echo "Select a firmware or download a firmware via URL, see https://micropython.org/download/ : "
  ls 
  cd ${previous_folder}

}

get_info(){
  device="${1}"
  device=$(get_connected_devices "${device}")
  result=$?
  [ ! -z "${device}" ] && \
    esptool.py --port ${device} flash_id 2>/dev/null && \
    return 0
  return 1
}

get_firmware(){
    firmware="${1}"
    mkdir -p $(dirname ${0})/firmware 2>/dev/null
    [ "${firmware}" = "" ] && _firmware_error $(dirname ${0}) && return 1
    local_file_path=$(dirname ${0})/firmware/${firmware}
    if [ ! -f ${local_file_path} ] && [ ! -d ${local_file_path} ] && [ "$(echo "${firmware}" | grep -E '^https?://')" != "" ] ;then
      new_firmware=$(dirname ${0})/firmware/$(basename ${firmware})
      curl ${firmware} > ${new_firmware} 2>/dev/null
      [ $(cat ${new_firmware} | wc -l) -eq 0 ] && _firmware_error $(dirname ${0}) && return 1
      firmware=${new_firmware}
      local_file_path=$(dirname ${0})/firmware/${firmware}
    fi
    [ -f ${local_file_path} ] || [ -d ${local_file_path} ] && echo "${local_file_path}" && return 0
    _firmware_error $(dirname ${0}) && return 1
}

_esp32(){
  # esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 esp32-20190125-v1.10.bin
  device="${1}"
  firmware="${2}"
  echo "we are in esp32-s3 mode..." 
  esptool.py \
      --chip esp32 \
      --port ${device} \
      --baud 460800 \
      write_flash \
      -z 0x1000 \
      ${firmware}
}

_esp32_s3(){
  # esptool.py --chip esp32s3 --port /dev/ttyACM0 erase_flash
  # esptool.py --chip esp32s3 --port /dev/ttyACM0 write_flash -z 0 board-20210902-v1.17.bin
  device="${1}"
  firmware="${2}"
  echo "we are in esp32-s3 mode..." 
  esptool.py \
      --chip esp32s3 \
      --port ${device} \
      --baud 460800 \
      --after hard_reset \
      write_flash \
      --flash_size detect \
      -z 0x0 \
      ${firmware}
}

_esp32_c3(){
    # esptool.py --chip esp32c3 --port /dev/ttyUSB0 erase_flash
    # esptool.py --chip esp32c3 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x0 esp32c3-20220117-v1.18.bin
    # esptool.exe --chip esp32c3 --port COM10 --baud 921600 --before default_reset --after hard_reset --no-stub  write_flash --flash_mode dio --flash_freq 80m 0x0 esp32c3-usb-20230426-v1.20.0.bin
    # https://wiki.seeedstudio.com/XIAO_ESP32C3_MicroPython/
  device="${1}"
  firmware="${2}"
  echo "we are in esp32-c3 mode..."
  esptool.py \
      --port ${device} \
      --chip esp32c3 \
      --baud 115200 \
      write_flash \
      -z 0x0 \
      ${firmware}
}

_esp8266(){
  device="${1}"
  firmware="${2}"
  echo "we are in standard esp8266 mode..."
  esptool.py \
      --port ${device} \
      write_flash \
      --flash_mode dio \
      --flash_size 4MB \
      0x0 \
      ${firmware}
}


install(){
    firmware=$(get_firmware ${1})
    [ $? = 1 ] && echo "${firmware}" && exit 1
    device="${2}"
    [ -z "${firmware}" ] || ([ ! -f "${firmware}" ] && [ ! -d "${firmware}" ]) && \
        echo "No firmware specified." && exit 1
    device=$(get_connected_devices "${device}")
    board=$(get_processor "${device}")
    [ -z "${device}" ] && echo "Please connect device first." && exit 1
    [ -z "${board}" ] && echo "Could not get board information." && exit 1
    [ "$(echo "${firmware}" | grep "${board}")" = "" ] && \
        echo "Check if firmware '${firmware}' fit to board '${board}' (maybe rename it)" && \
        exit 1
    # TODO: Download 

    echo "Writing device now..."

    [ "${board}" = "esp32-s3" ] && \
        _esp32_s3 "${device}" "${firmware}" && \
        done="1"

    [ "${board}" = "esp32-c3" ] && \
        _esp32_c3 "${device}" "${firmware}" && \
        done="1"

    [ "${board}" = "esp8266" ] && \
        _esp8266 "${device}" "${firmware}" && \
            done="1"

    [ "${board}" = "esp32" ] && \
        _esp32 "${device}" "${firmware}" && \
            done="1"

    [ -z "${done}" ] && \
      echo "Please check script implementation for board '${board}'." && exit 1
    declare -i success=$(rshell connect serial --baud 460800 ${device} | grep root | grep directories | grep /boot.py/ | wc -l)
    [ ${success} -eq 0 ] && echo "Something went wrong uploading firmware" && exit 1
    return 0
}

_compile_files(){
  source="${1}"
  echo
  echo "*** Compiling python files in '${source}'"
  files=$(find ${source} | grep -E '\.(py|html|css|js|ico)$')
  echo "found $(echo "${files}" | \
    wc -l | \
    sed 's/[^0-9]*//g;') files in '${source}' which needs to be checked."
  changed_files=""
  for file in ${files};do
    new_md5="$(cat ${file} | md5)"
    if [ ! -f ${file}.md5 ] || [ "${new_md5}" != "$(cat ${file}.md5)" ] ; then 
      echo "Compile '${file}'..."
      # python files
      if [ "$(echo "${file}" | grep '\.py$')" != "" ] ; then
        mpy_file="$(echo ${file} | sed 's/\.py/.mpy/g;')"
        rm ${mpy_file} 2>/dev/null
        mpy-cross ${file} 
        [ ! -f ${mpy_file} ] && exit 1
        changed_files="${changed_files} ${file}"
      fi
      # static file which could be compressed
      [ "$(echo "${file}" | grep -E '\.(css|js|ico)$' | grep 'static/')" != "" ] && \
        gzip --force ${file} 2>/dev/null && \
        changed_files="${changed_files} ${file}"
      echo "${new_md5}" > ${file}.md5
    fi
  done
  echo "$(echo ${changed_files} | wc -w| sed 's/[^0-9]*//g;') files in '${source}' are recompiled"
}

_update_links(){
  echo "*** Update links"
  source="${1}"
  destination="${2}"
  echo
  echo "*** Update link structure in '${destination}', pick files from '${source}'"
  existing_links=$(find ${destination} -type l)
  required_links=$(cat ${destination}/required.txt 2>/dev/null | \
    sed 's/#.*$//g;' | \
    grep '[^ ]') # ignore empty lines or comments
  for required_link in ${required_links}; do 
    echo -n -e "Checking '${required_link}'                            \r"
    [ ! -f ${source}/${required_link} ] && \
      echo -e "\n'${source}/${required_link}' does not exist, please check '${destination}/required.txt'" && \
      exit 1
    [ ! -f ${destination}/${required_link} ] && \
      echo -e "\nCreate missing link '${destination}/${required_link}'" && \
      mkdir -p $(dirname ${destination}/${required_link}) && \
      ln -s $(echo "${source}/${required_link}" | \
        sed "s|^./|$(seq $(echo "${source}/${required_link}" | \
        tr -cd '/' | wc -c) | sed "s|.*|../|g;" | tr -d '\n')|g;") \
        ${destination}/${required_link}
  done
  echo -e "\nCheck for files which could be removed on device"
  for existing_link in ${existing_links}; do
    found="0"
   for required_link in ${required_links}; do
      [ "${existing_link}" = "${destination}/${required_link}" ] && found="1" && break
   done
   [ "${found}" = "0" ] && echo -e "\nRemove link '${existing_link}'" && rm ${existing_link} 2>/dev/null
  done 
}

_prepare_files(){
  source="${1}"
  destination="${2}" 
  echo "*** Copy over files to '${destination}'"
  mkdir -p ${destination} 2>/dev/null
  rsync --recursive --checksum --copy-links ${source}/ ${destination}/
}

_collect_files(){
  source="${1}"
  destination="${2}" 
  echo "*** Copy over files to '${destination}' and cleanup" 
  mkdir -p ${destination} 2>/dev/null
  rsync --recursive --archive ${source}/ ${destination}/  

  # remove the not required files

  find ${destination} | grep -E '\.(py|md5|md|DS_Store)$' | grep -Ev '(main|boot)\.py$' | xargs rm 
  find ${destination} | grep -E '(main|boot)\.mpy$' | xargs rm 
  find ${destination} | grep -E '/static/[^/]+\.(js|css|ico)$' | xargs rm
  find ${destination} | grep '__pycache__' | xargs rm -rf
}

deploy(){
    folder="${1}"
    device="${2}"
    echo
    echo "*** Check setup"
    [ -z "${folder}" ] && echo "Please specify subfolder in ./src." && \
      ls ./src && \
      exit 1

    src_folder=$(dirname ${0})/src/${folder}
    [ ! -d ${src_folder} ] && echo "Check folder '${src_folder}'." && exit 1
    prepare_folder=$(dirname ${0})/build/${folder}/tmp
    output_folder=$(dirname ${0})/build/${folder}/output
    backup_folder=$(dirname ${0})/build/${folder}/backup
    mkdir -p ${backup_folder} 2>/dev/null
    lib_folder=$(dirname ${0})/lib

    _update_links ${lib_folder} ${src_folder}
    _prepare_files ${src_folder} ${prepare_folder}
    _compile_files ${prepare_folder}
    _collect_files ${prepare_folder} ${output_folder}
    
    current_folder=$(pwd)
    device=$(get_connected_devices "${device}")
    [ $? -eq 1 ] || [ -z "${device}" ] && echo "no device connected ...${device}" && exit 1
    board=$(get_processor "${device}")
    [ -z "${board}" ] && echo "Check if micropython is installed." && exit 1

    # experimental section

    new_files=$(diff --brief --recursive ${output_folder} ${backup_folder} | grep 'Only' | sed 's/^Only in //g;s/: /\//g;')
    changed_files=$(diff --brief --recursive ${output_folder} ${backup_folder} | grep 'Files' |cut -d " " -f 2)
    for newfile in ${new_files};do 
      [ -f ${newfile} ] && sub_path=$( echo "${newfile}" | sed 's#^.*/output/##g;') && echo "cp -f ${sub_path} /pyboard/${sub_path}"
      [ -d ${newfile} ] && sub_path=$( echo "${newfile}" | sed 's#^.*/output/##g;') && echo "cp -rf ${sub_path} /pyboard/${sub_path}"
    done
    for newfile in ${changed_files};do 
      sub_path=$( echo "${newfile}" | sed 's#^.*/output/##g;') && echo "cp -f ${sub_path} /pyboard/${sub_path}"
    done

    #################################################

    cd ${output_folder} 

    # create_folders=""
    # for i in 1 2 3 4;do
    # create_folders="${create_folders}\n$(find . -type d -depth ${i})"
    # done
    # create_folder_structure=$(echo -e "${create_folders}" | sed 's#^ *\./#mkdir #g;')

    export RSHELL_PORT=${device}
    echo "Upload files ..."
    rshell --port ${device} --buffer-size 30 -a  --file <( echo "echo" ; \
      echo "rsync --mirror --all . /pyboard" ) 
    cd ${current_folder}
    rm -rf ${backup_folder}/ 2>/dev/null
    cp -r ${output_folder}/ ${backup_folder}/ 2>/dev/null
    rshell --port ${device} --buffer-size 30 -a --file <( echo "echo" ; \
      echo "ls /pyboard" ; \
      echo "echo" ; \
      echo "repl")
    

    # make a backup of sent files


}

repl(){
    device="${1}"
    device=$(get_connected_devices "${device}")
    [ $? -eq 1 ] || [ -z "${device}" ] && echo "${device}" && exit 1
    board=$(get_processor "${device}")
    [ -z "${board}" ] && echo "Check if micropython is installed." && exit 1  
    echo "*** Check setup on port '${device}' board '${board}'"
    RSHELL_PORT=${device} \
    rshell \
      --baud 115200 \
      --suppress-reset \
      --buffer-size 2048 \
      --file <( echo "echo" ; echo "ls -la /pyboard" ; echo "echo" ; echo "repl")
}

check_installation
[ -z "${subcommand}" ] && help && exit 0 
[ "${subcommand}" = "deploy" ] && deploy ${2} ${3} && exit 0
[ "${subcommand}" = "install" ] && install ${2} ${3} && exit 0
[ "${subcommand}" = "repl" ] && repl ${2} && exit 0
[ "${subcommand}" = "info" ] && get_info ${2} && exit 0
help