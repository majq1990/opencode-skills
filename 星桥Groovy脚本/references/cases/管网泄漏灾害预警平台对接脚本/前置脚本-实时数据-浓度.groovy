import com.egova.json.utils.JsonUtils
import java.text.SimpleDateFormat

// 读取源系统推送的设备监测数据
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

// 安全转双精度，避免 BigDecimal
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
    variables['scriptMsg'] = 'deviceId为空，停止推送浓度实时数据'
    return 'api_stop'
}

def dataList = []
def sourceList = source.get("list")
if (sourceList instanceof List) {
    for (item in sourceList) {
        if (!(item instanceof Map)) {
            continue
        }

        def concentration = toDouble(item.get("concentration"))
        if (concentration == null) {
            continue
        }

        // 每条 list 数据单独转换成一条实时记录，时间取 recordTime
        def recordTime = toMillis(item.get("recordTime"))
        if (recordTime == null) {
            recordTime = System.currentTimeMillis()
        }

        dataList.add([
            "equipCode": equipCode,
            "time": recordTime,
            "data": [
                [
                    "fieldCode": "concentration",
                    "value": concentration
                ]
            ]
        ])
    }
}

if (dataList.isEmpty()) {
    variables['scriptMsg'] = '实时数据中未取到 concentration，停止推送'
    return 'api_stop'
}

request.setBody(JsonUtils.serialize(dataList))
