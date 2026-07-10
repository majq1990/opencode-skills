import com.egova.json.utils.JsonUtils
import java.text.SimpleDateFormat

// 读取源系统推送的报警信息
var bodyStr = request.getBody().getString()
if (bodyStr == null || bodyStr.trim() == "") {
    return
}

var source = JsonUtils.deserialize(bodyStr, Map.class)
if (!(source instanceof Map)) {
    request.setBody("[]")
    return
}

// 字符串判空
def hasText = { value ->
    value != null && String.valueOf(value).trim() != ""
}

// 安全转字符串
def toText = { value ->
    value == null ? null : String.valueOf(value).trim()
}

// 兼容 long 时间戳和 yyyy-MM-dd HH:mm:ss 字符串
def toMillis = { value ->
    if (value == null) {
        return null
    }
    if (value instanceof Number) {
        return ((Number) value).longValue()
    }
    def str = String.valueOf(value).trim()
    if (str == "") {
        return null
    }
    try {
        return Long.parseLong(str)
    } catch (Exception ignored) {
    }
    try {
        def cleanTimeStr = str.replace('T', ' ').replace('Z', '').take(19)
        def sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
        return sdf.parse(cleanTimeStr).getTime()
    } catch (Exception ignored) {
        return null
    }
}

def equipCode = toText(source.get("deviceId"))
if (!hasText(equipCode)) {
    variables['scriptMsg'] = 'deviceId为空，停止推送报警实时数据'
    return 'api_stop'
}

def alarmType = toText(source.get("alarmType"))
if (!hasText(alarmType)) {
    variables['scriptMsg'] = 'alarmType为空，停止推送报警实时数据'
    return 'api_stop'
}

def recordTime = toMillis(source.get("alarmDate"))
if (recordTime == null) {
    recordTime = System.currentTimeMillis()
}

def fieldItem = [
    "fieldCode": "alarm_state",
    // alarm_state 是枚举型监测项，按要求把 alarmType 推到 detail
    "detail": alarmType
]

// 如果现场还需要把 alarmState 转成 alarm 标记，可按确认后的规则补充
def exchangeData = [[
    "equipCode": equipCode,
    "time": recordTime,
    "data": [fieldItem]
]]

request.setBody(JsonUtils.serialize(exchangeData))
