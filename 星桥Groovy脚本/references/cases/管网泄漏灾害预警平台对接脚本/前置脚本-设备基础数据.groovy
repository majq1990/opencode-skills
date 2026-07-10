import com.egova.json.utils.JsonUtils

// 读取源系统推送的设备信息
var bodyStr = request.getBody().getString()
if (bodyStr == null || bodyStr.trim() == "") {
    return
}

var source = JsonUtils.deserialize(bodyStr, Map.class)
if (!(source instanceof Map)) {
    request.setBody("[]")
    return
}

// 这里必须替换成现场 IoT 平台的设备类型 ID，未确认前不做假设
def configuredEquipTypeId = null
if (configuredEquipTypeId == null) {
    variables['scriptMsg'] = '请先在前置脚本-设备基础数据.groovy 中配置设备类型ID'
    return 'api_stop'
}

// 字符串判空
def hasText = { value ->
    value != null && String.valueOf(value).trim() != ""
}

// 安全转字符串
def toText = { value ->
    value == null ? null : String.valueOf(value).trim()
}

// 安全转双精度，避免把 BigDecimal 传到后续接口
def toDouble = { value ->
    if (!hasText(value)) {
        return null
    }
    try {
        return Double.parseDouble(String.valueOf(value).trim())
    } catch (Exception ignored) {
        return null
    }
}

def equipCode = toText(source.get("deviceId"))
if (!hasText(equipCode)) {
    variables['scriptMsg'] = 'deviceId为空，停止推送设备基础数据'
    return 'api_stop'
}

def equipName = toText(source.get("deviceName"))
if (!hasText(equipName)) {
    equipName = toText(source.get("address"))
}

def address = toText(source.get("address"))
if (!hasText(address)) {
    address = toText(source.get("remark"))
}

// method=delete 时同步为无效设备，其余情况按有效设备处理
def validFlag = "delete".equalsIgnoreCase(toText(source.get("method"))) ? 0 : 1

// 设备基础数据固定带两个监测项：浓度 + 状态
def iotItem = [
    "uid": equipCode,
    "equipCode": equipCode,
    "equipName": equipName,
    "equipTypeId": configuredEquipTypeId,
    "address": address,
    "x": toDouble(source.get("xLng")),
    "y": toDouble(source.get("yLat")),
    "validFlag": validFlag,
    "fields": [
        [
            "fieldCode": "concentration",
            "fieldName": "浓度",
            "dataType": 1,
            "genAlarmFlag": 1,
            "displayOrder": 1
        ],
        [
            "fieldCode": "alarm_state",
            "fieldName": "状态",
            "dataType": 2,
            "genAlarmFlag": 1,
            "displayOrder": 2
        ]
    ]
]

// 去掉空值字段，避免传无效属性；fields 保留原样
iotItem = iotItem.findAll { entry ->
    entry.value != null && !(entry.value instanceof String && entry.value.trim() == "")
}

request.setBody(JsonUtils.serialize([iotItem]))
