import java.text.SimpleDateFormat
import cn.com.egova.webgis.coordconvert.ConvertTypeConst;
import cn.com.egova.webgis.coordconvert.CoordConvert;
import cn.com.egova.webgis.coordconvert.CoordConvertFactory;
import cn.com.egova.webgis.coordconvert.SingleConvertFactory;
import cn.com.egova.webgis.coordconvert.ConvertStepsFactory;
// 读取请求体
var bodyStr = request.getBody().getString()
if (bodyStr == null || bodyStr.trim() == "") {
    return
}

var root = com.egova.json.utils.JsonUtils.deserialize(bodyStr, Map.class)
def sourceList = root == null ? null : root.get("data")
if (!(sourceList instanceof List)) {
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

// 安全转整数
def toInt = { value ->
    if (!hasText(value)) {
        return null
    }
    try {
        return Integer.parseInt(String.valueOf(value).trim())
    } catch (Exception ignored) {
        return null
    }
}

// 安全转双精度
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

// 安全转安装时间毫秒
def toInstallMillis = { value ->
    if (!hasText(value)) {
        return null
    }
    try {
        def str = String.valueOf(value).trim()
        def sdf = new SimpleDateFormat("yyyy-MM-dd")
        sdf.setLenient(false)
        return sdf.parse(str).getTime()
    } catch (Exception ignored) {
        return null
    }
}

// 坐标转换器：BDMC -> WGS84经纬度
def bdConvert = CoordConvertFactory.getConvert("", "", "bdmc2wgs84ll")
def equipList = []


for (item in sourceList) {
    if (!(item instanceof Map)) {
        continue
    }

    // equipCode 按确认规则仅使用 text_log6v8
    def equipCode = toText(item.get("text_log6v8"))
    if (!hasText(equipCode)) {
        continue
    }

    // 坐标为空则跳过
    def rawX = toDouble(item.get("location_u097mk_longitude"))
    def rawY = toDouble(item.get("location_u097mk_latitude"))
    if (rawX == null || rawY == null) {
        continue
    }

    // 坐标转换失败则跳过
    def xyWgs84 = bdConvert.convertCoord(rawX, rawY)
    if (xyWgs84 == null || xyWgs84.size() < 2) {
        continue
    }

    def address = toText(item.get("detailed_address"))
    def equipName = toText(item.get("equipName"))
    if (!hasText(equipName)) {
        equipName = address
    }
    if (!hasText(equipName)) {
        continue
    }

    def cityCode = toText(item.get("region_u9lwvg_city_name_code"))
    def districtCode = toText(item.get("region_u9lwvg_district_name_code"))
    def streetCode = toText(item.get("region_u9lwvg_street_name_code"))
    def responsibleMobile = toText(item.get("text_4ckjbv"))
    def responsibleName = toText(item.get("user_name"))
    def validFlag =  (toInt(item.get("delete_flag")) == 0) ? 1 : 0
    // 设备基础数据对象（严格按 /api/admin/import 字段口径）
    def iotItem = [
        "uid": toText(item.get("autocode_acp2lh_column_value_k9qJr")),
        "equipCode": equipCode,
        "equipName": equipName,
        "equipTypeId": 41,
        "address": address,
        "x": xyWgs84[0],
        "y": xyWgs84[1],
        "manufacturerName": toText(item.get("heating_company_name")),
        "serialNumber": toText(item.get("text_aqfot7")),
        "installTime": toInstallMillis(item.get("installTime")),
        "cityCode": cityCode,
        "cityName": toText(item.get("region_u9lwvg_city_name")),
        "districtCode": districtCode,
        "districtName": toText(item.get("region_u9lwvg_district_name")),
        "streetCode": streetCode,
        "streetName": toText(item.get("region_u9lwvg_street_name")),
        "validFlag": validFlag,
        "responsibleName":responsibleName,
        "responsibleMobile":responsibleMobile,
        "fields": [
            [
                "fieldCode": "room_temperature",
                "fieldName": "室内温度",
                "fieldUnit": "℃",
                "dataType": 1,
                "genAlarmFlag": 1,
                "displayOrder": 1
            ],
            [
                "fieldCode": "power_status",
                "fieldName": "供电状态",
                "dataType": 2,
                "genAlarmFlag": 1,
                "displayOrder": 2
            ]
        ]
    ]

    // 去掉空值字段，避免传递无效属性
    iotItem = iotItem.findAll { it.value != null && !(it.value instanceof String && it.value.trim() == "") }
    equipList.add(iotItem)
}
// out.println(equipList);

// return 'api_stop';
// // 改写请求体，交给目标接口继续发送
request.setBody(com.egova.json.utils.JsonUtils.serialize(equipList))
