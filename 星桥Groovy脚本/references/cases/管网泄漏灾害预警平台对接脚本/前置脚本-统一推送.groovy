import org.springframework.http.HttpHeaders
import com.egova.api.util.http.HttpUtils
import com.egova.json.utils.JsonUtils
import java.text.SimpleDateFormat

// 统一前置脚本：
// 1. 建议挂在空接口 dex-api/free/req-resp
// 2. 自动识别基础数据、浓度实时数据、报警实时数据
// 3. 在前置脚本内主动推送到 IoT 对应接口

// ========== 配置区：以下 IP、端口、鉴权参数、设备类型 ID 需要按现场替换 ==========
var config = [
    tokenUrl        : 'http://10.161.133.68:10050/usercenter-api/oauth/extras/token',
    clientId        : 'usercenter',
    clientSecret    : '54ddc335f9',
    iotBaseUrl      : 'http://173.16.0.17:8084/iot-api',
    basicEquipTypeId: null
]

// ========== 工具方法区 ==========
var hasText = { value ->
    value != null && String.valueOf(value).trim() != ""
}

var toText = { value ->
    value == null ? null : String.valueOf(value).trim()
}

// 安全转双精度，避免 BigDecimal
var toDouble = { value ->
    if (!hasText(value)) {
        return null
    }
    try {
        return Double.parseDouble(String.valueOf(value).trim())
    } catch (Exception ignored) {
        return null
    }
}

// 兼容 long 时间戳和 yyyy-MM-dd HH:mm:ss / ISO 时间字符串
var toMillis = { value ->
    if (value == null) {
        return null
    }
    if (value instanceof Number) {
        return ((Number) value).longValue()
    }
    var str = String.valueOf(value).trim()
    if (str == "") {
        return null
    }
    try {
        return Long.parseLong(str)
    } catch (Exception ignored) {
    }
    try {
        var cleanTimeStr = str.replace('T', ' ').replace('Z', '').take(19)
        var sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
        return sdf.parse(cleanTimeStr).getTime()
    } catch (Exception ignored) {
        return null
    }
}

// ========== 主逻辑区 ==========
try {
    var bodyStr = request.getBody().getString()
    if (bodyStr == null || bodyStr.trim() == "") {
        variables['pushResult'] = [
            success: false,
            message: '请求体为空'
        ]
        return
    }

    var source = JsonUtils.deserialize(bodyStr, Map.class)
    if (!(source instanceof Map)) {
        variables['pushResult'] = [
            success: false,
            message: '请求体不是合法的 JSON 对象'
        ]
        return
    }

    // 获取 IoT token
    var tokenParams = [
        'url': config.tokenUrl,
        'clientId': config.clientId,
        'clientSecret': config.clientSecret
    ]
    var iottoken = tokenStore.load('default', tokenParams)?.value
    if (!hasText(iottoken)) {
        variables['pushResult'] = [
            success: false,
            message: '获取 iot token 失败'
        ]
        return
    }
    variables['iottoken'] = iottoken

    var targetPath = null
    var pushBody = null
    var scene = null

    // 报警信息：优先识别，避免和其他场景冲突
    if (source.containsKey('alarmType') || source.containsKey('alarmDate')) {
        scene = 'alarm'
        var equipCode = toText(source.get('deviceId'))
        var alarmType = toText(source.get('alarmType'))
        var recordTime = toMillis(source.get('alarmDate'))

        if (!hasText(equipCode)) {
            variables['pushResult'] = [
                success: false,
                scene  : scene,
                message: 'deviceId为空，不能推送报警实时数据'
            ]
            return
        }
        if (!hasText(alarmType)) {
            variables['pushResult'] = [
                success: false,
                scene  : scene,
                message: 'alarmType为空，不能推送报警实时数据'
            ]
            return
        }
        if (recordTime == null) {
            recordTime = System.currentTimeMillis()
        }

        targetPath = '/api/exchange/equip/list'
        pushBody = [[
            'equipCode': equipCode,
            'time': recordTime,
            'data': [[
                'fieldCode': 'alarm_state',
                // alarmType 按要求推送到 detail
                'detail': alarmType
            ]]
        ]]
    }
    // 设备上传数据：按 list 判断
    else if (source.get('list') instanceof List) {
        scene = 'realtime'
        var equipCode = toText(source.get('deviceId'))
        if (!hasText(equipCode)) {
            variables['pushResult'] = [
                success: false,
                scene  : scene,
                message: 'deviceId为空，不能推送浓度实时数据'
            ]
            return
        }

        var exchangeList = []
        for (item in source.get('list')) {
            if (!(item instanceof Map)) {
                continue
            }

            var concentration = toDouble(item.get('concentration'))
            if (concentration == null) {
                continue
            }

            var recordTime = toMillis(item.get('recordTime'))
            if (recordTime == null) {
                recordTime = System.currentTimeMillis()
            }

            exchangeList.add([
                'equipCode': equipCode,
                'time': recordTime,
                'data': [[
                    'fieldCode': 'concentration',
                    'value': concentration
                ]]
            ])
        }

        if (exchangeList.isEmpty()) {
            variables['pushResult'] = [
                success: false,
                scene  : scene,
                message: 'list 中未取到 concentration，不能推送浓度实时数据'
            ]
            return
        }

        targetPath = '/api/exchange/equip/list'
        pushBody = exchangeList
    }
    // 设备基础数据
    else if (source.containsKey('deviceId')) {
        scene = 'basic'
        if (config.basicEquipTypeId == null) {
            variables['pushResult'] = [
                success: false,
                scene  : scene,
                message: '请先在脚本中配置 basicEquipTypeId 设备类型 ID'
            ]
            return
        }

        var equipCode = toText(source.get('deviceId'))
        var equipName = toText(source.get('deviceName'))
        var address = toText(source.get('address'))
        if (!hasText(address)) {
            address = toText(source.get('remark'))
        }

        if (!hasText(equipCode)) {
            variables['pushResult'] = [
                success: false,
                scene  : scene,
                message: 'deviceId为空，不能推送设备基础数据'
            ]
            return
        }
        if (!hasText(equipName)) {
            equipName = equipCode
        }
        if (!hasText(address)) {
            address = equipName
        }

        // method=delete 视为无效设备，其余视为有效
        var validFlag = 'delete'.equalsIgnoreCase(toText(source.get('method'))) ? 0 : 1

        var equipItem = [
            'uid': equipCode,
            'equipCode': equipCode,
            'equipName': equipName,
            'equipTypeId': config.basicEquipTypeId,
            'address': address,
            'x': toDouble(source.get('xLng')),
            'y': toDouble(source.get('yLat')),
            'validFlag': validFlag,
            'fields': [
                [
                    'fieldCode': 'concentration',
                    'fieldName': '浓度',
                    'fieldUnit': '',
                    'dataType': 1,
                    'genAlarmFlag': 1,
                    'displayOrder': 1
                ],
                [
                    'fieldCode': 'alarm_state',
                    'fieldName': '状态',
                    'dataType': 2,
                    'genAlarmFlag': 1,
                    'displayOrder': 2
                ]
            ]
        ]

        equipItem = equipItem.findAll { entry ->
            entry.value != null && !(entry.value instanceof String && entry.value.trim() == "")
        }

        targetPath = '/api/admin/import'
        pushBody = [equipItem]
    }
    else {
        variables['pushResult'] = [
            success: false,
            message: '未识别到支持的数据格式'
        ]
        return
    }

    // 保存本次识别结果，便于后置脚本查看
    variables['pushScene'] = scene
    variables['pushRequest'] = pushBody
    variables['pushTargetPath'] = targetPath

    // 主动推送到 IoT 平台
    var response = HttpUtils.postJson(
        config.iotBaseUrl + targetPath,
        pushBody,
        String.class,
        { HttpHeaders headers ->
            headers.set('Content-Type', 'application/json')
            headers.set('Authorization', 'bearer ' + variables['iottoken'])
        }
    )

    variables['pushResult'] = [
        success   : response != null,
        scene     : scene,
        targetPath: targetPath,
        statusCode: response == null ? null : response.statusCode.value(),
        response  : response == null ? null : response.getBody()
    ]
} catch (Exception e) {
    variables['pushResult'] = [
        success: false,
        message: '脚本执行异常: ' + e.getMessage()
    ]
}
