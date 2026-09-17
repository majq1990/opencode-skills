#!/bin/bash

Color_Text() {
    echo -e " \e[0;$2m$1\e[0m"
}

Echo_Red() {
    echo -e "$(Color_Text "$1" "31")"
}

Echo_Green() {
    echo -e "$(Color_Text "$1" "32")"
}

Echo_Yellow() {
    echo -e "$(Color_Text "$1" "33")"
}

Echo_Blue() {
    echo -e "$(Color_Text "$1" "34")"
}

# 根据传入的配置数组，打印交互式选择项
function echo_selections() {
    param_type=$1
    index=1
    for var in $(eval echo '$'"{${param_type}_array[*]}"); do
        desc=$(eval echo '$'"{${param_type}_desc_array[$(($index - 1))]}")
        echo "$index: ${var}    $desc"
        let "index=index+1"
    done

    echo "q: 返回上一级"
}
